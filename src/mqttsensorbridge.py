#!/home/viam/dev/current_monitor/venv/bin/python

import asyncio
import json
import paho.mqtt.client as mqtt
from typing import Any, ClassVar, Dict, Mapping, Optional, Sequence
from viam.components.sensor import Sensor
from viam.logging import getLogger
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.resource.registry import Registry, ResourceCreatorRegistration
from viam.resource.types import Model, ModelFamily
from viam.utils import ValueTypes, struct_to_dict

LOGGER = getLogger(__name__)

class MQTTSensorBridge(Sensor):
    MODEL: ClassVar[Model] = Model(ModelFamily("chris", "iot-sensor"), "mqttsensorbridge")

    temp_value: float = 0.0  # Store the temperature value

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        LOGGER.info("MODULE VALIDATE")
        return []

    @classmethod
    def new(cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]) -> "MQTTSensorBridge":
        sensor = cls(config.name)
        sensor.reconfigure(config, dependencies)
        LOGGER.info("MODULE NEW")
        sensor.setup_mqtt()  # Set up MQTT when the sensor is created
        return sensor

    def __init__(self, name: str):
        super().__init__(name)

    def reconfigure(self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]):
        
        # Configure broker
        try:
            broker = config.attributes.fields.get("broker", {}).string_value
            if broker is None:
                raise ValueError("MQTT broker input needed")
            self.broker=broker
            LOGGER.info(f"broker: {self.broker}")
        except (ValueError, TypeError) as e:
            raise ValueError("broker must be string", e)

        try:
            self.username = config.attributes.fields.get("username", {}).string_value
            if not self.username:
                raise ValueError("Username must be provided")
        except (ValueError, TypeError) as e:
            raise ValueError("Error setting username", e)

        try:
            self.password = config.attributes.fields.get("password", {}).string_value
            if not self.password:
                raise ValueError("Password must be provided")
        except (ValueError, TypeError) as e:
            raise ValueError("Error setting password", e)

        try:
            self.tenant_id = config.attributes.fields.get("tenant_id", {}).string_value
            if not self.tenant_id:
                raise ValueError("Tenant ID must be provided")
        except (ValueError, TypeError) as e:
            raise ValueError("Error setting tenant_id", e)

        try:
            self.app_id = config.attributes.fields.get("app_id", {}).string_value
            if not self.app_id:
                raise ValueError("App ID must be provided")
        except (ValueError, TypeError) as e:
            raise ValueError("Error setting app_id", e)

        try:
            self.dev_id = config.attributes.fields.get("dev_id", {}).string_value
            if not self.dev_id:
                raise ValueError("Device ID must be provided")
        except (ValueError, TypeError) as e:
            raise ValueError("Error setting dev_id", e)

        try:
            self.port = config.attributes.fields.get("port", {}).number_value
            if self.port is None:
                raise ValueError("Port must be a valid number")
            self.port = int(self.port)
        except (ValueError, TypeError) as e:
            raise ValueError("Error setting port", e)

        try:
            self.payload_parameter = config.attributes.fields.get("payload_parameter", {}).string_value
            if self.port is None:
                raise ValueError("Input parameter to query")
            self.port = int(self.port)
        except (ValueError, TypeError) as e:
            raise ValueError("Error setting query parameter", e)

        LOGGER.info(f"Configured with username: {self.username}, password: {self.password}, tenant_id: {self.tenant_id}, app_id: {self.app_id}, dev_id: {self.dev_id}")
        
        try:
            LOGGER.info("MODULE CONFIGURED")
        except (ValueError, AttributeError) as e:
            LOGGER.error(f"Error in reconfiguring module: {e}")

    async def close(self):
        LOGGER.info("%s is closed.", self.name)

    async def do_command(self, command: Mapping[str, ValueTypes], *, timeout: Optional[float] = None, **kwargs) -> Mapping[str, ValueTypes]:
        return {}

    async def get_readings(self, extra: Optional[Dict[str, Any]] = None, **kwargs) -> Mapping[str, Any]:
        try:
            return {'temperature': self.temp_value}
        except Exception as e:
            LOGGER.error(f"Error in get_readings: {e}")
            return {'error': str(e)}

    def setup_mqtt(self):
        topic = f"v3/{self.app_id}@{self.tenant_id}/devices/{self.dev_id}/up"

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                LOGGER.info("Connected to MQTT Broker")
                client.subscribe(topic)
                LOGGER.info(f"Subscribed to topic: {topic}")
            else:
                LOGGER.error(f"Connection failed with code {rc}")

        def on_message(client, userdata, msg):
            LOGGER.info(f"Received message on topic: {msg.topic}")
            LOGGER.info(f"Message payload: {msg.payload.decode()}")
            # Parse the JSON message
            try:
                data = json.loads(msg.payload)
                decoded_payload = data["uplink_message"]["decoded_payload"]
                LOGGER.info(f"Decoded Payload: {json.dumps(decoded_payload, indent=2)}")
                # Check if the payload contains the temperature value
                if self.payload_parameter in decoded_payload:
                    self.temp_value = decoded_payload[self.payload_parameter]
                    LOGGER.info(f"Updated temperature value: {self.temp_value}")
                else:
                    LOGGER.info("Decoded payload does not contain temperature data.")
            except json.JSONDecodeError as e:
                LOGGER.error(f"Error decoding JSON: {e}")
            except KeyError as e:
                LOGGER.error(f"KeyError in parsed data: {e}")

        self.mqtt_client = mqtt.Client(client_id=self.dev_id)
        self.mqtt_client.username_pw_set(self.username, self.password)
        self.mqtt_client.tls_set(cert_reqs=mqtt.ssl.CERT_REQUIRED, tls_version=mqtt.ssl.PROTOCOL_TLS)
        self.mqtt_client.on_connect = on_connect
        self.mqtt_client.on_message = on_message
        try:
            self.mqtt_client.connect(self.broker, self.port, keepalive=60)
            self.mqtt_client.loop_start()
        except Exception as e:
            LOGGER.error(f"Error connecting to MQTT broker: {e}")
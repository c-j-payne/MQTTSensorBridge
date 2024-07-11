#!/home/viam/dev/current_monitor/venv/bin/python

import time
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

class CT101(Sensor):
    MODEL: ClassVar[Model] = Model(ModelFamily("chris", "iot-sensor"), "ct101")
    channel: int

    current_value: float = 0.0  # Store the current value

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        LOGGER.info("MODULE VALIDATE")
        return []

    @classmethod
    def new(cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]) -> "CT101":
        sensor = cls(config.name)
        sensor.reconfigure(config, dependencies)
        LOGGER.info("MODULE NEW")
        sensor.setup_mqtt()  # Set up MQTT when the sensor is created
        return sensor

    def __init__(self, name: str):
        super().__init__(name)

    def reconfigure(self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]):
        try:
            LOGGER.info("MODULE CONFIGURED")
        except (ValueError, AttributeError) as e:
            LOGGER.error(f"Error in reconfiguring CT101: {e}")
            self.chan = None

    async def close(self):
        LOGGER.info("%s is closed.", self.name)

    async def do_command(self, command: Mapping[str, ValueTypes], *, timeout: Optional[float] = None, **kwargs) -> Mapping[str, ValueTypes]:
        return {}

    async def get_readings(self, extra: Optional[Dict[str, Any]] = None, **kwargs) -> Mapping[str, Any]:
        try:
            return {'current': self.current_value}
        except Exception as e:
            LOGGER.error(f"Error in get_readings: {e}")
            return {'error': str(e)}

    def setup_mqtt(self):
        # MQTT broker details
        broker = "nam1.cloud.thethings.industries"
        port = 8883  # Secure MQTT port
        # MQTT credentials
        username = "chris-test@viam"
        password = "NNSXS.APVFJ2B3O3JJE2ZHNGZL2I2DBXXU7GBZ6TEEE3A.LY4TJYMN45KBHKDAJVCTXCF4B6VGNG6KEQZYGIOEBFGO7TAWXXZA"
        # TTI application and device details
        tenant_id = "viam"
        app_id = "chris-test"
        dev_id = "eui-24e124746e143655"  # Ensure the device ID is in lowercase
        topic = f"v3/{app_id}@{tenant_id}/devices/{dev_id}/up"

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
                self.current_value = decoded_payload.get("current", 0.0)  # Update the current value
                LOGGER.info(f"Updated current value: {self.current_value}")
            except json.JSONDecodeError as e:
                LOGGER.error(f"Error decoding JSON: {e}")

        self.mqtt_client = mqtt.Client(client_id=dev_id)
        self.mqtt_client.username_pw_set(username, password)
        self.mqtt_client.tls_set(cert_reqs=mqtt.ssl.CERT_REQUIRED, tls_version=mqtt.ssl.PROTOCOL_TLS)
        self.mqtt_client.on_connect = on_connect
        self.mqtt_client.on_message = on_message
        try:
            self.mqtt_client.connect(broker, port, keepalive=60)
            self.mqtt_client.loop_start()
        except Exception as e:
            LOGGER.error(f"Error connecting to MQTT broker: {e}")

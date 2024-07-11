import paho.mqtt.client as mqtt
import json
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
        print("Connected to MQTT Broker")
        client.subscribe(topic)
        print(f"Subscribed to topic: {topic}")
    else:
        print(f"Connection failed with code {rc}")
def on_message(client, userdata, msg):
    print(f"Received message on topic: {msg.topic}")
    print(f"Message payload: {msg.payload.decode()}")
    # Parse the JSON message
    try:
        data = json.loads(msg.payload)
        decoded_payload = data["uplink_message"]["decoded_payload"]
        print("Decoded Payload:")
        print(json.dumps(decoded_payload, indent=2))  # Print formatted JSON
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
client = mqtt.Client(client_id=dev_id)
client.username_pw_set(username, password)
client.tls_set(cert_reqs=mqtt.ssl.CERT_REQUIRED, tls_version=mqtt.ssl.PROTOCOL_TLS)
client.on_connect = on_connect
client.on_message = on_message
try:
    client.connect(broker, port, keepalive=60)
    client.loop_forever()
except KeyboardInterrupt:
    print("Interrupted by user")
finally:
    client.disconnect()
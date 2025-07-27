import paho.mqtt.client as mqtt
from fuzzy import processar_payload_mqtt

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, reason_code, properties):
    print(f">>> MQTT Conectado (código {reason_code})")
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("sys/ct2")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    processar_payload_mqtt(msg.payload.decode('utf-8'), False)

def connect():
    mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message

    mqttc.connect("broker.emqx.io", 1883, 60)

    mqttc.loop_forever()
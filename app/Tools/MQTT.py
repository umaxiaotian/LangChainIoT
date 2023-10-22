from typing import Optional, Type
from pydantic import BaseModel, Field

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
import paho.mqtt.client as mqtt
import queue


MQTT_BROKER = "mosquitto"
MQTT_PORT = 1883
MQTT_USERNAME = "admin"
MQTT_PASSWORD = "admin123"

message_queue = queue.Queue()


def on_message(client, userdata, message):
    message_queue.put(message.payload.decode("utf-8"))


client = mqtt.Client()
client.on_message = on_message
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

try:
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_start()
except:
    print("Could not connect to MQTT broker")


class MqttSentTool:
    name = "Mqtt_Tool"
    description = """
        Effective when turning on or off the LED.
        If you want to turn on the LED, you will receive the string “on”.
        Also, if you want the LED to turn off, you will receive the string "off".
        """

    def _run(self, message: str) -> str:
        result = client.publish("test", '{"led":"'+message+'"}')
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            return "I turned 'ON' the LED."
        else:
            return "I turned 'OFF' the LED."
            # return f"Sending completed."

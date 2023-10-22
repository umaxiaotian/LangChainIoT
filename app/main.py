import paho.mqtt.client as mqtt
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # 1. CORSMiddleware をインポート
import queue
from dotenv import load_dotenv
import os
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI
from Tools.AnimeRanking import AnimeRankingTool
from langchain.agents import load_tools
from langchain.agents import Tool, AgentExecutor
from Tools.MQTT import MqttSentTool

load_dotenv()  # .env ファイルから環境変数を読み込み
app = FastAPI(
    title="LangIoT"
)

# 2. CORS ミドルウェアを FastAPI アプリケーションに追加
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENAI_API_KEY = os.getenv("API_KEY")

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
    raise HTTPException(status_code=500, detail="Could not connect to MQTT broker")

@app.get("/publish/")
def publish_message(topic: str, message: str):
    result = client.publish(topic, message)
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        return {"status": "Message published successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to publish the message")

@app.get("/ai/")
def message(message: str):

    # AnimeRankingTool=AnimeRankingTool()
    chat = ChatOpenAI(temperature=0,openai_api_key=OPENAI_API_KEY)
    animerank = AnimeRankingTool()
    tools = [
            Tool(
                name="AnimeRankingTool",
                func=animerank._run,
                description=(
                    'Useful if you are looking for anime rankings.'
                    'The input has one key "rank" and contains the ranking of the anime. If no rank is specified, then "rank" will be set to None.'
                )
            ),
            Tool(
                name = "Mqtt_Tool",
                func=MqttSentTool()._run,
                  description = """
        Effective when turning on or off the LED.
        If you want to turn on the LED, you will receive the string “on”.
        Also, if you want the LED to turn off, you will receive the string "off".
        """
            )
        ]
    agent = initialize_agent(tools, chat, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)
    result = agent.run(message)
    return (result)

@app.get("/subscribe/{topic}/")
def subscribe_to_topic(topic: str):
    client.subscribe(topic)
    try:
        #応答を１０秒間まつ
        received_message = message_queue.get(timeout=10)
        return {"received_message": received_message}
    except queue.Empty:
        raise HTTPException(status_code=408, detail="No message received within the timeout period")

@app.on_event("shutdown")
def shutdown_event():
    client.loop_stop()
    client.disconnect()

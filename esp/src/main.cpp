#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// WiFiの設定
const char* ssid = ""; //SSID
const char* password = ""; //PASSWORD

// MQTTサーバの設定
const char* mqtt_server = ""; //MQTT BrokerのIP
const int mqtt_port = 1883;
const char* mqtt_user = "admin"; //本環境のデフォルトユーザー
const char* mqtt_password = "admin123"; //本環境のデフォルトユーザーのパスワード

WiFiClient espClient;
PubSubClient client(espClient);

void callback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  // コールバックメッセージをシリアルモニターに出力
  Serial.println("Received message on topic: " + String(topic));
  Serial.println("Message: " + message);

  if (message == "{\"led\":\"on\"}") {
    digitalWrite(D0, HIGH);
  } else if (message == "{\"led\":\"off\"}") {
    digitalWrite(D0, LOW);
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.println("Attempting MQTT connection...");
    if (client.connect("ESP8266Client", mqtt_user, mqtt_password)) {
      Serial.println("Connected to MQTT broker!");
      client.subscribe("test");
    } else {
      Serial.print("Failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(9600);  // ボーレートを9600に変更
  Serial.println("Starting up...");

  // WiFi接続
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  // MQTTコールバック関数の設定
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  // D0ピンの設定
  pinMode(D0, OUTPUT);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}

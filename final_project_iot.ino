#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_BMP280.h>
#include <Adafruit_SHT4x.h>
#include <ArduinoJson.h>
#include <WiFi.h>
#include <NTPClient.h>
#include <WiFiUdp.h>
#include <PubSubClient.h>

// กำหนดค่า WiFi และ MQTT
#define WIFI_SSID "834.194"
#define WIFI_PASSWORD "22222222"
#define MQTT_BROKER_IP "broker.emqx.io"
#define MQTT_PORT 1883
#define MQTT_CLIENT_ID "esp8266-client-68:67:25:26:0E:CC"
#define MQTT_TOKEN "emqx"
#define MQTT_SECRET "public"
  
// สร้างอ็อบเจกต์เซ็นเซอร์ต่างๆ
Adafruit_SHT4x humiditySensor;
Adafruit_BMP280 pressureSensor;
Adafruit_MPU6050 motionSensor;
   
// สร้าง WiFiClient และ PubSubClient สำหรับการเชื่อมต่อ MQTT
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", 7 * 3600);  // ใช้เวลา UTC+7
   
// ตัวแปรเก็บเวลาในการส่งข้อมูล
unsigned long lastDataPublishTime = 0;
int timeUpdateCounter = 0; // ตัวนับเพื่ออัปเดตเวลา
   
// ฟังก์ชันสำหรับการตั้งค่าและเริ่มใช้งานเซ็นเซอร์ต่างๆ
void initializeSensors() {
  Wire.begin(41, 40);  // กำหนดพอร์ต SDA, SCL
  humiditySensor.begin();
  motionSensor.begin(0x68);
  pressureSensor.begin(0x76);
  motionSensor.setAccelerometerRange(MPU6050_RANGE_2_G);
  motionSensor.setFilterBandwidth(MPU6050_BAND_21_HZ);
  Serial.println("Hardware initialized.");  // แจ้งว่าเซ็นเซอร์พร้อมใช้งาน
}
   
// ฟังก์ชันสำหรับการอัปเดตเวลาโดยใช้ NTP
void syncTimeWithNTP() {
  timeClient.update();
  unsigned long currentMillis = millis();
  if (currentMillis - (600000 * timeUpdateCounter) < 600000) {
    Serial.println(timeClient.getFormattedTime());  // แสดงเวลาในฟอร์แมตที่อ่านได้
  } else {
    timeUpdateCounter += 2;
    delay(600000);  // รอ 10 นาทีเพื่ออัปเดตเวลา
  }
}
   
// ฟังก์ชันเชื่อมต่อ WiFi
void setupWiFi() {
  Serial.println("Connecting to WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  Serial.println(WiFi.localIP());  // แสดง IP ที่ได้รับจาก WiFi
}
   
// ฟังก์ชันเชื่อมต่อกับ MQTT Broker
void setupMQTT() {
  mqttClient.setServer(MQTT_BROKER_IP, MQTT_PORT);
  if (mqttClient.connect(MQTT_CLIENT_ID, MQTT_TOKEN, MQTT_SECRET)) {
    mqttClient.subscribe("emqx/esp8266");  // Subscribe topic ที่ต้องการ
    mqttClient.subscribe("emqx/temp_humid");  
    Serial.println("MQTT connected.");
  } else {
    Serial.println("MQTT connection failed.");  // ถ้าไม่สามารถเชื่อมต่อได้
  }
}



// ฟังก์ชันสำหรับส่งข้อมูลเซ็นเซอร์ไปยัง MQTT
void publishSensorData() {
  char jsonPayload[200];
  sensors_event_t temperatureEvent, humidityEvent, pressureEvent;
  humiditySensor.getEvent(&humidityEvent, &temperatureEvent);  // อ่านข้อมูลจาก SHT4x
  float pressure = pressureSensor.readPressure();  // อ่านข้อมูลความดันจาก BMP280
  float humidity = humidityEvent.relative_humidity;  // อ่านข้อมูลความชื้นจาก SHT4x
  float temperature = temperatureEvent.temperature;  // อ่านข้อมูลอุณหภูมิจาก SHT4x
   
  // สร้างข้อความ JSON เพื่อส่งไปยัง MQTT
  const char jsonTemplate[] = "{\"data\":{\"pressure\": %.2f, \"temperature\": %.2f, \"humidity\": %.2f}}";
  sprintf(jsonPayload, jsonTemplate, pressure, temperature, humidity);
  mqttClient.publish("emqx/esp8266", jsonPayload);  // ส่งข้อมูลผ่าน MQTT
  const char jsonTemplate_1[] = "{\"data\"{\"temperature\": %.2f , \"humidity\": %.2f}}"; 
  sprintf(jsonPayload, jsonTemplate_1, temperature, humidity);
  mqttClient.publish("emqx/temp_humid", jsonPayload);  // ส่งข้อมูลผ่าน MQTT
  Serial.println(jsonPayload);  // แสดงข้อมูลที่ส่งออกไป
}
   
void setup() {
  Serial.begin(115200);
  pinMode(2, OUTPUT);  // กำหนดขา 2 เป็นขา OUTPUT (ใช้สำหรับควบคุมอุปกรณ์ต่างๆ เช่น LED)
  initializeSensors();
  setupWiFi();
  timeClient.begin();
  setupMQTT();
}
   
void loop() {
  syncTimeWithNTP();  // อัปเดตเวลา
   
  // ส่งข้อมูลทุกๆ 5 วินาที
  if (millis() - lastDataPublishTime > 5000) {
    lastDataPublishTime = millis();
    publishSensorData();
  }
   
  mqttClient.loop();  // ฟังก์ชันนี้ต้องเรียกใน loop() เพื่อตรวจสอบข้อความ MQTT
  delay(1000);  // รอ 1 วินาที
}

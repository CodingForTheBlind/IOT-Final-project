import paho.mqtt.client as mqtt
import influxdb_client
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import time
import json
import os
from dotenv import load_dotenv

load_dotenv()

INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN')

MQTT_BROKER_URL = "broker.emqx.io"
MQTT_PUBLISH_TOPIC = "emqx/temp_humid"
token = INFLUXDB_TOKEN
print(token)
db_client = InfluxDBClient(url="http://localhost:8086", token=token, org="my-org")
write_api = db_client.write_api(write_options=SYNCHRONOUS)
query_api = db_client.query_api()
bucket = "my-bucket"



#Connection success callback
def on_connect(client, userdata, flags, rc):
    print('Connected with result code '+str(rc))
    client.subscribe(MQTT_PUBLISH_TOPIC)


# Message receiving callback
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload)[9:-2])
    res = json.loads(str(msg.payload)[9:-2])
    print(res)
    p = Point("my_measurement").tag("location","CUEE-clubroom").field("temperature", res['temperature'])
    write_api.write(bucket=bucket,org="my-org", record=p)
    time.sleep(1)
    p = Point("my_measurement").tag("location","CUEE-clubroom").field("humidity", res['humidity'])
    write_api.write(bucket=bucket,org="my-org",record=p)
    time.sleep(1)



client = mqtt.Client()


# Specify callback function
client.on_connect = on_connect
client.on_message = on_message

# Establish a connection
client.connect('broker.emqx.io', 1883, 60)

client.loop_forever()


#bucket = "my-bucket"

#client = InfluxDBClient(url="http://localhost:8086", token="my-token", org="my-org")

#write_api = client.write_api(write_options=SYNCHRONOUS)
#query_api = client.query_api()

#p = Point("my_measurement").tag("time",str( time.gmtime(7) )).field("temperature", 25.3)

#write_api.write(bucket=bucket, record=p)

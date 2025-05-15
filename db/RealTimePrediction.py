import joblib
import pandas as pd
import numpy as np
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import time
import os
from dotenv import load_dotenv

load_dotenv()

#InfluxDB Configuration
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN')
INFLUXDB_ORG = "my-org"
INFLUXDB_BUCKET = "my-bucket"

#Load trained model
model = joblib.load('model.pkl')

#Connect to InfluxDB
client = InfluxDBClient(
    url=INFLUXDB_URL,
    token=INFLUXDB_TOKEN,
    org=INFLUXDB_ORG
)
query_api = client.query_api()
write_api = client.write_api(write_options=SYNCHRONOUS)

#Loop to predict every few seconds
while True:
    try:
        #Query the latest data (limit 1 for latest entry)
        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
          |> range(start: -1m)
          |> filter(fn: (r) => r._measurement == "my_measurement")
          |> filter(fn: (r) => r._field == "humidity")
          |> sort(columns: ["_time"], desc: true)
          |> limit(n:1)
        '''

        tables = query_api.query(query)
        if not tables or not tables[0].records:
            print("No data found. Waiting...")
            time.sleep(5)
            continue

        humid_value = tables[0].records[0].get_value()
        print(f"Latest humidity: {humid_value}")

        #Predict temperature
        pred_temp = model.predict(np.array([[humid_value]]))[0]
        print(f"Predicted temperature: {pred_temp:.2f} °C")

        #Write prediction back to InfluxDB
        point = (
            Point("predicted_result")
            .field("Predicted_Temp", float(pred_temp))
            .field("Humidity", float(humid_value))
        )
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
        print("Prediction written to InfluxDB.\n")

    except Exception as e:
        print("Error:", e)

    time.sleep(5)  # wait before next prediction

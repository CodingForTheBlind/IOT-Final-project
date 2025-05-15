import pandas as pd
from sklearn.svm import SVR
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
import joblib
from influxdb_client import InfluxDBClient, Point
import os
from dotenv import load_dotenv

load_dotenv()


#Connect to InfluxDB (adjust host, port, and database as needed)
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN')
client = InfluxDBClient(url="http://localhost:8086", token=INFLUXDB_TOKEN, org="my-org")

# Query the latest 1000 entries of temperature and humidity data


query_api = client.query_api()

query = """from(bucket: "my-bucket")
  |> range(start: -240m)
  |> filter(fn: (r) => r._measurement == "my_measurement")
  |> filter(fn:(r) => r.location == "CUEE-clubroom")\
  """
result = query_api.query(query, org="my-org")
results = {
    "time":[],
    "temperature":[],
    "humidity":[]
    }

for table in result:
    for record in table.records:
        if( record.get_time() not in results["time"]):results["time"].append(record.get_time())
        results[record.get_field()].append( record.get_value())
print(len(results["time"]),len(results["temperature"]),len(results["humidity"]))
results["time"] = results["time"][:len(results["time"])//2]
#print(results)
#Convert query result to a Pandas DataFrame
# points = list(result.get_points())
df = pd.DataFrame(results)
time = pd.to_datetime(df["time"],format='%Y/%m/%d %H:%M:%S')
df["time"]=time-time[0]
df['timestamp'] = df['time'].div(10**9)
df['timestamp'] = df['timestamp'].astype('int64')
df = df[['timestamp','humidity','temperature']]
print(df)

if df.empty:
    print("No data found in InfluxDB. Please check the database and measurement name.")
    exit()

print("Data retrieved successfully")
print(df.head())

#Prepare features and target
X = df[['humidity']]  # Feature (input): humidity
y = df['temperature']     # Target (output): temperature

#Split the dataset into training and testing sets (80/20 split)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

#Create and train a Linear Regression model
model = LinearRegression()
model.fit(X_train, y_train)

print(f"MAE: {mean_absolute_error(y_true=y_test,y_pred=model.predict(X_test)):.2f} , RMSE: {root_mean_squared_error(y_true=y_test,y_pred=model.predict(X_test)):.2f}")
#Save the trained model to a file
joblib.dump(model, 'model.pkl')

print("Model trained and saved as model.pkl")

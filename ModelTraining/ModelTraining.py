import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import joblib
from influxdb import InfluxDBClient

#Connect to InfluxDB (adjust host, port, and database as needed)
client = InfluxDBClient(host='localhost', port=8086)
client.switch_database('iot_data')  # Replace with your actual database name

# Query the latest 1000 entries of temperature and humidity data
query = 'SELECT temp, humid FROM sensor_data ORDER BY time DESC LIMIT 1000'
result = client.query(query)

#Convert query result to a Pandas DataFrame
points = list(result.get_points())
df = pd.DataFrame(points)

if df.empty:
    print("No data found in InfluxDB. Please check the database and measurement name.")
    exit()

print("Data retrieved successfully")
print(df.head())

#Prepare features and target
X = df[['humid']]  # Feature (input): humidity
y = df['temp']     # Target (output): temperature

#Split the dataset into training and testing sets (80/20 split)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

#Create and train a Linear Regression model
model = LinearRegression()
model.fit(X_train, y_train)

#Save the trained model to a file
joblib.dump(model, 'model.pkl')

print("Model trained and saved as model.pkl")

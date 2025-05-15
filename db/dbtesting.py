import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
import os
bucket = "my-bucket"
org = "my-org"
token = "lva49Uv7k3zQBxhu_WOZ7jwZBK99hwtZnm-J313sPfe51vAsz1PmeFdHLOP3vaKvIvUryoqZnlgUsuX2FkVsWw=="
# Store the URL of your InfluxDB instance
url="http://localhost:8086"
print(token)

client = influxdb_client.InfluxDBClient(
    url=url,
    token=token,
    org=org
)

# Write script
write_api = client.write_api(write_options=SYNCHRONOUS)

p = influxdb_client.Point("my_measurement").tag("location", "Prague").field("temperature", 25.3)
write_api.write(bucket=bucket, org=org, record=p)

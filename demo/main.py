import boto3
from botocore import UNSIGNED
from botocore.client import Config

s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))
response = s3.list_objects_v2(
    Bucket="sentinel-s2-l2a", Prefix="tiles/39/R/VK/2026/4/18/0"
)

count = 0
for obj in response.get("Contents", []):
    print(obj["Key"], " - ", obj["Size"], "bytes")
    count += obj["Size"]

print(count)

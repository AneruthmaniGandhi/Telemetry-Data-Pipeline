#!/usr/bin/env python3

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

# MinIO configuration  
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"

def create_buckets():
    """Create both raw-logs and processed-logs buckets in MinIO."""
    s3_client = boto3.client(
        's3',
        endpoint_url=f'http://{MINIO_ENDPOINT}',
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'
    )
    
    buckets = ["raw-logs", "processed-logs"]
    
    for bucket_name in buckets:
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"✅ Bucket {bucket_name} already exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                s3_client.create_bucket(Bucket=bucket_name)
                print(f"✅ Created bucket {bucket_name}")
            else:
                print(f"❌ Error with bucket {bucket_name}: {str(e)}")

if __name__ == "__main__":
    create_buckets() 
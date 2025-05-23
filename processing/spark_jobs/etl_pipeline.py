#!/usr/bin/env python3

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_json, struct
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, 
    BooleanType, TimestampType, MapType
)
import logging
import sys
import boto3
import json
import io
from botocore.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MinIO configuration
MINIO_ENDPOINT = "minio:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
RAW_BUCKET = "raw-logs"
PROCESSED_BUCKET = "processed-logs"

def create_spark_session():
    """Create and configure a Spark session."""
    import os
    
    # Set Python executable paths to fix version mismatch
    python_path = "/home/airflow/.local/bin/python"
    os.environ['PYSPARK_PYTHON'] = python_path
    os.environ['PYSPARK_DRIVER_PYTHON'] = python_path
    
    return (SparkSession.builder
            .appName("Telemetry ETL")
            .config("spark.sql.adaptive.enabled", "false")
            .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
            .config("spark.pyspark.python", python_path)
            .config("spark.pyspark.driver.python", python_path)
            .getOrCreate())

def get_s3_client():
    """Create a boto3 S3 client for MinIO."""
    return boto3.client(
        's3',
        endpoint_url=f'http://{MINIO_ENDPOINT}',
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'
    )

def read_jsonl_from_minio(s3_client, bucket, prefix="logs/"):
    """Read JSONL files from MinIO using boto3."""
    data = []
    
    try:
        # List objects in the bucket with the prefix
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        
        if 'Contents' not in response:
            logger.warning(f"No files found in bucket {bucket} with prefix {prefix}")
            return data
            
        for obj in response['Contents']:
            if obj['Key'].endswith('.jsonl'):
                logger.info(f"Reading file: {obj['Key']}")
                
                # Get the object
                file_response = s3_client.get_object(Bucket=bucket, Key=obj['Key'])
                content = file_response['Body'].read().decode('utf-8')
                
                # Parse JSONL (each line is a JSON object)
                for line in content.strip().split('\n'):
                    if line.strip():
                        try:
                            json_obj = json.loads(line)
                            data.append(json_obj)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse line: {line}, error: {e}")
                            
    except Exception as e:
        logger.error(f"Error reading from MinIO: {str(e)}")
        raise
        
    return data

def write_parquet_to_minio(df, s3_client, bucket, key="telemetry.parquet"):
    """Write DataFrame to MinIO as Parquet using local temp storage."""
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = os.path.join(temp_dir, "temp_parquet")
        
        # Write to local temp directory first
        df.write.mode("overwrite").parquet(temp_path)
        
        # Upload all parquet files to MinIO
        for root, dirs, files in os.walk(temp_path):
            for file in files:
                if file.endswith('.parquet'):
                    local_file_path = os.path.join(root, file)
                    s3_key = f"{key}/{file}"
                    
                    logger.info(f"Uploading {file} to s3://{bucket}/{s3_key}")
                    s3_client.upload_file(local_file_path, bucket, s3_key)

def get_schema():
    """Define the schema for telemetry logs."""
    return StructType([
        StructField("timestamp", TimestampType(), True),
        StructField("equipment_id", StringType(), True),
        StructField("status", StringType(), True),
        StructField("error_code", StringType(), True),
        StructField("sensor_readings", StructType([
            StructField("temperature", DoubleType(), True),
            StructField("vibration", DoubleType(), True),
            StructField("power_consumption", DoubleType(), True)
        ]), True),
        StructField("location", StringType(), True),
        StructField("maintenance_due", BooleanType(), True)
    ])

def main():
    """Main ETL process."""
    try:
        # Create Spark session
        spark = create_spark_session()
        logger.info("Created Spark session")

        # Create S3 client
        s3_client = get_s3_client()
        logger.info("Created S3 client for MinIO")
        
        # Read JSON data from MinIO
        logger.info("Reading JSON files from MinIO...")
        raw_data = read_jsonl_from_minio(s3_client, RAW_BUCKET)
        
        if not raw_data:
            logger.error("No data found in MinIO")
            sys.exit(1)
            
        logger.info(f"Read {len(raw_data)} records from MinIO")
        
        # Create DataFrame from the data
        df = spark.createDataFrame(raw_data)
        
        # Show sample data
        logger.info("Sample data from raw logs:")
        df.show(5, truncate=False)
        
        # Show schema
        logger.info("Schema of raw logs:")
        df.printSchema()
        
        # Show basic statistics
        logger.info("Count of records: %d", df.count())
        
        # Write to Parquet format in MinIO
        logger.info("Writing data to Parquet format...")
        write_parquet_to_minio(df, s3_client, PROCESSED_BUCKET)
        
        logger.info("Successfully wrote Parquet files to MinIO bucket: %s", PROCESSED_BUCKET)
        
        # Stop Spark session
        spark.stop()
        logger.info("ETL process completed successfully")
        
    except Exception as e:
        logger.error(f"ETL process failed: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
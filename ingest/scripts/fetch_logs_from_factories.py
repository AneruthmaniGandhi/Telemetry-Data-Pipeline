#!/usr/bin/env python3

import os
import json
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from datetime import datetime
from validate_log import validate_log_line
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MinIO configuration
MINIO_ENDPOINT = "host.docker.internal:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
BUCKET_NAME = "raw-logs"

def get_s3_client():
    """Create and return an S3 client configured for MinIO."""
    return boto3.client(
        's3',
        endpoint_url=f'http://{MINIO_ENDPOINT}',
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'  # MinIO doesn't care about region
    )

def ensure_bucket_exists(s3_client):
    """Create the bucket if it doesn't exist."""
    try:
        s3_client.head_bucket(Bucket=BUCKET_NAME)
        logger.info(f"Bucket {BUCKET_NAME} already exists")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            s3_client.create_bucket(Bucket=BUCKET_NAME)
            logger.info(f"Created bucket {BUCKET_NAME}")
        else:
            raise

def list_uploaded_files(s3_client):
    """List all files in the raw-logs bucket."""
    try:
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME)
        if 'Contents' in response:
            logger.info("\nUploaded files in MinIO:")
            logger.info("-" * 50)
            for obj in response['Contents']:
                size_mb = obj['Size'] / (1024 * 1024)
                last_modified = obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
                logger.info(f"File: {obj['Key']}")
                logger.info(f"Size: {size_mb:.2f} MB")
                logger.info(f"Last Modified: {last_modified}")
                logger.info("-" * 50)
        else:
            logger.info("No files found in bucket")
    except Exception as e:
        logger.error(f"Failed to list files: {str(e)}")

def upload_log_file(s3_client, file_path):
    """Read, validate, and upload log file to MinIO."""
    # Generate a unique key based on timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    key = f"logs/{timestamp}_{os.path.basename(file_path)}"
    
    valid_logs = []
    invalid_logs = []
    
    # Read and validate logs
    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
                
            result = validate_log_line(line)
            if isinstance(result, str):
                logger.error(f"Line {line_num}: {result}")
                invalid_logs.append(line)
            else:
                valid_logs.append(line)
    
    if not valid_logs:
        logger.error("No valid logs found in file")
        return False
    
    # Upload valid logs
    try:
        # Create a temporary file with only valid logs
        temp_file = f"{file_path}.valid"
        with open(temp_file, 'w') as f:
            f.write('\n'.join(valid_logs))
        
        # Upload to MinIO
        s3_client.upload_file(temp_file, BUCKET_NAME, key)
        logger.info(f"Successfully uploaded {len(valid_logs)} valid logs to {key}")
        
        # Clean up temp file
        os.remove(temp_file)
        
        # Log summary
        if invalid_logs:
            logger.warning(f"Skipped {len(invalid_logs)} invalid logs")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to upload logs: {str(e)}")
        return False

def main():
    """Main function to process log files."""
    # Get S3 client
    s3_client = get_s3_client()
    
    # Ensure bucket exists
    ensure_bucket_exists(s3_client)
    
    # Process log files
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    for filename in os.listdir(log_dir):
        if filename.endswith('.jsonl'):
            file_path = os.path.join(log_dir, filename)
            logger.info(f"Processing {filename}")
            if upload_log_file(s3_client, file_path):
                logger.info(f"Successfully processed {filename}")
            else:
                logger.error(f"Failed to process {filename}")
    
    # List uploaded files
    list_uploaded_files(s3_client)

if __name__ == "__main__":
    main() 
# apps/events/upload_to_cloud.py
import os
import boto3
from datetime import datetime
from botocore.exceptions import NoCredentialsError, ClientError
from apps.events.utils.log_line import log_line

def upload_backup_to_cloud(file_path, log=None, folder="backups"):
    """
    Upload a file to S3 and return the S3 key (string) or None if failed.
    - log: StringIO object to record logs
    """
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    S3_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
    S3_REGION = os.getenv("AWS_S3_REGION", "ap-southeast-1")

    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY or not S3_BUCKET_NAME:
        log_line(log, "Missing AWS credentials or bucket name.", level="ERROR")
        return None

    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=S3_REGION
    )

    # Ensure bucket exists
    try:
        s3.head_bucket(Bucket=S3_BUCKET_NAME)
    except ClientError:
        log_line(log, f"Bucket '{S3_BUCKET_NAME}' not found. Creating...")
        s3.create_bucket(
            Bucket=S3_BUCKET_NAME,
            CreateBucketConfiguration={"LocationConstraint": S3_REGION}
        )

    filename = os.path.basename(file_path)
    s3_key = f"{folder}/{datetime.now().strftime('%Y-%m-%d')}/{filename}"

    try:
        log_line(log, f"Uploading {filename} to S3 bucket '{S3_BUCKET_NAME}'...")
        s3.upload_file(file_path, S3_BUCKET_NAME, s3_key)
        log_line(log, f"Upload successful: s3://{S3_BUCKET_NAME}/{s3_key}")
        return str(s3_key)

    except FileNotFoundError:
        log_line(log, f"File not found: {file_path}", level="ERROR")
    except NoCredentialsError:
        log_line(log, "AWS credentials not available.", level="ERROR")
    except Exception as e:
        log_line(log, f"Upload failed: {str(e)}", level="ERROR")

    return None
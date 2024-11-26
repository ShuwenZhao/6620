import os
import boto3
import json
import logging
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
s3_client = boto3.client('s3')
logs_client = boto3.client('logs')

BUCKET_NAME = os.environ['BUCKET_NAME']
LOGGING_LAMBDA_NAME = os.environ['LOGGING_LAMBDA_NAME']
LOG_GROUP_NAME = f"/aws/lambda/{LOGGING_LAMBDA_NAME}"


def get_largest_object():
    """
    Fetch the largest object from the S3 bucket.
    """
    try:
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME)
        objects = response.get('Contents', [])

        if not objects:
            logger.info(f"No objects found in bucket {BUCKET_NAME}.")
            return None

        # Find the largest object
        largest_object = max(objects, key=lambda obj: obj['Size'])
        logger.info(f"Largest object: {largest_object['Key']} of size {largest_object['Size']} bytes.")
        return largest_object['Key'], largest_object['Size']

    except ClientError as e:
        logger.error(f"Failed to list objects in bucket {BUCKET_NAME}: {e}")
        return None


def get_object_size_from_logs(object_name):
    """
    Search CloudWatch Logs to find the object size for a deleted object.
    """
    try:
        query = f'{{ $.object_name = "{object_name}" }}'
        response = logs_client.filter_log_events(
            logGroupName=LOG_GROUP_NAME,
            filterPattern=query,
        )

        # Look through the events to find the object creation log
        for event in response['events']:
            log_data = json.loads(event['message'])
            if log_data['action'] == 'ObjectCreated:Put' and log_data['object_name'] == object_name:
                return log_data.get('size_delta', 0)

        logger.warning(f"Could not find size for object: {object_name} in logs.")
        return 0

    except ClientError as e:
        logger.error(f"Failed to fetch logs for object {object_name}: {e}")
        return 0


def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")

    # Ensure this function only runs when the alarm is in ALARM state
    try:
        if event.get('detail', {}).get('state', {}).get('value') != 'ALARM':
            logger.info("CloudWatch Alarm is not in ALARM state. Exiting.")
            return {"statusCode": 200, "body": "No action taken."}

    except KeyError as e:
        logger.error(f"Missing keys in event: {e}")
        return {"statusCode": 400, "body": "Invalid event format."}

    # Get the largest object from the bucket
    largest_object = get_largest_object()

    if not largest_object:
        return {"statusCode": 200, "body": "No objects to delete."}

    object_name, object_size = largest_object

    # Fetch the object size for deleted objects from logs if needed
    if object_size == 0:
        object_size = get_object_size_from_logs(object_name)

    # Delete the object
    try:
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=object_name)
        logger.info(f"Deleted object {object_name} of size {object_size} bytes.")
        return {"statusCode": 200, "body": f"Deleted object {object_name} of size {object_size} bytes."}

    except ClientError as e:
        logger.error(f"Failed to delete object {object_name}: {e}")
        return {"statusCode": 500, "body": f"Failed to delete object {object_name}."}

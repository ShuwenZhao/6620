import os
import boto3
from datetime import datetime

####################
# PART 2: SIZE TRACKING LAMBDA
####################

# Retrieve bucket and table names from environment variables
bucket_name = os.environ['BUCKET_NAME']
table_name = os.environ['TABLE_NAME']

# Initialize S3 and DynamoDB clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(table_name)


def get_total_size(bucket_name):
    total_size = 0
    total_objects = 0

    # List all objects in the bucket and calculate total size
    response = s3.list_objects_v2(Bucket=bucket_name)
    if 'Contents' in response:
        for obj in response['Contents']:
            total_size += obj['Size']
            total_objects += 1
    else:
        print(f"No objects found in bucket {bucket_name}")

    print(f"Total size of bucket {bucket_name}: {total_size} bytes with {total_objects} objects")
    return total_size, total_objects


# This lambda function receives an event when an S3 object is created, updated, or deleted.
# Computes the total size of the objects in the bucket.
# Writes the bucket name, total size, number of objects, and timestamp into the DynamoDB table.
def lambda_handler(event, context):
    print(f"Received event: {event}")

    # Get the bucket name from the event
    try:
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        print(f"Processing S3 bucket: {bucket_name}")
    except Exception as e:
        print(f"Error extracting bucket name from event: {e}")
        raise e

    # Get the total size and object count in the bucket
    try:
        total_size, total_objects = get_total_size(bucket_name)
    except Exception as e:
        print(f"Error getting total size of bucket {bucket_name}: {e}")
        raise e

    timestamp = datetime.now().isoformat()
    print(f"Timestamp: {timestamp}")

    # Store size info in DynamoDB
    try:
        table.put_item(
            Item={
                'bucket_name': bucket_name,
                'timestamp': timestamp,
                'total_size': total_size,
                'total_objects': total_objects
            }
        )
        print(f"Successfully stored size info in DynamoDB for bucket: {bucket_name}")
    except Exception as e:
        print(f"Error writing to DynamoDB: {e}")
        raise e

    return {
        'statusCode': 200,
        'body': f"Bucket size recorded: {total_size} bytes, {total_objects} objects."
    }

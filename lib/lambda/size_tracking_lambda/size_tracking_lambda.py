import json
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


# This lambda handler is for processing messages from the SQS queue. 
# Each message contains an S3 event.
def lambda_handler(event, context):
    print(f"Received event: {event}")

    try:
        # Iterate through SQS messages
        for record in event['Records']:
            # Extract the SNS message from the SQS record
            sns_message = json.loads(record['body'])
            
            # Extract the original S3 event from the SNS message
            s3_event = json.loads(sns_message['Message'])['Records'][0]

            # Extract bucket name and object key from the S3 event
            bucket_name = s3_event['s3']['bucket']['name']
            object_key = s3_event['s3']['object']['key']
            object_size = s3_event['s3']['object'].get('size', 0)  # Default size to 0 if not present

            print(f"Processing S3 bucket: {bucket_name}, Object: {object_key}, Size: {object_size}")

            # Compute total size and object count
            total_size, total_objects = get_total_size(bucket_name)

            # Store size info in DynamoDB
            timestamp = datetime.now().isoformat()
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
        print(f"Error processing event: {e}")
        raise e

    return {
        'statusCode': 200,
        'body': "Event processed successfully."
    }

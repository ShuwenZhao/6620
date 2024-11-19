import boto3
import os

# Initialize S3 client
s3 = boto3.client('s3')

# Get bucket name from environment variables
bucket_name = os.environ['BUCKET_NAME']

# List all objects in the bucket and find the largest one.
def get_largest_object(bucket_name):
    try:
        response = s3.list_objects_v2(Bucket=bucket_name)
        if 'Contents' not in response:
            print(f"No objects found in bucket {bucket_name}")
            return None
        
        # Find the largest object
        largest_object = max(response['Contents'], key=lambda obj: obj['Size'])
        return largest_object
    except Exception as e:
        print(f"Error listing objects in bucket {bucket_name}: {e}")
        raise e

# Delete the specified object from the bucket.
def delete_object(bucket_name, object_key):
    try:
        s3.delete_object(Bucket=bucket_name, Key=object_key)
        print(f"Deleted object {object_key} from bucket {bucket_name}")
    except Exception as e:
        print(f"Error deleting object {object_key} from bucket {bucket_name}: {e}")
        raise e

# Entry point for the Cleaner Lambda. 
# Deletes the largest object from the bucket to reduce size.
def lambda_handler(event, context):
    print(f"Received event: {event}")

    # Get the largest object in the bucket
    largest_object = get_largest_object(bucket_name)
    if not largest_object:
        return {
            'statusCode': 200,
            'body': "No objects in the bucket to delete."
        }
    
    # Delete the largest object
    object_key = largest_object['Key']
    object_size = largest_object['Size']
    print(f"Largest object: {object_key}, size: {object_size} bytes")

    delete_object(bucket_name, object_key)

    return {
        'statusCode': 200,
        'body': f"Deleted largest object: {object_key} (size: {object_size} bytes)"
    }

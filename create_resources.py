import boto3
from botocore.exceptions import ClientError

####################
# PART 1: CREATE RESOURCES
####################

# Initialize AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')


def create_s3_bucket(bucket_name):
    try:
        s3.create_bucket(Bucket=bucket_name)
        print(f"S3 bucket '{bucket_name}' created successfully.")
    except Exception as e:
        print(f"Error creating bucket: {e}")


def create_dynamodb_table(table_name):
    try:
        # Create DynamoDB table with attributes to store bucket size history
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'bucket_name', 'KeyType': 'HASH'},  # Partition key
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}   # Sort key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'bucket_name', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print(f"DynamoDB table '{table_name}' created successfully.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"Table '{table_name}' already exists.")
        else:
            print(f"Error creating table: {e}")


# Create S3 bucket and DynamoDB table
create_s3_bucket('test-bucket-swzhao-2024')
create_dynamodb_table('S3-object-size-history')

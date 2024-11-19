import os
import boto3
import time
import requests

####################
# PART 4: DRIVER LAMBDA
####################

# Retrieve bucket and table names from environment variables
bucket_name = os.environ['BUCKET_NAME']
table_name = os.environ['TABLE_NAME']
plotting_lambda_api_url = os.environ['PLOTTING_LAMBDA_API_URL']

# Initialize S3 and API Gateway clients
s3 = boto3.client('s3')


def create_object(object_name, content):
    s3.put_object(Bucket=bucket_name, Key=object_name, Body=content)
    print(f"Created {object_name} with content '{content}'")


def call_plotting_lambda_api():
    response = requests.post(plotting_lambda_api_url)
    print(f"Called plotting lambda API, response: {response.status_code}")


def lambda_handler(event, context):
    try:
        # Step 1: Create assignment1.txt
        create_object("assignment1.txt", "Empty Assignment 1")  # size: 19 bytes
        time.sleep(10)

        # Step 2: Create assignment2.txt
        create_object("assignment2.txt", "Empty Assignment 2222222222")  # size: 28 bytes
        time.sleep(10)

        # Step 3: Create assignment3.txt
        create_object("assignment3.txt", "33")  # size: 2 bytes
        time.sleep(10) 

        # Step 4: Call the plotting lambda API
        call_plotting_lambda_api()

        return {
            "statusCode": 200,
            "body": "Driver Lambda executed successfully"
        }
    except Exception as e:
        print(f"Error in Driver Lambda: {e}")
        raise

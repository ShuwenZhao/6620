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

# Initialize S3 and API Gateway clients
s3 = boto3.client('s3')

# Define the API Gateway endpoint for the plotting Lambda
PLOTTING_LAMBDA_API_URL = 'https://1uuh0nppu4.execute-api.us-east-1.amazonaws.com/prod/plot'


def create_object():
    # Create the object `assignment1.txt` with content "Empty Assignment 1"
    s3.put_object(Bucket=bucket_name, Key='assignment1.txt', Body="Empty Assignment 1")
    print("Created assignment1.txt with content 'Empty Assignment 1'")


def update_object():
    # Update the object `assignment1.txt` with new content "Empty Assignment 2222222222"
    s3.put_object(Bucket=bucket_name, Key='assignment1.txt', Body="Empty Assignment 2222222222")
    print("Updated assignment1.txt with content 'Empty Assignment 2222222222'")


def delete_object():
    # Delete the object `assignment1.txt`
    s3.delete_object(Bucket=bucket_name, Key='assignment1.txt')
    print("Deleted assignment1.txt")


def create_assignment2():
    # Create the object `assignment2.txt` with content "33"
    s3.put_object(Bucket=bucket_name, Key='assignment2.txt', Body="33")
    print("Created assignment2.txt with content '33'")


def call_plotting_lambda_api():
    # Call the API for the plotting lambda to trigger the plot generation
    response = requests.post(PLOTTING_LAMBDA_API_URL)
    print("Called plotting lambda API, response:", response.status_code)


def lambda_handler(event, context):
    # Step 1: Create assignment1.txt
    create_object()
    time.sleep(3)

    # Step 2: Update assignment1.txt
    update_object()
    time.sleep(3)

    # Step 3: Delete assignment1.txt
    delete_object()
    time.sleep(3)

    # Step 4: Create assignment2.txt
    create_assignment2()
    time.sleep(3)

    # Step 5: Call the plotting Lambda API
    call_plotting_lambda_api()

    return {
        'statusCode': 200,
        'body': "Driver Lambda executed successfully"
    }

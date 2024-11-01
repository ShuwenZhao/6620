import os
import boto3
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

####################
# PART 3: PLOTTING LAMBDA
####################

# Retrieve bucket and table names from environment variables
bucket_name = os.environ['BUCKET_NAME']
table_name = os.environ['TABLE_NAME']

# Initialize S3 and DynamoDB clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
table = dynamodb.Table(table_name)


def query_data(bucket_name, time_range):
    # Get the current time and calculate the start time (10 seconds ago)
    end_time = datetime.now()
    start_time = end_time - timedelta(seconds=time_range)

    # Query DynamoDB for entries within the last 10 seconds
    response = table.query(
        KeyConditionExpression="bucket_name = :bucket_name AND #ts BETWEEN :start AND :end",
        ExpressionAttributeNames={"#ts": "timestamp"},
        ExpressionAttributeValues={
            ":bucket_name": bucket_name,
            ":start": start_time.isoformat(),
            ":end": end_time.isoformat()
        }
    )
    return response['Items']


def generate_basic_plot(data):
    # Extract timestamps and sizes from the data
    timestamps = [item['timestamp'] for item in data]
    sizes = [item['total_size'] for item in data]

    # Convert timestamps from strings to datetime objects for better plotting
    timestamps = [datetime.fromisoformat(ts) for ts in timestamps]

    # Get the maximum size in the data (historical high)
    max_size = max(sizes) if sizes else 0

    # Generate a basic plot
    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, sizes, label='Bucket Size')

    # Plot a horizontal line for the historical high
    plt.axhline(max_size, color='red', linestyle='--', label='Historical High')

    # Label axes
    plt.xlabel('Timestamp')
    plt.ylabel('Size (bytes)')
    plt.title('S3 Bucket Size Over Time')

    # Format x-axis to avoid overlapping timestamps
    plt.xticks(rotation=45, ha='right')

    # Add legend
    plt.legend()

    # Adjust layout
    plt.tight_layout()

    # Save the plot to /tmp directory
    plt.savefig('/tmp/plot.png')

    # Upload the plot to S3
    with open('/tmp/plot.png', 'rb') as plot_file:
        s3.upload_fileobj(plot_file, os.environ['BUCKET_NAME'], 'plot.png')


def lambda_handler(event, context):
    # Query DynamoDB for the last 10 seconds of data
    data = query_data(bucket_name, 10)

    if not data:
        return {
            'statusCode': 200,
            'body': "No data available for plotting."
        }

    # Generate and upload a basic plot
    generate_basic_plot(data)

    return {
        'statusCode': 200,
        'body': "Plot created and uploaded to S3."
    }

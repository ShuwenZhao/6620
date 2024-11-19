import json
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Lambda function to log S3 events from the LoggingQueue in JSON format.
def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    
    for record in event['Records']:
        try:
            # Parse the SQS message body
            body = json.loads(record['body'])
            
            # Extract the SNS message
            sns_message = json.loads(body['Message'])
            
            # Extract the S3 event details
            s3_event = sns_message['Records'][0]
            event_name = s3_event['eventName']  # e.g., "ObjectCreated:Put" or "ObjectRemoved:Delete"
            object_name = s3_event['s3']['object']['key']
            size_delta = s3_event['s3']['object'].get('size', 0)

            # Adjust size_delta for deletion events
            if "ObjectRemoved" in event_name:
                size_delta = -size_delta

            # Create log message
            log_message = {"action": event_name, "object_name": object_name, "size_delta": size_delta}
            logger.info(json.dumps(log_message))
        
        except KeyError as e:
            logger.warning(f"KeyError: {e}, Record: {record}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}, Record: {record}")
            
    return {"statusCode": 200, "body": "Logs generated successfully"}
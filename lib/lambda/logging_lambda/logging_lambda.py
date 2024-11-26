import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    for record in event['Records']:
        try:
            body = json.loads(record['body'])
            sns_message = json.loads(body['Message'])
            s3_event = sns_message['Records'][0]
            event_name = s3_event['eventName']
            object_name = s3_event['s3']['object']['key']
            size_delta = s3_event['s3']['object'].get('size', 0)

            if "ObjectRemoved" in event_name:
                size_delta = -size_delta

            log_message = {"action": event_name, "object_name": object_name, "size_delta": size_delta}
            logger.info(json.dumps(log_message))
        except Exception as e:
            logger.error(f"Error processing record: {e}")
    return {"statusCode": 200, "body": "Processed S3 events successfully"}

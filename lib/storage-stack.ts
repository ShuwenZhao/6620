import * as cdk from 'aws-cdk-lib';
import { Stack, StackProps } from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as s3n from 'aws-cdk-lib/aws-s3-notifications';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as snsSubscriptions from 'aws-cdk-lib/aws-sns-subscriptions';

export class StorageStack extends Stack {
  public readonly bucket: s3.Bucket;
  public readonly table: dynamodb.Table;
  public readonly snsTopic: sns.Topic;
  public readonly sizeTrackingQueue: sqs.Queue;
  public readonly loggingQueue: sqs.Queue;

  constructor(scope: cdk.App, id: string, props?: StackProps) {
    super(scope, id, props);

    // Create the S3 bucket
    this.bucket = new s3.Bucket(this, 'TestBucket', {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true, // Automatically delete objects if bucket is removed
    });

    // Create the DynamoDB table
    this.table = new dynamodb.Table(this, 'S3ObjectSizeHistory', {
      partitionKey: { name: 'bucket_name', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'timestamp', type: dynamodb.AttributeType.STRING },
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Add a secondary index
    this.table.addGlobalSecondaryIndex({
      indexName: 'SizeIndex',
      partitionKey: { name: 'bucket_name', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'total_size', type: dynamodb.AttributeType.NUMBER },
    });

    // SNS Topic
    this.snsTopic = new sns.Topic(this, 'S3EventsTopic', {
      displayName: 'SNS topic for S3 events',
    });

    // Create the SQS Queues
    this.sizeTrackingQueue = new sqs.Queue(this, 'SizeTrackingQueue', {
      visibilityTimeout: cdk.Duration.seconds(30),
    });

    this.loggingQueue = new sqs.Queue(this, 'LoggingQueue', {
      visibilityTimeout: cdk.Duration.seconds(30),
    });

    // Subscribe SQS Queues to the SNS Topic
    this.snsTopic.addSubscription(new snsSubscriptions.SqsSubscription(this.sizeTrackingQueue));
    this.snsTopic.addSubscription(new snsSubscriptions.SqsSubscription(this.loggingQueue));

    // S3 Bucket sends events to SNS Topic
    this.bucket.addEventNotification(
      s3.EventType.OBJECT_CREATED,
      new s3n.SnsDestination(this.snsTopic)
    );
    this.bucket.addEventNotification(
      s3.EventType.OBJECT_REMOVED,
      new s3n.SnsDestination(this.snsTopic)
    );

    // Outputs
    new cdk.CfnOutput(this, 'BucketName', { value: this.bucket.bucketName });
    new cdk.CfnOutput(this, 'TableName', { value: this.table.tableName });
    new cdk.CfnOutput(this, 'SnsTopicArn', { value: this.snsTopic.topicArn });
    new cdk.CfnOutput(this, 'SizeTrackingQueueUrl', { value: this.sizeTrackingQueue.queueUrl });
    new cdk.CfnOutput(this, 'LoggingQueueUrl', { value: this.loggingQueue.queueUrl });
  }
}

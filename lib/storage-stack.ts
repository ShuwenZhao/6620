import * as cdk from 'aws-cdk-lib';
import { Stack, StackProps } from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

export class StorageStack extends Stack {
  public readonly bucket: s3.Bucket;
  public readonly table: dynamodb.Table;

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
  }
}

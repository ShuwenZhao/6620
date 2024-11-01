import * as cdk from 'aws-cdk-lib';
import { Stack, StackProps } from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';

interface LambdaStackProps extends StackProps {
  bucket: s3.Bucket;
  table: dynamodb.Table;
}

export class LambdaStack extends Stack {
  public readonly sizeTrackingLambda: lambda.Function;
  public readonly plottingLambda: lambda.Function;
  public readonly driverLambda: lambda.Function;

  constructor(scope: cdk.App, id: string, props: LambdaStackProps) {
    super(scope, id, props);

    const { bucket, table } = props;

    // Size-Tracking Lambda
    this.sizeTrackingLambda = new lambda.Function(this, 'SizeTrackingLambda', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'size_tracking_lambda.lambda_handler',
      code: lambda.Code.fromAsset('lib/lambda/size_tracking_lambda'),
      environment: {
        BUCKET_NAME: bucket.bucketName,
        TABLE_NAME: table.tableName,
      },
    });

    // Plotting Lambda
    this.plottingLambda = new lambda.Function(this, 'PlottingLambda', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'plotting_lambda.lambda_handler',
      code: lambda.Code.fromAsset('lib/lambda/plotting_lambda'),
      environment: {
        TABLE_NAME: table.tableName,
      },
    });

    // Driver Lambda
    this.driverLambda = new lambda.Function(this, 'DriverLambda', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'driver_lambda.lambda_handler',
      code: lambda.Code.fromAsset('lib/lambda/driver_lambda'),
      environment: {
        BUCKET_NAME: bucket.bucketName,
        PLOTTING_LAMBDA_API_URL: 'https://1uuh0nppu4.execute-api.us-east-1.amazonaws.com/prod/plot',
      },
    });

    // Grant permissions
    this.driverLambda.addToRolePolicy(new iam.PolicyStatement({
      actions: ['s3:PutObject', 's3:GetObject', 's3:DeleteObject', 's3:ListBucket'],
      resources: ['arn:aws:s3:::test-bucket-swzhao-2024', 'arn:aws:s3:::test-bucket-swzhao-2024/*'],
    }));
    bucket.grantReadWrite(this.sizeTrackingLambda);
    table.grantReadWriteData(this.sizeTrackingLambda);
    table.grantReadData(this.plottingLambda);
  }
}

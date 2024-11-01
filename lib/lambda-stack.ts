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
        BUCKET_NAME: props.bucket.bucketName,
        TABLE_NAME: props.table.tableName,
      },
      timeout: cdk.Duration.seconds(80),
    });

    // Driver Lambda
    this.driverLambda = new lambda.Function(this, 'DriverLambda', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'driver_lambda.lambda_handler',
      code: lambda.Code.fromAsset('lib/lambda/driver_lambda'),
      environment: {
        BUCKET_NAME: props.bucket.bucketName,
        TABLE_NAME: props.table.tableName,
        PLOTTING_LAMBDA_API_URL: 'https://1uuh0nppu4.execute-api.us-east-1.amazonaws.com/prod/plot',
      },
      timeout: cdk.Duration.seconds(80),
    });

   // Grant necessary permissions
   props.bucket.grantRead(this.sizeTrackingLambda);
   props.bucket.grantPut(this.sizeTrackingLambda);
   props.table.grantWriteData(this.sizeTrackingLambda); 
   props.bucket.grantPut(this.driverLambda);
   props.bucket.grantDelete(this.driverLambda);
   props.table.grantReadData(this.plottingLambda);
   props.bucket.grantPut(this.plottingLambda);
  }
}

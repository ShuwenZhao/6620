import * as cdk from 'aws-cdk-lib';
import { Stack, StackProps } from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as lambdaEventSources from 'aws-cdk-lib/aws-lambda-event-sources';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as cloudwatchActions from 'aws-cdk-lib/aws-cloudwatch-actions';

interface LambdaStackProps extends StackProps {
  bucket: s3.Bucket;
  table: dynamodb.Table;
  sizeTrackingQueue: sqs.Queue;
  loggingQueue: sqs.Queue;
}

export class LambdaStack extends Stack {
  public readonly sizeTrackingLambda: lambda.Function;
  public readonly plottingLambda: lambda.Function;
  public readonly driverLambda: lambda.Function;
  public readonly loggingLambda: lambda.Function;
  public readonly cleanerLambda: lambda.Function;

  constructor(scope: cdk.App, id: string, props: LambdaStackProps) {
    super(scope, id, props);

    const { bucket, table, sizeTrackingQueue, loggingQueue } = props;

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

    // Add the SQS event source for SizeTrackingQueue
    this.sizeTrackingLambda.addEventSource(
      new lambdaEventSources.SqsEventSource(sizeTrackingQueue)
    );

    // Logging Lambda
    this.loggingLambda = new lambda.Function(this, 'LoggingLambda', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'logging_lambda.lambda_handler',
      code: lambda.Code.fromAsset('lib/lambda/logging_lambda'),
    });

    // Add the SQS event source for LoggingQueue
    this.loggingLambda.addEventSource(
      new lambdaEventSources.SqsEventSource(loggingQueue)
    );

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

    // Grant Logging Lambda access to CloudWatch logs
    this.loggingLambda.addToRolePolicy(
      new cdk.aws_iam.PolicyStatement({
        actions: ['logs:CreateLogGroup', 'logs:CreateLogStream', 'logs:PutLogEvents'],
        resources: ['*'],
      })
    );
    // Grant necessary permissions to the logging lambda
    props.bucket.grantRead(this.loggingLambda);

    // Cleaner Lambda
    this.cleanerLambda = new lambda.Function(this, 'CleanerLambda', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'cleaner_lambda.lambda_handler',
      code: lambda.Code.fromAsset('lib/lambda/cleaner_lambda'),
      environment: {
        BUCKET_NAME: props.bucket.bucketName,
      },
    });
    // Grant necessary permissions to the Cleaner Lambda
    props.bucket.grantRead(this.cleanerLambda); 
    props.bucket.grantDelete(this.cleanerLambda);

    // Create Metric Filter for Logging Lambda
    const logGroup = logs.LogGroup.fromLogGroupName(
      this,
      'LoggingLambdaLogGroup',
      `/aws/lambda/${this.loggingLambda.functionName}`
    );

    new logs.MetricFilter(this, 'SizeDeltaMetricFilter', {
      logGroup,
      metricNamespace: 'Assignment4App',
      metricName: 'TotalObjectSize',
      filterPattern: logs.FilterPattern.stringValue('$.size_delta', '=', 'exists'),
      metricValue: '$.size_delta',
    });

    // CloudWatch Alarm for the metric
    const sizeDeltaAlarm = new cloudwatch.Alarm(this, 'SizeDeltaAlarm', {
      metric: new cloudwatch.Metric({
        namespace: 'Assignment4App',
        metricName: 'TotalObjectSize',
        statistic: 'Sum',
        period: cdk.Duration.minutes(2),
      }),
      threshold: 20, // Threshold for the SUM of metric
      evaluationPeriods: 1,
    });

    // Set Cleaner Lambda as the alarm action
    sizeDeltaAlarm.addAlarmAction(new cloudwatchActions.LambdaAction(this.cleanerLambda));
  }
}

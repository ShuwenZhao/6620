import * as cdk from 'aws-cdk-lib';
import { StorageStack } from '../lib/storage-stack';
import { LambdaStack } from '../lib/lambda-stack';
import { ApiGatewayStack } from '../lib/api-gateway-stack';

const app = new cdk.App();

// Deploy the StorageStack
const storageStack = new StorageStack(app, 'StorageStack');

// Deploy the LambdaStack with the SQS queues as props
const lambdaStack = new LambdaStack(app, 'LambdaStack', {
  bucket: storageStack.bucket,
  table: storageStack.table,
  sizeTrackingQueue: storageStack.sizeTrackingQueue,
  loggingQueue: storageStack.loggingQueue,

});

// Deploy the ApiGatewayStack
new ApiGatewayStack(app, 'ApiGatewayStack', {
  plottingLambda: lambdaStack.plottingLambda,
});

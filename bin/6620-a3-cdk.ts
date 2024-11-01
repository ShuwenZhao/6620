import * as cdk from 'aws-cdk-lib';
import { StorageStack } from '../lib/storage-stack';
import { LambdaStack } from '../lib/lambda-stack';
import { ApiGatewayStack } from '../lib/api-gateway-stack';

const app = new cdk.App();

const storageStack = new StorageStack(app, 'StorageStack');
const lambdaStack = new LambdaStack(app, 'LambdaStack', {
  bucket: storageStack.bucket,
  table: storageStack.table,
});
new ApiGatewayStack(app, 'ApiGatewayStack', {
  plottingLambda: lambdaStack.plottingLambda,
});

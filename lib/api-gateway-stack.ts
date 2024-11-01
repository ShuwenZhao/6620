import * as cdk from 'aws-cdk-lib';
import { Stack, StackProps } from 'aws-cdk-lib';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as lambda from 'aws-cdk-lib/aws-lambda';

interface ApiGatewayStackProps extends StackProps {
  plottingLambda: lambda.Function;
}

export class ApiGatewayStack extends Stack {
  constructor(scope: cdk.App, id: string, props: ApiGatewayStackProps) {
    super(scope, id, props);

    const { plottingLambda } = props;

    const api = new apigateway.RestApi(this, 'PlottingApi', {
      restApiName: 'Plotting Service',
    });

    // Define API endpoint
    const plotResource = api.root.addResource('plot');
    plotResource.addMethod('POST', new apigateway.LambdaIntegration(plottingLambda));
  }
}

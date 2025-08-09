import json
import boto3
import os

step_functions_alert=boto3.client('stepfunctions')

STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN')

def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))
    
    for record in event['Records']:
        message = json.loads(record['body'])
        print("Processing message: " + json.dumps(message, indent=2))
        
        # Start the Step Function execution
        response = step_functions_alert.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            input=json.dumps(message)
        )
        
        print("Started Step Function execution with ARN: " + response['executionArn'])
    
    return {
        'statusCode': 200,
        'body': json.dumps('Processing complete')
    }
#!/usr/bin/env python3
"""
Script to retrieve the API key value for testing
"""

import boto3
import json

def get_api_key():
    try:
        # Get CloudFormation outputs
        cf = boto3.client('cloudformation')
        response = cf.describe_stacks(StackName='ServerlessOrderProcessing')
        
        outputs = response['Stacks'][0]['Outputs']
        api_key_id = None
        api_endpoint = None
        
        for output in outputs:
            if output['OutputKey'] == 'ApiKeyId':
                api_key_id = output['OutputValue']
            elif output['OutputKey'] == 'ApiEndpoint':
                api_endpoint = output['OutputValue']
        
        if not api_key_id:
            print("❌ API Key ID not found in stack outputs")
            return
        
        # Get the actual API key value
        apigateway = boto3.client('apigateway')
        key_response = apigateway.get_api_key(
            apiKey=api_key_id,
            includeValue=True
        )
        
        api_key_value = key_response['value']
        
        print("🔑 API Authentication Details")
        print("=" * 40)
        print(f"API Endpoint: {api_endpoint}")
        print(f"API Key: {api_key_value}")
        print()
        print("📝 Usage Example:")
        print(f"curl -X POST {api_endpoint} \\")
        print(f"  -H 'Content-Type: application/json' \\")
        print(f"  -H 'x-api-key: {api_key_value}' \\")
        print("  -d '{\"CustomerName\":\"John Doe\",\"Items\":[\"laptop\",\"mouse\"]}'")
        print()
        print("🔒 Security Notes:")
        print("- Keep this API key secure and don't commit it to version control")
        print("- The API key has rate limiting: 50 requests/second, 10,000/day")
        print("- You can create additional keys or modify limits in AWS Console")
        
    except Exception as e:
        print(f"❌ Error retrieving API key: {e}")

if __name__ == "__main__":
    get_api_key()
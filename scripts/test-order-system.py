#!/usr/bin/env python3
"""
Test script for the order processing system
Tests the complete flow from order submission to completion
"""

import requests
import json
import time
import boto3
from datetime import datetime

def get_api_key():
    """Get API key from CloudFormation stack"""
    try:
        import boto3
        cf = boto3.client('cloudformation')
        response = cf.describe_stacks(StackName='ServerlessOrderProcessing')
        
        outputs = response['Stacks'][0]['Outputs']
        api_key_id = None
        
        for output in outputs:
            if output['OutputKey'] == 'ApiKeyId':
                api_key_id = output['OutputValue']
                break
        
        if not api_key_id:
            return None
        
        # Get the actual API key value
        apigateway = boto3.client('apigateway')
        key_response = apigateway.get_api_key(
            apiKey=api_key_id,
            includeValue=True
        )
        
        return key_response['value']
    except Exception as e:
        print(f"⚠️  Could not retrieve API key: {e}")
        return None

def test_order_submission(api_endpoint):
    """Test order submission via API Gateway"""
    
    # Get API key for authentication
    api_key = get_api_key()
    
    test_orders = [
        {
            "CustomerName": "John Doe",
            "Items": ["laptop", "mouse", "keyboard"]
        },
        {
            "CustomerName": "Jane Smith", 
            "Items": ["monitor", "headphones"]
        },
        {
            "CustomerName": "Bob Johnson",
            "Items": ["tablet", "speaker", "webcam"]
        }
    ]
    
    print(f"Testing order submission to: {api_endpoint}")
    if api_key:
        print(f"Using API Key: {api_key[:8]}...")
    else:
        print("⚠️  No API key found - requests may fail if authentication is required")
    
    for i, order in enumerate(test_orders, 1):
        try:
            print(f"\n--- Test Order {i} ---")
            print(f"Customer: {order['CustomerName']}")
            print(f"Items: {order['Items']}")
            
            headers = {'Content-Type': 'application/json'}
            if api_key:
                headers['x-api-key'] = api_key
            
            response = requests.post(
                api_endpoint,
                headers=headers,
                data=json.dumps(order),
                timeout=30
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                print("✅ Order submitted successfully")
            elif response.status_code == 403:
                print("❌ Authentication failed - check API key")
            else:
                print("❌ Order submission failed")
                
        except Exception as e:
            print(f"❌ Error submitting order: {e}")
        
        time.sleep(2)  # Wait between orders

def check_order_status():
    """Check order status in DynamoDB"""
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('OrdersTable')
        
        print("\n--- Checking Order Status ---")
        
        # Scan for recent orders
        response = table.scan(
            Limit=10,
            ProjectionExpression='OrderId, CustomerName, #status, OrderDate',
            ExpressionAttributeNames={'#status': 'Status'}
        )
        
        orders = response.get('Items', [])
        
        if orders:
            print(f"Found {len(orders)} orders:")
            for order in orders:
                print(f"  Order ID: {order.get('OrderId', 'N/A')}")
                print(f"  Customer: {order.get('CustomerName', 'N/A')}")
                print(f"  Status: {order.get('Status', 'N/A')}")
                print(f"  Date: {order.get('OrderDate', 'N/A')}")
                print("  ---")
        else:
            print("No orders found")
            
    except Exception as e:
        print(f"❌ Error checking order status: {e}")

def check_inventory_levels():
    """Check current inventory levels"""
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('InventoryTable')
        
        print("\n--- Current Inventory Levels ---")
        
        response = table.scan()
        items = response.get('Items', [])
        
        if items:
            for item in sorted(items, key=lambda x: x['ItemName']):
                print(f"  {item['ItemName']}: {item.get('Stock', 0)} units")
        else:
            print("No inventory items found")
            
    except Exception as e:
        print(f"❌ Error checking inventory: {e}")

def check_sqs_messages():
    """Check SQS queue for messages"""
    try:
        sqs = boto3.client('sqs')
        
        # Get queue URL
        response = sqs.get_queue_url(QueueName='OrdersQueue')
        queue_url = response['QueueUrl']
        
        print(f"\n--- Checking SQS Queue ---")
        print(f"Queue URL: {queue_url}")
        
        # Get queue attributes
        attrs = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
        )
        
        visible_messages = attrs['Attributes'].get('ApproximateNumberOfMessages', '0')
        invisible_messages = attrs['Attributes'].get('ApproximateNumberOfMessagesNotVisible', '0')
        
        print(f"Visible messages: {visible_messages}")
        print(f"In-flight messages: {invisible_messages}")
        
    except Exception as e:
        print(f"❌ Error checking SQS: {e}")

def main():
    print("🚀 Order Processing System Test")
    print("=" * 50)
    
    # You'll need to update this with your actual API endpoint after deployment
    api_endpoint = "https://YOUR_API_ID.execute-api.ap-south-1.amazonaws.com/Prod/submitorder"
    
    print("⚠️  Please update the API endpoint in this script with your actual endpoint")
    print(f"Current endpoint: {api_endpoint}")
    
    # Uncomment the line below after updating the endpoint
    # test_order_submission(api_endpoint)
    
    # Check system status
    check_inventory_levels()
    check_order_status()
    check_sqs_messages()
    
    print("\n✅ Test complete!")

if __name__ == "__main__":
    main()
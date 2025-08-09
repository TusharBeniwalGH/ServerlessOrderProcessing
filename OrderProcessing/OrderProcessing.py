import boto3
import json
import os

dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')

INVENTORY_TABLE = os.environ['INVENTORY_TABLE']
FULFILLMENT_QUEUE_URL = os.environ['SQS_QUEUE_URL']

inventory_table = dynamodb.Table(INVENTORY_TABLE)

def item_available(item_name):
    try:
        response = inventory_table.get_item(Key={'ItemName': item_name})
        print(f"{response}")
        item = response.get('Item')
        if item and int(item.get('Stock', 0)) > 0:
            return True
    except Exception as e:
        print(f"Error checking inventory for {item_name}: {e}")
    return False

def lambda_handler(event, context):
    for record in event['Records']:
        if record['eventName'] == 'INSERT':
            new_image = record['dynamodb']['NewImage']
            order_id = new_image['OrderId']['S']
            items = json.loads(new_image['Items']['S'])
            customer_name = new_image.get('CustomerName', {}).get('S', 'Unknown')

            print(f"Checking inventory for Order {order_id}: {items}")

            inventory_ok = all(item_available(item) for item in items)

            if inventory_ok:
                print(f"Inventory OK for Order {order_id}, sending to SQS...")
                sqs.send_message(
                    QueueUrl=FULFILLMENT_QUEUE_URL,
                    MessageBody=json.dumps({
                        'order_id': order_id,
                        'customer_name': customer_name,
                        'items': items
                    })
                )
            else:
                print(f"Inventory NOT available for Order {order_id}, skipping fulfillment.")

    return {
        'statusCode': 200,
        'body': json.dumps('Processing complete')
    }

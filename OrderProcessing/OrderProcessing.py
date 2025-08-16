import boto3
import json
import os
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')

INVENTORY_TABLE = os.environ['INVENTORY_TABLE']
FULFILLMENT_QUEUE_URL = os.environ['SQS_QUEUE_URL']
ORDERS_TABLE = os.environ.get('ORDERS_TABLE', 'OrdersTable')

inventory_table = dynamodb.Table(INVENTORY_TABLE)
orders_table = dynamodb.Table(ORDERS_TABLE)

def item_available(item_name, quantity=1):
    """Check if item is available in inventory"""
    try:
        response = inventory_table.get_item(Key={'ItemName': item_name})
        item = response.get('Item')
        if item and int(item.get('Stock', 0)) >= quantity:
            return True
    except Exception as e:
        print(f"Error checking inventory for {item_name}: {e}")
    return False

def reserve_inventory(item_name, quantity=1):
    """Reserve inventory by decrementing stock"""
    try:
        response = inventory_table.update_item(
            Key={'ItemName': item_name},
            UpdateExpression='ADD Stock :val',
            ExpressionAttributeValues={':val': -quantity},
            ConditionExpression='Stock >= :val',
            ReturnValues='UPDATED_NEW'
        )
        new_stock = response['Attributes']['Stock']
        print(f"Reserved {quantity} of {item_name}. New stock: {new_stock}")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print(f"Insufficient stock for {item_name}")
            return False
        print(f"Error reserving inventory for {item_name}: {e}")
        return False

def update_order_status(order_id, status, reason=None):
    """Update order status in DynamoDB"""
    try:
        update_expression = 'SET #status = :status, LastUpdated = :timestamp'
        expression_values = {
            ':status': status,
            ':timestamp': json.dumps({"timestamp": str(boto3.Session().region_name)})
        }
        
        if reason:
            update_expression += ', StatusReason = :reason'
            expression_values[':reason'] = reason
            
        orders_table.update_item(
            Key={'OrderId': order_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames={'#status': 'Status'},
            ExpressionAttributeValues=expression_values
        )
        print(f"Updated order {order_id} status to {status}")
    except Exception as e:
        print(f"Error updating order status: {e}")

def lambda_handler(event, context):
    for record in event['Records']:
        if record['eventName'] == 'INSERT':
            new_image = record['dynamodb']['NewImage']
            order_id = new_image['OrderId']['S']
            items = json.loads(new_image['Items']['S'])
            customer_name = new_image.get('CustomerName', {}).get('S', 'Unknown')

            print(f"Processing new order {order_id} for {customer_name}: {items}")

            # Count item quantities
            item_counts = {}
            for item in items:
                item_counts[item] = item_counts.get(item, 0) + 1

            # Check inventory availability
            inventory_check_passed = True
            unavailable_items = []
            
            for item_name, quantity in item_counts.items():
                if not item_available(item_name, quantity):
                    inventory_check_passed = False
                    unavailable_items.append(f"{item_name} (need {quantity})")

            if inventory_check_passed:
                # Reserve inventory
                reservation_successful = True
                reserved_items = []
                
                for item_name, quantity in item_counts.items():
                    if reserve_inventory(item_name, quantity):
                        reserved_items.append(item_name)
                    else:
                        reservation_successful = False
                        # Rollback previously reserved items
                        for rollback_item in reserved_items:
                            rollback_quantity = item_counts[rollback_item]
                            try:
                                inventory_table.update_item(
                                    Key={'ItemName': rollback_item},
                                    UpdateExpression='ADD Stock :val',
                                    ExpressionAttributeValues={':val': rollback_quantity}
                                )
                                print(f"Rolled back reservation for {rollback_item}")
                            except Exception as e:
                                print(f"Error rolling back {rollback_item}: {e}")
                        break

                if reservation_successful:
                    print(f"Inventory reserved for Order {order_id}, sending to fulfillment...")
                    
                    # Update order status
                    update_order_status(order_id, 'Processing')
                    
                    # Send to SQS for fulfillment
                    sqs.send_message(
                        QueueUrl=FULFILLMENT_QUEUE_URL,
                        MessageBody=json.dumps({
                            'order_id': order_id,
                            'customer_name': customer_name,
                            'items': items,
                            'item_counts': item_counts
                        })
                    )
                else:
                    print(f"Failed to reserve inventory for Order {order_id}")
                    update_order_status(order_id, 'Failed', 'Inventory reservation failed')
            else:
                print(f"Inventory NOT available for Order {order_id}: {unavailable_items}")
                update_order_status(order_id, 'Failed', f'Items unavailable: {", ".join(unavailable_items)}')

    return {
        'statusCode': 200,
        'body': json.dumps('Processing complete')
    }

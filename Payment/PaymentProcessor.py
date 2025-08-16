import json
import boto3
import os
import random
import time
from decimal import Decimal

def lambda_handler(event, context):
    try:
        print(f"Processing payment for order: {json.dumps(event)}")
        
        order_id = event.get('order_id')
        customer_name = event.get('customer_name')
        items = event.get('items', [])
        
        if not order_id:
            raise ValueError("Missing order_id in event")
        
        # Calculate total amount (mock pricing)
        item_prices = {
            'laptop': 999.99,
            'mouse': 29.99,
            'keyboard': 79.99,
            'monitor': 299.99
        }
        
        total_amount = sum(item_prices.get(item.lower(), 50.0) for item in items)
        
        # Simulate payment processing
        payment_result = process_payment(order_id, total_amount, customer_name)
        
        if payment_result['success']:
            return {
                'statusCode': 200,
                'payment_status': 'SUCCESS',
                'transaction_id': payment_result['transaction_id'],
                'amount': total_amount,
                'order_id': order_id,
                'body': json.dumps('Payment processed successfully!')
            }
        else:
            return {
                'statusCode': 400,
                'payment_status': 'FAILED',
                'error': payment_result['error'],
                'order_id': order_id,
                'body': json.dumps(f'Payment failed: {payment_result["error"]}')
            }
            
    except Exception as e:
        print(f"Payment processing error: {str(e)}")
        return {
            'statusCode': 500,
            'payment_status': 'ERROR',
            'error': str(e),
            'order_id': event.get('order_id', 'unknown'),
            'body': json.dumps(f'Payment processing error: {str(e)}')
        }

def process_payment(order_id, amount, customer_name):
    """
    Mock payment processing - replace with actual payment gateway integration
    (Stripe, PayPal, etc.)
    """
    try:
        # Simulate processing time
        time.sleep(0.5)
        
        # Simulate 90% success rate
        if random.random() < 0.9:
            transaction_id = f"txn_{order_id}_{int(time.time())}"
            print(f"Payment successful for order {order_id}: ${amount}")
            return {
                'success': True,
                'transaction_id': transaction_id,
                'amount': amount
            }
        else:
            # Simulate payment failure
            errors = ['Insufficient funds', 'Card declined', 'Invalid card number']
            error = random.choice(errors)
            print(f"Payment failed for order {order_id}: {error}")
            return {
                'success': False,
                'error': error
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'Payment gateway error: {str(e)}'
        }
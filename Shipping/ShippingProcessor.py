import json
import boto3
import os
import random
import time
from datetime import datetime, timedelta

def lambda_handler(event, context):
    try:
        print(f"Processing shipping for order: {json.dumps(event)}")
        
        order_id = event.get('order_id')
        customer_name = event.get('customer_name')
        items = event.get('items', [])
        payment_status = event.get('payment_status')
        
        if not order_id:
            raise ValueError("Missing order_id in event")
            
        if payment_status != 'SUCCESS':
            return {
                'statusCode': 400,
                'shipping_status': 'CANCELLED',
                'error': 'Payment not successful',
                'order_id': order_id,
                'body': json.dumps('Shipping cancelled - payment failed')
            }
        
        # Calculate shipping details
        shipping_result = calculate_shipping(order_id, items, customer_name)
        
        if shipping_result['success']:
            return {
                'statusCode': 200,
                'shipping_status': 'SCHEDULED',
                'tracking_number': shipping_result['tracking_number'],
                'estimated_delivery': shipping_result['estimated_delivery'],
                'shipping_cost': shipping_result['shipping_cost'],
                'carrier': shipping_result['carrier'],
                'order_id': order_id,
                'body': json.dumps('Shipping scheduled successfully!')
            }
        else:
            return {
                'statusCode': 400,
                'shipping_status': 'FAILED',
                'error': shipping_result['error'],
                'order_id': order_id,
                'body': json.dumps(f'Shipping failed: {shipping_result["error"]}')
            }
            
    except Exception as e:
        print(f"Shipping processing error: {str(e)}")
        return {
            'statusCode': 500,
            'shipping_status': 'ERROR',
            'error': str(e),
            'order_id': event.get('order_id', 'unknown'),
            'body': json.dumps(f'Shipping processing error: {str(e)}')
        }

def calculate_shipping(order_id, items, customer_name):
    """
    Mock shipping calculation - replace with actual carrier API integration
    (FedEx, UPS, DHL, etc.)
    """
    try:
        # Simulate processing time
        time.sleep(0.3)
        
        # Calculate shipping cost based on items
        base_cost = 9.99
        item_weight = len(items) * 2.5  # Mock weight calculation
        shipping_cost = base_cost + (item_weight * 0.5)
        
        # Select carrier based on cost optimization
        carriers = ['FedEx', 'UPS', 'DHL', 'USPS']
        carrier = random.choice(carriers)
        
        # Generate tracking number
        tracking_number = f"{carrier[:3].upper()}{order_id[-6:]}{random.randint(1000, 9999)}"
        
        # Calculate estimated delivery (3-7 business days)
        delivery_days = random.randint(3, 7)
        estimated_delivery = (datetime.now() + timedelta(days=delivery_days)).strftime('%Y-%m-%d')
        
        # Simulate 95% success rate
        if random.random() < 0.95:
            print(f"Shipping scheduled for order {order_id}: {carrier} - {tracking_number}")
            return {
                'success': True,
                'tracking_number': tracking_number,
                'estimated_delivery': estimated_delivery,
                'shipping_cost': round(shipping_cost, 2),
                'carrier': carrier
            }
        else:
            # Simulate shipping failure
            errors = ['Address validation failed', 'Carrier unavailable', 'Shipping restrictions']
            error = random.choice(errors)
            print(f"Shipping failed for order {order_id}: {error}")
            return {
                'success': False,
                'error': error
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'Shipping service error: {str(e)}'
        }
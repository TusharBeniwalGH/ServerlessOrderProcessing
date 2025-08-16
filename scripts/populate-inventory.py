#!/usr/bin/env python3
"""
Script to populate the inventory table with sample data
Run this after deploying the stack to have test inventory items
"""

import boto3
import json
from decimal import Decimal

def populate_inventory():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('InventoryTable')
    
    # Sample inventory items (using Decimal for prices)
    inventory_items = [
        {'ItemName': 'laptop', 'Stock': 50, 'Price': Decimal('999.99'), 'Description': 'High-performance laptop'},
        {'ItemName': 'mouse', 'Stock': 100, 'Price': Decimal('29.99'), 'Description': 'Wireless optical mouse'},
        {'ItemName': 'keyboard', 'Stock': 75, 'Price': Decimal('79.99'), 'Description': 'Mechanical keyboard'},
        {'ItemName': 'monitor', 'Stock': 30, 'Price': Decimal('299.99'), 'Description': '24-inch LED monitor'},
        {'ItemName': 'headphones', 'Stock': 60, 'Price': Decimal('149.99'), 'Description': 'Noise-canceling headphones'},
        {'ItemName': 'webcam', 'Stock': 40, 'Price': Decimal('89.99'), 'Description': 'HD webcam'},
        {'ItemName': 'speaker', 'Stock': 25, 'Price': Decimal('199.99'), 'Description': 'Bluetooth speaker'},
        {'ItemName': 'tablet', 'Stock': 20, 'Price': Decimal('399.99'), 'Description': '10-inch tablet'}
    ]
    
    print("Populating inventory table...")
    
    success_count = 0
    for item in inventory_items:
        try:
            table.put_item(Item=item)
            print(f"✅ Added {item['ItemName']}: {item['Stock']} units at ${item['Price']}")
            success_count += 1
        except Exception as e:
            print(f"❌ Error adding {item['ItemName']}: {e}")
    
    print(f"\nInventory population complete! Successfully added {success_count}/{len(inventory_items)} items.")
    
    # Verify the data was added
    try:
        print("\n📋 Verifying inventory...")
        response = table.scan()
        items = response.get('Items', [])
        print(f"Total items in inventory: {len(items)}")
        
        for item in sorted(items, key=lambda x: x['ItemName']):
            print(f"  {item['ItemName']}: {item['Stock']} units @ ${item['Price']}")
            
    except Exception as e:
        print(f"⚠️  Could not verify inventory: {e}")

if __name__ == "__main__":
    populate_inventory()
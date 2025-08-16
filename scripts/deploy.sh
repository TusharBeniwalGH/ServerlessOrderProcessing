#!/bin/bash

# Development helper script for the Order Processing System
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

show_help() {
    echo "🚀 Order Processing System - Development Helper"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  deploy          Quick deploy (build + deploy)"
    echo "  status          Show system status and endpoints"
    echo "  test            Run system tests"
    echo "  populate        Populate inventory with sample data"
    echo "  clean           Clean up build artifacts"
    echo "  monitor         Show monitoring dashboard URLs"
    echo "  delete          Delete the entire AWS stack"
    echo "  help            Show this help message"
    echo ""
}

get_stack_outputs() {
    aws cloudformation describe-stacks \
        --stack-name ServerlessOrderProcessing \
        --query 'Stacks[0].Outputs' \
        --output table 2>/dev/null || echo "Stack not found or not deployed"
}

show_status() {
    print_status "System Status"
    echo "=============="
    get_stack_outputs
    echo ""
    
    print_info "Quick test command:"
    API_ENDPOINT=$(aws cloudformation describe-stacks \
        --stack-name ServerlessOrderProcessing \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
        --output text 2>/dev/null)
    
    if [ ! -z "$API_ENDPOINT" ] && [ "$API_ENDPOINT" != "None" ]; then
        echo "curl -X POST $API_ENDPOINT \\"
        echo "  -H 'Content-Type: application/json' \\"
        echo "  -d '{\"CustomerName\":\"Test User\",\"Items\":[\"laptop\",\"mouse\"]}'"
    fi
}

quick_deploy() {
    print_status "Quick deployment..."
    sam build && sam deploy
    
    if [ $? -eq 0 ]; then
        print_status "Deployment successful! 🎉"
        show_status
    else
        print_error "Deployment failed!"
        exit 1
    fi
}



run_tests() {
    print_status "Running system tests..."
    
    # Check if inventory is populated
    python3 -c "
import boto3
try:
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('InventoryTable')
    response = table.scan(Limit=1)
    if not response.get('Items'):
        print('⚠️  Inventory table is empty. Run: $0 populate')
        exit(1)
    print('✅ Inventory table has data')
except Exception as e:
    print(f'❌ Error checking inventory: {e}')
    exit(1)
"
    
    if [ $? -eq 0 ]; then
        python3 scripts/test-order-system.py
    fi
}

populate_inventory() {
    print_status "Populating inventory..."
    python3 scripts/populate-inventory.py
}

show_monitoring() {
    print_status "Monitoring Resources"
    echo "===================="
    
    REGION=$(aws configure get region)
    
    echo "CloudWatch Dashboards:"
    echo "https://$REGION.console.aws.amazon.com/cloudwatch/home?region=$REGION#dashboards:"
    echo ""
    echo "Step Functions Console:"
    echo "https://$REGION.console.aws.amazon.com/states/home?region=$REGION#/statemachines"
    echo ""
    echo "DynamoDB Tables:"
    echo "https://$REGION.console.aws.amazon.com/dynamodbv2/home?region=$REGION#tables"
    echo ""
    echo "Lambda Functions:"
    echo "https://$REGION.console.aws.amazon.com/lambda/home?region=$REGION#/functions"
}

clean_build() {
    print_status "Cleaning build artifacts..."
    rm -rf .aws-sam/
    print_status "Clean complete!"
}

delete_stack() {
    print_status "Deleting AWS stack..."
    print_warning "This will delete ALL resources in the stack including:"
    echo "  - All Lambda functions"
    echo "  - DynamoDB tables (and ALL data)"
    echo "  - SQS queues"
    echo "  - Step Functions"
    echo "  - API Gateway"
    echo "  - CloudWatch alarms"
    echo ""
    
    read -p "Are you sure you want to delete the stack? Type 'DELETE' to confirm: " confirmation
    
    if [ "$confirmation" = "DELETE" ]; then
        print_status "Deleting stack ServerlessOrderProcessing..."
        sam delete --stack-name ServerlessOrderProcessing --no-prompts
        
        if [ $? -eq 0 ]; then
            print_status "Stack deleted successfully! 🗑️"
        else
            print_error "Stack deletion failed!"
            exit 1
        fi
    else
        print_status "Stack deletion cancelled."
    fi
}

# Main script logic
case "${1:-help}" in
    deploy)
        quick_deploy
        ;;
    status)
        show_status
        ;;
    test)
        run_tests
        ;;
    populate)
        populate_inventory
        ;;
    monitor)
        show_monitoring
        ;;
    clean)
        clean_build
        ;;
    delete)
        delete_stack
        ;;
    help|*)
        show_help
        ;;
esac
# Serverless Order Processing System

A serverless order processing system built with AWS SAM, featuring event-driven architecture, API key authentication, proper error handling, and comprehensive monitoring.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Client/User   │    │   API Gateway    │    │  OrderSubmission    │
│                 │───▶│  (API Key Auth)  │───▶│   Lambda (.NET)     │
│  curl/Postman   │    │  Rate Limiting   │    │                     │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
                                                           │
                                                           ▼
                       ┌─────────────────────────────────────────────────┐
                       │              DynamoDB Orders Table              │
                       │  ┌─────────────────────────────────────────┐   │
                       │  │ OrderId, CustomerName, Items, Status    │   │
                       │  │ GSI: StatusIndex, CustomerIndex         │   │
                       │  └─────────────────────────────────────────┘   │
                       └─────────────────────────────────────────────────┘
                                                │
                                                ▼ (DynamoDB Stream)
                       ┌─────────────────────────────────────────────────┐
                       │         OrderProcessing Lambda (Python)        │
                       │  • Check inventory availability                 │
                       │  • Atomic stock reservation                     │
                       │  • Update order status                          │
                       │  • Rollback on failure                          │
                       └─────────────────────────────────────────────────┘
                                    │                        │
                                    ▼                        ▼
                    ┌─────────────────────┐    ┌─────────────────────────┐
                    │ DynamoDB Inventory  │    │      SQS Queue          │
                    │      Table          │    │  ┌─────────────────┐   │
                    │ ┌─────────────────┐ │    │  │ Successful      │   │
                    │ │ ItemName, Stock │ │    │  │ Orders Only     │   │
                    │ │ Price, Desc     │ │    │  └─────────────────┘   │
                    │ └─────────────────┘ │    │          │              │
                    └─────────────────────┘    │          ▼              │
                                               │  ┌─────────────────┐   │
                                               │  │ Dead Letter     │   │
                                               │  │ Queue (DLQ)     │   │
                                               │  └─────────────────┘   │
                                               └─────────────────────────┘
                                                          │
                                                          ▼
                       ┌─────────────────────────────────────────────────┐
                       │        SQSProcessor Lambda (Python)            │
                       │        Triggers Step Functions                  │
                       └─────────────────────────────────────────────────┘
                                                │
                                                ▼
                       ┌─────────────────────────────────────────────────┐
                       │              Step Functions Workflow            │
                       │                                                 │
                       │  ┌─────────────┐    ┌─────────────────────┐   │
                       │  │ PaymentStep │───▶│   ShippingStep      │   │
                       │  │ (Retry 3x)  │    │   (Retry 2x)        │   │
                       │  └─────────────┘    └─────────────────────┘   │
                       │         │                       │             │
                       │         ▼                       ▼             │
                       │  ┌─────────────┐    ┌─────────────────────┐   │
                       │  │PaymentFailed│    │  ShippingFailed     │   │
                       │  └─────────────┘    └─────────────────────┘   │
                       └─────────────────────────────────────────────────┘
                                    │                        │
                                    ▼                        ▼
                    ┌─────────────────────┐    ┌─────────────────────────┐
                    │ PaymentProcessor    │    │ ShippingProcessor       │
                    │ Lambda (Python)     │    │ Lambda (Python)         │
                    │ • Mock payment      │    │ • Carrier selection     │
                    │ • 90% success rate  │    │ • Tracking numbers      │
                    │ • Transaction IDs   │    │ • Delivery estimates    │
                    └─────────────────────┘    └─────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                          Monitoring & Observability                    │
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐ │
│  │ CloudWatch      │  │ X-Ray Tracing   │  │ CloudWatch Alarms       │ │
│  │ Logs & Metrics  │  │ End-to-End      │  │ • Function Errors       │ │
│  │                 │  │ Request Traces  │  │ • DLQ Messages          │ │
│  └─────────────────┘  └─────────────────┘  │ • Step Function Fails   │ │
│                                            └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

## Features

- **Multi-language support**: .NET 8 for API, Python for processing
- **Event-driven architecture**: DynamoDB Streams, SQS, Step Functions
- **API Authentication**: API key-based authentication with rate limiting
- **Inventory management**: Real-time stock checking and atomic reservation
- **Error handling**: Dead letter queues, retry logic, comprehensive error states
- **Monitoring**: X-Ray tracing, CloudWatch alarms, custom metrics
- **Cross-platform**: Windows PowerShell and Linux/Mac bash scripts
- **Scalability**: Serverless auto-scaling, pay-per-use pricing

## Prerequisites

- AWS CLI configured with appropriate permissions
- SAM CLI installed
- Python 3.12+ for scripts and inventory management
- .NET 8 SDK for local development
- PowerShell (Windows) or Bash (Linux/Mac)

## Quick Start

### 1. Deploy the System

**Windows (PowerShell):**
```powershell
.\scripts\deploy.ps1 deploy
```

**Linux/Mac (Bash):**
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh deploy
```

**Manual deployment:**
```bash
sam build
sam deploy
```

### 2. Populate Inventory

**Using helper script:**
```powershell
# Windows
.\scripts\deploy.ps1 populate

# Linux/Mac
./scripts/deploy.sh populate
```

**Manual:**
```bash
python scripts/populate-inventory.py
```

### 3. Get API Key for Authentication

```powershell
# Windows
.\scripts\deploy.ps1 apikey

# Linux/Mac  
./scripts/deploy.sh apikey

# Manual
python scripts/get-api-key.py
```

### 4. Test the System

```powershell
# Windows
.\scripts\deploy.ps1 test

# Linux/Mac
./scripts/deploy.sh test

# Manual
python scripts/test-order-system.py
```

## API Usage with Authentication

### Submit an Order (Authenticated)

```bash
curl -X POST https://YOUR_API_ENDPOINT/submitorder \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY_HERE" \
  -d '{
    "CustomerName": "John Doe",
    "Items": ["laptop", "mouse", "keyboard"]
  }'
```

### Response
```json
{
  "statusCode": 200,
  "body": "Order submitted successfully"
}
```

### Authentication Errors
```json
{
  "statusCode": 403,
  "body": "Forbidden"
}
```

## System Components

### 1. Order Submission (OrderSubmission/)
- **Runtime**: .NET 8
- **Trigger**: API Gateway POST /submitorder (API key required)
- **Function**: Validates and stores orders in DynamoDB with status tracking

### 2. Order Processing (OrderProcessing/)
- **Runtime**: Python 3.12
- **Trigger**: DynamoDB Stream from Orders table
- **Function**: Checks inventory availability, atomically reserves stock, updates order status

### 3. SQS Processor (SQSProcessorFunction/)
- **Runtime**: Python 3.12
- **Trigger**: SQS messages from Orders queue
- **Function**: Triggers Step Functions workflow for payment and shipping

### 4. Payment Processor (Payment/)
- **Runtime**: Python 3.12
- **Trigger**: Step Functions
- **Function**: Processes payments with retry logic (mock implementation with 90% success rate)

### 5. Shipping Processor (Shipping/)
- **Runtime**: Python 3.12
- **Trigger**: Step Functions
- **Function**: Handles shipping logistics with carrier selection (mock implementation)

## Database Schema

### Orders Table
- **Primary Key**: OrderId (String)
- **Attributes**: CustomerName, Items, Status, OrderDate, LastUpdated, StatusReason
- **GSI**: StatusIndex (query by status), CustomerIndex (query by customer)
- **Stream**: NEW_AND_OLD_IMAGES for real-time processing

### Inventory Table
- **Primary Key**: ItemName (String)
- **Attributes**: Stock (Number), Price (Decimal), Description (String)
- **Operations**: Atomic stock reservation with conditional updates

## Authentication & Security

### API Key Authentication
- **Rate Limiting**: 50 requests/second, 10,000 requests/day
- **Burst Limit**: 100 concurrent requests
- **Usage Plans**: Configurable quotas and throttling
- **Key Management**: Retrievable via helper scripts

### Security Features
- IAM roles with least-privilege access
- API Gateway request validation
- DynamoDB encryption at rest
- Lambda environment variable encryption
- CloudWatch log encryption

## Monitoring & Observability

### CloudWatch Alarms
- **OrderSubmission-Errors**: Alerts on Lambda function errors (threshold: 5 errors in 5 minutes)
- **OrdersDeadLetterQueue-Messages**: Alerts when messages appear in DLQ
- **OrderWorkflow-Failures**: Alerts on Step Function execution failures

### X-Ray Tracing
- End-to-end request tracing across all services
- Performance bottleneck identification
- Error root cause analysis with detailed traces
- Service map visualization

### Custom Metrics
- Order processing rates and success/failure ratios
- Inventory reservation success rates
- Payment processing success rates
- API authentication failure rates

## Helper Scripts

### Windows PowerShell (`scripts/deploy.ps1`)
```powershell
.\scripts\deploy.ps1 deploy     # Quick deployment
.\scripts\deploy.ps1 status     # Show system status and endpoints
.\scripts\deploy.ps1 test       # Run comprehensive tests
.\scripts\deploy.ps1 populate   # Populate inventory with sample data
.\scripts\deploy.ps1 apikey     # Get API key for authentication
.\scripts\deploy.ps1 monitor    # Show monitoring dashboard URLs
.\scripts\deploy.ps1 clean      # Clean build artifacts
```

### Linux/Mac Bash (`scripts/deploy.sh`)
```bash
./scripts/deploy.sh deploy      # Quick deployment
./scripts/deploy.sh status      # Show system status and endpoints
./scripts/deploy.sh test        # Run comprehensive tests
./scripts/deploy.sh populate    # Populate inventory with sample data
./scripts/deploy.sh monitor     # Show monitoring dashboard URLs
./scripts/deploy.sh clean       # Clean build artifacts
```

### Standalone Scripts
- `scripts/populate-inventory.py` - Populate inventory with sample data
- `scripts/get-api-key.py` - Retrieve API key for authentication
- `scripts/test-order-system.py` - Comprehensive system testing

## Error Handling & Resilience

### Retry Logic
- **Lambda functions**: Automatic retries with exponential backoff
- **Step Functions**: Separate retry policies for TaskFailed and ALL errors
- **SQS**: Dead letter queue after 3 failed delivery attempts
- **DynamoDB**: Conditional updates for inventory reservation with rollback

### Error States & Recovery
- **Payment failures** → Order status updated to "Failed", inventory released
- **Inventory unavailable** → Order rejected immediately, customer notified
- **Shipping issues** → Order marked for manual intervention
- **System failures** → Messages preserved in dead letter queue for replay

### Inventory Management
- **Atomic reservations**: Stock decremented only if sufficient quantity available
- **Rollback mechanism**: Failed reservations automatically restore stock levels
- **Concurrent safety**: Conditional updates prevent overselling

## Cost Optimization

- Pay-per-request DynamoDB billing
- Lambda provisioned concurrency for critical functions
- SQS message batching
- CloudWatch log retention policies

## Development

### Local Testing
```bash
# Start SAM local API
sam local start-api

# Test locally (no API key required for local)
curl http://localhost:3000/submitorder \
  -H "Content-Type: application/json" \
  -d '{"CustomerName":"Test","Items":["laptop"]}'
```

### Development Workflow
1. **Make changes** to Lambda functions or template
2. **Quick deploy**: `.\scripts\deploy.ps1 deploy` (Windows) or `./scripts/deploy.sh deploy` (Linux/Mac)
3. **Test changes**: `.\scripts\deploy.ps1 test`
4. **Monitor**: Check CloudWatch or use `.\scripts\deploy.ps1 monitor`

### Adding New Features
1. Update the SAM template (`template.yaml`)
2. Implement the Lambda function code
3. Add appropriate IAM permissions (least-privilege)
4. Update monitoring and alarms
5. Add tests to `scripts/test-order-system.py`
6. Update documentation

## Troubleshooting

### Common Issues

1. **API calls returning 403 Forbidden**
   - **Solution**: Get API key with `.\scripts\deploy.ps1 apikey` and include `x-api-key` header
   - **Check**: Verify API key is not expired or disabled

2. **Orders not processing**
   - **Check**: DynamoDB Stream is enabled on Orders table
   - **Verify**: IAM permissions for OrderProcessingFunction
   - **Review**: CloudWatch logs for processing errors

3. **Inventory errors (Float types not supported)**
   - **Solution**: Use `Decimal` types instead of `float` in Python code
   - **Fixed**: Already resolved in `scripts/populate-inventory.py`

4. **Step Functions failing**
   - **Check**: Lambda function errors in CloudWatch
   - **Verify**: IAM role permissions for Step Functions
   - **Review**: Step Function execution history in AWS Console

5. **SAM deployment errors**
   - **States.ALL error**: Fixed - `States.ALL` must appear alone in ErrorEquals
   - **SQS VisibilityTimeoutSeconds**: Fixed - use `VisibilityTimeout` instead

### Useful Commands

```powershell
# Windows PowerShell
.\scripts\deploy.ps1 status          # Check system status
.\scripts\deploy.ps1 apikey          # Get API key
.\scripts\deploy.ps1 monitor         # Open monitoring dashboards

# Check stack status
aws cloudformation describe-stacks --stack-name ServerlessOrderProcessing

# Monitor Step Functions
aws stepfunctions list-executions --state-machine-arn YOUR_STATE_MACHINE_ARN

# View recent logs (manual)
sam logs --stack-name ServerlessOrderProcessing --start-time '10min ago'
```

### Debug Tips
- **Use helper scripts** instead of manual commands for consistency
- **Check API key** first if getting authentication errors
- **Populate inventory** before testing order submission
- **Monitor CloudWatch** alarms for system health

## Production Considerations

### Before Going Live
- [ ] Replace mock payment/shipping with real integrations (Stripe, PayPal, FedEx, UPS)
- [ ] Set up proper monitoring dashboards in CloudWatch
- [ ] Configure SNS notifications for CloudWatch alarms
- [ ] ✅ API key authentication implemented (consider upgrading to Cognito for user management)
- [ ] Set up CI/CD pipeline with GitHub Actions or AWS CodePipeline
- [ ] ✅ Comprehensive test suite implemented
- [ ] Configure backup and disaster recovery for DynamoDB
- [ ] Set up proper logging retention policies
- [ ] Implement request/response validation schemas

### Scaling Considerations
- **Monitor Lambda concurrent executions** and set reserved concurrency if needed
- **Consider DynamoDB provisioned capacity** for predictable high-volume workloads
- **Implement API Gateway caching** for frequently accessed data
- **Use CloudFront** for global distribution and reduced latency
- **Add ElastiCache** for inventory caching to reduce DynamoDB reads
- **Implement batch processing** for high-volume order scenarios

### Security Enhancements for Production
- **Upgrade to Cognito User Pools** for user authentication and management
- **Implement request signing** for additional API security
- **Add WAF rules** to protect against common attacks
- **Enable GuardDuty** for threat detection
- **Use Secrets Manager** for sensitive configuration data
- **Implement field-level encryption** for PII data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
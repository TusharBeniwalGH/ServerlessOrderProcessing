# Development helper script for the Order Processing System (PowerShell)
param(
    [Parameter(Position=0)]
    [ValidateSet("deploy", "status", "test", "populate", "monitor", "clean", "apikey", "help")]
    [string]$Command = "help"
)

$StackName = "ServerlessOrderProcessing"

# Colors for PowerShell
function Write-Status($Message) {
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Error-Custom($Message) {
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Warning-Custom($Message) {
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Info($Message) {
    Write-Host "[DEBUG] $Message" -ForegroundColor Blue
}

function Show-Help {
    Write-Host ""
    Write-Host "🚀 Order Processing System - Development Helper (PowerShell)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\scripts\deploy.ps1 [COMMAND]"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  deploy          Quick deploy (build + deploy)"
    Write-Host "  status          Show system status and endpoints"
    Write-Host "  test            Run system tests"
    Write-Host "  populate        Populate inventory with sample data"
    Write-Host "  clean           Clean up build artifacts"
    Write-Host "  monitor         Show monitoring dashboard URLs"
    Write-Host "  apikey          Get API key for authentication"
    Write-Host "  help            Show this help message"
    Write-Host ""
}

function Get-StackOutputs {
    try {
        Write-Host "Getting stack outputs..."
        aws cloudformation describe-stacks --stack-name $StackName --query "Stacks[0].Outputs" --output table
    }
    catch {
        Write-Host "Stack not found or not deployed"
    }
}

function Show-Status {
    Write-Status "System Status"
    Write-Host "=============="
    Get-StackOutputs
    Write-Host ""
    
    Write-Info "Getting API authentication details..."
    python scripts\get-api-key.py
}

function Invoke-QuickDeploy {
    Write-Status "Quick deployment..."
    
    # Change to project root directory (one level up from scripts)
    $originalLocation = Get-Location
    Set-Location (Split-Path $PSScriptRoot -Parent)
    
    try {
        sam build
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "Build failed!"
            exit 1
        }
        
        sam deploy
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "Deployment failed!"
            exit 1
        }
        else {
            Write-Status "Deployment successful! 🎉"
            Show-Status
        }
    }
    finally {
        # Return to original location
        Set-Location $originalLocation
    }
}



function Invoke-Tests {
    Write-Status "Running system tests..."
    
    # Check if Python is available
    try {
        python --version | Out-Null
    }
    catch {
        Write-Error-Custom "Python is not installed or not in PATH"
        exit 1
    }
    
    # Check if inventory is populated
    $checkInventory = @"
import boto3
try:
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('InventoryTable')
    response = table.scan(Limit=1)
    if not response.get('Items'):
        exit(1)
    print('✅ Inventory table has data')
except Exception as e:
    print(f'❌ Error checking inventory: {e}')
    exit(1)
"@
    
    $result = python -c $checkInventory
    if ($LASTEXITCODE -ne 0) {
        Write-Warning-Custom "Inventory table is empty. Run: .\scripts\deploy.ps1 populate"
        exit 1
    }
    
    Write-Host $result
    python scripts\test-order-system.py
}

function Set-InventoryData {
    Write-Status "Populating inventory..."
    python populate-inventory.py
}

function Show-Monitoring {
    Write-Status "Monitoring Resources"
    Write-Host "===================="
    
    try {
        $Region = aws configure get region
        if (-not $Region) { $Region = "us-east-1" }
        
        Write-Host "CloudWatch Dashboards:"
        Write-Host "https://$Region.console.aws.amazon.com/cloudwatch/home?region=$Region#dashboards:"
        Write-Host ""
        Write-Host "Step Functions Console:"
        Write-Host "https://$Region.console.aws.amazon.com/states/home?region=$Region#/statemachines"
        Write-Host ""
        Write-Host "DynamoDB Tables:"
        Write-Host "https://$Region.console.aws.amazon.com/dynamodbv2/home?region=$Region#tables"
        Write-Host ""
        Write-Host "Lambda Functions:"
        Write-Host "https://$Region.console.aws.amazon.com/lambda/home?region=$Region#/functions"
    }
    catch {
        Write-Warning-Custom "Could not retrieve AWS region"
    }
}

function Remove-BuildArtifacts {
    Write-Status "Cleaning build artifacts..."
    
    # Change to project root directory
    $originalLocation = Get-Location
    Set-Location (Split-Path $PSScriptRoot -Parent)
    
    try {
        if (Test-Path ".aws-sam") {
            Remove-Item -Recurse -Force ".aws-sam"
        }
        Write-Status "Clean complete!"
    }
    finally {
        Set-Location $originalLocation
    }
}

function Get-ApiKey {
    Write-Status "Getting API Key..."
    python scripts\get-api-key.py
}

# Main script logic
switch ($Command) {
    "deploy" { Invoke-QuickDeploy }
    "status" { Show-Status }
    "test" { Invoke-Tests }
    "populate" { Set-InventoryData }
    "monitor" { Show-Monitoring }
    "clean" { Remove-BuildArtifacts }
    "apikey" { Get-ApiKey }
    default { Show-Help }
}
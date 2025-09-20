#!/usr/bin/env python3
"""
Deployment script for AWS Lambda function
"""

import boto3
import zipfile
import os
import json
from pathlib import Path
import tempfile
import shutil


def create_lambda_package():
    """Create a deployment package for Lambda"""
    
    # Create temporary directory for package
    with tempfile.TemporaryDirectory() as temp_dir:
        package_dir = Path(temp_dir) / "package"
        package_dir.mkdir()
        
        print("Creating Lambda deployment package...")
        
        # Copy source code
        src_files = [
            "lambda_handler.py",
            "main.py"
        ]
        
        for item in src_files:
            src_path = Path(item)
            if src_path.is_file():
                shutil.copy2(src_path, package_dir / src_path.name)
                print(f"  Added: {src_path.name}")
        
        # Create zip file
        zip_path = Path("lambda_deployment.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(package_dir)
                    zipf.write(file_path, arcname)
        
        print(f"Package created: {zip_path}")
        return zip_path


def deploy_lambda_function(function_name="mongodb-mcp-api", region="us-east-1"):
    """Deploy the Lambda function"""
    
    # Create package
    zip_path = create_lambda_package()
    
    # Initialize Lambda client
    lambda_client = boto3.client('lambda', region_name=region)
    
    try:
        # Read zip file
        with open(zip_path, 'rb') as f:
            zip_content = f.read()
        
        # Check if function exists
        function_exists = False
        try:
            lambda_client.get_function(FunctionName=function_name)
            function_exists = True
        except lambda_client.exceptions.ResourceNotFoundException:
            pass
        
        if function_exists:
            # Update existing function
            print(f"Updating existing function: {function_name}")
            response = lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_content
            )
        else:
            # Create new function
            print(f"Creating new function: {function_name}")
            
            # Get account ID for role ARN
            sts = boto3.client('sts')
            account_id = sts.get_caller_identity()['Account']
            role_arn = f"arn:aws:iam::{account_id}:role/lambda-execution-role"
            
            response = lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.10',
                Role=role_arn,
                Handler='lambda_handler.lambda_handler',
                Code={'ZipFile': zip_content},
                Description='MongoDB MCP API Lambda Function',
                Timeout=300,  # 5 minutes
                MemorySize=1024,
                Environment={
                    'Variables': {
                        'LAMBDA_RUNTIME': 'true',
                        'PYTHONPATH': '/var/task'
                    }
                }
            )
        
        print(f"Function ARN: {response['FunctionArn']}")
        
        # Create API Gateway integration (optional)
        create_api_gateway(function_name, region)
        
    finally:
        # Clean up
        if zip_path.exists():
            zip_path.unlink()


def create_api_gateway(function_name, region):
    """Create API Gateway for the Lambda function"""
    
    apigateway = boto3.client('apigateway', region_name=region)
    lambda_client = boto3.client('lambda', region_name=region)
    
    try:
        # Create REST API
        api = apigateway.create_rest_api(
            name=f'{function_name}-api',
            description='MongoDB MCP API Gateway'
        )
        api_id = api['id']
        
        # Get root resource
        resources = apigateway.get_resources(restApiId=api_id)
        root_id = resources['items'][0]['id']
        
        # Create resource
        resource = apigateway.create_resource(
            restApiId=api_id,
            parentId=root_id,
            pathPart='mongodb-mcp'
        )
        resource_id = resource['id']
        
        # Create method
        apigateway.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            authorizationType='NONE'
        )
        
        # Get account ID
        sts = boto3.client('sts')
        account_id = sts.get_caller_identity()['Account']
        
        # Set up Lambda integration
        lambda_arn = f"arn:aws:lambda:{region}:{account_id}:function:{function_name}"
        
        apigateway.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=f"arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
        )
        
        # Deploy API
        deployment = apigateway.create_deployment(
            restApiId=api_id,
            stageName='dev'
        )
        
        api_url = f"https://{api_id}.execute-api.{region}.amazonaws.com/dev/mongodb-mcp"
        print(f"API URL: {api_url}")
        
        # Add Lambda permission for API Gateway
        try:
            lambda_client.add_permission(
                FunctionName=function_name,
                StatementId='api-gateway-invoke',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f"arn:aws:execute-api:{region}:{account_id}:{api_id}/*/*"
            )
        except lambda_client.exceptions.ResourceConflictException:
            pass  # Permission already exists
        
    except Exception as e:
        print(f"Error creating API Gateway: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy MongoDB MCP Lambda Function")
    parser.add_argument("--function-name", default="mongodb-mcp-api", help="Lambda function name")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    
    args = parser.parse_args()
    
    deploy_lambda_function(args.function_name, args.region)
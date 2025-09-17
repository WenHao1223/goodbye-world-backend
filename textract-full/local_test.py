#!/usr/bin/env python3
"""
Local test script for Lambda function without deployment
"""

import json
import base64
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_local():
    """Test the Lambda function locally"""
    
    # Set Lambda environment flag
    os.environ['LAMBDA_RUNTIME'] = 'true'
    
    # Import the handler
    from lambda_handler import lambda_handler
    
    # Test file path
    test_file = Path("media/receipt.pdf")
    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        print("Available files in media/:")
        media_dir = Path("media")
        if media_dir.exists():
            for f in media_dir.iterdir():
                if f.is_file():
                    print(f"  {f.name}")
        return
    
    # Read and encode test file
    with open(test_file, 'rb') as f:
        file_content = base64.b64encode(f.read()).decode('utf-8')
    
    # Create test event
    event = {
        "httpMethod": "POST",
        "body": json.dumps({
            "file_content": file_content,
            "filename": test_file.name,
            "mode": "tfbq",
            "category": "receipt",
            "region": "us-east-1"
        })
    }
    
    print("Testing Lambda function locally...")
    print(f"File: {test_file}")
    print(f"File size: {len(file_content)} characters (base64)")
    
    try:
        # Call the handler
        result = lambda_handler(event, {})
        
        print(f"\nStatus Code: {result['statusCode']}")
        
        if result['statusCode'] == 200:
            body = json.loads(result['body'])
            print("SUCCESS!")
            print(f"Console output: {body.get('console_output', 'N/A')[:200]}...")

            # Show available data
            data_types = []
            for key in ['text', 'forms', 'tables', 'queries', 'extracted_data']:
                if key in body:
                    data_types.append(key)

            if data_types:
                print(f"Available data: {', '.join(data_types)}")
            else:
                print("No analysis data returned")

        else:
            body = json.loads(result['body'])
            print("ERROR!")
            print(f"Error: {body.get('error', 'Unknown error')}")
            if 'stdout' in body:
                print(f"Stdout: {body['stdout']}")
            if 'stderr' in body:
                print(f"Stderr: {body['stderr']}")

    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()


def test_health():
    """Test the health endpoint"""
    
    from lambda_handler import health_handler
    
    event = {"httpMethod": "GET"}
    result = health_handler(event, {})
    
    print(f"Health check status: {result['statusCode']}")
    body = json.loads(result['body'])
    print(f"Response: {body}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Lambda function locally")
    parser.add_argument("--health", action="store_true", help="Test health endpoint")
    
    args = parser.parse_args()
    
    if args.health:
        test_health()
    else:
        test_local()

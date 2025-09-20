#!/usr/bin/env python3
"""
Local test script for Lambda function without deployment
"""

import json
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
    
    # Test instruction
    test_instruction = "find account from tnb service"
    
    # Create test event
    event = {
        "httpMethod": "POST",
        "body": json.dumps({
            "instruction": test_instruction
        })
    }
    
    print("Testing Lambda function locally...")
    print(f"Instruction: {test_instruction}")
    
    try:
        # Call the handler
        result = lambda_handler(event, {})
        
        print(f"\nStatus Code: {result['statusCode']}")
        
        if result['statusCode'] == 200:
            body = json.loads(result['body'])
            print("SUCCESS!")
            print(f"Console output: {body.get('console_output', 'N/A')}")
            
            if 'parsed_result' in body:
                print(f"Parsed result: {json.dumps(body['parsed_result'], indent=2)}")
            
        else:
            body = json.loads(result['body'])
            print("ERROR!")
            print(f"Error: {body.get('error', 'Unknown error')}")
            if 'console_output' in body:
                print(f"Console output: {body['console_output']}")
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
    parser.add_argument("--instruction", help="Custom instruction to test")
    
    args = parser.parse_args()
    
    if args.health:
        test_health()
    else:
        if args.instruction:
            # Override the test instruction
            import lambda_handler
            # Modify the test_local function to use custom instruction
            test_instruction = args.instruction
        test_local()
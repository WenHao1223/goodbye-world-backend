import json
import os
import sys
from typing import Dict, Any

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import GovernmentServiceClient, execute_instruction

def lambda_handler(event, context):
    """
    AWS Lambda handler for MongoDB MCP operations
    """
    try:
        # Parse the request
        if 'body' in event:
            if isinstance(event['body'], str):
                body = json.loads(event['body'])
            else:
                body = event['body']
        else:
            body = event
        
        # Get the instruction from the request
        instruction = body.get('instruction', '')
        
        if not instruction:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps({
                    'error': 'Missing instruction parameter',
                    'message': 'Please provide an instruction in the request body'
                })
            }
        
        # Initialize the client
        client = GovernmentServiceClient()
        
        # Parse the instruction
        operation_data = client.parse_instruction(instruction)
        
        # Execute the operation
        result = client.execute_operation(operation_data)
        
        # Prepare the response
        response_data = {
            'instruction': instruction,
            'parsed_operation': operation_data,
            'result': result,
            'status': 'success'
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps(response_data, indent=2, default=str)
        }
        
    except Exception as e:
        error_response = {
            'error': str(e),
            'status': 'failed',
            'instruction': body.get('instruction', '') if 'body' in locals() else ''
        }
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps(error_response, indent=2, default=str)
        }

# For OPTIONS requests (CORS preflight)
def handle_options():
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'POST, OPTIONS'
        },
        'body': ''
    }
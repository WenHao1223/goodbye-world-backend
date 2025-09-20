import json
import os
import sys
from typing import Dict, Any

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import IntentClassifier

def lambda_handler(event, context):
    """
    AWS Lambda handler for intent classification operations
    """
    try:
        # Handle OPTIONS requests for CORS
        if event.get('httpMethod') == 'OPTIONS':
            return handle_options()
        
        # Parse the request
        if 'body' in event:
            if isinstance(event['body'], str):
                body = json.loads(event['body'])
            else:
                body = event['body']
        else:
            body = event
        
        # Get the user input from the request
        user_input = body.get('user_input', '')
        
        if not user_input:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps({
                    'error': 'Missing user_input parameter',
                    'message': 'Please provide user_input in the request body'
                })
            }
        
        # Initialize the intent classifier
        classifier = IntentClassifier()
        
        # Classify the intent
        result = classifier.classify_intent(user_input)
        
        # Prepare the response
        response_data = {
            'user_input': user_input,
            'classification_result': result,
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
        import traceback
        error_response = {
            'error': str(e),
            'traceback': traceback.format_exc(),
            'status': 'failed',
            'user_input': body.get('user_input', '') if 'body' in locals() else ''
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

def health_handler(event, context):
    """
    Health check endpoint
    """
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'status': 'healthy',
            'service': 'aws-brain-intent-classifier',
            'timestamp': context.aws_request_id if context else 'local'
        })
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
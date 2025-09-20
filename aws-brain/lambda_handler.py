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
        
        # Get the required fields from the request
        user_id = body.get('userId', '')
        session_id = body.get('sessionId', '')
        message = body.get('message', '')
        created_at = body.get('createdAt', '')
        attachment_url = body.get('attachmentUrl', [])
        
        if not user_id or not session_id or not message:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps({
                    'error': 'Missing required parameters',
                    'message': 'Please provide userId, sessionId, and message in the request body'
                })
            }
        
        # Initialize the intent classifier
        classifier = IntentClassifier()
        
        # Process the request
        result = classifier.process_request({
            'user_id': user_id,
            'session_id': session_id,
            'message': message,
            'created_at': created_at,
            'attachment_url': attachment_url
        })
        
        # Prepare the response in the expected format
        response_data = {
            'id': result.get('id', ''),
            'reply': result.get('reply', ''),
            'sessionId': result.get('sessionId', session_id),
            'attachments': result.get('attachments', []),
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
            'user_id': body.get('userId', '') if 'body' in locals() else '',
            'session_id': body.get('sessionId', '') if 'body' in locals() else '',
            'message': body.get('message', '') if 'body' in locals() else ''
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
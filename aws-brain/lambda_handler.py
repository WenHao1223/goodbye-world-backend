import json
import os
import sys
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('aws-brain-lambda')

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import IntentClassifier

def lambda_handler(event, context):
    """
    AWS Lambda handler for intent classification operations
    """
    logger.info("🚀 AWS Lambda handler started")
    logger.info(f"📥 Raw event: {json.dumps(event, indent=2, default=str)}")
    logger.info(f"🎯 Context: {context}")
    
    try:
        # Handle OPTIONS requests for CORS
        if event.get('httpMethod') == 'OPTIONS':
            logger.info("✅ Handling OPTIONS request for CORS")
            return handle_options()
        
        # Parse the request
        if 'body' in event:
            if isinstance(event['body'], str):
                body = json.loads(event['body'])
            else:
                body = event['body']
        else:
            body = event
        
        logger.info(f"📊 Parsed request body: {json.dumps(body, indent=2)}")
        
        # Get the required fields from the request
        user_id = body.get('userId', '')
        session_id = body.get('sessionId', '')
        message = body.get('message', '')
        created_at = body.get('createdAt', '')
        attachment_url = body.get('attachmentUrl', [])
        
        logger.info(f"👤 Extracted userId: {user_id}")
        logger.info(f"🔗 Extracted sessionId: {session_id}")
        logger.info(f"💬 Extracted message: {message}")
        logger.info(f"📎 Extracted attachmentUrl: {attachment_url}")
        
        if not user_id or not session_id or not message:
            logger.warning("❌ Missing required parameters")
            error_response = {
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
            logger.info(f"📤 Returning error response: {json.dumps(error_response, indent=2)}")
            return error_response
        
        # Initialize the intent classifier
        logger.info("🧠 Initializing IntentClassifier")
        classifier = IntentClassifier()
        
        # Process the request
        logger.info("⚡ Processing request with IntentClassifier")
        result = classifier.process_request({
            'user_id': user_id,
            'session_id': session_id,
            'message': message,
            'created_at': created_at,
            'attachment_url': attachment_url
        })
        
        logger.info(f"✅ IntentClassifier result: {json.dumps(result, indent=2, default=str)}")
        
        # Prepare the response in the expected format
        response_data = {
            'id': result.get('id', ''),
            'reply': result.get('reply', ''),
            'sessionId': result.get('sessionId', session_id),
            'attachments': result.get('attachments', []),
            'status': 'success'
        }
        
        final_response = {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps(response_data, indent=2, default=str)
        }
        
        logger.info("=" * 80)
        logger.info("🎉 LAMBDA HANDLER RESPONSE TO API GATEWAY")
        logger.info("=" * 80)
        logger.info(f"📤 Final response: {json.dumps(final_response, indent=2, default=str)}")
        logger.info("=" * 80)
        
        return final_response
        
    except Exception as e:
        import traceback
        logger.error(f"❌ Lambda handler error: {str(e)}")
        logger.error(f"📚 Traceback: {traceback.format_exc()}")
        
        error_response = {
            'error': str(e),
            'traceback': traceback.format_exc(),
            'status': 'failed',
            'user_id': body.get('userId', '') if 'body' in locals() else '',
            'session_id': body.get('sessionId', '') if 'body' in locals() else '',
            'message': body.get('message', '') if 'body' in locals() else ''
        }
        
        final_error_response = {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps(error_response, indent=2, default=str)
        }
        
        logger.info(f"📤 Error response: {json.dumps(final_error_response, indent=2, default=str)}")
        return final_error_response

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
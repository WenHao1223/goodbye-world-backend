import json
import os
import sys
import logging
from datetime import datetime, timezone
from typing import Dict, Any

# Configure logging for CloudWatch
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # Force reconfiguration
)
logger = logging.getLogger('aws-brain-lambda')

# Ensure logs go to stdout for Lambda CloudWatch
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import IntentClassifier

def get_iso_timestamp() -> str:
    """
    Get current timestamp in ISO format (UTC)
    """
    return datetime.now(timezone.utc).isoformat()

def lambda_handler(event, context):
    """
    AWS Lambda handler for intent classification operations
    """
    logger.info("🚀 AWS Lambda handler started")
    logger.info(f"📥 Raw event: {json.dumps(event, indent=2, default=str)}")
    logger.info(f"🎯 Context: {context}")
    
    # Print to stdout for CloudWatch visibility
    print("🚀 AWS Lambda handler started")
    print(f"📥 Raw event: {json.dumps(event, indent=2, default=str)}")
    print(f"🎯 Context: {context}")
    
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
        attachment = body.get('attachment', [])
        
        logger.info(f"👤 Extracted userId: {user_id}")
        logger.info(f"🔗 Extracted sessionId: {session_id}")
        logger.info(f"💬 Extracted message: {message}")
        logger.info(f"📎 Extracted attachment: {attachment}")
        
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
                    'status': {
                        'statusCode': '400',
                        'message': 'Missing required parameters'
                    },
                    'data': {
                        'messageId': '',
                        'message': 'Please provide userId, sessionId, and message in the request body',
                        'sessionId': session_id,
                        'attachment': [],
                        'createdAt': created_at or get_iso_timestamp()
                    }
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
            'attachment': attachment
        })
        
        logger.info(f"✅ IntentClassifier result: {json.dumps(result, indent=2, default=str)}")
        
        # Prepare the response in the expected format
        response_data = {
            'status': {
                'statusCode': '200',
                'message': 'Success'
            },
            'data': {
                'messageId': result.get('messageId', ''),
                'message': result.get('message', ''),
                'sessionId': result.get('sessionId', session_id),
                'attachment': result.get('attachment', []),
                'createdAt': result.get('createdAt', get_iso_timestamp())
            }
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
        
        # Print to stdout for CloudWatch visibility
        print("=" * 80)
        print("🎉 LAMBDA HANDLER RESPONSE TO API GATEWAY")
        print("=" * 80)
        print(f"📤 Final response: {json.dumps(final_response, indent=2, default=str)}")
        print("=" * 80)
        
        return final_response
        
    except Exception as e:
        import traceback
        logger.error(f"❌ Lambda handler error: {str(e)}")
        logger.error(f"📚 Traceback: {traceback.format_exc()}")
        
        # Print to stdout for CloudWatch visibility
        print(f"❌ Lambda handler error: {str(e)}")
        print(f"📚 Traceback: {traceback.format_exc()}")
        
        error_response = {
            'status': {
                'statusCode': "500",
                'message': f"Internal server error: {str(e)}"
            },
            'data': {
                'messageId': body.get('userId', '') if 'body' in locals() else '',
                'message': '',
                'sessionId': body.get('sessionId', '') if 'body' in locals() else '',
                'attachment': [],
                'createdAt': get_iso_timestamp(),
                'error': str(e),
                'traceback': traceback.format_exc()
            }
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
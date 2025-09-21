import json
from datetime import datetime, timezone
from main import IntentClassifier

def get_iso_timestamp() -> str:
    """
    Get current timestamp in ISO format (UTC)
    """
    return datetime.now(timezone.utc).isoformat()

def test_local():
    """
    Test the intent classifier locally
    """
    classifier = IntentClassifier()
    
    # Test cases for different intents including session management
    current_time = get_iso_timestamp()
    test_requests = [
        {
            'user_id': 'test_user_123',
            'session_id': '(new-session)',
            'message': 'Hello, I need help',
            'created_at': current_time,
            'attachment': []
        },
        {
            'user_id': 'test_user_123',
            'session_id': 'session_123',
            'message': 'I want to check my driving license status',  # No topic
            'created_at': current_time,
            'attachment': []
        },
        {
            'user_id': 'test_user_123',
            'session_id': 'session_123',  # Same session
            'message': 'I want to renew my license',  # New topic: "renew license" - should create new session
            'created_at': current_time,
            'attachment': []
        },
        {
            'user_id': 'test_user_123',
            'session_id': 'session_456',  # This will be updated to new session ID from previous request
            'message': 'How much does license renewal cost?',  # Same topic: "renew license" - should continue same session
            'created_at': current_time,
            'attachment': []
        },
        {
            'user_id': 'test_user_123',
            'session_id': 'session_456',  # This will be updated
            'message': 'I need to pay my TNB bill',  # New topic: "pay tnb bill" - should create new session
            'created_at': current_time,
            'attachment': []
        },
        {
            'user_id': 'test_user_123',
            'session_id': 'session_789',  # This will be updated
            'message': 'What is my TNB account balance?',  # Same topic: "pay tnb bill" - should continue same session
            'created_at': current_time,
            'attachment': []
        },
        {
            'user_id': 'test_user_123',
            'session_id': 'session_101',
            'message': 'Thank you for your help, goodbye',  # Conversation ending
            'created_at': current_time,
            'attachment': []
        },
        {
            'user_id': 'test_user_456',
            'session_id': 'session_456',
            'message': 'I have a document to upload',
            'created_at': current_time,
            'attachment': [{
                'url': 'https://example.com/license.jpg',
                'type': 'image/jpeg',
                'name': 'license.jpg'
            }]
        }
    ]
    
    print("Testing Intent Classifier with Validation Requests")
    print("=" * 60)
    
    for i, request_data in enumerate(test_requests, 1):
        print(f"\nTest Case {i}:")
        print(f"Input: {json.dumps(request_data, indent=2)}")
        try:
            result = classifier.process_request(request_data)
            print(f"Result: {json.dumps(result, indent=2)}")
            
            # Highlight validation requests
            if 'upload a photo' in result.get('message', '') or 'take a photo' in result.get('message', ''):
                print("🔐 VALIDATION REQUEST DETECTED!")
                if 'IC' in result.get('message', '') or 'license' in result.get('message', ''):
                    print("📄 → User should upload IC or driving license")
                elif 'TNB bill' in result.get('message', ''):
                    print("📋 → User should snap upper part of TNB bill")
        except Exception as e:
            print(f"Error: {str(e)}")

def test_lambda_locally():
    """
    Test the lambda handler locally
    """
    from lambda_handler import lambda_handler
    
    test_event = {
        'body': json.dumps({
            'userId': 'test_user_123',
            'sessionId': '(new-session)',
            'message': 'I want to apply for a driving license',
            'createdAt': get_iso_timestamp(),
            'attachment': []
        }),
        'httpMethod': 'POST'
    }
    
    try:
        result = lambda_handler(test_event, None)
        print("\nLambda Handler Test Result:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Lambda Handler Error: {str(e)}")

if __name__ == "__main__":
    test_local()
    test_lambda_locally()
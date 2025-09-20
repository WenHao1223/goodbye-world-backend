import json
from main import IntentClassifier

def test_local():
    """
    Test the intent classifier locally
    """
    classifier = IntentClassifier()
    
    # Test cases for different intents
    test_requests = [
        {
            'user_id': 'test_user_123',
            'session_id': '(new-session)',
            'message': 'Hello, I need help',
            'created_at': '2025-09-21T10:00:00Z',
            'attachment': []
        },
        {
            'user_id': 'test_user_123',
            'session_id': 'session_123',
            'message': 'I want to check my driving license status',
            'created_at': '2025-09-21T10:01:00Z',
            'attachment': []
        },
        {
            'user_id': 'test_user_123',
            'session_id': 'session_123',
            'message': 'Thank you for your help, goodbye',
            'created_at': '2025-09-21T10:02:00Z',
            'attachment': []
        },
        {
            'user_id': 'test_user_456',
            'session_id': 'session_456',
            'message': 'I have a document to upload',
            'created_at': '2025-09-21T10:03:00Z',
            'attachment': [{
                'url': 'https://example.com/license.jpg',
                'type': 'image/jpeg',
                'name': 'license.jpg'
            }]
        }
    ]
    
    print("Testing Intent Classifier Locally")
    print("=" * 50)
    
    for i, request_data in enumerate(test_requests, 1):
        print(f"\nTest Case {i}:")
        print(f"Input: {json.dumps(request_data, indent=2)}")
        try:
            result = classifier.process_request(request_data)
            print(f"Result: {json.dumps(result, indent=2)}")
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
            'createdAt': '2025-09-21T10:00:00Z',
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
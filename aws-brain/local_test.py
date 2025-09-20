import json
import requests
from main import IntentClassifier

def test_local():
    """
    Test the intent classifier locally
    """
    classifier = IntentClassifier()
    
    # Test cases
    test_inputs = [
        "I want to apply for a driving license",
        "How do I renew my TNB account?",
        "Check my bank account balance",
        "What documents do I need for license application?"
    ]
    
    print("Testing Intent Classifier Locally")
    print("=" * 50)
    
    for user_input in test_inputs:
        print(f"\nInput: {user_input}")
        result = classifier.classify_intent(user_input)
        print(f"Result: {json.dumps(result, indent=2)}")

def test_lambda_locally():
    """
    Test the lambda handler locally
    """
    from lambda_handler import lambda_handler
    
    test_event = {
        'body': json.dumps({
            'user_input': 'I want to apply for a driving license'
        }),
        'httpMethod': 'POST'
    }
    
    result = lambda_handler(test_event, None)
    print("\nLambda Handler Test Result:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_local()
    test_lambda_locally()
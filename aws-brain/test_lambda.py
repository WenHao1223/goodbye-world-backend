import unittest
import json
from lambda_handler import lambda_handler, health_handler
from main import IntentClassifier

class TestIntentClassifier(unittest.TestCase):
    
    def setUp(self):
        self.classifier = IntentClassifier()
    
    def test_classify_intent_basic(self):
        """Test basic intent classification"""
        result = self.classifier.classify_intent("I want to apply for a driving license")
        self.assertIsInstance(result, dict)
        self.assertIn('intent', result)
        self.assertIn('confidence', result)
    
    def test_classify_intent_empty_input(self):
        """Test intent classification with empty input"""
        result = self.classifier.classify_intent("")
        self.assertIsInstance(result, dict)

class TestLambdaHandler(unittest.TestCase):
    
    def test_lambda_handler_success(self):
        """Test lambda handler with valid input"""
        event = {
            'body': json.dumps({
                'user_input': 'I want to apply for a driving license'
            }),
            'httpMethod': 'POST'
        }
        
        result = lambda_handler(event, None)
        self.assertEqual(result['statusCode'], 200)
        
        body = json.loads(result['body'])
        self.assertIn('classification_result', body)
        self.assertEqual(body['status'], 'success')
    
    def test_lambda_handler_missing_input(self):
        """Test lambda handler with missing user input"""
        event = {
            'body': json.dumps({}),
            'httpMethod': 'POST'
        }
        
        result = lambda_handler(event, None)
        self.assertEqual(result['statusCode'], 400)
        
        body = json.loads(result['body'])
        self.assertIn('error', body)
    
    def test_lambda_handler_options(self):
        """Test lambda handler with OPTIONS method"""
        event = {
            'httpMethod': 'OPTIONS'
        }
        
        result = lambda_handler(event, None)
        self.assertEqual(result['statusCode'], 200)
        self.assertIn('Access-Control-Allow-Origin', result['headers'])
    
    def test_health_handler(self):
        """Test health check endpoint"""
        result = health_handler({}, None)
        self.assertEqual(result['statusCode'], 200)
        
        body = json.loads(result['body'])
        self.assertEqual(body['status'], 'healthy')
        self.assertIn('service', body)

if __name__ == '__main__':
    unittest.main()
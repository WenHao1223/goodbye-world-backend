import json
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lambda_handler import lambda_handler

def deploy_to_aws():
    """
    Deploy the lambda function to AWS using serverless
    """
    import subprocess
    
    try:
        print("Installing dependencies...")
        subprocess.run(["npm", "install"], check=True)
        
        print("Deploying to AWS...")
        subprocess.run(["serverless", "deploy"], check=True)
        
        print("Deployment completed successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"Deployment failed: {e}")
        return False
    
    return True

def test_deployed_lambda():
    """
    Test the deployed lambda function
    """
    import requests
    
    # Replace with your actual API Gateway URL after deployment
    api_url = "https://your-api-gateway-url.amazonaws.com/dev/brain/classify"
    
    test_data = {
        "user_input": "I want to apply for a driving license"
    }
    
    try:
        response = requests.post(api_url, json=test_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error testing deployed lambda: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "deploy":
        deploy_to_aws()
    else:
        print("Usage:")
        print("  python deploy_lambda.py deploy    # Deploy to AWS")
        print("  python deploy_lambda.py           # Show usage")
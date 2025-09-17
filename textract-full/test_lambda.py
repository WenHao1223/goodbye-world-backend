#!/usr/bin/env python3
"""
Test client for the Lambda function
"""

import json
import base64
import requests
from pathlib import Path


def test_lambda_local(file_path, mode="tfbq", category=None, region="us-east-1"):
    """Test Lambda function locally"""
    
    # Import the handler
    from lambda_handler import lambda_handler
    
    # Read and encode file
    with open(file_path, 'rb') as f:
        file_content = base64.b64encode(f.read()).decode('utf-8')
    
    # Create test event
    event = {
        "httpMethod": "POST",
        "body": json.dumps({
            "file_content": file_content,
            "filename": Path(file_path).name,
            "mode": mode,
            "category": category,
            "region": region
        })
    }
    
    # Call handler
    result = lambda_handler(event, {})
    
    print("Response:")
    print(json.dumps(result, indent=2))
    
    return result


def test_lambda_api(api_url, file_path, mode="tfbq", category=None, region="us-east-1"):
    """Test deployed Lambda function via API Gateway"""
    
    # Read and encode file
    with open(file_path, 'rb') as f:
        file_content = base64.b64encode(f.read()).decode('utf-8')
    
    # Create request payload
    payload = {
        "file_content": file_content,
        "filename": Path(file_path).name,
        "mode": mode,
        "category": category,
        "region": region
    }
    
    # Make request
    response = requests.post(
        api_url,
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))
    
    return response


def create_test_html():
    """Create a test HTML page for the Lambda API"""
    
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Textract Full Lambda API Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        button { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        .result { margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 4px; }
        .error { background-color: #f8d7da; color: #721c24; }
        .success { background-color: #d4edda; color: #155724; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Textract Full Lambda API Test</h1>
        
        <form id="uploadForm">
            <div class="form-group">
                <label for="apiUrl">API URL:</label>
                <input type="url" id="apiUrl" placeholder="https://your-api-id.execute-api.region.amazonaws.com/prod/analyze" required>
            </div>
            
            <div class="form-group">
                <label for="file">Select File:</label>
                <input type="file" id="file" accept=".pdf,.jpg,.jpeg,.png" required>
            </div>
            
            <div class="form-group">
                <label for="mode">Analysis Mode:</label>
                <select id="mode">
                    <option value="tfbq">All (Text, Forms, Tables, Queries)</option>
                    <option value="t">Text Only</option>
                    <option value="f">Forms Only</option>
                    <option value="b">Tables Only</option>
                    <option value="q">Queries Only</option>
                    <option value="tf">Text + Forms</option>
                    <option value="tb">Text + Tables</option>
                    <option value="fb">Forms + Tables</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="category">Document Category (optional):</label>
                <select id="category">
                    <option value="">None</option>
                    <option value="licence">License</option>
                    <option value="receipt">Receipt</option>
                    <option value="idcard">ID Card</option>
                    <option value="passport">Passport</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="region">AWS Region:</label>
                <input type="text" id="region" value="us-east-1">
            </div>
            
            <button type="submit">Analyze Document</button>
        </form>
        
        <div id="result" class="result" style="display: none;"></div>
    </div>

    <script>
        document.getElementById('uploadForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const apiUrl = document.getElementById('apiUrl').value;
            const fileInput = document.getElementById('file');
            const mode = document.getElementById('mode').value;
            const category = document.getElementById('category').value;
            const region = document.getElementById('region').value;
            const resultDiv = document.getElementById('result');
            
            if (!fileInput.files[0]) {
                alert('Please select a file');
                return;
            }
            
            // Show loading
            resultDiv.style.display = 'block';
            resultDiv.className = 'result';
            resultDiv.innerHTML = 'Processing... Please wait.';
            
            try {
                // Read file as base64
                const file = fileInput.files[0];
                const reader = new FileReader();
                
                reader.onload = async function(e) {
                    const fileContent = e.target.result.split(',')[1]; // Remove data:type;base64, prefix
                    
                    const payload = {
                        file_content: fileContent,
                        filename: file.name,
                        mode: mode,
                        category: category || undefined,
                        region: region
                    };
                    
                    try {
                        const response = await fetch(apiUrl, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(payload)
                        });
                        
                        const result = await response.json();
                        
                        if (response.ok) {
                            resultDiv.className = 'result success';
                            resultDiv.innerHTML = '<h3>Success!</h3><pre>' + JSON.stringify(result, null, 2) + '</pre>';
                        } else {
                            resultDiv.className = 'result error';
                            resultDiv.innerHTML = '<h3>Error</h3><pre>' + JSON.stringify(result, null, 2) + '</pre>';
                        }
                    } catch (error) {
                        resultDiv.className = 'result error';
                        resultDiv.innerHTML = '<h3>Error</h3><p>' + error.message + '</p>';
                    }
                };
                
                reader.readAsDataURL(file);
                
            } catch (error) {
                resultDiv.className = 'result error';
                resultDiv.innerHTML = '<h3>Error</h3><p>' + error.message + '</p>';
            }
        });
    </script>
</body>
</html>"""
    
    with open('test_lambda.html', 'w') as f:
        f.write(html_content)
    
    print("Created test_lambda.html")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Textract Full Lambda Function")
    parser.add_argument("--file", help="Path to test file")
    parser.add_argument("--mode", default="tfbq", help="Analysis mode")
    parser.add_argument("--category", help="Document category")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--api-url", help="API Gateway URL (for remote testing)")
    parser.add_argument("--create-html", action="store_true", help="Create test HTML page")
    
    args = parser.parse_args()
    
    if args.create_html:
        create_test_html()
    elif args.file and args.api_url:
        test_lambda_api(args.api_url, args.file, args.mode, args.category, args.region)
    elif args.file:
        test_lambda_local(args.file, args.mode, args.category, args.region)
    else:
        print("Error: --file is required unless using --create-html")

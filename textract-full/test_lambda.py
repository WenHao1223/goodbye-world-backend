#!/usr/bin/env python3
"""
Test client for the Lambda function
"""

import json
import base64
import requests
from pathlib import Path


def test_lambda_local(file_path, mode="tfbq", category=None, queries=None, prompt=None, custom=False, region="us-east-1"):
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
            "queries": queries,
            "prompt": prompt,
            "custom": custom,
            "region": region
        })
    }
    
    # Call handler
    result = lambda_handler(event, {})
    
    print("Response:")
    print(json.dumps(result, indent=2))
    
    return result


def test_lambda_api(api_url, file_path, mode="tfbq", category=None, queries=None, prompt=None, custom=False, region="us-east-1"):
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
        "queries": queries,
        "prompt": prompt,
        "custom": custom,
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
        textarea { height: 80px; resize: vertical; }
        button { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        .result { margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 4px; max-height: 600px; overflow-y: auto; }
        .error { background-color: #f8d7da; color: #721c24; }
        .success { background-color: #d4edda; color: #155724; }
        pre {
            white-space: pre-wrap;
            word-wrap: break-word;
            overflow-wrap: break-word;
            max-width: 100%;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.4;
            background-color: #f8f9fa;
            padding: 10px;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            overflow-x: auto;
        }
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
                    <option value="t">Text Only (t)</option>
                    <option value="tf">Text + Forms (tf)</option>
                    <option value="tb">Text + Tables (tb)</option>
                    <option value="tq">Text + Queries (tq)</option>
                    <option value="tfq">Text + Forms + Queries (tfq)</option>
                    <option value="tbq">Text + Tables + Queries (tfbq)</option>
                    <option value="tfbq" selected>All Analysis Types (Text + Forms + Tables + Queries) (tfbq)</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="category">Document Category (optional - auto-detected if not provided):</label>
                <select id="category">
                    <option value="">Auto-detect (recommended)</option>
                    <option value="licence">Driver's License</option>
                    <option value="receipt">Receipt/Invoice</option>
                    <option value="bank-receipt">Bank Receipt/Statement</option>
                    <option value="idcard">ID Card</option>
                    <option value="passport">Passport</option>
                </select>
                <small style="color: #666;">Leave as "Auto-detect" to let AI classify the document type automatically.</small>
            </div>

            <div class="form-group">
                <label for="custom">Custom Mode:</label>
                <input type="checkbox" id="custom" style="width: auto; margin-right: 8px;">
                <span id="customToggle" style="cursor:pointer;">Use custom queries/prompts even if category has default files</span>
                <br><small style="color: #666;">Enable this to override category-based queries/prompts with your custom ones.</small>
                <br><small style="color: #666;">Required for document category other than license.</small>
                <br><small style="color: #666;">Analysis mode must include "q" for custom queries to work.</small>
            </div>

            <div class="form-group">
                <label for="queries">Custom Queries (optional):</label>
                <textarea id="queries" placeholder="What is the transaction amount?&#10;What is the beneficiary name?&#10;What is the reference number?"></textarea>
                <br><small style="color: #666;">Enter custom questions separated by semicolons (;) or new lines.</small>
                <br><small style="color: #666;">Custom mode ON: Use your own queries if you have them. If not, use the default queries for the category.</small>
                <br><small style="color: #666;">Custom mode OFF: Use the default queries for the category, and add your own queries if you have any.</small>
                <br><small style="color: #666;">Refer sample queries <a href="https://github.com/WenHao1223/great-ai-hackathon-test/tree/master/textract-full/src/queries" style="color: #666" target="_blank">here</a>.</small>
            </div>

            <div class="form-group">
                <label for="prompt">Custom Prompt (optional):</label>
                <textarea id="prompt" placeholder="Extract transaction details as JSON:&#10;{&#10;  &quot;amount&quot;: &quot;transaction amount as number&quot;,&#10;  &quot;date&quot;: &quot;date in YYYY-MM-DD format&quot;,&#10;  &quot;beneficiary&quot;: &quot;recipient name&quot;,&#10;  &quot;reference&quot;: &quot;reference or transaction ID&quot;&#10;}"></textarea>
                <small style="color: #666;">Enter custom prompt for Bedrock AI extraction. Overrides category-based prompts when provided.</small>
                <br><small style="color: #666;">Refer sample prompts <a href="https://github.com/WenHao1223/great-ai-hackathon-test/tree/master/textract-full/src/prompts" style="color: #666" target="_blank">here</a>.</small>
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
        // Toggle checkbox when span is clicked
        document.getElementById('customToggle').addEventListener('click', function() {
            const customCheckbox = document.getElementById('custom');
            customCheckbox.checked = !customCheckbox.checked;
        });

        document.getElementById('uploadForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const apiUrl = document.getElementById('apiUrl').value;
            const fileInput = document.getElementById('file');
            const mode = document.getElementById('mode').value;
            const category = document.getElementById('category').value;
            const queries = document.getElementById('queries').value.trim();
            const prompt = document.getElementById('prompt').value.trim();
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
                    
                    const custom = document.getElementById('custom').checked;
                    
                    const payload = {
                        file_content: fileContent,
                        filename: file.name,
                        mode: mode,
                        category: category || undefined,
                        queries: queries || undefined,
                        prompt: prompt || undefined,
                        custom: custom,
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
                            let html = '<h3>Analysis Complete!</h3>';
                            
                            // Show category detection if available
                            if (result.category_detection) {
                                html += '<h4>📋 Category Detection</h4>';
                                html += '<p><strong>Detected:</strong> ' + result.category_detection.detected_category + '</p>';
                                html += '<p><strong>Confidence:</strong> ' + (result.category_detection.confidence * 100).toFixed(1) + '%</p>';
                            }
                            
                            // Show blur analysis if available
                            if (result.blur_analysis && result.blur_analysis.overall_assessment) {
                                html += '<h4>🔍 Image Quality</h4>';
                                html += '<p><strong>Quality:</strong> ' + (result.blur_analysis.overall_assessment.is_blurry ? 'Poor (Blurry)' : 'Good') + '</p>';
                                if (result.blur_analysis.textract_analysis) {
                                    html += '<p><strong>Confidence:</strong> ' + result.blur_analysis.textract_analysis.median_confidence.toFixed(1) + '%</p>';
                                }
                            }
                            
                            html += '<h4>📄 Full Results</h4>';
                            html += '<pre>' + JSON.stringify(result, null, 2) + '</pre>';
                            resultDiv.innerHTML = html;
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
    
    with open('test_lambda.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Created test_lambda.html")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Textract Full Lambda Function")
    parser.add_argument("--file", help="Path to test file")
    parser.add_argument("--mode", default="tfbq", help="Analysis mode")
    parser.add_argument("--category", help="Document category")
    parser.add_argument("--queries", help="Custom queries separated by semicolons")
    parser.add_argument("--prompt", help="Custom prompt for Bedrock AI extraction")
    parser.add_argument("--custom", action="store_true", help="Use custom mode")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--api-url", help="API Gateway URL (for remote testing)")
    parser.add_argument("--create-html", action="store_true", help="Create test HTML page")

    args = parser.parse_args()

    if args.create_html:
        create_test_html()
    elif args.file and args.api_url:
        test_lambda_api(args.api_url, args.file, args.mode, args.category, args.queries, args.prompt, args.custom, args.region)
    elif args.file:
        test_lambda_local(args.file, args.mode, args.category, args.queries, args.prompt, args.custom, args.region)
    else:
        print("Error: --file is required unless using --create-html")

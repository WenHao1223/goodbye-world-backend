#!/usr/bin/env python3
"""
Test client for the MongoDB MCP Lambda function
"""

import json
import requests
from pathlib import Path


def test_lambda_local(instruction="Find licence with identity number of 041223070745"):
    """Test Lambda function locally"""

    # Import the handler
    from lambda_handler import lambda_handler

    # Create test event
    event = {
        "httpMethod": "POST",
        "body": json.dumps({
            "instruction": instruction
        })
    }
    
    # Call handler
    result = lambda_handler(event, {})
    
    print("Response:")
    print(json.dumps(result, indent=2))
    
    return result


def test_lambda_api(api_url, instruction="Find licence with identity number of 041223070745"):
    """Test deployed Lambda function via API Gateway"""

    # Create request payload
    payload = {
        "instruction": instruction
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
    """Create a test HTML page for the MongoDB MCP Lambda API"""
    
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>MongoDB MCP Lambda API Test</title>
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
        .examples { background-color: #e9ecef; padding: 15px; border-radius: 4px; margin-bottom: 20px; }
        .examples h4 { margin-top: 0; }
        .examples h5 { margin: 15px 0 10px 0; color: #495057; border-bottom: 1px solid #dee2e6; padding-bottom: 5px; }
        .step { margin-bottom: 15px; }
        .code-block { 
            position: relative; 
            margin: 8px 0; 
            background-color: #f8f9fa; 
            border: 1px solid #dee2e6; 
            border-radius: 4px; 
            padding: 10px 40px 10px 10px;
        }
        .code-block code { 
            display: block; 
            font-family: 'Courier New', monospace; 
            font-size: 12px; 
            line-height: 1.4;
            white-space: pre-wrap;
            word-wrap: break-word;
            margin: 0;
        }
        .copy-btn { 
            position: absolute; 
            top: 5px; 
            right: 5px; 
            background: #007bff; 
            color: white; 
            border: none; 
            border-radius: 3px; 
            padding: 3px 6px; 
            cursor: pointer; 
            font-size: 12px;
        }
        .copy-btn:hover { background-color: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>MongoDB MCP Lambda API Test</h1>
        
        <div class="examples">
            <h4>📝 Key Prompts Examples</h4>
            
            <h5>License Renewal</h5>
            <div class="step">
                <strong>1. Check for license record</strong>
                <div class="code-block">
                    <code>Find licence with identity number of 041223070745</code>
                    <button onclick="copyToClipboard('Find licence with identity number of 041223070745')" class="copy-btn">📋</button>
                </div>
                <div class="code-block">
                    <code>Find licence with license number of 0107011 mZyPs9aZ</code>
                    <button onclick="copyToClipboard('Find licence with license number of 0107011 mZyPs9aZ')" class="copy-btn">📋</button>
                </div>
            </div>
            
            <div class="step">
                <strong>2. Find JPJ service account</strong>
                <div class="code-block">
                    <code>Find account with service from JPJ</code>
                    <button onclick="copyToClipboard('Find account with service from JPJ')" class="copy-btn">📋</button>
                </div>
            </div>
            
            <div class="step">
                <strong>3. Create transaction record</strong>
                <div class="code-block">
                    <code>Create transaction record via DuitNow with these transaction details:
{
  "beneficiary_name": "Jabatan Pengangkutan Jalan Malaysia",
  "beneficiary_account_number": "5123456789012345",
  "receiving_bank": "Maybank",
  "recipient_reference": "0488-MB-MAYBANK22/43",
  "reference_id": "837356732M",
  "payment_details": "license renewal",
  "amount": "RM 40.00",
  "successful_timestamp": "15 Sep 2025, 3:13 PM"
}</code>
                    <button onclick="copyToClipboard(`Create transaction record via DuitNow with these transaction details:
{
  \"beneficiary_name\": \"Jabatan Pengangkutan Jalan Malaysia\",
  \"beneficiary_account_number\": \"5123456789012345\",
  \"receiving_bank\": \"Maybank\",
  \"recipient_reference\": \"0488-MB-MAYBANK22/43\",
  \"reference_id\": \"837356732M\",
  \"payment_details\": \"license renewal\",
  \"amount\": \"RM 40.00\",
  \"successful_timestamp\": \"15 Sep 2025, 3:13 PM\"
}`)" class="copy-btn">📋</button>
                </div>
            </div>
            
            <div class="step">
                <strong>4. Extend validity (1-10 years only)</strong>
                <div class="code-block">
                    <code>Update licence of identity number of 041223070745, validity extend 2 years</code>
                    <button onclick="copyToClipboard('Update licence of identity number of 041223070745, validity extend 2 years')" class="copy-btn">📋</button>
                </div>
                <div class="code-block">
                    <code>Update licence of license number of 0107011 mZyPs9aZ, validity extend 2 years</code>
                    <button onclick="copyToClipboard('Update licence of license number of 0107011 mZyPs9aZ, validity extend 2 years')" class="copy-btn">📋</button>
                </div>
                <div class="code-block">
                    <code>Extend 2 years licence 041223070745</code>
                    <button onclick="copyToClipboard('Extend 2 years licence 041223070745')" class="copy-btn">📋</button>
                </div>
                <div class="code-block">
                    <code>Extend 2 years licence 0107011 mZyPs9aZ</code>
                    <button onclick="copyToClipboard('Extend 2 years licence 0107011 mZyPs9aZ')" class="copy-btn">📋</button>
                </div>
            </div>
            
            <h5>TNB Bill Payment</h5>
            <div class="step">
                <strong>1. Check for unpaid TNB bills</strong>
                <div class="code-block">
                    <code>Find latest unpaid TNB bills for account number 220001234513</code>
                    <button onclick="copyToClipboard('Find latest unpaid TNB bills for account number 220001234513')" class="copy-btn">📋</button>
                </div>
            </div>
            
            <div class="step">
                <strong>2. Show TNB service account details</strong>
                <div class="code-block">
                    <code>Find account with service from TNB</code>
                    <button onclick="copyToClipboard('Find account with service from TNB')" class="copy-btn">📋</button>
                </div>
            </div>
            
            <div class="step">
                <strong>3. Make payment and create transaction record</strong>
                <div class="code-block">
                    <code>Update TNB bill 220001234513 sent via Maybank Online Banking with these transaction details:
{
  "beneficiary_name": "Tenaga Nasional Berhad",
  "beneficiary_account_number": "3987654321098765",
  "receiving_bank": "CIMB Bank",
  "recipient_reference": "OLB20250918003",
  "reference_id": "OLB20250918003",
  "payment_details": "TNB bill payment",
  "amount": "RM 60.00",
  "successful_timestamp": "15 Sep 2025, 3:13 PM"
}</code>
                    <button onclick="copyToClipboard(`Update TNB bill 220001234513 sent via Maybank Online Banking with these transaction details:
{
  \"beneficiary_name\": \"Tenaga Nasional Berhad\",
  \"beneficiary_account_number\": \"3987654321098765\",
  \"receiving_bank\": \"CIMB Bank\",
  \"recipient_reference\": \"OLB20250918003\",
  \"reference_id\": \"OLB20250918003\",
  \"payment_details\": \"TNB bill payment\",
  \"amount\": \"RM 60.00\",
  \"successful_timestamp\": \"15 Sep 2025, 3:13 PM\"
}`)" class="copy-btn">📋</button>
                </div>
            </div>
        </div>
        
        <form id="testForm">
            <div class="form-group">
                <label for="apiUrl">API URL:</label>
                <input type="url" id="apiUrl" placeholder="https://your-api-id.execute-api.region.amazonaws.com/dev/mongodb-mcp" required>
            </div>
            
            <div class="form-group">
                <label for="instruction">Instruction:</label>
                <textarea id="instruction" placeholder="Enter your natural language instruction here..." required>Find licence with identity number of 041223070745</textarea>
                <small style="color: #666;">Enter any natural language instruction for database operations.</small>
            </div>
            
            <button type="submit">Execute Instruction</button>
        </form>
        
        <div id="result" class="result" style="display: none;"></div>
    </div>

    <script>
        function copyToClipboard(text) {
            // Set the text in the instruction textarea
            document.getElementById('instruction').value = text;
            
            // Also copy to clipboard
            navigator.clipboard.writeText(text).then(function() {
                // Visual feedback
                const btn = event.target;
                const originalText = btn.innerHTML;
                btn.innerHTML = '✅';
                btn.style.backgroundColor = '#28a745';
                setTimeout(() => {
                    btn.innerHTML = originalText;
                    btn.style.backgroundColor = '#007bff';
                }, 1000);
            }).catch(function(err) {
                console.error('Could not copy text: ', err);
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                
                // Visual feedback for fallback
                const btn = event.target;
                const originalText = btn.innerHTML;
                btn.innerHTML = '✅';
                btn.style.backgroundColor = '#28a745';
                setTimeout(() => {
                    btn.innerHTML = originalText;
                    btn.style.backgroundColor = '#007bff';
                }, 1000);
            });
        }

        function setInstruction(instruction) {
            document.getElementById('instruction').value = instruction;
        }

        document.getElementById('testForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const apiUrl = document.getElementById('apiUrl').value;
            const instruction = document.getElementById('instruction').value.trim();
            const resultDiv = document.getElementById('result');
            
            if (!instruction) {
                alert('Please enter an instruction');
                return;
            }
            
            // Show loading
            resultDiv.style.display = 'block';
            resultDiv.className = 'result';
            resultDiv.innerHTML = 'Processing... Please wait.';
            
            try {
                const payload = {
                    instruction: instruction
                };
                
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
                    let html = '<h3>✅ Execution Complete!</h3>';
                    
                    // Show instruction
                    html += '<h4>📝 Instruction</h4>';
                    html += '<p><strong>' + result.instruction + '</strong></p>';
                    
                    // Show parsed operation if available
                    if (result.parsed_operation) {
                        html += '<h4>🔍 Parsed Operation</h4>';
                        html += '<pre>' + JSON.stringify(result.parsed_operation, null, 2) + '</pre>';
                    }
                    
                    // Show result if available
                    if (result.result) {
                        html += '<h4>📊 Result</h4>';
                        html += '<pre>' + JSON.stringify(result.result, null, 2) + '</pre>';
                    }
                    
                    // Show console output if available
                    if (result.console_output) {
                        html += '<h4>💻 Console Output</h4>';
                        html += '<pre>' + result.console_output + '</pre>';
                    }
                    
                    html += '<h4>📄 Full Response</h4>';
                    html += '<pre>' + JSON.stringify(result, null, 2) + '</pre>';
                    resultDiv.innerHTML = html;
                } else {
                    resultDiv.className = 'result error';
                    resultDiv.innerHTML = '<h3>❌ Error</h3><pre>' + JSON.stringify(result, null, 2) + '</pre>';
                }
            } catch (error) {
                resultDiv.className = 'result error';
                resultDiv.innerHTML = '<h3>❌ Error</h3><p>' + error.message + '</p>';
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
    
    parser = argparse.ArgumentParser(description="Test MongoDB MCP Lambda Function")
    parser.add_argument("--instruction", default="Find licence with identity number of 041223070745", help="Instruction to test")
    parser.add_argument("--api-url", help="API Gateway URL (for remote testing)")
    parser.add_argument("--create-html", action="store_true", help="Create test HTML page")

    args = parser.parse_args()

    if args.create_html:
        create_test_html()
    elif args.api_url:
        test_lambda_api(args.api_url, args.instruction)
    else:
        test_lambda_local(args.instruction)
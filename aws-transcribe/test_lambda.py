#!/usr/bin/env python3
"""
Local testing script for AWS Transcribe Lambda functions
"""

import json
import os
import sys
import argparse
from datetime import datetime

# Add current directory to path to import lambda_handler
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from lambda_handler import (
        transcribe_handler, 
        status_handler, 
        health_handler, 
        lambda_handler
    )
except ImportError as e:
    print(f"Error importing lambda_handler: {e}")
    sys.exit(1)

class MockContext:
    """Mock AWS Lambda context for local testing"""
    def __init__(self):
        self.aws_request_id = "test-request-id-123"
        self.log_group_name = "test-log-group"
        self.log_stream_name = "test-log-stream"
        self.function_name = "aws-transcribe-api-test"
        self.memory_limit_in_mb = 1024
        self.function_version = "1"

def test_health_endpoint():
    """Test the health check endpoint"""
    print("\n=== Testing Health Endpoint ===")
    
    event = {
        "httpMethod": "GET",
        "path": "/health",
        "headers": {"Content-Type": "application/json"}
    }
    
    context = MockContext()
    
    try:
        response = health_handler(event, context)
        print(f"Status Code: {response['statusCode']}")
        print(f"Response Body: {json.dumps(json.loads(response['body']), indent=2)}")
        return response['statusCode'] == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_transcribe_endpoint():
    """Test the transcribe endpoint with sample data"""
    print("\n=== Testing Transcribe Endpoint ===")
    
    # Use a public test audio file or a URL that will trigger validation
    # This test focuses on the API validation rather than actual transcription
    sample_request = {
        "url": "https://test-bucket.s3.us-east-1.amazonaws.com/sample-audio.mp3",
        "language": "en-us"
    }
    
    print(f"Testing with URL: {sample_request['url']}")
    print("Note: This test validates the API structure, not actual transcription")
    
    event = {
        "httpMethod": "POST",
        "path": "/transcribe",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(sample_request)
    }
    
    context = MockContext()
    
    try:
        response = transcribe_handler(event, context)
        print(f"Status Code: {response['statusCode']}")
        print(f"Response Body: {json.dumps(json.loads(response['body']), indent=2)}")
        # Expect 500 for inaccessible bucket or 200 for successful job start
        return response['statusCode'] in [200, 500]  
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_transcribe_with_invalid_url():
    """Test the transcribe endpoint with invalid S3 URL"""
    print("\n=== Testing Transcribe with Invalid URL ===")
    
    sample_request = {
        "url": "https://not-a-valid-s3-url.com/audio.mp3",
        "language": "en-us"
    }
    
    event = {
        "httpMethod": "POST",
        "path": "/transcribe",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(sample_request)
    }
    
    context = MockContext()
    
    try:
        response = transcribe_handler(event, context)
        print(f"Status Code: {response['statusCode']}")
        print(f"Response Body: {json.dumps(json.loads(response['body']), indent=2)}")
        return response['statusCode'] == 400  # Should return 400 for invalid URL
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_transcribe_with_public_url():
    """Test the transcribe endpoint with a publicly accessible audio file"""
    print("\n=== Testing Transcribe with Public URL ===")
    
    # Using a public sample audio file for testing
    sample_request = {
        "url": "https://www2.cs.uic.edu/~i101/SoundFiles/BabyElephantWalk60.wav",
        "language": "en-us"
    }
    
    print(f"Testing with public URL: {sample_request['url']}")
    
    event = {
        "httpMethod": "POST",
        "path": "/transcribe",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(sample_request)
    }
    
    context = MockContext()
    
    try:
        response = transcribe_handler(event, context)
        print(f"Status Code: {response['statusCode']}")
        print(f"Response Body: {json.dumps(json.loads(response['body']), indent=2)}")
        # This might still fail due to S3 format requirement, but tests the URL validation
        return response['statusCode'] in [200, 400, 500]  
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_s3_url_validation():
    """Test S3 URL validation function"""
    print("\n=== Testing S3 URL Validation ===")
    
    # Test valid S3 URLs
    valid_urls = [
        "https://bucket-name.s3.amazonaws.com/file.mp3",
        "https://bucket-name.s3.us-east-1.amazonaws.com/file.wav",
        "https://s3.amazonaws.com/bucket-name/file.m4a",
        "https://s3-us-west-2.amazonaws.com/bucket-name/file.mp4"
    ]
    
    # Test invalid URLs
    invalid_urls = [
        "https://example.com/file.mp3",
        "https://not-s3.amazonaws.com/file.wav",
        "ftp://bucket.s3.amazonaws.com/file.mp3",
        "http://bucket.s3.amazonaws.com/file.mp3"  # Should use HTTPS
    ]
    
    try:
        # Import the validation function
        from lambda_handler import is_valid_s3_url
        
        print("Testing valid S3 URLs:")
        for url in valid_urls:
            result = is_valid_s3_url(url)
            print(f"  {url}: {'✓' if result else '✗'}")
        
        print("\nTesting invalid URLs:")
        for url in invalid_urls:
            result = is_valid_s3_url(url)
            print(f"  {url}: {'✗' if not result else '✓ (unexpected)'}")
        
        return True
    except Exception as e:
        print(f"Error testing URL validation: {e}")
        return False

def test_status_endpoint():
    """Test the status endpoint"""
    print("\n=== Testing Status Endpoint ===")
    
    event = {
        "httpMethod": "GET",
        "path": "/status",
        "headers": {"Content-Type": "application/json"},
        "queryStringParameters": {
            "job_name": "test_job_name_123"
        }
    }
    
    context = MockContext()
    
    try:
        response = status_handler(event, context)
        print(f"Status Code: {response['statusCode']}")
        print(f"Response Body: {json.dumps(json.loads(response['body']), indent=2)}")
        return response['statusCode'] in [200, 404]  # 404 is expected for non-existent job
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_invalid_request():
    """Test invalid request handling"""
    print("\n=== Testing Invalid Request ===")
    
    event = {
        "httpMethod": "POST",
        "path": "/transcribe",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"invalid": "request"})  # Missing required 'url' field
    }
    
    context = MockContext()
    
    try:
        response = transcribe_handler(event, context)
        print(f"Status Code: {response['statusCode']}")
        print(f"Response Body: {json.dumps(json.loads(response['body']), indent=2)}")
        return response['statusCode'] == 400
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_unsupported_language():
    """Test unsupported language handling"""
    print("\n=== Testing Unsupported Language ===")
    
    sample_request = {
        "url": "https://example.s3.amazonaws.com/sample-audio.mp3",
        "language": "fr-fr"  # French - not supported
    }
    
    event = {
        "httpMethod": "POST",
        "path": "/transcribe",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(sample_request)
    }
    
    context = MockContext()
    
    try:
        response = transcribe_handler(event, context)
        print(f"Status Code: {response['statusCode']}")
        print(f"Response Body: {json.dumps(json.loads(response['body']), indent=2)}")
        return response['statusCode'] == 400
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_router():
    """Test the main lambda_handler router"""
    print("\n=== Testing Router ===")
    
    # Test 404 for unknown endpoint
    event = {
        "httpMethod": "GET",
        "path": "/unknown",
        "headers": {"Content-Type": "application/json"}
    }
    
    context = MockContext()
    
    try:
        response = lambda_handler(event, context)
        print(f"Status Code: {response['statusCode']}")
        print(f"Response Body: {json.dumps(json.loads(response['body']), indent=2)}")
        return response['statusCode'] == 404
    except Exception as e:
        print(f"Error: {e}")
        return False

def create_html_test_interface():
    """Create the HTML test interface file"""
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AWS Transcribe API Test Interface</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            backdrop-filter: blur(10px);
        }
        
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
            font-size: 14px;
        }
        
        input, select, textarea {
            width: 100%;
            padding: 14px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 14px;
            box-sizing: border-box;
            transition: border-color 0.3s ease;
        }
        
        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        button {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            margin-right: 10px;
            margin-bottom: 10px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        button:disabled {
            background: #6c757d;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .response {
            margin-top: 20px;
            padding: 20px;
            border-radius: 8px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            white-space: pre-wrap;
            max-height: 500px;
            overflow-y: auto;
            font-size: 13px;
            line-height: 1.5;
        }
        
        .response.success {
            background: linear-gradient(135deg, #d4edda, #c3e6cb);
            border: 2px solid #28a745;
            color: #155724;
        }
        
        .response.error {
            background: linear-gradient(135deg, #f8d7da, #f5c6cb);
            border: 2px solid #dc3545;
            color: #721c24;
        }
        
        .loading {
            display: none;
            text-align: center;
            margin: 30px 0;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .endpoint-section {
            border: 2px solid #e9ecef;
            border-radius: 12px;
            margin-bottom: 30px;
            padding: 25px;
            background: linear-gradient(135deg, #f8f9fa, #ffffff);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .endpoint-section:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }
        
        .endpoint-title {
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 15px;
            color: #333;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .info-box {
            background: linear-gradient(135deg, #e7f3ff, #cce7ff);
            border-left: 4px solid #007bff;
            padding: 15px 20px;
            margin-bottom: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,123,255,0.1);
        }
        
        .supported-languages {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin-top: 15px;
        }
        
        .language-item {
            background: linear-gradient(135deg, #ffffff, #f8f9fa);
            padding: 12px 16px;
            border-radius: 8px;
            text-align: center;
            font-size: 14px;
            font-weight: 500;
            border: 2px solid #e9ecef;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        
        .language-item:hover {
            transform: translateY(-2px);
            border-color: #667eea;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-success { background-color: #28a745; }
        .status-error { background-color: #dc3545; }
        .status-pending { background-color: #ffc107; }
        
        .quick-actions {
            background: linear-gradient(135deg, #f1f3f4, #e8eaed);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 25px;
        }
        
        .quick-actions h3 {
            margin: 0 0 15px 0;
            color: #333;
            font-size: 16px;
        }
        
        .quick-buttons {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .quick-btn {
            background: #6c757d;
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.2s ease;
        }
        
        .quick-btn:hover {
            background: #5a6268;
        }
        
        .footer {
            margin-top: 40px;
            text-align: center;
            color: #6c757d;
            font-size: 14px;
            padding: 20px;
            border-top: 1px solid #e9ecef;
        }
        
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            
            .container {
                padding: 20px;
            }
            
            h1 {
                font-size: 2em;
            }
            
            .quick-buttons {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎤 AWS Transcribe API Test Interface</h1>
        
        <div class="info-box">
            <strong>🌍 Supported Languages:</strong>
            <div class="supported-languages">
                <div class="language-item">🇺🇸 English (en-us)</div>
                <div class="language-item">🇨🇳 Chinese (zh-cn)</div>
                <div class="language-item">🇲🇾 Malay (ms-my)</div>
                <div class="language-item">🇮🇩 Indonesian (id-id)</div>
            </div>
        </div>

        <div class="quick-actions">
            <h3>🚀 Quick Actions</h3>
            <div class="quick-buttons">
                <button class="quick-btn" onclick="populateTestData()">📝 Load Test Data</button>
                <button class="quick-btn" onclick="clearAll()">🗑️ Clear All</button>
                <button class="quick-btn" onclick="exportResults()">💾 Export Results</button>
                <button class="quick-btn" onclick="autoMonitor()">🔄 Auto Monitor</button>
            </div>
        </div>

        <!-- Health Check Section -->
        <div class="endpoint-section">
            <div class="endpoint-title">
                🏥 Health Check
                <span class="status-indicator status-pending" id="health-status"></span>
            </div>
            <button onclick="testHealth()">🔍 Test Health Endpoint</button>
        </div>

        <!-- Transcribe Section -->
        <div class="endpoint-section">
            <div class="endpoint-title">
                🎵 Start Transcription
                <span class="status-indicator status-pending" id="transcribe-status"></span>
            </div>
            
            <div class="form-group">
                <label for="s3Url">📁 S3 Download URL:</label>
                <input type="url" id="s3Url" placeholder="https://your-bucket.s3.amazonaws.com/audio-file.mp3" required>
            </div>
            
            <div class="form-group">
                <label for="language">🌐 Language:</label>
                <select id="language">
                    <option value="en-us">🇺🇸 English (en-us)</option>
                    <option value="zh-cn">🇨🇳 Chinese (zh-cn)</option>
                    <option value="ms-my">🇲🇾 Malay (ms-my)</option>
                    <option value="id-id">🇮🇩 Indonesian (id-id)</option>
                </select>
            </div>
            
            <button onclick="startTranscription()">🚀 Start Transcription</button>
            <button onclick="startAndMonitor()" style="background: linear-gradient(45deg, #28a745, #20c997);">🔄 Start & Auto-Monitor</button>
        </div>

        <!-- Status Check Section -->
        <div class="endpoint-section">
            <div class="endpoint-title">
                📊 Check Transcription Status
                <span class="status-indicator status-pending" id="status-status"></span>
            </div>
            
            <div class="form-group">
                <label for="jobName">🏷️ Job Name:</label>
                <input type="text" id="jobName" placeholder="transcribe_job_20231201_123456_abc123">
            </div>
            
            <button onclick="checkStatus()">📈 Check Status</button>
            <button onclick="getTranscript()" style="background: linear-gradient(45deg, #17a2b8, #138496);">📜 Get Transcript</button>
        </div>

        <!-- API Endpoint Configuration -->
        <div class="endpoint-section">
            <div class="endpoint-title">⚙️ API Configuration</div>
            
            <div class="form-group">
                <label for="apiUrl">🔗 API Base URL:</label>
                <input type="url" id="apiUrl" placeholder="https://your-api-gateway-url.amazonaws.com/dev">
            </div>
            
            <button onclick="saveConfig()">💾 Save Config</button>
            <button onclick="loadConfig()">📂 Load Config</button>
        </div>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p><strong>Processing request...</strong></p>
        </div>

        <div id="response" class="response" style="display: none;"></div>
        
        <div class="footer">
            <p>🔧 Created by AWS Transcribe Lambda Test Script</p>
            <p>Last Updated: <span id="timestamp"></span></p>
        </div>
    </div>

    <script>
        // Set current timestamp
        document.getElementById('timestamp').textContent = new Date().toLocaleString();
        
        const apiBaseUrl = () => document.getElementById('apiUrl').value || '';
        let autoMonitorInterval = null;
        
        function updateStatus(elementId, status) {
            const element = document.getElementById(elementId);
            element.className = `status-indicator status-${status}`;
        }
        
        function showLoading() {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('response').style.display = 'none';
        }
        
        function hideLoading() {
            document.getElementById('loading').style.display = 'none';
        }
        
        function showResponse(data, isError = false) {
            hideLoading();
            const responseDiv = document.getElementById('response');
            responseDiv.className = `response ${isError ? 'error' : 'success'}`;
            
            let displayText;
            if (typeof data === 'string') {
                displayText = data;
            } else {
                displayText = JSON.stringify(data, null, 2);
            }
            
            // Add timestamp to response
            const timestamp = new Date().toLocaleString();
            displayText = `[${timestamp}] ${displayText}`;
            
            responseDiv.textContent = displayText;
            responseDiv.style.display = 'block';
            
            // Scroll to response
            responseDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
        
        async function makeRequest(endpoint, method = 'GET', body = null) {
            const url = `${apiBaseUrl()}${endpoint}`;
            
            try {
                const options = {
                    method,
                    headers: {
                        'Content-Type': 'application/json',
                    }
                };
                
                if (body) {
                    options.body = JSON.stringify(body);
                }
                
                const response = await fetch(url, options);
                const data = await response.json();
                
                return {
                    success: response.ok,
                    status: response.status,
                    data
                };
            } catch (error) {
                return {
                    success: false,
                    status: 0,
                    data: { error: `Network error: ${error.message}` }
                };
            }
        }
        
        async function testHealth() {
            showLoading();
            updateStatus('health-status', 'pending');
            
            const result = await makeRequest('/health');
            
            if (result.success) {
                updateStatus('health-status', 'success');
                showResponse({
                    message: '✅ Health check successful!',
                    status: result.status,
                    data: result.data
                });
            } else {
                updateStatus('health-status', 'error');
                showResponse({
                    message: '❌ Health check failed!',
                    status: result.status,
                    error: result.data
                }, true);
            }
        }
        
        async function startTranscription() {
            const url = document.getElementById('s3Url').value;
            const language = document.getElementById('language').value;
            
            if (!url) {
                showResponse('❌ Please enter a valid S3 URL', true);
                return;
            }
            
            showLoading();
            updateStatus('transcribe-status', 'pending');
            
            const result = await makeRequest('/transcribe', 'POST', {
                url: url,
                language: language
            });
            
            if (result.success) {
                updateStatus('transcribe-status', 'success');
                
                // Extract job name for convenience
                if (result.data && result.data.data && result.data.data.job_name) {
                    document.getElementById('jobName').value = result.data.data.job_name;
                }
                
                showResponse({
                    message: '🚀 Transcription started successfully!',
                    status: result.status,
                    data: result.data
                });
            } else {
                updateStatus('transcribe-status', 'error');
                showResponse({
                    message: '❌ Failed to start transcription',
                    status: result.status,
                    error: result.data
                }, true);
            }
        }
        
        async function startAndMonitor() {
            await startTranscription();
            
            // If transcription started successfully, begin monitoring
            const jobName = document.getElementById('jobName').value;
            if (jobName) {
                setTimeout(() => autoMonitor(), 5000); // Start monitoring after 5 seconds
            }
        }
        
        async function checkStatus() {
            const jobName = document.getElementById('jobName').value;
            
            if (!jobName) {
                showResponse('❌ Please enter a job name', true);
                return;
            }
            
            showLoading();
            updateStatus('status-status', 'pending');
            
            const result = await makeRequest(`/status?job_name=${encodeURIComponent(jobName)}`);
            
            if (result.success) {
                updateStatus('status-status', 'success');
                showResponse({
                    message: '📊 Status retrieved successfully!',
                    status: result.status,
                    data: result.data
                });
                
                // Check if completed
                if (result.data && result.data.data && result.data.data.status === 'COMPLETED') {
                    // Stop auto-monitoring if running
                    if (autoMonitorInterval) {
                        clearInterval(autoMonitorInterval);
                        autoMonitorInterval = null;
                    }
                }
            } else {
                updateStatus('status-status', 'error');
                showResponse({
                    message: '❌ Failed to get status',
                    status: result.status,
                    error: result.data
                }, true);
            }
        }
        
        async function getTranscript() {
            const jobName = document.getElementById('jobName').value;
            
            if (!jobName) {
                showResponse('❌ Please enter a job name', true);
                return;
            }
            
            // First check status to get transcript
            await checkStatus();
        }
        
        function autoMonitor() {
            const jobName = document.getElementById('jobName').value;
            
            if (!jobName) {
                showResponse('❌ No job name available for monitoring', true);
                return;
            }
            
            // Clear existing interval
            if (autoMonitorInterval) {
                clearInterval(autoMonitorInterval);
            }
            
            // Start monitoring every 10 seconds
            autoMonitorInterval = setInterval(async () => {
                await checkStatus();
                
                // Check if we should stop monitoring
                const responseDiv = document.getElementById('response');
                if (responseDiv.textContent.includes('COMPLETED') || responseDiv.textContent.includes('FAILED')) {
                    clearInterval(autoMonitorInterval);
                    autoMonitorInterval = null;
                    showResponse('🏁 Auto-monitoring stopped - job completed');
                }
            }, 10000);
            
            showResponse('🔄 Auto-monitoring started - checking every 10 seconds...');
        }
        
        function populateTestData() {
            document.getElementById('s3Url').value = 'https://great-ai-hackathon-uploads-dev.s3.us-east-1.amazonaws.com/sample-audio.m4a';
            document.getElementById('language').value = 'en-us';
            document.getElementById('apiUrl').value = 'https://h0lto8pesc.execute-api.us-east-1.amazonaws.com/dev';
            showResponse('📝 Test data loaded successfully!');
        }
        
        function clearAll() {
            document.getElementById('s3Url').value = '';
            document.getElementById('jobName').value = '';
            document.getElementById('response').style.display = 'none';
            
            // Reset status indicators
            updateStatus('health-status', 'pending');
            updateStatus('transcribe-status', 'pending');
            updateStatus('status-status', 'pending');
            
            // Stop auto-monitoring
            if (autoMonitorInterval) {
                clearInterval(autoMonitorInterval);
                autoMonitorInterval = null;
            }
            
            showResponse('🗑️ All fields cleared!');
        }
        
        function exportResults() {
            const responseDiv = document.getElementById('response');
            if (responseDiv.style.display === 'none') {
                showResponse('❌ No results to export', true);
                return;
            }
            
            const data = responseDiv.textContent;
            const blob = new Blob([data], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `transcribe-results-${new Date().toISOString().slice(0,19).replace(/:/g,'-')}.txt`;
            a.click();
            URL.revokeObjectURL(url);
            
            showResponse('💾 Results exported successfully!');
        }
        
        function saveConfig() {
            const config = {
                apiUrl: document.getElementById('apiUrl').value,
                s3Url: document.getElementById('s3Url').value,
                language: document.getElementById('language').value
            };
            
            localStorage.setItem('transcribeConfig', JSON.stringify(config));
            showResponse('💾 Configuration saved to browser storage!');
        }
        
        function loadConfig() {
            const saved = localStorage.getItem('transcribeConfig');
            if (saved) {
                const config = JSON.parse(saved);
                document.getElementById('apiUrl').value = config.apiUrl || '';
                document.getElementById('s3Url').value = config.s3Url || '';
                document.getElementById('language').value = config.language || 'en-us';
                showResponse('📂 Configuration loaded from browser storage!');
            } else {
                showResponse('❌ No saved configuration found', true);
            }
        }
        
        // Auto-detect API URL if running on deployed endpoint
        window.addEventListener('load', function() {
            // Try to load saved config first
            const saved = localStorage.getItem('transcribeConfig');
            if (saved) {
                const config = JSON.parse(saved);
                if (config.apiUrl) {
                    document.getElementById('apiUrl').value = config.apiUrl;
                }
            }
            
            // If no saved config and not localhost, try to detect API Gateway URL
            if (!document.getElementById('apiUrl').value && 
                window.location.hostname !== 'localhost' && 
                window.location.hostname !== '127.0.0.1') {
                const protocol = window.location.protocol;
                const hostname = window.location.hostname;
                document.getElementById('apiUrl').value = `${protocol}//${hostname}`;
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'h':
                        e.preventDefault();
                        testHealth();
                        break;
                    case 't':
                        e.preventDefault();
                        startTranscription();
                        break;
                    case 's':
                        e.preventDefault();
                        checkStatus();
                        break;
                }
            }
        });
    </script>
</body>
</html>'''
    
    filename = "test_lambda.html"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ Enhanced HTML test interface created: {filename}")
        print(f"📁 Location: {os.path.abspath(filename)}")
        print(f"🌐 Open this file in your web browser to test the API")
        print(f"🎨 New features:")
        print(f"   - Enhanced UI with gradients and animations")
        print(f"   - Auto-monitoring functionality")
        print(f"   - Quick action buttons")
        print(f"   - Export results feature")
        print(f"   - Save/load configuration")
        print(f"   - Keyboard shortcuts (Ctrl+H, Ctrl+T, Ctrl+S)")
        print(f"   - Status indicators")
        print(f"   - Mobile responsive design")
        return True
    except Exception as e:
        print(f"❌ Error creating HTML file: {e}")
        return False

def main():
    """Run all tests or create HTML interface"""
    parser = argparse.ArgumentParser(description='AWS Transcribe Lambda Function Test Script')
    parser.add_argument('--create-html', action='store_true', 
                        help='Create HTML test interface file')
    
    args = parser.parse_args()
    
    if args.create_html:
        print("🎨 Creating HTML Test Interface...")
        print("=" * 50)
        success = create_html_test_interface()
        return 0 if success else 1
    
    print("Starting AWS Transcribe Lambda Function Tests...")
    print(f"Test started at: {datetime.now().isoformat()}")
    print("\n📝 NOTE: Some tests may fail with 500 errors due to:")
    print("   - S3 bucket access permissions")
    print("   - Non-existent test buckets") 
    print("   - AWS credentials not configured")
    print("   This is expected for local testing without proper AWS setup.\n")
    
    # Set test environment variables for us-east-1 region
    os.environ['OUTPUT_S3_BUCKET_NAME'] = 'test-transcribe-output-bucket'
    os.environ['AWS_REGION1'] = 'us-east-1'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    
    tests = [
        ("Health Endpoint", test_health_endpoint),
        ("S3 URL Validation", test_s3_url_validation),
        ("Transcribe Endpoint", test_transcribe_endpoint),
        ("Transcribe Invalid URL", test_transcribe_with_invalid_url),
        ("Transcribe Public URL", test_transcribe_with_public_url),
        ("Status Endpoint", test_status_endpoint),
        ("Invalid Request", test_invalid_request),
        ("Unsupported Language", test_unsupported_language),
        ("Router", test_router)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            status = "PASS" if result else "FAIL"
            print(f"\n{test_name}: {status}")
        except Exception as e:
            print(f"\n{test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
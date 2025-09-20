#!/usr/bin/env python3
"""
Test script for S3 Upload Lambda function
"""

import json
import base64
import requests
from pathlib import Path
import mimetypes


def test_upload_json_api(api_url, file_path):
    """Test file upload using JSON API (base64 encoded)"""
    
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return None
    
    # Read file content
    with open(file_path, 'rb') as f:
        file_content = f.read()
    
    # Encode to base64
    content_b64 = base64.b64encode(file_content).decode('utf-8')
    
    # Guess content type
    content_type, _ = mimetypes.guess_type(str(file_path))
    if not content_type:
        content_type = 'application/octet-stream'
    
    # Prepare request
    payload = {
        "filename": file_path.name,
        "content": content_b64,
        "content_type": content_type
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    print(f"Uploading {file_path.name} ({len(file_content)} bytes) via JSON API...")
    
    try:
        response = requests.post(f"{api_url}/upload", json=payload, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Upload successful!")
            print(f"Filename: {result.get('filename')}")
            print(f"Size: {result.get('size')} bytes")
            print(f"Download URL: {result.get('download_url')}")
            return result
        else:
            print(f"Upload failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None


def test_get_download_url(api_url, file_key):
    """Test getting download URL for a file"""
    
    print(f"Getting download URL for: {file_key}")
    
    try:
        response = requests.get(f"{api_url}/download/{file_key}")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Download URL generated!")
            print(f"URL: {result.get('download_url')}")
            print(f"Expires in: {result.get('expiration_seconds')} seconds")
            return result
        else:
            print(f"Failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None


def test_list_files(api_url):
    """Test listing files in bucket"""
    
    print("Listing files in bucket...")
    
    try:
        response = requests.get(f"{api_url}/files")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            files = result.get('files', [])
            print(f"Found {len(files)} files:")
            
            for file_info in files[:10]:  # Show first 10 files
                print(f"  - {file_info['key']} ({file_info['size']} bytes)")
            
            if len(files) > 10:
                print(f"  ... and {len(files) - 10} more files")
            
            return result
        else:
            print(f"Failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None


def test_health_check(api_url):
    """Test health endpoint"""
    
    print("Testing health check...")
    
    try:
        response = requests.get(f"{api_url}/health")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Health check passed!")
            print(f"Status: {result.get('status')}")
            print(f"Service: {result.get('service')}")
            print(f"Bucket: {result.get('bucket')}")
            return result
        else:
            print(f"Health check failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None


def create_test_file():
    """Create a test file for upload"""
    
    test_file = Path("test_upload.txt")
    
    content = """This is a test file for S3 upload.
Created by the test script.
Timestamp: """ + str(Path(__file__).stat().st_mtime)
    
    with open(test_file, 'w') as f:
        f.write(content)
    
    print(f"Created test file: {test_file}")
    return test_file


def create_html_test_file(api_url):
    """Create an HTML test interface file"""
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>S3 Upload API Test</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .section {{
            margin-bottom: 30px;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }}
        .section h2 {{
            margin-top: 0;
            color: #333;
        }}
        input, textarea, button {{
            margin: 10px 0;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 3px;
            width: 100%;
            box-sizing: border-box;
        }}
        button {{
            background-color: #007bff;
            color: white;
            border: none;
            cursor: pointer;
            font-size: 16px;
        }}
        button:hover {{
            background-color: #0056b3;
        }}
        button:disabled {{
            background-color: #6c757d;
            cursor: not-allowed;
        }}
        .result {{
            margin-top: 15px;
            padding: 15px;
            border-radius: 3px;
            white-space: pre-wrap;
            font-family: monospace;
            font-size: 12px;
        }}
        .success {{
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }}
        .error {{
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }}
        .info {{
            background-color: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
        }}
        .file-list {{
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #ddd;
            padding: 10px;
            margin-top: 10px;
        }}
        .file-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 5px 0;
            border-bottom: 1px solid #eee;
        }}
        .file-item:last-child {{
            border-bottom: none;
        }}
        .download-btn {{
            background-color: #28a745;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
            width: auto;
        }}
        .download-btn:hover {{
            background-color: #218838;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>S3 Upload API Test Interface</h1>
        
        <!-- Configuration Section -->
        <div class="section">
            <h2>Configuration</h2>
            <label for="apiUrl">API Base URL:</label>
            <input type="text" id="apiUrl" placeholder="https://your-api-id.execute-api.us-east-1.amazonaws.com/dev" value="{api_url}">
            <button onclick="testHealth()">Test Connection</button>
            <div id="healthResult" class="result" style="display: none;"></div>
        </div>

        <!-- File Upload Section -->
        <div class="section">
            <h2>File Upload</h2>
            <label for="fileInput">Select File:</label>
            <input type="file" id="fileInput" accept="*/*">
            <button onclick="uploadFile()" id="uploadBtn">Upload File</button>
            <div id="uploadResult" class="result" style="display: none;"></div>
        </div>

        <!-- File List Section -->
        <div class="section">
            <h2>Files in Bucket</h2>
            <button onclick="listFiles()">Refresh File List</button>
            <div id="fileList" class="file-list" style="display: none;"></div>
            <div id="listResult" class="result" style="display: none;"></div>
        </div>

        <!-- Download URL Test Section -->
        <div class="section">
            <h2>Generate Download URL</h2>
            <label for="fileKey">File Key:</label>
            <input type="text" id="fileKey" placeholder="filename.ext">
            <button onclick="getDownloadUrl()">Generate Download URL</button>
            <div id="downloadResult" class="result" style="display: none;"></div>
        </div>
    </div>

    <script>
        // Utility functions
        function getApiUrl() {{
            return document.getElementById('apiUrl').value.replace(/\\/$/, '');
        }}

        function showResult(elementId, message, type = 'info') {{
            const element = document.getElementById(elementId);
            element.className = `result ${{type}}`;
            element.textContent = message;
            element.style.display = 'block';
        }}

        function showJsonResult(elementId, data, type = 'success') {{
            const element = document.getElementById(elementId);
            element.className = `result ${{type}}`;
            element.textContent = JSON.stringify(data, null, 2);
            element.style.display = 'block';
        }}

        // Test health endpoint
        async function testHealth() {{
            const apiUrl = getApiUrl();
            if (!apiUrl) {{
                showResult('healthResult', 'Please enter API URL', 'error');
                return;
            }}

            try {{
                showResult('healthResult', 'Testing connection...', 'info');
                
                const response = await fetch(`${{apiUrl}}/health`);
                const data = await response.json();
                
                if (response.ok) {{
                    showJsonResult('healthResult', data, 'success');
                }} else {{
                    showJsonResult('healthResult', data, 'error');
                }}
            }} catch (error) {{
                showResult('healthResult', `Connection failed: ${{error.message}}`, 'error');
            }}
        }}

        // Upload file
        async function uploadFile() {{
            const apiUrl = getApiUrl();
            const fileInput = document.getElementById('fileInput');
            
            if (!apiUrl) {{
                showResult('uploadResult', 'Please enter API URL', 'error');
                return;
            }}
            
            if (!fileInput.files.length) {{
                showResult('uploadResult', 'Please select a file', 'error');
                return;
            }}

            const file = fileInput.files[0];
            const uploadBtn = document.getElementById('uploadBtn');
            
            try {{
                uploadBtn.disabled = true;
                uploadBtn.textContent = 'Uploading...';
                showResult('uploadResult', 'Reading file...', 'info');

                // Convert file to base64
                const base64Content = await fileToBase64(file);
                
                showResult('uploadResult', 'Uploading to S3...', 'info');

                const payload = {{
                    filename: file.name,
                    content: base64Content,
                    content_type: file.type || 'application/octet-stream'
                }};

                const response = await fetch(`${{apiUrl}}/upload`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify(payload)
                }});

                const data = await response.json();
                
                if (response.ok) {{
                    showJsonResult('uploadResult', data, 'success');
                    // Auto-refresh file list
                    setTimeout(listFiles, 1000);
                }} else {{
                    showJsonResult('uploadResult', data, 'error');
                }}
            }} catch (error) {{
                showResult('uploadResult', `Upload failed: ${{error.message}}`, 'error');
            }} finally {{
                uploadBtn.disabled = false;
                uploadBtn.textContent = 'Upload File';
            }}
        }}

        // Convert file to base64
        function fileToBase64(file) {{
            return new Promise((resolve, reject) => {{
                const reader = new FileReader();
                reader.readAsDataURL(file);
                reader.onload = () => {{
                    // Remove the data URL prefix
                    const base64 = reader.result.split(',')[1];
                    resolve(base64);
                }};
                reader.onerror = error => reject(error);
            }});
        }}

        // List files in bucket
        async function listFiles() {{
            const apiUrl = getApiUrl();
            if (!apiUrl) {{
                showResult('listResult', 'Please enter API URL', 'error');
                return;
            }}

            try {{
                showResult('listResult', 'Loading files...', 'info');
                
                const response = await fetch(`${{apiUrl}}/files`);
                const data = await response.json();
                
                if (response.ok) {{
                    displayFileList(data.files || []);
                    showJsonResult('listResult', data, 'success');
                }} else {{
                    showJsonResult('listResult', data, 'error');
                    document.getElementById('fileList').style.display = 'none';
                }}
            }} catch (error) {{
                showResult('listResult', `Failed to list files: ${{error.message}}`, 'error');
                document.getElementById('fileList').style.display = 'none';
            }}
        }}

        // Display file list
        function displayFileList(files) {{
            const fileListDiv = document.getElementById('fileList');
            
            if (files.length === 0) {{
                fileListDiv.innerHTML = '<p>No files found in bucket</p>';
            }} else {{
                fileListDiv.innerHTML = files.map(file => `
                    <div class="file-item">
                        <div>
                            <strong>${{file.key}}</strong><br>
                            <small>${{formatFileSize(file.size)}} - ${{new Date(file.last_modified).toLocaleString()}}</small>
                        </div>
                        <button class="download-btn" onclick="getDownloadUrlForFile('${{file.key}}')">
                            Get Download URL
                        </button>
                    </div>
                `).join('');
            }}
            
            fileListDiv.style.display = 'block';
        }}

        // Format file size
        function formatFileSize(bytes) {{
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }}

        // Get download URL
        async function getDownloadUrl() {{
            const apiUrl = getApiUrl();
            const fileKey = document.getElementById('fileKey').value;
            
            if (!apiUrl) {{
                showResult('downloadResult', 'Please enter API URL', 'error');
                return;
            }}
            
            if (!fileKey) {{
                showResult('downloadResult', 'Please enter file key', 'error');
                return;
            }}

            try {{
                showResult('downloadResult', 'Generating download URL...', 'info');
                
                const response = await fetch(`${{apiUrl}}/download/${{encodeURIComponent(fileKey)}}`);
                const data = await response.json();
                
                if (response.ok) {{
                    showJsonResult('downloadResult', data, 'success');
                }} else {{
                    showJsonResult('downloadResult', data, 'error');
                }}
            }} catch (error) {{
                showResult('downloadResult', `Failed to generate URL: ${{error.message}}`, 'error');
            }}
        }}

        // Get download URL for specific file (called from file list)
        function getDownloadUrlForFile(fileKey) {{
            document.getElementById('fileKey').value = fileKey;
            getDownloadUrl();
        }}

        // Initialize page
        document.addEventListener('DOMContentLoaded', function() {{
            // API URL is pre-filled from command line parameter
        }});
    </script>
</body>
</html>'''
    
    html_file = Path("test_lambda.html")
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Created HTML test file: {html_file}")
    print(f"Open {html_file} in your browser to test the API")
    return html_file


def main():
    # Configuration
    API_URL = "https://your-api-id.execute-api.us-east-1.amazonaws.com/dev"
    
    print("S3 Upload API Test Script")
    print("=" * 50)
    
    # Test health check first
    print("\n1. Health Check")
    print("-" * 20)
    health_result = test_health_check(API_URL)
    
    if not health_result:
        print("Health check failed. Exiting.")
        return
    
    # Create test file
    print("\n2. Creating Test File")
    print("-" * 20)
    test_file = create_test_file()
    
    # Test upload
    print("\n3. Testing File Upload")
    print("-" * 20)
    upload_result = test_upload_json_api(API_URL, test_file)
    
    if upload_result:
        file_key = upload_result.get('filename')
        
        # Test get download URL
        print("\n4. Testing Download URL Generation")
        print("-" * 20)
        download_result = test_get_download_url(API_URL, file_key)
        
        if download_result:
            print(f"\nYou can download the file using:")
            print(f"curl -o downloaded_{file_key} '{download_result['download_url']}'")
    
    # Test list files
    print("\n5. Testing File Listing")
    print("-" * 20)
    list_result = test_list_files(API_URL)
    
    # Cleanup test file
    if test_file.exists():
        test_file.unlink()
        print(f"\nCleaned up: {test_file}")
    
    print("\nTest completed!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test S3 Upload API")
    parser.add_argument("--api-url", help="API Gateway URL (required for testing, optional for --create-html)")
    parser.add_argument("--file", help="File to upload (optional, will create test file if not provided)")
    parser.add_argument("--create-html", action="store_true", help="Create an HTML test interface file")
    
    args = parser.parse_args()
    
    # If create-html flag is set, create HTML file and exit
    if args.create_html:
        api_url = args.api_url or ""
        create_html_test_file(api_url)
        exit(0)
    
    # For testing mode, API URL is required
    if not args.api_url:
        parser.error("--api-url is required when not using --create-html")
    
    # Update API_URL in main function
    API_URL = args.api_url.rstrip('/')
    
    print("S3 Upload API Test Script")
    print("=" * 50)
    
    # Test health check first
    print("\n1. Health Check")
    print("-" * 20)
    health_result = test_health_check(API_URL)
    
    if not health_result:
        print("Health check failed. Exiting.")
        exit(1)
    
    # Determine test file
    if args.file:
        test_file = Path(args.file)
        if not test_file.exists():
            print(f"File not found: {test_file}")
            exit(1)
    else:
        print("\n2. Creating Test File")
        print("-" * 20)
        test_file = create_test_file()
    
    # Test upload
    print("\n3. Testing File Upload")
    print("-" * 20)
    upload_result = test_upload_json_api(API_URL, test_file)
    
    if upload_result:
        file_key = upload_result.get('filename')
        
        # Test get download URL
        print("\n4. Testing Download URL Generation")
        print("-" * 20)
        download_result = test_get_download_url(API_URL, file_key)
        
        if download_result:
            print(f"\nYou can download the file using:")
            print(f"curl -o downloaded_{file_key} '{download_result['download_url']}'")
    
    # Test list files
    print("\n5. Testing File Listing")
    print("-" * 20)
    list_result = test_list_files(API_URL)
    
    # Cleanup test file if we created it
    if not args.file and test_file.exists():
        test_file.unlink()
        print(f"\nCleaned up: {test_file}")
    
    print("\nTest completed!")
# S3 Upload API Service

A serverless file upload service built with AWS Lambda, API Gateway, and S3. This service allows you to upload files to S3 and get presigned download URLs.

## Quick Start

**API Base URL:** `https://5gkaebz86a.execute-api.us-east-1.amazonaws.com/dev`

**Test the API immediately:**
```python
import requests
import base64

# Health Check
response = requests.get("https://5gkaebz86a.execute-api.us-east-1.amazonaws.com/dev/health")
print("Health:", response.json())

# Upload a file (replace 'your-file.jpg' with actual file path)
with open('your-file.jpg', 'rb') as f:
    content = base64.b64encode(f.read()).decode('utf-8')

upload_data = {
    "filename": "your-file.jpg", 
    "content": content,
    "content_type": "image/jpeg"
}
response = requests.post("https://5gkaebz86a.execute-api.us-east-1.amazonaws.com/dev/upload", json=upload_data)
print("Upload:", response.json())
```

## Features

- **File Upload**: Upload files via JSON API with base64 encoding
- **Download URLs**: Generate presigned URLs for secure file downloads
- **File Listing**: List all files in the S3 bucket
- **Health Check**: Monitor service status
- **CORS Support**: Cross-origin requests enabled
- **Auto-scaling**: Serverless architecture scales automatically

## API Endpoints

### Base URL
```
https://5gkaebz86a.execute-api.us-east-1.amazonaws.com/dev
```

### Available Endpoints

#### 1. Health Check
```
GET /health
```
Returns service status and configuration.

**Example Response:**
```json
{
  "status": "healthy",
  "service": "s3-upload-api",
  "bucket": "great-ai-hackathon-uploads-dev",
  "timestamp": "2025-09-20T17:33:22.165195",
  "request_id": "7aface27-9927-42b7-ad9d-932c65f95928"
}
```

**Python Example:**
```python
import requests

def check_health():
    url = "https://5gkaebz86a.execute-api.us-east-1.amazonaws.com/dev/health"
    response = requests.get(url)
    return response.json()

# Usage
health_status = check_health()
print(f"Service status: {health_status['status']}")
```

#### 2. Upload File
```
POST /upload
```
Upload a file using JSON with base64 encoded content.

**Request Body:**
```json
{
  "filename": "license.jpeg",
  "content": "base64_encoded_file_content",
  "content_type": "image/jpeg"
}
```

**Example Response:**
```json
{
  "message": "File uploaded successfully",
  "filename": "license_20250920_173332_95234ada.jpeg",
  "bucket": "great-ai-hackathon-uploads-dev",
  "size": 85267,
  "content_type": "image/jpeg",
  "download_url": "https://great-ai-hackathon-uploads-dev.s3.amazonaws.com/license_20250920_173332_95234ada.jpeg?AWSAccessKeyId=...",
  "expiration_seconds": 3600,
  "upload_timestamp": "2025-09-20T17:33:32.258547"
}
```

**Python Example:**
```python
import requests
import base64

def upload_file(file_path, content_type=None):
    # Read and encode file
    with open(file_path, 'rb') as file:
        file_content = base64.b64encode(file.read()).decode('utf-8')
    
    # Determine content type if not provided
    if not content_type:
        if file_path.lower().endswith('.jpeg') or file_path.lower().endswith('.jpg'):
            content_type = 'image/jpeg'
        elif file_path.lower().endswith('.png'):
            content_type = 'image/png'
        elif file_path.lower().endswith('.pdf'):
            content_type = 'application/pdf'
        else:
            content_type = 'application/octet-stream'
    
    # Prepare request
    url = "https://5gkaebz86a.execute-api.us-east-1.amazonaws.com/dev/upload"
    payload = {
        "filename": file_path.split('/')[-1],  # Extract filename
        "content": file_content,
        "content_type": content_type
    }
    
    response = requests.post(url, json=payload)
    return response.json()

# Usage
result = upload_file("license.jpeg", "image/jpeg")
print(f"Upload successful: {result['filename']}")
print(f"Download URL: {result['download_url']}")
```

#### 3. List Files
```
GET /files?limit=100&prefix=
```
List files in the S3 bucket.

**Query Parameters:**
- `limit` (optional): Maximum number of files to return (default: 100)
- `prefix` (optional): Filter files by key prefix

**Example Response:**
```json
{
  "files": [
    {
      "key": "license_20250920_173332_95234ada.jpeg",
      "size": 85267,
      "last_modified": "2025-09-20T17:33:33+00:00",
      "etag": "7fb79a548919372f51c6cb42ff24c866"
    }
  ],
  "count": 1,
  "bucket": "great-ai-hackathon-uploads-dev",
  "prefix": "",
  "is_truncated": false
}
```

**Python Example:**
```python
import requests

def list_files(limit=100, prefix=""):
    url = "https://5gkaebz86a.execute-api.us-east-1.amazonaws.com/dev/files"
    params = {}
    if limit != 100:
        params['limit'] = limit
    if prefix:
        params['prefix'] = prefix
    
    response = requests.get(url, params=params)
    return response.json()

# Usage
files = list_files()
print(f"Found {files['count']} files:")
for file in files['files']:
    print(f"- {file['key']} ({file['size']} bytes)")
```

#### 4. Generate Download URL
```
GET /download/{file_key}
```
Generate a presigned download URL for a specific file.

**Example Response:**
```json
{
  "download_url": "https://great-ai-hackathon-uploads-dev.s3.amazonaws.com/license_20250920_173332_95234ada.jpeg?AWSAccessKeyId=...",
  "file_key": "license_20250920_173332_95234ada.jpeg",
  "bucket": "great-ai-hackathon-uploads-dev",
  "expiration_seconds": 3600,
  "generated_at": "2025-09-20T17:33:39.805326"
}
```

**Python Example:**
```python
import requests

def generate_download_url(file_key):
    url = f"https://5gkaebz86a.execute-api.us-east-1.amazonaws.com/dev/download/{file_key}"
    response = requests.get(url)
    return response.json()

# Usage
file_key = "license_20250920_173332_95234ada.jpeg"
download_info = generate_download_url(file_key)
print(f"Download URL: {download_info['download_url']}")
print(f"Expires in: {download_info['expiration_seconds']} seconds")
```

### Complete Python Usage Example

```python
import requests
import base64
import time

class S3UploadAPI:
    def __init__(self):
        self.base_url = "https://5gkaebz86a.execute-api.us-east-1.amazonaws.com/dev"
    
    def health_check(self):
        """Check API health status"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def upload_file(self, file_path, content_type=None):
        """Upload a file to S3"""
        with open(file_path, 'rb') as file:
            file_content = base64.b64encode(file.read()).decode('utf-8')
        
        # Auto-detect content type
        if not content_type:
            if file_path.lower().endswith(('.jpeg', '.jpg')):
                content_type = 'image/jpeg'
            elif file_path.lower().endswith('.png'):
                content_type = 'image/png'
            elif file_path.lower().endswith('.pdf'):
                content_type = 'application/pdf'
            else:
                content_type = 'application/octet-stream'
        
        payload = {
            "filename": file_path.split('/')[-1],
            "content": file_content,
            "content_type": content_type
        }
        
        response = requests.post(f"{self.base_url}/upload", json=payload)
        return response.json()
    
    def list_files(self, limit=100, prefix=""):
        """List files in the bucket"""
        params = {}
        if limit != 100:
            params['limit'] = limit
        if prefix:
            params['prefix'] = prefix
        
        response = requests.get(f"{self.base_url}/files", params=params)
        return response.json()
    
    def get_download_url(self, file_key):
        """Generate download URL for a file"""
        response = requests.get(f"{self.base_url}/download/{file_key}")
        return response.json()

# Example usage
if __name__ == "__main__":
    api = S3UploadAPI()
    
    # Check health
    health = api.health_check()
    print(f"API Status: {health['status']}")
    
    # Upload a file
    upload_result = api.upload_file("example.jpg", "image/jpeg")
    print(f"Uploaded: {upload_result['filename']}")
    
    # List files
    files = api.list_files()
    print(f"Total files: {files['count']}")
    
    # Get download URL
    if files['files']:
        file_key = files['files'][0]['key']
        download_url = api.get_download_url(file_key)
        print(f"Download URL: {download_url['download_url']}")
```

## Deployment

### Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Node.js** (for Serverless Framework)
3. **Python 3.10+**
4. **Serverless Framework**

```bash
npm install -g serverless
```

### Environment Variables

Set these environment variables or update `serverless.yml`:

```bash
export S3_BUCKET_NAME=your-bucket-name
export PRESIGNED_URL_EXPIRATION=3600  # 1 hour in seconds
```

### Deploy using Serverless Framework

1. **Install dependencies:**
```bash
npm install
```

2. **Deploy the service:**
```bash
# Deploy to dev stage (default)
serverless deploy

# Deploy to specific stage and region
serverless deploy --stage prod --region us-west-2
```

3. **Deploy to specific AWS profile:**
```bash
serverless deploy --aws-profile your-profile
```

### Deploy using Python Script

Alternatively, use the provided deployment script:

```bash
python deploy_lambda.py --function-name s3-upload-api --region us-east-1 --bucket-name your-bucket-name
```

### Manual Deployment Steps

If you prefer manual deployment:

1. **Create S3 bucket**
2. **Create IAM role** with S3 permissions
3. **Package and deploy Lambda function**
4. **Create API Gateway** with proper routes
5. **Configure CORS** for web access

## Configuration

### S3 Bucket Permissions

The Lambda function needs these S3 permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket-name",
        "arn:aws:s3:::your-bucket-name/*"
      ]
    }
  ]
}
```

### CORS Configuration

The S3 bucket should have CORS configured to allow web uploads:
```json
{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
      "AllowedOrigins": ["*"],
      "MaxAgeSeconds": 3000
    }
  ]
}
```

## Testing

### Using Python Test Script

```bash
# Install requests library (if using HTTP tests)
pip install requests

# Generate HTML test interface (no API URL required)
python test_lambda.py --create-html

# Generate HTML test interface with pre-filled API URL
python test_lambda.py --create-html --api-url https://your-api-id.execute-api.us-east-1.amazonaws.com/dev

# Run automated tests
python test_lambda.py --api-url https://your-api-id.execute-api.us-east-1.amazonaws.com/dev

# Test with specific file
python test_lambda.py --api-url https://your-api-id.execute-api.us-east-1.amazonaws.com/dev --file document.pdf
```

#### Test Script Options:
- `--create-html`: Generate an interactive HTML test interface (API URL optional)
- `--api-url`: API Gateway URL (required for testing, optional for HTML generation)
- `--file`: Specific file to upload (optional, creates test file if not provided)

### Using HTML Test Interface

**Option 1: Generate from script**
```bash
python test_lambda.py --create-html
```
This creates `test_lambda.html` that you can open in your browser.

**Option 2: Use existing file**
Open the existing `test_lambda.html` in your browser and enter your API URL manually.

**Option 2: Use existing file**
Open the existing `test_lambda.html` in your browser and enter your API URL manually.

**Features of HTML test interface:**
- Interactive file upload with drag-and-drop support
- Real-time API health checking
- File listing and management
- Download URL generation with one-click
- Responsive design that works on mobile
- No external dependencies required
- Auto-generated file includes your API URL pre-configured

### Quick Start Testing

1. **Generate HTML test interface:**
   ```bash
   python test_lambda.py --create-html --api-url YOUR_API_URL
   ```

2. **Open the generated file:**
   ```bash
   # Windows
   start test_lambda.html
   
   # macOS
   open test_lambda.html
   
   # Linux
   xdg-open test_lambda.html
   ```

3. **Test your API:** Use the web interface to upload files and test all endpoints

### Using curl

**Health Check:**
```bash
curl https://5gkaebz86a.execute-api.us-east-1.amazonaws.com/dev/health
```

**Upload a file:**
```bash
# Encode file to base64 (Linux/Mac)
base64_content=$(base64 -i license.jpeg)

# For Windows (PowerShell)
# $base64_content = [Convert]::ToBase64String([IO.File]::ReadAllBytes("license.jpeg"))

# Upload via API
curl -X POST https://5gkaebz86a.execute-api.us-east-1.amazonaws.com/dev/upload \
  -H "Content-Type: application/json" \
  -d "{
    \"filename\": \"license.jpeg\",
    \"content\": \"$base64_content\",
    \"content_type\": \"image/jpeg\"
  }"
```

**List files:**
```bash
curl https://5gkaebz86a.execute-api.us-east-1.amazonaws.com/dev/files
```

**Get download URL:**
```bash
curl https://5gkaebz86a.execute-api.us-east-1.amazonaws.com/dev/download/license_20250920_173332_95234ada.jpeg
```

## Testing Workflow

### 1. Quick HTML Interface Setup
```bash
# Generate and open HTML test interface
python test_lambda.py --create-html --api-url YOUR_API_URL
```
Then open `test_lambda.html` in your browser for interactive testing.

### 2. Automated Python Testing
```bash
# Run comprehensive API tests
python test_lambda.py --api-url YOUR_API_URL

# Test with your own file
python test_lambda.py --api-url YOUR_API_URL --file path/to/your/file.pdf
```

### 3. Manual curl Testing
Use the curl examples above for command-line testing.

## File Upload Process

1. **Client encodes file** to base64
2. **API receives** JSON with filename, content, and content_type
3. **Lambda function** decodes base64 content
4. **File uploaded** to S3 with unique filename (timestamp + UUID)
5. **Presigned download URL** generated and returned
6. **Client receives** upload confirmation with download URL

## Security Considerations

- **Presigned URLs** expire after 1 hour by default
- **Unique filenames** prevent conflicts and unauthorized access
- **CORS** configured for web browser compatibility
- **Content type validation** based on file extension
- **Size limits** enforced by API Gateway (10MB default)

## File Naming Convention

Uploaded files are renamed to prevent conflicts:
```
original_filename_YYYYMMDD_HHMMSS_UUID.extension
```

Example: `document.pdf` becomes `document_20240921_143052_a1b2c3d4.pdf`

## Error Handling

The API returns appropriate HTTP status codes:

- **200**: Success
- **400**: Bad request (missing parameters, invalid content)
- **404**: File not found
- **500**: Internal server error

All error responses include details:
```json
{
  "error": "Error message",
  "status_code": 400,
  "timestamp": "2024-09-21T14:30:52.123456"
}
```

## Monitoring and Logs

- **CloudWatch Logs**: All Lambda function logs
- **API Gateway Logs**: Request/response logging
- **CloudWatch Metrics**: Function invocations, errors, duration
- **S3 Metrics**: Storage usage, request metrics

## Cost Optimization

- **Lambda**: Pay per request and compute time
- **S3**: Pay for storage and requests
- **API Gateway**: Pay per API call
- **Data Transfer**: Outbound data transfer charges apply

Estimated costs for 1000 file uploads per month:
- Lambda: ~$0.20
- S3 Storage (1GB): ~$0.023
- API Gateway: ~$3.50
- **Total**: ~$3.72/month

## Limitations

- **File size limit**: 6MB base64 encoded (4.5MB binary) via API Gateway
- **Timeout**: 29 seconds maximum execution time
- **Memory**: 1024MB allocated to Lambda function
- **Concurrent uploads**: Limited by Lambda concurrency limits

## Troubleshooting

### Common Issues

1. **CORS errors**: Check API Gateway CORS configuration
2. **Permission denied**: Verify IAM role has S3 permissions
3. **File too large**: Use multipart upload for large files
4. **Timeout**: Increase Lambda timeout for large files

### Debug Commands

```bash
# Check serverless logs
serverless logs -f upload --tail

# Test health endpoint
curl https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/health

# List CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/s3-upload-api
```

## Future Enhancements

- **Multipart upload** support for large files
- **File type validation** and virus scanning
- **Authentication** and authorization
- **File compression** before upload
- **Metadata** storage and search
- **CDN integration** for faster downloads
- **File versioning** and backup
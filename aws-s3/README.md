# S3 Upload API Service

A serverless file upload service built with AWS Lambda, API Gateway, and S3. This service allows you to upload files to S3 and get presigned download URLs.

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
https://{api-id}.execute-api.{region}.amazonaws.com/dev
```

### Endpoints

#### 1. Health Check
```
GET /health
```
Returns service status and configuration.

#### 2. Upload File
```
POST /upload
```
Upload a file using JSON with base64 encoded content.

**Request Body:**
```json
{
  "filename": "example.pdf",
  "content": "base64_encoded_file_content",
  "content_type": "application/pdf"
}
```

**Response:**
```json
{
  "message": "File uploaded successfully",
  "filename": "example_20240921_143052_a1b2c3d4.pdf",
  "bucket": "great-ai-hackathon-uploads-dev",
  "size": 12345,
  "content_type": "application/pdf",
  "download_url": "https://s3.amazonaws.com/...",
  "expiration_seconds": 3600,
  "upload_timestamp": "2024-09-21T14:30:52.123456"
}
```

#### 3. Get Download URL
```
GET /download/{file_key}
```
Generate a presigned download URL for a specific file.

**Response:**
```json
{
  "download_url": "https://s3.amazonaws.com/...",
  "file_key": "example_20240921_143052_a1b2c3d4.pdf",
  "bucket": "great-ai-hackathon-uploads-dev",
  "expiration_seconds": 3600,
  "generated_at": "2024-09-21T14:35:12.123456"
}
```

#### 4. List Files
```
GET /files?limit=100&prefix=
```
List files in the S3 bucket.

**Query Parameters:**
- `limit` (optional): Maximum number of files to return (default: 100)
- `prefix` (optional): Filter files by key prefix

**Response:**
```json
{
  "files": [
    {
      "key": "example_20240921_143052_a1b2c3d4.pdf",
      "size": 12345,
      "last_modified": "2024-09-21T14:30:52.123456",
      "etag": "d41d8cd98f00b204e9800998ecf8427e"
    }
  ],
  "count": 1,
  "bucket": "great-ai-hackathon-uploads-dev",
  "prefix": "",
  "is_truncated": false
}
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

**Upload a file:**
```bash
# Encode file to base64
base64_content=$(base64 -i your-file.pdf)

# Upload via API
curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/upload \
  -H "Content-Type: application/json" \
  -d "{
    \"filename\": \"your-file.pdf\",
    \"content\": \"$base64_content\",
    \"content_type\": \"application/pdf\"
  }"
```

**Get download URL:**
```bash
curl https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/download/your-file.pdf
```

**List files:**
```bash
curl https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/files
```

**Health check:**
```bash
curl https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/health
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
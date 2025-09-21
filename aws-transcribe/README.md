# AWS Transcribe API

A serverless AWS Lambda function that provides multi-language audio/video transcription services using AWS Transcribe. This service supports English, Chinese, Malay, and Indonesian languages and accepts S3 dow**Manual Testing with curl**

**1. Health Check:**
```bash
curl "https://h0lto8pesc.execute-api.us-east-1.amazonaws.com/dev/health"
```

**2. Quick Transcribe (Process URL):**
```bash
curl -X POST "https://h0lto8pesc.execute-api.us-east-1.amazonaws.com/dev/process-url" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"https://great-ai-hackathon-uploads-dev.s3.us-east-1.amazonaws.com/sample-audio.m4a\"}"
```

**3. Start Transcription Job:**
```bash
curl -X POST "https://h0lto8pesc.execute-api.us-east-1.amazonaws.com/dev/transcribe" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"https://your-bucket.s3.amazonaws.com/audio.mp3\", \"language\": \"en-us\"}"
```

**4. Check Job Status:**
```bash
curl "https://h0lto8pesc.execute-api.us-east-1.amazonaws.com/dev/status?job_name=transcribe_job_20231201_123456_abc123"
```s input.

## 🎤 Features

- **Multi-language Support**: English (en-us), Chinese (zh-cn), Malay (ms-my), Indonesian (id-id)
- **S3 Integration**: Accept S3 downloadable URLs for audio/video files
- **RESTful API**: Simple HTTP endpoints for transcription operations
- **Real-time Status**: Check transcription job status and retrieve results
- **Standardized Response**: Consistent JSON response format
- **CORS Enabled**: Frontend-friendly with CORS support

## � Deployed Service

**Live API Base URL:** `https://h0lto8pesc.execute-api.us-east-1.amazonaws.com/dev`

### Quick Test Commands

```bash
# Health check
curl "https://h0lto8pesc.execute-api.us-east-1.amazonaws.com/dev/health"

# Start transcription (replace with your S3 URL)
curl -X POST "https://h0lto8pesc.execute-api.us-east-1.amazonaws.com/dev/transcribe" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"https://your-s3-bucket.amazonaws.com/audio-file.mp3\", \"language\": \"en-us\"}"

# Process URL (transcribe immediately and get transcript)
curl -X POST "https://h0lto8pesc.execute-api.us-east-1.amazonaws.com/dev/process-url" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"https://your-s3-bucket.amazonaws.com/audio-file.mp3\"}"

# Check status (replace JOB_NAME with actual job name from transcribe response)
curl "https://h0lto8pesc.execute-api.us-east-1.amazonaws.com/dev/status?job_name=JOB_NAME"
```

## �📋 API Endpoints

### 1. Start Transcription
**POST** `/transcribe`

Start a new transcription job for an audio/video file.

**Request Body:**
```json
{
  "url": "https://your-bucket.s3.amazonaws.com/audio-file.mp3",
  "language": "en-us"
}
```

**Response Format:**
```json
{
  "status": {
    "statusCode": 200,
    "message": "Transcription job started successfully"
  },
  "data": {
    "job_name": "transcribe_job_20231201_123456_abc123",
    "job_status": "IN_PROGRESS",
    "language_code": "en-us",
    "media_url": "https://your-bucket.s3.amazonaws.com/audio-file.mp3",
    "creation_time": "2023-12-01T12:34:56.789Z",
    "estimated_completion_time": "Processing time varies based on audio length"
  }
}
```

### 2. Check Status
**GET** `/status?job_name=<job_name>`

Check the status of a transcription job and retrieve results if completed.

**Response Format:**
```json
{
  "status": {
    "statusCode": 200,
    "message": "Job status retrieved successfully"
  },
  "data": {
    "job_name": "transcribe_job_20231201_123456_abc123",
    "status": "COMPLETED",
    "language_code": "en-US",
    "creation_time": "2023-12-01T12:34:56.789Z",
    "completion_time": "2023-12-01T12:36:45.123Z",
    "transcript": "Hello, this is the transcribed text from your audio file.",
    "transcript_uri": "https://s3.amazonaws.com/bucket/transcript.json"
  }
}
```

### 3. Health Check
**GET** `/health`

Check if the service is running and get supported languages.

**Response Format:**
```json
{
  "status": {
    "statusCode": 200,
    "message": "Service is healthy"
  },
  "data": {
    "service": "aws-transcribe-api",
    "supported_languages": ["en-us", "zh-cn", "ms-my", "id-id"],
    "timestamp": "2023-12-01T12:34:56.789Z",
    "request_id": "test-request-id-123"
  }
}
```

### 4. Process URL (Quick Transcribe)
**POST** `/process-url`

Process an S3 URL and return the completed transcript immediately. This endpoint starts a transcription job and waits for completion before returning the result.

**Request Body:**
```json
{
  "url": "https://your-bucket.s3.amazonaws.com/audio-file.mp3"
}
```

**Response Format:**
```json
{
  "status": {
    "statusCode": 200,
    "message": "Transcription completed successfully"
  },
  "data": {
    "message": "Well, mu xiang Xinjiang one or jia hay to the chat like update or the license or for the TMB the viewliha Maiajingua some baobaya."
  }
}
```

**Usage Examples:**
```bash
# Using the sample audio file
curl -X POST "https://h0lto8pesc.execute-api.us-east-1.amazonaws.com/dev/process-url" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"https://great-ai-hackathon-uploads-dev.s3.us-east-1.amazonaws.com/sample-audio.m4a\"}"

# Using your own S3 URL
curl -X POST "https://h0lto8pesc.execute-api.us-east-1.amazonaws.com/dev/process-url" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"https://your-bucket.s3.amazonaws.com/audio-file.mp3\"}"
```

**Features:**
- ✅ **Synchronous**: Returns completed transcript immediately
- ✅ **Default Language**: Uses English (en-us) automatically  
- ✅ **No Job Tracking**: No need to check status separately
- ✅ **Quick Response**: Best for shorter audio files
- ⚠️ **Timeout**: May timeout for very long audio files (use `/transcribe` endpoint instead)

## 🚀 Supported Languages

| Language | Code | AWS Transcribe Code |
|----------|------|-------------------|
| English (US) | `en-us` | `en-US` |
| Chinese (Simplified) | `zh-cn` | `zh-CN` |
| Malay (Malaysia) | `ms-my` | `ms-MY` |
| Indonesian | `id-id` | `id-ID` |

## 🛠️ Setup and Deployment

### Prerequisites

- Node.js 18+ 
- Python 3.10+
- AWS CLI configured
- Serverless Framework

### Quick Setup

1. **Install dependencies:**
   ```bash
   python deploy_lambda.py install
   ```

2. **Run local tests:**
   ```bash
   python deploy_lambda.py test
   ```

3. **Deploy to AWS:**
   ```bash
   python deploy_lambda.py deploy
   ```

### Manual Setup

1. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Deploy using Serverless:**
   ```bash
   npx serverless deploy --stage dev
   ```

### Environment Variables

The following environment variables are automatically configured:

- `OUTPUT_S3_BUCKET_NAME`: S3 bucket for transcription outputs
- `AWS_REGION1`: AWS region for services
- `LAMBDA_RUNTIME`: Runtime flag

## 🧪 Testing

### Local Testing

Run the test suite:
```bash
python test_lambda.py
```

### Web Interface Testing

Open `test_lambda.html` in your browser for an interactive testing interface.

### Manual Testing with curl

**Start transcription:**
```bash
curl -X POST https://your-api-url/dev/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-bucket.s3.amazonaws.com/audio.mp3",
    "language": "en-us"
  }'
```

**Check status:**
```bash
curl "https://your-api-url/dev/status?job_name=transcribe_job_20231201_123456_abc123"
```

## 📁 File Structure

```
aws-transcribe/
├── lambda_handler.py      # Main Lambda function
├── serverless.yml         # Serverless Framework configuration
├── requirements.txt       # Python dependencies
├── package.json          # Node.js dependencies
├── deploy_lambda.py      # Deployment script
├── test_lambda.py        # Local testing script
├── test_lambda.html      # Web testing interface
└── README.md            # This file
```

## 🔧 Configuration

### Serverless Configuration

The `serverless.yml` file includes:

- **IAM Roles**: Permissions for Transcribe and S3 access
- **API Gateway**: RESTful endpoints with CORS
- **S3 Bucket**: Automatic creation of output bucket
- **Environment Variables**: Runtime configuration

### Lambda Function Features

- **Error Handling**: Comprehensive error responses
- **Input Validation**: URL and language validation
- **CORS Support**: Cross-origin resource sharing
- **Logging**: CloudWatch integration

## 📊 Response Format

All API responses follow this standardized format:

```json
{
  "status": {
    "statusCode": <HTTP_STATUS_CODE>,
    "message": "<DESCRIPTIVE_MESSAGE>"
  },
  "data": {
    "message": "<RESPONSE_DATA_OR_MESSAGE>"
  }
}
```

## 🚫 Error Handling

Common error scenarios:

- **400 Bad Request**: Missing URL, invalid language, malformed JSON
- **404 Not Found**: Transcription job not found
- **500 Internal Server Error**: AWS service errors, unexpected exceptions

## 🔒 Security

- **IAM Roles**: Least privilege access
- **CORS**: Configured for web access
- **Input Validation**: URL and parameter validation
- **No Sensitive Data**: No hardcoded credentials

## 📈 Monitoring

- **CloudWatch Logs**: Automatic logging
- **Health Endpoint**: Service status monitoring
- **Error Tracking**: Detailed error responses

## 🗑️ Cleanup

To remove the deployment:
```bash
python deploy_lambda.py remove
```

Or manually:
```bash
npx serverless remove --stage dev
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test your changes locally
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:

1. Check the test endpoints using `test_lambda.html`
2. Review CloudWatch logs for errors
3. Validate S3 URL accessibility
4. Ensure supported audio/video formats

## 📚 References

- [AWS Transcribe Documentation](https://docs.aws.amazon.com/transcribe/)
- [Serverless Framework Documentation](https://www.serverless.com/framework/docs/)
- [AWS Lambda Python Documentation](https://docs.aws.amazon.com/lambda/latest/dg/python-programming-model.html)
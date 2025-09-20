# AWS Brain Intent Classification Service

This service handles intent classification for the Great AI Hackathon project.

## Structure

- `lambda_handler.py` - AWS Lambda handler for the API
- `main.py` - Main intent classification logic
- `serverless.yml` - Serverless configuration for deployment
- `requirements.txt` - Python dependencies
- `package.json` - Node.js dependencies for serverless

## API Endpoints

### POST /brain/classify
Classifies user intent from text input

**Request Body:**
```json
{
  "user_input": "I want to apply for a driving license"
}
```

**Response:**
```json
{
  "user_input": "I want to apply for a driving license",
  "classification_result": {
    "intent": "license_application",
    "confidence": 0.95,
    "service": "licensing"
  },
  "status": "success"
}
```

### GET /health
Health check endpoint

## Deployment

```bash
npm install
serverless deploy
```

## Testing

```bash
python local_test.py
```
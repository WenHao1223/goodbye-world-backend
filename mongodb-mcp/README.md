# MongoDB MCP Server with AWS Integration

MongoDB Model Context Protocol (MCP) server integrated with AWS SageMaker and Bedrock for AI-powered database operations.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
```
ATLAS_URI=your_mongodb_connection_string
AWS_REGION=us-east-1
AWS_PROFILE=your_aws_profile
SAGEMAKER_ENDPOINT=your_sagemaker_endpoint
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

## Usage

### Start MCP Server
```bash
python mongodb_mcp_server.py
```

### Send Instructions via Main Client
```bash
python main.py "Create a new collection to store movie purchases data that includes geospatial and timeseries fields"
```

### Example Instructions
- "Create a new collection to store movie purchases data that includes geospatial and timeseries fields"
- "Insert a document with user purchase data including location and timestamp"
- "Find all documents where location is near coordinates [40.7128, -74.0060]"
- "Update all documents to add a processed flag"

## Features

- **AI-Powered Instructions**: Uses AWS Bedrock to parse natural language instructions
- **MongoDB Operations**: Create collections, insert/update documents, queries
- **Geospatial Support**: Automatic 2dsphere index creation
- **Timeseries Support**: Timeseries collection creation
- **AWS Integration**: SageMaker and Bedrock for AI processing

## Architecture

```
main.py → AWS Bedrock → MongoDB MCP Server → MongoDB Atlas
```

The system processes natural language instructions through AWS AI services and executes corresponding MongoDB operations.
# Textract Full - Document Analysis Suite

A comprehensive document analysis tool that combines AWS Textract, Bedrock, and intelligent blur detection. Available as both CLI and serverless Lambda API.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- AWS CLI configured with appropriate permissions

### Installation
```bash
# Clone and setup
cd textract-full
uv sync
```

### Basic Usage
```bash
# Analyze a document locally
uv run python cli.py --file media/receipt.pdf --mode tfbq --category receipt

# Test Lambda function locally
uv run python local_test.py

# Test deployed Lambda API
uv run python test_lambda.py --api-url YOUR_API_URL --file media/receipt.pdf --mode tfbq --category receipt
```

## 📋 Table of Contents

- [Local CLI Usage](#-local-cli-usage)
- [Lambda API](#-lambda-api)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Common Commands](#-common-commands)
- [API Reference](#-api-reference)
- [Troubleshooting](#-troubleshooting)

## 📚 Documentation

- **[Quick Reference](docs/QUICK_REFERENCE.md)** - Essential commands and parameters
- **[Examples](docs/EXAMPLES.md)** - Detailed usage examples and use cases
- **[Development Guide](docs/DEVELOPMENT.md)** - Setup, testing, and contribution guidelines

## 💻 Local CLI Usage

### Command Line Interface

```bash
# Basic syntax
uv run python cli.py --file <path> --mode <mode> [options]
```

### Arguments

| Argument | Description | Default | Required |
|----------|-------------|---------|----------|
| `--file` | Path to input file (JPEG/PNG/PDF) | - | ✅ |
| `--mode` | Analysis mode: t(ext), f(orms), b(tables), q(uery) | `tfbq` | ❌ |
| `--category` | Document type: `licence`, `receipt`, `idcard`, `passport` | - | ❌ |
| `--region` | AWS region | `us-east-1` | ❌ |
| `--profile` | AWS profile name | `default` | ❌ |

### Common Local Commands

```bash
# Full analysis of a receipt
uv run python cli.py --file media/receipt.pdf --mode tfbq --category receipt --region us-east-1

# Text extraction only with blur detection
uv run python cli.py --file media/licence.jpeg --mode t --region us-east-1

# Forms and tables analysis
uv run python cli.py --file media/receipt.pdf --mode fb --region us-east-1

# License analysis with specific profile
uv run python cli.py --file media/licence.jpeg --mode tfbq --category licence --profile your-profile
```

## ☁️ Lambda API

### Deployment

#### Option 1: Serverless Framework (Recommended)
```bash
# Install dependencies
npm install -g serverless serverless-python-requirements

# Deploy to AWS
serverless deploy --region us-east-1
```

#### Option 2: Manual Deployment
```bash
# Create deployment package
python deploy_lambda.py --function-name textract-full-api --region us-east-1
```

### Testing Lambda

#### Local Testing
```bash
# Test Lambda function locally (simulates Lambda environment)
uv run python local_test.py

# Test health endpoint
uv run python local_test.py --health
```

#### Remote Testing
```bash
# Test deployed API
uv run python test_lambda.py --api-url https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/analyze --file media/receipt.pdf --mode tfbq --category receipt

# Create web test interface
uv run python test_lambda.py --create-html
# Then open test_lambda.html in browser
```

### Lambda API Usage

#### JSON Request Format
```bash
curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "file_content": "base64-encoded-file-content",
    "filename": "document.pdf",
    "mode": "tfbq",
    "category": "receipt",
    "region": "us-east-1"
  }'
```

#### Health Check
```bash
curl https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/health
```

## 🎯 Features

### 1. **AWS Textract Integration**
- **Text Detection**: Extract text with confidence scores
- **Form Analysis**: Key-value pair extraction
- **Table Analysis**: Structured table data extraction
- **Query Analysis**: Answer specific questions about documents

### 2. **Intelligent Blur Detection**
- **Local**: OpenCV Laplacian variance + Textract confidence analysis
- **Lambda**: Enhanced Textract confidence analysis with statistical metrics
- **Metrics**: Average, median, and standard deviation of OCR confidence
- **Quality Assessment**: Excellent, good, fair, or poor ratings
- **API Integration**: Structured `blur_analysis` field in Lambda responses

### 3. **AWS Bedrock Integration**
- **Structured Extraction**: Convert documents to structured JSON
- **Document Categories**: Specialized prompts for different document types
- **AI-Powered**: Uses Claude AI for intelligent data extraction

### 4. **Dual Deployment Options**
- **Local CLI**: Full-featured command-line interface
- **Lambda API**: Serverless REST API with automatic scaling
- **Consistent Results**: Same analysis quality in both environments

## 📁 Project Structure

```
textract-full/
├── src/                          # Core source code
│   ├── main.py                   # Main CLI logic
│   ├── textract_enhanced.py      # Textract integration
│   ├── bedrock_mapper.py         # Bedrock integration
│   ├── blur_detection.py         # Blur detection logic
│   ├── logger.py                 # Logging utilities
│   ├── prompts/                  # Bedrock prompts
│   │   ├── licence.txt
│   │   ├── receipt.txt
│   │   ├── idcard.txt
│   │   └── passport.txt
│   └── queries/                  # Textract queries
│       ├── licence.json
│       ├── receipt.json
│       ├── idcard.json
│       └── passport.json
├── docs/                         # Documentation
│   ├── QUICK_REFERENCE.md        # Essential commands
│   ├── EXAMPLES.md               # Usage examples
│   └── DEVELOPMENT.md            # Development guide
├── media/                        # Sample test files
├── log/                          # Local analysis results
├── output/                       # Extracted structured data
├── cli.py                        # CLI entry point
├── lambda_handler.py             # Lambda function handler
├── local_test.py                 # Local Lambda testing
├── test_lambda.py                # Lambda API testing
├── deploy_lambda.py              # Deployment script
├── serverless.yml                # Serverless Framework config
├── pyproject.toml                # Project dependencies
├── requirements.txt       # Lambda-specific dependencies
└── README.md                     # This file
```

## ⚡ Common Commands

### Development & Testing
```bash
# Install/update dependencies
uv sync

# Run local analysis
uv run python cli.py --file media/receipt.pdf --mode tfbq --category receipt

# Test Lambda locally
uv run python local_test.py

# Deploy to AWS
serverless deploy --region us-east-1

# Test deployed API
uv run python test_lambda.py --api-url YOUR_API_URL --file media/receipt.pdf --mode tfbq --category receipt

# Create web test interface
uv run python test_lambda.py --create-html
```

### Analysis Modes
```bash
# Text only (with blur detection)
uv run python cli.py --file media/document.pdf --mode t

# Forms only
uv run python cli.py --file media/document.pdf --mode f

# Tables only
uv run python cli.py --file media/document.pdf --mode b

# Queries only (requires category)
uv run python cli.py --file media/receipt.pdf --mode q --category receipt

# All analysis types
uv run python cli.py --file media/receipt.pdf --mode tfbq --category receipt
```

### Document Categories
```bash
# Receipt analysis
uv run python cli.py --file media/receipt.pdf --mode tfbq --category receipt

# License analysis
uv run python cli.py --file media/licence.jpeg --mode tfbq --category licence

# ID card analysis
uv run python cli.py --file media/idcard.jpg --mode tfbq --category idcard

# Passport analysis
uv run python cli.py --file media/passport.jpg --mode tfbq --category passport
```

## 📊 Blur Analysis API Field

The Lambda API now includes a dedicated `blur_analysis` field that provides comprehensive image quality assessment:

```json
{
  "blur_analysis": {
    "textract_analysis": {
      "median_confidence": 99.89,
      "average_confidence": 99.62,
      "std_confidence": 0.51,
      "quality_assessment": "excellent"
    },
    "overall_assessment": {
      "is_blurry": false,
      "confidence_level": "high"
    }
  }
}
```

### Blur Analysis Metrics

| Field | Description | Values |
|-------|-------------|---------|
| `median_confidence` | Median OCR confidence score | 0-100 |
| `average_confidence` | Average OCR confidence score | 0-100 |
| `std_confidence` | Standard deviation of confidence scores | 0+ |
| `quality_assessment` | Overall image quality rating | excellent, good, fair, poor |
| `is_blurry` | Boolean blur detection result | true, false |
| `confidence_level` | Assessment confidence level | high, medium, low |

### Quality Assessment Criteria

- **Excellent**: Avg > 98%, Median > 95%, Std < 2.0
- **Good**: Avg > 95%, Median > 90%, Std < 5.0
- **Fair**: Avg > 90%, Median > 85%
- **Poor**: Below fair thresholds

## 📚 API Reference

### Local CLI Response
```
=== TEXT DETECTION ===
text = "Sample Text" | confidence = 99.89

=== FORM ANALYSIS ===
Key: Value pairs extracted from forms

=== TABLE ANALYSIS ===
Structured table data with rows and columns

=== QUERY ANALYSIS ===
Q: What is the transaction amount?
A: $100.00

=== BLUR DETECTION ===
Textract confidence - Median: 99.89, Avg: 99.75, Std: 0.51
Quality assessment: excellent
Overall: CLEAR (confidence: high)

=== BEDROCK EXTRACTION ===
{
  "transaction_date": "2025-09-15",
  "transaction_amount": "$100.00",
  "beneficiary_name": "John Doe"
}
```

### Lambda API Response
```json
{
  "status": "success",
  "console_output": "Processing log...",
  "text": [
    {"text": "Sample Text", "confidence": 99.89}
  ],
  "forms": {
    "Key": ["Value"]
  },
  "tables": {
    "tables": [
      {"table_id": 1, "rows": [["Cell1", "Cell2"]]}
    ]
  },
  "queries": {
    "What is the amount?": "$100.00"
  },
  "blur_analysis": {
    "textract_analysis": {
      "median_confidence": 99.89,
      "average_confidence": 99.62,
      "std_confidence": 0.51,
      "quality_assessment": "excellent"
    },
    "overall_assessment": {
      "is_blurry": false,
      "confidence_level": "high"
    }
  },
  "extracted_data": {
    "transaction_date": "2025-09-15",
    "transaction_amount": "$100.00"
  }
}
```

### Error Response
```json
{
  "error": "Error description",
  "returncode": 1,
  "stdout": "...",
  "stderr": "..."
}
```

## 🔧 Configuration

### AWS Permissions Required
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "textract:DetectDocumentText",
        "textract:AnalyzeDocument",
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    }
  ]
}
```

### Supported File Types
- **PDF**: Up to 11 pages, max 5 MB
- **JPEG/JPG**: Max 5 MB
- **PNG**: Max 5 MB

### Lambda Limitations
- **Request Size**: 6 MB (affects base64 file uploads)
- **Timeout**: 5 minutes maximum
- **Memory**: Configurable up to 10 GB
- **Blur Detection**: Uses Textract confidence analysis (no OpenCV)

## 🐛 Troubleshooting

### Common Issues

#### Local Development
```bash
# Module not found errors
uv sync

# AWS credentials not configured
aws configure

# Permission denied errors
aws sts get-caller-identity
```

#### Lambda Deployment
```bash
# Serverless deployment fails
npm install -g serverless serverless-python-requirements

# Function timeout
# Increase timeout in serverless.yml or use smaller files

# Memory errors
# Increase memory allocation in serverless.yml
```

#### API Testing
```bash
# Test local Lambda function
uv run python local_test.py

# Test deployed API
uv run python test_lambda.py --api-url YOUR_URL --file media/receipt.pdf --mode t

# Check API Gateway logs
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/textract-full-api
```

### File Size Issues
- **Local**: No size limit (within AWS service limits)
- **Lambda**: 6 MB request limit for base64 encoded files (~4.5 MB original file)

### Performance Tips
- Use `--mode t` for fastest processing (text only)
- Smaller files process faster
- Lambda has cold start delay (~1-3 seconds)

## 📊 Comparison: Local vs Lambda

| Feature | Local CLI | Lambda API |
|---------|-----------|------------|
| **Deployment** | No deployment needed | Serverless deployment |
| **Scaling** | Single instance | Auto-scaling |
| **File Upload** | Direct file path | Base64 in JSON |
| **AWS Credentials** | Local AWS config | IAM role |
| **Blur Detection** | Full OpenCV analysis | Textract confidence analysis + API field |
| **Timeout** | No limit | 5 minutes |
| **File Size** | AWS service limits | 6 MB request limit |
| **Cost** | Compute + AWS services | Lambda + AWS services |
| **Cold Start** | None | 1-3 seconds |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test both local and Lambda versions
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

---

**Happy Document Analysis! 🎉**
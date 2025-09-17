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
# Analyze a driver's license locally
uv run python cli.py --file media/licence.jpeg --mode tfbq --category licence

# Test Lambda function locally
uv run python local_test.py

# Test deployed Lambda API
uv run python test_lambda.py --api-url YOUR_API_URL --file media/licence.jpeg --mode tfbq --category licence
```

## 📋 Table of Contents

- [Local CLI Usage](#-local-cli-usage)
- [Lambda API](#-lambda-api)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Common Commands](#-common-commands)
- [API Usage Examples](#-api-usage-examples)
- [Blur Analysis API Field](#-blur-analysis-api-field)
- [Quick Reference](#-quick-reference)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)



## 💻 Local CLI Usage

### Command Line Interface

```bash
# Basic syntax
uv run python cli.py --file <path> --mode <mode> [options]
```

### Arguments

| Argument     | Description                                               | Default     | Required |
| ------------ | --------------------------------------------------------- | ----------- | -------- |
| `--file`     | Path to input file (JPEG/PNG/PDF)                         | -           | ✅       |
| `--mode`     | Analysis mode: t(ext), f(orms), b(tables), q(uery)        | `tfbq`      | ❌       |
| `--category` | Document type: `licence`, `receipt`, `idcard`, `passport` | -           | ❌       |
| `--region`   | AWS region                                                | `us-east-1` | ❌       |
| `--profile`  | AWS profile name                                          | `default`   | ❌       |

### Common Local Commands

```bash
# Full analysis of a driver's license
uv run python cli.py --file media/licence.jpeg --mode tfbq --category licence --region us-east-1

# Text extraction only with blur detection
uv run python cli.py --file media/licence.jpeg --mode t --region us-east-1

# Forms and tables analysis
uv run python cli.py --file media/licence.jpeg --mode fb --region us-east-1

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
uv run python cli.py --file media/licence.jpeg --mode tfbq --category licence

# Test Lambda locally
uv run python local_test.py

# Deploy to AWS
serverless deploy --region us-east-1

# Test deployed API
uv run python test_lambda.py --api-url YOUR_API_URL --file media/licence.jpeg --mode tfbq --category licence

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
uv run python cli.py --file media/licence.jpeg --mode q --category licence

# All analysis types
uv run python cli.py --file media/licence.jpeg --mode tfbq --category licence
```

### Document Categories

```bash
# License analysis (primary example)
uv run python cli.py --file media/licence.jpeg --mode tfbq --category licence

# Receipt analysis
uv run python cli.py --file media/receipt.pdf --mode tfbq --category receipt

# ID card analysis
uv run python cli.py --file media/idcard.jpg --mode tfbq --category idcard

# Passport analysis
uv run python cli.py --file media/passport.jpg --mode tfbq --category passport
```

## 🌐 API Usage Examples

### JavaScript (Browser)
```javascript
// File upload and analysis
const fileInput = document.getElementById('file');
const file = fileInput.files[0];
const reader = new FileReader();

reader.onload = async function(e) {
  const fileContent = e.target.result.split(',')[1];

  const response = await fetch('https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      file_content: fileContent,
      filename: file.name,
      mode: 'tfbq',
      category: 'licence',
      region: 'us-east-1'
    })
  });

  const result = await response.json();

  // Access blur analysis
  if (result.blur_analysis) {
    const blur = result.blur_analysis;
    const textract = blur.textract_analysis;
    const overall = blur.overall_assessment;

    console.log(`Quality: ${textract.quality_assessment}`);
    console.log(`Is Blurry: ${overall.is_blurry}`);
    console.log(`Confidence: ${overall.confidence_level}`);
    console.log(`Median Confidence: ${textract.median_confidence.toFixed(2)}%`);

    // Quality-based processing
    if (textract.quality_assessment === 'excellent') {
      console.log('High quality image - proceed with confidence');
    } else if (overall.is_blurry) {
      console.log('Blurry image detected - results may be less accurate');
    }
  }
};

reader.readAsDataURL(file);
```

### Python (Requests)
```python
import requests
import base64

# Read and encode file
with open('media/licence.jpeg', 'rb') as f:
    file_content = base64.b64encode(f.read()).decode('utf-8')

# Make API call
response = requests.post(
    'https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/analyze',
    json={
        'file_content': file_content,
        'filename': 'licence.jpeg',
        'mode': 'tfbq',
        'category': 'licence',
        'region': 'us-east-1'
    }
)

result = response.json()

# Access blur analysis
if 'blur_analysis' in result:
    blur_info = result['blur_analysis']
    print(f"Quality: {blur_info['textract_analysis']['quality_assessment']}")
    print(f"Is Blurry: {blur_info['overall_assessment']['is_blurry']}")
    print(f"Confidence: {blur_info['overall_assessment']['confidence_level']}")
```

### cURL
```bash
# Encode file to base64
FILE_CONTENT=$(base64 -w 0 media/licence.jpeg)

# Make API call
curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/analyze \
  -H "Content-Type: application/json" \
  -d "{
    \"file_content\": \"$FILE_CONTENT\",
    \"filename\": \"licence.jpeg\",
    \"mode\": \"tfbq\",
    \"category\": \"licence\",
    \"region\": \"us-east-1\"
  }"
```

## 📊 Blur Analysis API Field

The Lambda API now includes a dedicated `blur_analysis` field that provides comprehensive image quality assessment:

```json
{
  "blur_analysis": {
    "laplacian": {
      "method": "laplacian",
      "score": 4743.317898724083,
      "is_blurry": false,
      "quality": "sharp"
    },
    "textract_analysis": {
      "total_items": 53,
      "min_confidence": 34.21656036376953,
      "max_confidence": 99.990234375,
      "median_confidence": 96.84188079833984,
      "average_confidence": 95.69545777638753,
      "std_confidence": 11.519045489650455,
      "low_confidence_count": 22,
      "low_confidence_percentage": 41.509433962264154,
      "likely_blurry": false,
      "quality_assessment": "excellent"
    },
    "overall_assessment": {
      "is_blurry": false,
      "blur_indicators": [],
      "confidence_level": "high"
    }
  }
}
```

### Blur Analysis Complete Structure

#### **Laplacian Analysis** (Local only, defaults in Lambda)

| Field       | Type    | Description                        | Values                              |
| ----------- | ------- | ---------------------------------- | ----------------------------------- |
| `method`    | string  | Analysis method used               | `"laplacian"`                       |
| `score`     | float   | Laplacian variance score           | `0.0+` (higher = sharper)           |
| `is_blurry` | boolean | Laplacian-based blur detection     | `true`, `false`                     |
| `quality`   | string  | Laplacian-based quality assessment | `"sharp"`, `"moderate"`, `"blurry"` |

#### **Textract Analysis**

| Field                       | Type    | Description                             | Values                                      |
| --------------------------- | ------- | --------------------------------------- | ------------------------------------------- |
| `total_items`               | integer | Number of text items detected           | `0+`                                        |
| `min_confidence`            | float   | Lowest confidence score                 | `0.0 - 100.0`                               |
| `max_confidence`            | float   | Highest confidence score                | `0.0 - 100.0`                               |
| `median_confidence`         | float   | Median confidence score                 | `0.0 - 100.0`                               |
| `average_confidence`        | float   | Average confidence score                | `0.0 - 100.0`                               |
| `std_confidence`            | float   | Standard deviation of confidence scores | `0.0+`                                      |
| `low_confidence_count`      | integer | Number of items below 85% confidence    | `0+`                                        |
| `low_confidence_percentage` | float   | Percentage of low-confidence items      | `0.0 - 100.0`                               |
| `likely_blurry`             | boolean | Textract-based blur assessment          | `true`, `false`                             |
| `quality_assessment`        | string  | Overall quality rating                  | `"excellent"`, `"good"`, `"fair"`, `"poor"` |

#### **Overall Assessment**

| Field              | Type    | Description                  | Values                                                             |
| ------------------ | ------- | ---------------------------- | ------------------------------------------------------------------ |
| `is_blurry`        | boolean | Final blur detection result  | `true`, `false`                                                    |
| `blur_indicators`  | array   | Methods that detected blur   | `[]`, `["textract"]`, `["laplacian"]`, `["laplacian", "textract"]` |
| `confidence_level` | string  | Confidence in the assessment | `"high"`, `"medium"`, `"low"`                                      |

### Blur Detection Algorithm

#### **Quality Assessment Criteria**

| Quality       | Median Confidence | Average Confidence | Description                         |
| ------------- | ----------------- | ------------------ | ----------------------------------- |
| **Excellent** | > 95%             | > 90%              | Very high quality, clear text       |
| **Good**      | > 90%             | > 85%              | Good quality, readable text         |
| **Fair**      | > 85%             | > 80%              | Acceptable quality, mostly readable |
| **Poor**      | ≤ 85%             | ≤ 80%              | Poor quality, difficult to read     |

#### **Blur Detection Logic**

An image is considered **blurry** if ANY of these conditions are met:

1. **Very low median confidence**: `median_confidence < 80.0`
2. **Very low average confidence**: `average_confidence < 75.0`
3. **High percentage of poor items**: `low_confidence_percentage > 50.0` (>50% below 85%)
4. **Extreme inconsistency with poor quality**: `std_confidence > 20.0 AND median_confidence < 85.0`

#### **Confidence Level Determination**

| Level      | Median | Average | Low Conf % | Description               |
| ---------- | ------ | ------- | ---------- | ------------------------- |
| **High**   | > 95%  | > 90%   | < 20%      | Very confident assessment |
| **High**   | > 90%  | > 85%   | < 35%      | Confident assessment      |
| **Medium** | > 85%  | > 80%   | < 50%      | Moderately confident      |
| **Low**    | ≤ 85%  | ≤ 80%   | ≥ 50%      | Low confidence assessment |

#### **Blur Indicators Interpretation**

| Indicators                  | Meaning                                        | Confidence |
| --------------------------- | ---------------------------------------------- | ---------- |
| `[]`                        | No blur detected by any method                 | High       |
| `["textract"]`              | Only confidence analysis detected blur         | Medium     |
| `["laplacian"]`             | Only image analysis detected blur (local only) | Medium     |
| `["laplacian", "textract"]` | Both methods detected blur (local only)        | Very High  |

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
  "text": [{ "text": "Sample Text", "confidence": 99.89 }],
  "forms": {
    "Key": ["Value"]
  },
  "tables": {
    "tables": [{ "table_id": 1, "rows": [["Cell1", "Cell2"]] }]
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

## � Quick Reference

### CLI Commands
```bash
# Basic text extraction
uv run python cli.py --file media/licence.jpeg --mode t

# Full analysis with AI extraction
uv run python cli.py --file media/licence.jpeg --mode tfbq --category licence

# Forms and tables only
uv run python cli.py --file media/licence.jpeg --mode fb

# Custom queries
uv run python cli.py --file media/licence.jpeg --mode q --category licence
```

### Mode Parameters
- `t` - Text detection only
- `f` - Forms analysis (key-value pairs)
- `b` - Tables analysis (structured data)
- `q` - Queries analysis (requires category)
- `tfbq` - All analysis types

### Categories (for queries and AI extraction)
- `receipt` - Receipt/invoice analysis
- `licence` - Driver's license analysis
- `idcard` - ID card analysis
- `passport` - Passport analysis

### API Response Structure
```json
{
  "status": "success",
  "console_output": "Processing log...",
  "text": [{"text": "...", "confidence": 99.5}],
  "forms": {"key": "value"},
  "tables": [{"headers": [], "rows": []}],
  "queries": {"question": "answer"},
  "blur_analysis": {
    "laplacian": {"score": 4743.32, "is_blurry": false, "quality": "sharp"},
    "textract_analysis": {"median_confidence": 96.84, "quality_assessment": "excellent"},
    "overall_assessment": {"is_blurry": false, "confidence_level": "high"}
  },
  "extracted_data": {"field": "value"}
}
```

### Environment Variables
```bash
export AWS_REGION=us-east-1
export AWS_PROFILE=default
```

## �🐛 Troubleshooting

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
uv run python test_lambda.py --api-url YOUR_URL --file media/licence.jpeg --mode t

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

| Feature             | Local CLI              | Lambda API                               |
| ------------------- | ---------------------- | ---------------------------------------- |
| **Deployment**      | No deployment needed   | Serverless deployment                    |
| **Scaling**         | Single instance        | Auto-scaling                             |
| **File Upload**     | Direct file path       | Base64 in JSON                           |
| **AWS Credentials** | Local AWS config       | IAM role                                 |
| **Blur Detection**  | Full OpenCV analysis   | Textract confidence analysis + API field |
| **Timeout**         | No limit               | 5 minutes                                |
| **File Size**       | AWS service limits     | 6 MB request limit                       |
| **Cost**            | Compute + AWS services | Lambda + AWS services                    |
| **Cold Start**      | None                   | 1-3 seconds                              |

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

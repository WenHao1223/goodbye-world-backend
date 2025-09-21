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
uv run python cli.py --file media/license.jpeg --mode tfbq --category license

# Test Lambda function locally
uv run python local_test.py

# Test deployed Lambda API
uv run python test_lambda.py --api-url YOUR_API_URL --file media/license.jpeg --mode tfbq --category license
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
| `--category` | Document type: `idcard`, `license`, `license-front`, `license-back`, `tnb`, `receipt` (auto-detected if not provided) | -           | ❌       |
| `--queries`  | Custom queries separated by semicolons or newlines        | -           | ❌       |
| `--prompt`   | Custom prompt for Bedrock AI extraction                   | -           | ❌       |
| `--custom`   | Use custom queries/prompts even if category files exist   | `False`     | ❌       |
| `--region`   | AWS region                                                | `us-east-1` | ❌       |
| `--profile`  | AWS profile name                                          | `default`   | ❌       |

### Common Local Commands

```bash
# Full analysis with auto-detection (no category needed)
uv run python cli.py --file media/license.jpeg --mode tfbq --region us-east-1

# Full analysis of a driver's license (explicit category)
uv run python cli.py --file media/license.jpeg --mode tfbq --category license --region us-east-1

# TNB utility bill analysis
uv run python cli.py --file media/tnb-bill.pdf --mode tfbq --category tnb --region us-east-1

# License front side analysis
uv run python cli.py --file media/license-front.jpeg --mode tfbq --category license-front --region us-east-1

# Text extraction only with blur detection
uv run python cli.py --file media/license.jpeg --mode t --region us-east-1

# Forms and tables analysis
uv run python cli.py --file media/license.jpeg --mode fb --region us-east-1

# Auto-detection with custom queries/prompts
uv run python cli.py --file media/license.jpeg --mode tfbq --custom --queries "What is the issuing authority?" --region us-east-1
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
    "custom": false,
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
- **Auto Category Detection**: Automatically detect document type using AI

### 2. **Intelligent Blur Detection**

- **Local**: OpenCV Laplacian variance + Textract confidence analysis
- **Lambda**: Enhanced Textract confidence analysis with statistical metrics
- **Metrics**: Average, median, and standard deviation of OCR confidence
- **Quality Assessment**: Excellent, good, fair, or poor ratings
- **API Integration**: Structured `blur_analysis` field in Lambda responses

### 3. **AWS Bedrock Integration**

- **Structured Extraction**: Convert documents to structured JSON
- **Document Categories**: Specialized prompts for different document types
- **Auto Category Detection**: AI-powered document classification
- **Custom Mode**: Override category-based prompts and queries
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
│   │   ├── license.txt
│   │   ├── license-front.txt
│   │   ├── license-back.txt
│   │   ├── receipt.txt
│   │   ├── idcard.txt
│   │   └── tnb.txt
│   └── queries/                  # Textract queries
│       ├── license.txt
│       ├── license-front.txt
│       ├── license-back.txt
│       ├── receipt.txt
│       ├── idcard.txt
│       └── tnb.txt
├── docs/                         # Documentation
│   ├── QUICK_REFERENCE.md        # Essential commands
│   ├── EXAMPLES.md               # Usage examples
│   └── DEVELOPMENT.md            # Development guide
├── media/                        # Sample test files
├── log/                          # Local analysis results
│   └── {filename}_{timestamp}/   # Individual analysis logs
│       ├── textract.log          # Complete processing log
│       ├── text.json             # Text detection results
│       ├── forms.json            # Form analysis results
│       ├── tables.json           # Table analysis results
│       ├── queries.json          # Query analysis results
│       ├── blur_analysis.json    # Blur detection results
│       └── category_detection.json # Auto-detection results
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
uv run python cli.py --file media/license.jpeg --mode tfbq --category license

# Test Lambda locally
uv run python local_test.py

# Deploy to AWS
serverless deploy --region us-east-1

# Test deployed API
uv run python test_lambda.py --api-url YOUR_API_URL --file media/license.jpeg --mode tfbq --category license

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
uv run python cli.py --file media/license.jpeg --mode q --category license

# Custom queries only
uv run python cli.py --file media/license.jpeg --mode q --queries "What is the issuing authority?;What is the photo quality?"

# Category + custom queries combined
uv run python cli.py --file media/license.jpeg --mode q --category license --queries "What is the issuing authority?"

# Custom prompt for Bedrock AI extraction
uv run python cli.py --file media/license.jpeg --mode tfb --prompt "Extract name, birth date, license number, and expiry date as JSON"

# All analysis types
uv run python cli.py --file media/license.jpeg --mode tfbq --category license
```

### Document Categories

```bash
# Auto-detected analysis (recommended)
uv run python cli.py --file media/license.jpeg --mode tfbq

# License analysis (explicit category)
uv run python cli.py --file media/license.jpeg --mode tfbq --category license

# Receipt analysis with auto-detection
uv run python cli.py --file media/receipt.pdf --mode tfbq

# ID card analysis with custom mode
uv run python cli.py --file media/idcard.jpg --mode tfbq --category idcard

# TNB bill analysis
uv run python cli.py --file media/tnb-bill.pdf --mode tfbq --category tnb

# License front analysis  
uv run python cli.py --file media/license-front.jpeg --mode tfbq --category license-front
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
      category: 'license',
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
with open('media/license.jpeg', 'rb') as f:
    file_content = base64.b64encode(f.read()).decode('utf-8')

# Make API call
response = requests.post(
    'https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/analyze',
    json={
        'file_content': file_content,
        'filename': 'license.jpeg',
        'mode': 'tfbq',
        'category': 'license',
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
FILE_CONTENT=$(base64 -w 0 media/license.jpeg)

# Make API call
curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/analyze \
  -H "Content-Type: application/json" \
  -d "{
    \"file_content\": \"$FILE_CONTENT\",
    \"filename\": \"license.jpeg\",
    \"mode\": \"tfbq\",
    \"category\": \"license\",
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
  "category_detection": {
    "detected_category": "receipt",
    "confidence": 0.95,
    "timestamp": "20250109_143022"
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

## 🔄 Auto-Detection Features

### Document Category Detection

The system automatically detects document categories using AI analysis of extracted text, forms, and tables:

```bash
# Auto-detection (recommended - no --category needed)
uv run python cli.py --file document.pdf --mode tfbq
```

**How it works:**
1. **Initial Analysis**: Extracts text, forms, and tables using Textract
2. **AI Classification**: Uses Bedrock Claude AI to analyze content and classify document type
3. **Category Assignment**: Applies detected category for queries and prompts
4. **Results Saved**: Detection results saved to `category_detection.json`

**Supported Categories:**
- `idcard` - Identity cards, national IDs, employee IDs
- `license` - Driver's license, driving permits (combined/single-sided)
- `license-front` - Front side of driver's license specifically
- `license-back` - Back side of driver's license specifically  
- `tnb` - TNB utility bills, electricity bills
- `receipt` - Purchase receipts, invoices from retail stores

**Detection Confidence:**
- High confidence (0.7-1.0): Very reliable classification
- Medium confidence (0.4-0.7): Moderately reliable
- Low confidence (0.0-0.4): Less reliable, may need manual verification

### Manual Category Override

```bash
# Specify category explicitly (skips auto-detection)
uv run python cli.py --file document.pdf --mode tfbq --category tnb
```

### Custom Mode

Use `--custom` to override category-based files with your own queries/prompts:

```bash
# Custom mode with explicit queries (ignores category query files)
uv run python cli.py --file document.pdf --mode q --custom --queries "What is the date?;What is the amount?"

# Custom mode with explicit prompt (ignores category prompt files)
uv run python cli.py --file document.pdf --mode tfb --custom --prompt "Extract all dates as JSON"

# Custom mode for categories without extensive default files
uv run python cli.py --file license-back.jpeg --mode q --category license-back --queries "What is the license number?"
```

**Custom Mode Rules:**
- If `--custom` is used and no custom queries/prompts provided, system checks for category files
- All new categories have supporting files, but `--custom` can override them
- Use custom mode to test new queries or prompts for existing categories

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
# Auto-detected analysis (recommended)
uv run python cli.py --file media/license.jpeg --mode tfbq

# Basic text extraction
uv run python cli.py --file media/license.jpeg --mode t

# Full analysis with explicit category
uv run python cli.py --file media/license.jpeg --mode tfbq --category license

# Forms and tables only
uv run python cli.py --file media/license.jpeg --mode fb

# Custom queries with auto-detection
uv run python cli.py --file media/license.jpeg --mode q --queries "What is the name?"
```

### Mode Parameters
- `t` - Text detection only
- `f` - Forms analysis (key-value pairs)
- `b` - Tables analysis (structured data)
- `q` - Queries analysis (requires category)
- `tfbq` - All analysis types

### Categories (for queries and AI extraction)
- **Auto-detected** - AI automatically detects document type (recommended)
- `idcard` - Identity cards, national IDs, employee IDs
- `license` - Driver's licenses, driving permits (combined/single-sided)
- `license-front` - Front side of driver's license specifically
- `license-back` - Back side of driver's license specifically
- `tnb` - TNB utility bills, electricity bills
- `receipt` - Purchase receipts, invoices from retail stores

### Analysis Modes (`--mode`)
- `t` - Text detection only (fastest)
- `f` - Forms analysis (key-value pairs)
- `b` - Tables analysis (structured data)
- `q` - Queries analysis (requires category or custom queries)
- `tfbq` - All analysis types (recommended)

### Custom Mode (`--custom`)
- Forces use of custom queries/prompts even when category files exist
- Required for categories without default files (like `bank-receipt`)
- Enables development and testing of new document types
- Must provide `--queries` or `--prompt` when no category files exist

## 📝 Advanced Usage

### Custom Queries (`--queries`)

Provide custom questions for Textract to answer about the document:

```bash
# Single query
uv run python cli.py --file document.pdf --mode q --queries "What is the total amount?"

# Multiple queries (semicolon or newline separated)
uv run python cli.py --file document.pdf --mode q --queries "What is the date?;What is the amount?;Who is the recipient?"

# Multiline format
uv run python cli.py --file document.pdf --mode q --queries "What is the transaction date?
What is the reference number?
What is the beneficiary name?"
```

**Query Best Practices:**
- Ask specific, direct questions
- Use clear, simple language
- Questions should be answerable from visible text
- Avoid overly complex or interpretive questions

### Custom Prompts (`--prompt`)

Provide custom instructions for Bedrock AI to extract structured data:

```bash
# Basic extraction
uv run python cli.py --file document.pdf --mode tfb --prompt "Extract all monetary amounts and dates as JSON"

# Structured JSON extraction
uv run python cli.py --file receipt.pdf --mode tfb --prompt "Extract: {\"merchant\": \"store name\", \"total\": \"amount as number\", \"date\": \"YYYY-MM-DD format\"}"

# Bank receipt extraction
uv run python cli.py --file bank-receipt.pdf --mode tfb --prompt "Extract transaction details: amount, date, beneficiary name, reference ID as JSON"
```

**Prompt Guidelines:**
- Specify desired output format (JSON recommended)
- Define field names and data types
- Include formatting instructions (date formats, etc.)
- Specify how to handle missing data (use null)

### Argument Combinations

```bash
# Auto-detection with custom queries
uv run python cli.py --file document.pdf --mode tfbq --queries "Additional question?"

# Explicit category with custom prompt
uv run python cli.py --file document.pdf --mode tfb --category receipt --prompt "Custom extraction prompt"

# Custom mode overriding category files
uv run python cli.py --file document.pdf --mode tfbq --category license --custom --queries "Custom questions" --prompt "Custom prompt"

# Bank receipt with required custom content
uv run python cli.py --file bank-receipt.pdf --mode q --category bank-receipt --custom --queries "What is the transaction amount?"
```

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

### Testing Auto-Detection
```bash
# Run the test script
uv run python test_auto_detection.py

# Manual testing
uv run python cli.py --file media/license.jpeg --mode tfbq
# Check log/{filename}_{timestamp}/category_detection.json for results
```

## 📝 Developer Guide: Custom Queries and Prompts

### Writing Custom Queries

Queries are questions that Textract will attempt to answer based on the document content.

#### **Query Best Practices:**

1. **Be Specific**: Ask for exact information you need
   ```
   ✅ Good: "What is the expiry date?"
   ❌ Avoid: "What are the dates?"
   ```

2. **Use Clear Language**: Simple, direct questions work best
   ```
   ✅ Good: "What is the full name?"
   ✅ Good: "What is the license class?"
   ✅ Good: "What is the address?"
   ```

3. **Avoid Duplicates**: Don't repeat queries from category files
   ```bash
   # Check existing queries first
   cat src/queries/license.txt
   ```

4. **Format Correctly**: Separate multiple queries with semicolons or new lines
   ```bash
   # Using semicolons
   --queries "What is the issuing authority?;What is the photo quality?;What is the security code?"

   # Using new lines (in scripts or multi-line input)
   --queries "What is the issuing authority?
   What is the photo quality?
   What is the security code?"
   ```

#### **Query Examples by Document Type:**

**Driver's License:**
```bash
--queries "What is the issuing state?;What is the restriction code?;What is the endorsement?"
```

**ID Card:**
```bash
--queries "What is the issuing country?;What is the document number?;What is the place of birth?"
```

**Receipt/Invoice:**
```bash
--queries "What is the tax amount?;What is the payment method?;What is the cashier name?"
```

**License Front:**
```bash
--queries "What is the issuing authority?;What is the photo quality?;What are the restrictions?"
```

**License Back:**
```bash
--queries "What are the endorsements?;What is the organ donor status?;What are the conditions?"
```

### Writing Custom Prompts

Prompts are used by Bedrock AI for structured data extraction in `src/prompts/{category}.txt`.

#### **Example Prompt Structure:**
```
Extract the following information from this driver's license text and return as JSON:

{
  "full_name": "Full name of the license holder",
  "identity_no": "Identity/IC number",
  "date_of_birth": "Date of birth in YYYY-MM-DD format",
  "nationality": "Nationality",
  "license_number": "License number",
  "license_classes": ["Array of license classes"],
  "valid_from": "Valid from date in YYYY-MM-DD format",
  "valid_to": "Valid to date in YYYY-MM-DD format",
  "address": "Full address"
}

Rules:
- Use null for missing information
- Format dates as YYYY-MM-DD
- Extract exact text, don't interpret
- Return only valid JSON
```

#### **Testing Custom Queries and Prompts:**
```bash
# Custom queries only
uv run python cli.py --file document.pdf --mode q --queries "Your question?"

# Category + custom queries
uv run python cli.py --file document.pdf --mode tfbq --category license --queries "Additional question?"

# Custom prompt for AI extraction
uv run python cli.py --file document.pdf --mode tfb --prompt "Extract specific fields as JSON"

# Via Lambda API with custom prompt
uv run python test_lambda.py --file document.pdf --prompt "Your custom prompt" --api-url YOUR_URL
```

### Custom Prompt Engineering

The `--prompt` parameter allows you to override category-based prompts for Bedrock AI extraction, enabling rapid prototyping and adaptation to new document types.

#### **Custom Prompt Examples:**

**Simple Extraction:**
```bash
--prompt "Extract the name, date, and amount from this document and return as JSON."
```

**Structured JSON Output:**
```bash
--prompt "Extract the following information and return as JSON:
{
  \"document_type\": \"type of document\",
  \"issuer\": \"issuing organization\",
  \"recipient\": \"recipient name\",
  \"date_issued\": \"date in YYYY-MM-DD format\",
  \"amount\": \"monetary amount as number\",
  \"reference_number\": \"reference or ID number\"
}"
```

**Receipt Analysis:**
```bash
--prompt "Analyze this receipt and extract:
{
  \"merchant\": \"store name\",
  \"date\": \"transaction date\",
  \"total\": \"total amount\",
  \"tax\": \"tax amount\",
  \"items\": [\"list of purchased items\"]
}
Return only valid JSON."
```

**Invoice Processing:**
```bash
--prompt "Extract invoice details as JSON:
{
  \"invoice_number\": \"invoice ID\",
  \"vendor\": \"vendor name\",
  \"customer\": \"customer name\",
  \"date\": \"invoice date\",
  \"due_date\": \"payment due date\",
  \"subtotal\": \"subtotal amount\",
  \"tax_rate\": \"tax percentage\",
  \"total\": \"total amount\"
}"
```

#### **Prompt Best Practices:**

1. **Specify Output Format**: Always request JSON for structured data
2. **Define Field Names**: Use clear, consistent field names
3. **Handle Missing Data**: Instruct to use null for missing information
4. **Format Guidelines**: Specify date formats, number formats, etc.
5. **Validation Rules**: Add constraints for better accuracy

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
uv run python test_lambda.py --api-url YOUR_URL --file media/license.jpeg --mode t

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

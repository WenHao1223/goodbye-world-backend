# Examples and Use Cases

This document provides detailed examples of using Textract Full for various document types and scenarios.

## 📋 Document Types

### 1. Receipt Analysis

```bash
# Full receipt analysis
uv run python cli.py --file media/receipt.pdf --mode tfbq --category receipt --region us-east-1

# Expected output includes:
# - Transaction date and amount
# - Merchant information
# - Payment details
# - Tax information
```

**Sample Receipt Output:**
```json
{
  "transaction_date": "2025-09-15",
  "transaction_amount": "RM 100.00",
  "beneficiary_name": "DELLAND PROPERTY MANAGEMENT SDN BHD",
  "beneficiary_account": "8881 0134 2238 3",
  "reference_id": "837356732M",
  "sending_bank": "AmBANK BERHAD",
  "receiving_bank": "AmBANK BERHAD"
}
```

### 2. License Analysis

```bash
# Driver's license analysis
uv run python cli.py --file media/licence.jpeg --mode tfbq --category licence --region us-east-1

# Extracts:
# - Personal information
# - License details
# - Expiration dates
# - Restrictions
```

### 3. ID Card Analysis

```bash
# National ID card analysis
uv run python cli.py --file media/idcard.jpg --mode tfbq --category idcard --region us-east-1

# Extracts:
# - Full name
# - ID number
# - Date of birth
# - Address
```

### 4. Passport Analysis

```bash
# Passport analysis
uv run python cli.py --file media/passport.jpg --mode tfbq --category passport --region us-east-1

# Extracts:
# - Personal details
# - Passport number
# - Issue/expiry dates
# - Nationality
```

## 🔍 Analysis Modes

### Text Only (Fastest)
```bash
# Quick text extraction with blur detection
uv run python cli.py --file media/document.pdf --mode t --region us-east-1

# Use cases:
# - Quick text extraction
# - Blur quality assessment
# - OCR confidence analysis
```

### Forms Analysis
```bash
# Extract key-value pairs
uv run python cli.py --file media/form.pdf --mode f --region us-east-1

# Use cases:
# - Application forms
# - Survey responses
# - Structured documents
```

### Table Analysis
```bash
# Extract tabular data
uv run python cli.py --file media/invoice.pdf --mode b --region us-east-1

# Use cases:
# - Invoices
# - Financial statements
# - Data tables
```

### Query Analysis
```bash
# Answer specific questions
uv run python cli.py --file media/receipt.pdf --mode q --category receipt --region us-east-1

# Use cases:
# - Specific data extraction
# - Automated processing
# - Validation workflows
```

## 🌐 Lambda API Examples

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
      category: 'receipt',
      region: 'us-east-1'
    })
  });
  
  const result = await response.json();
  console.log(result);
};

reader.readAsDataURL(file);
```

### Python (Requests)
```python
import requests
import base64

# Read and encode file
with open('media/receipt.pdf', 'rb') as f:
    file_content = base64.b64encode(f.read()).decode('utf-8')

# Make API call
response = requests.post(
    'https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/analyze',
    json={
        'file_content': file_content,
        'filename': 'receipt.pdf',
        'mode': 'tfbq',
        'category': 'receipt',
        'region': 'us-east-1'
    }
)

result = response.json()
print(result)
```

### cURL
```bash
# Encode file to base64
FILE_CONTENT=$(base64 -w 0 media/receipt.pdf)

# Make API call
curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/analyze \
  -H "Content-Type: application/json" \
  -d "{
    \"file_content\": \"$FILE_CONTENT\",
    \"filename\": \"receipt.pdf\",
    \"mode\": \"tfbq\",
    \"category\": \"receipt\",
    \"region\": \"us-east-1\"
  }"
```

## 🧪 Testing Scenarios

### Quality Assessment
```bash
# Test with high-quality image
uv run python cli.py --file media/clear-receipt.pdf --mode t

# Test with blurry image
uv run python cli.py --file media/blur.jpg --mode t

# Compare confidence scores and blur detection results
```

### Performance Testing
```bash
# Small file (fast processing)
uv run python cli.py --file media/small-receipt.jpg --mode tfbq --category receipt

# Large file (slower processing)
uv run python cli.py --file media/large-document.pdf --mode tfbq

# Multiple pages
uv run python cli.py --file media/multi-page.pdf --mode tfbq
```

### Error Handling
```bash
# Unsupported file type
uv run python cli.py --file media/document.xlsx --mode t

# File too large
uv run python cli.py --file media/huge-file.pdf --mode t

# Invalid category
uv run python cli.py --file media/receipt.pdf --mode q --category invalid
```

## 📊 Output Examples

### Console Output
```
[INFO] Using file: media/receipt.pdf
[INFO] Using mode: tfbq
[INFO] Document category: receipt
[INFO] Using region: us-east-1

=== TEXT DETECTION ===
text = "Maybank" | confidence = 99.89
text = "DuitNow Transfer" | confidence = 99.91
...

=== FORM ANALYSIS ===
Amount: ['RM 100.00']
Reference ID: ['837356732M']
...

=== TABLE ANALYSIS ===
Table 1:
  | DuitNow Transfer | Successful |
  | Reference ID 837356732M | 15 Sep 2025, 3:13 PM |

=== QUERY ANALYSIS ===
Q: What is the transaction amount?
A: RM 100.00
...

=== BLUR DETECTION ===
Textract confidence - Median: 99.89, Avg: 99.75, Std: 0.51
Quality assessment: excellent
Overall: CLEAR (confidence: high)

=== BEDROCK EXTRACTION ===
{
  "transaction_date": "2025-09-15",
  "transaction_amount": "RM 100.00",
  ...
}

=== PROCESSING COMPLETE ===
[INFO] Textract results saved to: log/receipt_20250917_143545
[INFO] Extracted data saved to: output/receipt_20250917_143545.json
[INFO] Image quality appears good
```

### File Outputs

**log/receipt_20250917_143545/text.json**
```json
[
  {"text": "Maybank", "confidence": 99.89},
  {"text": "DuitNow Transfer", "confidence": 99.91}
]
```

**log/receipt_20250917_143545/forms.json**
```json
{
  "Amount": ["RM 100.00"],
  "Reference ID": ["837356732M"]
}
```

**output/receipt_20250917_143545.json**
```json
{
  "transaction_date": "2025-09-15",
  "transaction_amount": "RM 100.00",
  "beneficiary_name": "DELLAND PROPERTY MANAGEMENT SDN BHD"
}
```

## 🎯 Best Practices

### File Preparation
- Use high-resolution images (300 DPI or higher)
- Ensure good lighting and contrast
- Avoid skewed or rotated documents
- Keep file sizes under 5 MB for optimal performance

### Mode Selection
- Use `t` for quick text extraction
- Use `tf` for forms with text
- Use `tfbq` for comprehensive analysis
- Use specific modes to reduce processing time

### Category Selection
- Always specify category for query analysis
- Use appropriate category for best extraction results
- Categories are optimized for specific document types

### Error Handling
- Check file size before processing
- Validate file types (PDF, JPEG, PNG only)
- Handle API timeouts gracefully
- Implement retry logic for network issues

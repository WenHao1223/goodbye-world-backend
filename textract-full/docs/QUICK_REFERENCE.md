# Quick Reference

## 🚀 Essential Commands

### Setup
```bash
cd textract-full && uv sync
```

### Local Analysis
```bash
# Full analysis
uv run python cli.py --file media/receipt.pdf --mode tfbq --category receipt

# Text only (fastest)
uv run python cli.py --file media/document.pdf --mode t

# With specific AWS profile
uv run python cli.py --file media/receipt.pdf --mode tfbq --category receipt --profile your-profile
```

### Lambda
```bash
# Deploy
serverless deploy --region us-east-1

# Test locally
uv run python local_test.py

# Test API
uv run python test_lambda.py --api-url YOUR_URL --file media/receipt.pdf --mode tfbq --category receipt

# Web interface
uv run python test_lambda.py --create-html
```

## 📋 Parameters

### Modes
- `t` - Text extraction + blur detection
- `f` - Form analysis (key-value pairs)
- `b` - Table analysis
- `q` - Query analysis (requires category)
- `tfbq` - All analysis types

### Categories
- `receipt` - Financial receipts
- `licence` - Driver's licenses
- `idcard` - National ID cards
- `passport` - Passports

### File Types
- PDF (≤11 pages, ≤5MB)
- JPEG/JPG (≤5MB)
- PNG (≤5MB)

## 🔗 API Endpoints

### Lambda API
```
POST /analyze - Document analysis
GET /health - Health check
```

### Request Format
```json
{
  "file_content": "base64-encoded-content",
  "filename": "document.pdf",
  "mode": "tfbq",
  "category": "receipt",
  "region": "us-east-1"
}
```

## 📁 Output Locations

### Local
- `log/` - Textract results (JSON files)
- `output/` - Bedrock extractions (JSON files)

### Lambda
- `/tmp/log/` - Temporary Textract results
- `/tmp/output/` - Temporary extractions
- API response - All results in JSON

## 🔧 Troubleshooting

### Common Fixes
```bash
# Dependencies
uv sync

# AWS credentials
aws configure

# File permissions
chmod +r media/document.pdf

# Lambda deployment
npm install -g serverless serverless-python-requirements
```

### Error Codes
- `400` - Bad request (invalid file/parameters)
- `500` - Processing error (check logs)
- `timeout` - File too large or complex

## 📊 Performance Tips

### Speed Optimization
- Use `--mode t` for fastest processing
- Smaller files process faster
- Local processing is faster than Lambda

### Quality Tips
- High-resolution images (300+ DPI)
- Good lighting and contrast
- Straight, unrotated documents
- Clear, unblurred text

## 🎯 Use Cases

### Quick Text Extraction
```bash
uv run python cli.py --file document.pdf --mode t
```

### Receipt Processing
```bash
uv run python cli.py --file receipt.pdf --mode tfbq --category receipt
```

### Form Data Extraction
```bash
uv run python cli.py --file form.pdf --mode f
```

### Table Data Extraction
```bash
uv run python cli.py --file invoice.pdf --mode b
```

### Specific Questions
```bash
uv run python cli.py --file receipt.pdf --mode q --category receipt
```

## 🌐 Lambda URLs

Replace `YOUR_API_ID` with your actual API Gateway ID:

```
https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/dev/analyze
https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/dev/health
```

## 📱 Testing

### Local Testing
```bash
# CLI test
uv run python cli.py --file media/receipt.pdf --mode t

# Lambda test
uv run python local_test.py
```

### API Testing
```bash
# Health check
curl https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/dev/health

# Document analysis
uv run python test_lambda.py --api-url YOUR_URL --file media/receipt.pdf --mode t
```

## 🔍 Blur Detection Results

### Local (with OpenCV)
```
Laplacian score: 150.25 - Quality: good
Textract confidence - Median: 99.89, Avg: 99.75, Std: 0.51
Overall: CLEAR (confidence: high)
```

### Lambda (Textract only)
```
OpenCV not available - using Textract confidence analysis only
Textract confidence - Median: 99.89, Avg: 99.62, Std: 0.51
Quality assessment: excellent
Overall: CLEAR (confidence: high)
```

## 📈 Confidence Levels

### Quality Assessment
- **Excellent**: Avg > 98%, Median > 95%, Std < 2.0
- **Good**: Avg > 95%, Median > 90%, Std < 5.0
- **Fair**: Avg > 90%, Median > 85%
- **Poor**: Below fair thresholds

### Blur Detection
- **CLEAR**: Good OCR confidence, low variance
- **BLURRY**: Poor OCR confidence, high variance

## 🎨 Output Examples

### Console Output
```
=== TEXT DETECTION ===
text = "Sample Text" | confidence = 99.89

=== BLUR DETECTION ===
Overall: CLEAR (confidence: high)

=== BEDROCK EXTRACTION ===
{"amount": "$100.00", "date": "2025-09-15"}
```

### API Response
```json
{
  "status": "success",
  "text": [{"text": "Sample", "confidence": 99.89}],
  "extracted_data": {"amount": "$100.00"}
}
```

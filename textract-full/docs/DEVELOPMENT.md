# Development Guide

This guide covers development setup, testing, and contribution guidelines for Textract Full.

## 🛠️ Development Setup

### Prerequisites
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- AWS CLI configured
- Node.js (for Serverless Framework)

### Initial Setup
```bash
# Clone repository
git clone <repository-url>
cd textract-full

# Install dependencies
uv sync

# Verify installation
uv run python cli.py --help
```

### Environment Configuration
```bash
# Configure AWS credentials
aws configure

# Test AWS access
aws sts get-caller-identity

# Set environment variables (optional)
export AWS_REGION=us-east-1
export AWS_PROFILE=your-profile
```

## 🧪 Testing

### Local Testing
```bash
# Test CLI with sample files
uv run python cli.py --file media/receipt.pdf --mode tfbq --category receipt

# Test specific components
uv run python cli.py --file media/receipt.pdf --mode t  # Text only
uv run python cli.py --file media/receipt.pdf --mode f  # Forms only
uv run python cli.py --file media/receipt.pdf --mode b  # Tables only
uv run python cli.py --file media/receipt.pdf --mode q --category receipt  # Queries only
```

### Lambda Testing
```bash
# Test Lambda function locally
uv run python local_test.py

# Test health endpoint
uv run python local_test.py --health

# Test with different files
LAMBDA_RUNTIME=true uv run python cli.py --file media/receipt.pdf --mode t
```

### API Testing
```bash
# Deploy to AWS
serverless deploy --region us-east-1

# Test deployed API
uv run python test_lambda.py --api-url YOUR_API_URL --file media/receipt.pdf --mode tfbq --category receipt

# Create web test interface
uv run python test_lambda.py --create-html
```

## 📁 Code Structure

### Core Components

#### `src/main.py`
- Main CLI logic and workflow orchestration
- Argument parsing and validation
- Component integration

#### `src/textract_enhanced.py`
- AWS Textract integration
- Text, form, table, and query analysis
- File validation and processing

#### `src/bedrock_mapper.py`
- AWS Bedrock integration
- Structured data extraction
- Prompt management

#### `src/blur_detection.py`
- Image quality assessment
- OpenCV integration (local)
- Textract confidence analysis (Lambda)

#### `src/logger.py`
- Logging utilities
- Output formatting

### Lambda Components

#### `lambda_handler.py`
- AWS Lambda entry point
- API Gateway integration
- Request/response handling

#### `local_test.py`
- Local Lambda testing
- Environment simulation

#### `test_lambda.py`
- API testing utilities
- Web interface generation

## 🔧 Configuration Files

### `pyproject.toml`
- Project metadata and dependencies
- Build configuration
- Entry points

### `serverless.yml`
- Serverless Framework configuration
- AWS Lambda settings
- API Gateway configuration

### `requirements-lambda.txt`
- Lambda-specific dependencies
- Optimized for serverless deployment

## 🚀 Deployment

### Local Development
```bash
# No deployment needed
uv run python cli.py --file media/receipt.pdf --mode tfbq --category receipt
```

### Lambda Deployment
```bash
# Option 1: Serverless Framework
serverless deploy --region us-east-1

# Option 2: Custom deployment script
python deploy_lambda.py --function-name textract-full-api --region us-east-1

# Option 3: Manual AWS CLI
aws lambda create-function --function-name textract-full-api ...
```

## 🐛 Debugging

### Local Debugging
```bash
# Enable verbose logging
export PYTHONPATH=.
python -m pdb cli.py --file media/receipt.pdf --mode t

# Check AWS credentials
aws sts get-caller-identity

# Validate file access
ls -la media/receipt.pdf
```

### Lambda Debugging
```bash
# Check CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/textract-full-api

# Test locally with Lambda environment
LAMBDA_RUNTIME=true uv run python local_test.py

# Debug deployment
serverless deploy --verbose
```

### Common Issues

#### Import Errors
```bash
# Ensure dependencies are installed
uv sync

# Check Python path
echo $PYTHONPATH
```

#### AWS Permission Errors
```bash
# Check IAM permissions
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::ACCOUNT:role/lambda-role \
  --action-names textract:DetectDocumentText \
  --resource-arns "*"
```

#### File Processing Errors
```bash
# Check file format
file media/receipt.pdf

# Check file size
ls -lh media/receipt.pdf

# Test with different files
uv run python cli.py --file media/licence.jpeg --mode t
```

## 📝 Adding New Features

### Adding New Document Categories

1. **Create prompt file**
```bash
# Add new prompt
echo "Extract data from passport..." > src/prompts/passport.txt
```

2. **Create query file**
```bash
# Add new queries
cat > src/queries/passport.json << EOF
{
  "queries": [
    {"text": "What is the passport number?"},
    {"text": "What is the expiry date?"}
  ]
}
EOF
```

3. **Update argument validation**
```python
# In src/main.py
parser.add_argument("--category", choices=["licence", "receipt", "idcard", "passport", "new_category"])
```

### Adding New Analysis Modes

1. **Update mode validation**
```python
# In src/main.py
# Add new mode letter, e.g., 's' for signatures
```

2. **Implement analysis logic**
```python
# In src/textract_enhanced.py
if 's' in mode:
    # Add signature analysis logic
    pass
```

3. **Update documentation**
```markdown
# Update README.md with new mode
- s(ignatures): Detect and analyze signatures
```

### Adding New Output Formats

1. **Create formatter**
```python
# In src/formatters.py
def format_as_csv(data):
    # Convert data to CSV format
    pass
```

2. **Update CLI arguments**
```python
# In src/main.py
parser.add_argument("--output-format", choices=["json", "csv", "xml"])
```

3. **Integrate formatter**
```python
# In src/main.py
if args.output_format == "csv":
    formatted_data = format_as_csv(results)
```

## 🧪 Testing New Features

### Unit Testing
```bash
# Create test file
cat > tests/test_new_feature.py << EOF
import unittest
from src.new_module import new_function

class TestNewFeature(unittest.TestCase):
    def test_new_function(self):
        result = new_function("test_input")
        self.assertEqual(result, "expected_output")

if __name__ == "__main__":
    unittest.main()
EOF

# Run tests
python -m pytest tests/
```

### Integration Testing
```bash
# Test with real files
uv run python cli.py --file media/test_document.pdf --mode new_mode

# Test Lambda integration
LAMBDA_RUNTIME=true uv run python cli.py --file media/test_document.pdf --mode new_mode
```

### Performance Testing
```bash
# Time execution
time uv run python cli.py --file media/large_document.pdf --mode tfbq

# Memory usage
python -m memory_profiler cli.py --file media/document.pdf --mode tfbq
```

## 📋 Code Quality

### Linting
```bash
# Install linting tools
uv add --dev black flake8 mypy

# Format code
uv run black src/

# Check style
uv run flake8 src/

# Type checking
uv run mypy src/
```

### Documentation
```bash
# Generate documentation
uv add --dev sphinx

# Build docs
cd docs/
make html
```

## 🤝 Contributing

### Pull Request Process

1. **Fork the repository**
2. **Create feature branch**
```bash
git checkout -b feature/new-feature
```

3. **Make changes and test**
```bash
# Test locally
uv run python cli.py --file media/receipt.pdf --mode tfbq --category receipt

# Test Lambda
uv run python local_test.py
```

4. **Commit changes**
```bash
git add .
git commit -m "Add new feature: description"
```

5. **Push and create PR**
```bash
git push origin feature/new-feature
# Create pull request on GitHub
```

### Code Standards
- Follow PEP 8 style guidelines
- Add type hints for new functions
- Include docstrings for public methods
- Write tests for new features
- Update documentation

### Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass locally and in Lambda
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] Performance impact considered

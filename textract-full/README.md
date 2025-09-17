# Textract Full

Combined CLI tool for AWS Textract, Bedrock, and Blur Detection.

## Installation

```bash
cd textract-full
uv sync
```

## Usage

```bash
# Activate virtual environment
.venv\Scripts\activate

# Run the CLI
python cli.py --file path/to/image.jpg --mode tfbq --category licence --region us-east-1 --profile your-profile
```

### Arguments

- `--file`: Path to input file (JPEG/PNG/PDF)
- `--mode`: Analysis mode - combine letters: t(ext), f(orms), b(tables), q(uery) (default: tfbq)
- `--category`: Document category for queries: licence, receipt, idcard, passport
- `--region`: AWS region (default: us-east-1)
- `--profile`: AWS profile name (optional)

### Examples

```bash
# Analyze a driving licence
python cli.py --file media/licence.jpeg --mode tfbq --category licence --region us-east-1 --profile greataihackathon-personal

# Analyze a receipt with text and forms only
python cli.py --file media/receipt.pdf --mode tf --category receipt --region us-east-1

# Just text extraction with blur detection
python cli.py --file media/blur.jpg --mode t --region us-east-1
```

## Features

1. **Textract Analysis**: Text, forms, tables, and queries
2. **Blur Detection**: Image quality assessment using OpenCV and Textract confidence scores
3. **Bedrock Extraction**: Structured data extraction using Claude AI
4. **Integrated Workflow**: All three components in a single command

## Output

- Textract results saved to `log/` directory
- Extracted structured data saved to `output/` directory
- Blur analysis included in console output
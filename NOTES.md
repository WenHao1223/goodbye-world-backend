# Set IAM credentials in .venv
```bash
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
```

```cmd
set AWS_ACCESS_KEY_ID=...
set AWS_SECRET_ACCESS_KEY=...
```

# Set IAM credentials in AWS CLI
```bash
aws configure --profile greataihackathon-personal
aws sts get-caller-identity
```

# Run
## Extract Text
`--mode`: t(ext), f(orms), b(tables), q(uery) - combine letters like tfbq
`--category`: licence-front, licence-back
```bash
python aws-textract/textract_local.py --image aws-textract/files/paystub.jpg --region us-east-1 --profile greataihackathon-personal
```

```bash
python aws-textract/textract_enhanced_local.py --file aws-textract/files/licence.jpeg --mode tfbq --category licence --region us-east-1 --profile greataihackathon-personal 
python aws-textract/textract_enhanced_local.py --file aws-textract/files/mingjia-licence.jpg --mode tf --region us-east-1 --profile greataihackathon-personal
python aws-textract/textract_enhanced_local.py --file aws-textract/files/blur.jpg --mode tf --region us-east-1 --profile greataihackathon-personal
python aws-textract/textract_enhanced_local.py --file aws-textract/files/bank-receipt.pdf --mode tfbq --category receipt --region us-east-1 --profile greataihackathon-personal
```

## Check if image is blurry
```bash
python blur-detection/analyze_current_results.py
```

```bash
python blur-detection/analyze_blur.py --file log/blur_20250917_152542/textract.log
python blur-detection/analyze_blur.py --file log/bank-receipt_20250917_013838/textract.log
```

## Check Bedrock Model Available
```bash
python check-bedrock-models.py --region us-east-1 --profile greataihackathon-personal
```

## Mapper
```bash
python aws-bedrock/bedrock-mapper.py --files log/licence_20250916_231316/text.json log/licence_20250916_231316/forms.json --category licence --region us-east-1 --profile greataihackathon-personal
python aws-bedrock/bedrock-mapper.py --files log/licence_20250917_001133/textract.log --category licence --region us-east-1 --profile greataihackathon-personal
python aws-bedrock/bedrock-mapper.py --files log/mingjia-licence_20250917_001506/textract.log --category licence --region us-east-1 --profile greataihackathon-personal
```
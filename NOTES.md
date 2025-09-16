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
python aws-textract/textract_local.py --profile greataihackathon-personal --image aws-textract/files/paystub.jpg --region us-east-1
python aws-textract/textract_enhanced_local.py --profile greataihackathon-personal --file aws-textract/files/bank-receipt.pdf --region us-east-1
```

```bash
python aws-textract/textract_enhanced_local.py --profile greataihackathon-personal --file aws-textract/files/licence.jpeg --region us-east-1 --mode tfbq --category licence
python aws-textract/textract_enhanced_local.py --profile greataihackathon-personal --file aws-textract/files/mingjia-licence.jpg --region us-east-1 --mode tf
```

## Check Bedrock Model Available
```bash
python check-bedrock-models.py --profile greataihackathon-personal --region us-east-1
```

## Mapper
```bash
python aws-bedrock/bedrock-mapper.py --files log/licence_20250916_231316/text.json log/licence_20250916_231316/forms.json --category licence --profile greataihackathon-personal
python aws-bedrock/bedrock-mapper.py --files log/licence_20250917_001133/textract.log --category licence --profile greataihackathon-personal
python aws-bedrock/bedrock-mapper.py --files log/mingjia-licence_20250917_001506/textract.log --category licence --profile greataihackathon-personal
```
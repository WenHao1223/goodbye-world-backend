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
python aws-textract/textract_local.py --profile greataihackathon-personal --file aws-textract/files/paystub.jpg --region us-east-1
python aws-textract/textract_enhanced_local.py --profile greataihackathon-personal --file aws-textract/files/paystub.jpg --region us-east-1 --mode tfbq
python aws-textract/textract_enhanced_local.py --profile greataihackathon-personal --file aws-textract/files/licence.jpeg --region us-east-1 --mode q --category licence
```

## Check Bedrock Model Available
```bash
python check-bedrock-models.py --profile greataihackathon-personal --region us-east-1
```

## Mapper
```bash
python aws-bedrock/bedrock-mapper.py --files log/licence_tfbq_20250916_215456.log --profile greataihackathon-personal
python aws-bedrock/bedrock-mapper.py --files output/licence_20250916_215456_b.json output/licence_20250916_215456_f.json --profile greataihackathon-personal
python aws-bedrock/bedrock-mapper.py --files output/licence_20250916_215456_b.json output/licence_20250916_215456_f.json output/licence_20250916_215456_q.json --profile greataihackathon-personal
```
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
`--category`: licence-front, licence-back
```bash
python aws-textract/textract_local.py --profile greataihackathon-personal --file aws-textract/files/paystub.jpg --region us-east-1
python aws-textract/textract_enhanced_local.py --profile greataihackathon-personal --file aws-textract/files/paystub.jpg --region us-east-1 --mode tfbq
python aws-textract/textract_enhanced_local.py --profile greataihackathon-personal --file aws-textract/files/licence.jpeg --region us-east-1 --mode q --category licence
```

## Mapper
```bash
python aws-textract/mapper/licence_mapper.py --file output/licence_20250916_211544_q.json
```
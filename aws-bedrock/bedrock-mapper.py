import argparse
import sys
import json
from pathlib import Path
import re

import boto3

def load_textract_json(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def get_system_prompt():
    return """Extract Malaysian driving licence fields from the provided data.
Return STRICTLY valid JSON matching this schema:
{
  "full_name": string|null,
  "identity_no": string|null,
  "date_of_birth": "YYYY-MM-DD"|null,
  "nationality": string|null,
  "licence_number": string|null,
  "licence_classes": [string]|null,
  "valid_from": "YYYY-MM-DD"|null,
  "valid_to": "YYYY-MM-DD"|null,
  "address": string|null
}
CRITICAL RULES:
- ONLY extract data that is EXPLICITLY present in the input
- DO NOT make up or guess any values
- If a field is not found, use null
- Convert dates from DD/MM/YYYY to YYYY-MM-DD format
- Identity number: ONLY from "No. Pengenalan / Identity No." field
- Licence number: ONLY a combination of 2 parts
  * first part, 7-digit numeric codes that are clearly licence numbers (NOT dates, NOT identity numbers), e.g. "1234567"
  * second part, 8-digit alphanumeric codes that are a randomised mix of upper/lowercase letters + numbers, e.g. "AbC12xYz"
  * join the two parts with a space in between, e.g. "1234567 AbC12xYz"
- Licence classes: ONLY from "Kelas / Class" field, split into array
- Validity dates: ONLY from "Tempoh / Validity" field
- Address: ONLY from "Alamat / Address" field
- Nationality: ONLY from "Warganegara / Nationality" field
- Full name: ONLY if explicitly found in the data
- Return only valid JSON, no explanations
"""

def extract_fields(textract_log: str, region: str, profile: str | None = None):
    session_kwargs = {"region_name": region}
    if profile:
        session_kwargs["profile_name"] = profile
    
    session = boto3.Session(**session_kwargs)
    bedrock = session.client("bedrock-runtime")
    
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "temperature": 0,
        "messages": [
            {
                "role": "user",
                "content": f"{get_system_prompt()}\n\nExtract ONLY the data that is explicitly present in this input:\n{textract_log}"
            }
        ]
    }
    
    resp = bedrock.invoke_model(modelId="anthropic.claude-3-haiku-20240307-v1:0", body=json.dumps(payload))
    result = json.loads(resp["body"].read())
    raw_text = result["content"][0]["text"]
    
    # Try to find JSON in the response
    json_start = raw_text.find('{')
    json_end = raw_text.rfind('}') + 1
    
    if json_start != -1 and json_end > json_start:
        try:
            return json.loads(raw_text[json_start:json_end])
        except json.JSONDecodeError:
            pass
    
    return {}

def main():
    parser = argparse.ArgumentParser(description="Extract Malaysian driving licence fields from Textract JSON")
    parser.add_argument("--files", nargs="+", required=True, help="Path(s) to the Textract JSON file(s)")
    parser.add_argument("--region", required=False, default="us-east-1", help="AWS region, e.g., us-east-1")
    parser.add_argument("--profile", required=False, default=None, help="AWS profile name to use (optional).")
    args = parser.parse_args()
    
    # Combine all files into one text
    combined_text = ""
    for i, file_path in enumerate(args.files):
        file_content = load_textract_json(file_path)
        combined_text += f"\n\n=== FILE {i+1}: {file_path} ===\n{file_content}"
    
    extracted = extract_fields(combined_text, args.region, args.profile)
    print(json.dumps(extracted, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()

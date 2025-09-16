import argparse
import sys
import json
from pathlib import Path
import re
from datetime import datetime
from io import StringIO

import boto3

def load_textract_json(file_path: Path):
    with open(file_path, "r", encoding="latin-1") as f:
        return f.read()

from typing import Literal

def get_system_prompt(type: Literal["licence", "receipt", "idcard", "passport"]):
    if type == "licence":
        prompt_file = Path("aws-bedrock/prompts/licence.txt")
        if prompt_file.exists():
            with open(prompt_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        else:
            sys.exit(f"[ERROR] Prompt file {prompt_file} not found.")
    elif type == "receipt":
        pass
    # based on research on gov SOPs
    elif type == "idcard":
        pass
    elif type == "passport":
        pass
    else:
        sys.exit(f"[ERROR] Unknown prompt type: {type}")

def extract_fields(textract_log: str, type: Literal["licence", "receipt", "idcard", "passport"], region: str, profile: str | None = None):
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
                "content": f"{get_system_prompt(type)}\n\nExtract ONLY the data that is explicitly present in this input:\n{textract_log}"
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
    parser.add_argument("--type", required=False, default="licence", choices=["licence", "receipt", "idcard", "passport"], help="Type of document to extract: licence, receipt, idcard, passport")
    parser.add_argument("--region", required=False, default="us-east-1", help="AWS region, e.g., us-east-1")
    parser.add_argument("--profile", required=False, default=None, help="AWS profile name to use (optional).")
    args = parser.parse_args()
    
    # Capture terminal output
    log_output = StringIO()
    
    def log_print(msg):
        print(msg)
        log_output.write(msg + "\n") 
    
    # Print parsed arguments
    log_print(f"[INFO] Using files: {', '.join(args.files)}")
    log_print(f"[INFO] Using region: {args.region}")
    log_print(f"[INFO] Document type: {args.type}")
    log_print(f"[INFO] Using profile: {args.profile if args.profile else 'default'}")
    log_print(f"[INFO] Using prompt: aws-bedrock/prompts/licence.txt")
    
    # Combine all files into one text
    combined_text = ""
    for i, file_path in enumerate(args.files):
        file_content = load_textract_json(file_path)
        combined_text += f"\n\n=== FILE {i+1}: {file_path} ===\n{file_content}"
    
    log_print("\n=== BEDROCK EXTRACTION ===")
    extracted = extract_fields(combined_text, args.type, args.region, args.profile)
    result_json = json.dumps(extracted, indent=2, ensure_ascii=False)
    log_print(result_json)
    
    # Create output directories
    output_dir = Path("output")
    log_dir = Path("log")
    output_dir.mkdir(exist_ok=True)
    log_dir.mkdir(exist_ok=True)
    
    # Generate timestamp and filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = Path(args.files[0]).stem if len(args.files) == 1 else "combined"
    
    # Save extracted data
    with open(output_dir / f"{base_name}_extracted_{timestamp}.json", "w", encoding="utf-8") as f:
        f.write(result_json)
    
    # Save log
    with open(log_dir / f"{base_name}_mapper_{timestamp}.log", "w", encoding="utf-8") as f:
        f.write(log_output.getvalue())
    
    log_print(f"\n[INFO] Results saved to output/{base_name}_extracted_{timestamp}.json")
    log_print(f"[INFO] Log saved to log/{base_name}_mapper_{timestamp}.log")

if __name__ == "__main__":
    main()

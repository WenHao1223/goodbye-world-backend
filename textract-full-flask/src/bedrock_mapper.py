import json
from pathlib import Path
from datetime import datetime
from io import StringIO
from typing import Literal
import sys

import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Capture terminal output
log_output = StringIO()
def log_print(msg):
    print(msg)
    log_output.write(msg + "\n") 

def get_system_prompt(category: Literal["licence", "receipt", "idcard", "passport"]):
    prompt_path = Path(__file__).parent / "prompts" / f"{category}.txt"
    log_print(f"[INFO] Using prompt: {prompt_path}")
    if prompt_path.exists():
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    else:
        sys.exit(f"[ERROR] Prompt file {prompt_path} not found.")

def extract_fields(textract_log: str, category: Literal["licence", "receipt", "idcard", "passport"], region: str, profile: str | None = None):
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
                "content": f"{get_system_prompt(category)}\n\nExtract ONLY the data that is explicitly present in this input:\n{textract_log}"
            }
        ]
    }

    # Invoke Bedrock model
    try:
        resp = bedrock.invoke_model(modelId="anthropic.claude-3-haiku-20240307-v1:0", body=json.dumps(payload))
    except (BotoCoreError, ClientError) as e:
        sys.exit(f"[ERROR] Bedrock invocation failed: {e}")
    
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

def run_bedrock_extraction(textract_log: str, category: str, region: str, profile: str, filename: str, timestamp: str):
    from .logger import log_print
    
    log_print("\n=== BEDROCK EXTRACTION ===")
    extracted = extract_fields(textract_log, category, region, profile)
    result_json = json.dumps(extracted, indent=2, ensure_ascii=False)
    log_print(result_json)
    
    # Create output directories
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Save extracted data
    output_file = output_dir / f"{filename}_{timestamp}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result_json)
    
    log_print(f"\n[INFO] Results saved to {output_file}")
    
    return extracted, output_file
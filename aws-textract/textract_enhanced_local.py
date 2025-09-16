#!/usr/bin/env python3
"""
textract_enhanced_local.py — Run Amazon Textract locally with both text detection and form analysis.

Usage:
  python textract_enhanced_local.py --file /path/to/input.jpg --region us-east-1 --mode text
  python textract_enhanced_local.py --file /path/to/form.png --region us-east-1 --mode forms
  # Optionally use a specific AWS profile:
  AWS_PROFILE=myprofile python textract_enhanced_local.py --file input.png --region us-east-1 --mode both

Credentials:
  This script uses standard AWS credential resolution (env vars, shared ~/.aws/ files, or SSO).
"""

import argparse
import sys
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from io import StringIO

import boto3
from botocore.exceptions import BotoCoreError, ClientError

def get_kv_map(client, file_bytes):
    response = client.analyze_document(
        Document={'Bytes': file_bytes},
        FeatureTypes=['FORMS']
    )
    blocks = response['Blocks']
    
    key_map = {}
    value_map = {}
    block_map = {}
    for block in blocks:
        block_id = block['Id']
        block_map[block_id] = block
        if block['BlockType'] == "KEY_VALUE_SET":
            if 'KEY' in block['EntityTypes']:
                key_map[block_id] = block
            else:
                value_map[block_id] = block
    
    return key_map, value_map, block_map

def get_kv_relationship(key_map, value_map, block_map):
    kvs = defaultdict(list)
    for block_id, key_block in key_map.items():
        value_block = find_value_block(key_block, value_map)
        key = get_text(key_block, block_map)
        val = get_text(value_block, block_map)
        kvs[key].append(val)
    return kvs

def find_value_block(key_block, value_map):
    for relationship in key_block['Relationships']:
        if relationship['Type'] == 'VALUE':
            for value_id in relationship['Ids']:
                value_block = value_map[value_id]
    return value_block

def get_text(result, blocks_map):
    text = ''
    if 'Relationships' in result:
        for relationship in result['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    word = blocks_map[child_id]
                    if word['BlockType'] == 'WORD':
                        text += word['Text'] + ' '
                    if word['BlockType'] == 'SELECTION_ELEMENT':
                        if word['SelectionStatus'] == 'SELECTED':
                            text += 'X'
    return text

def detect_document_text(file_path: Path, region: str, profile: str | None = None):
    session_kwargs = {}
    if profile:
        session_kwargs["profile_name"] = profile
    if region:
        session_kwargs["region_name"] = region

    session = boto3.Session(**session_kwargs)
    client = session.client("textract")

    with file_path.open("rb") as f:
        file_bytes = f.read()

    try:
        resp = client.detect_document_text(Document={"Bytes": file_bytes})
        return resp, client, file_bytes
    except (BotoCoreError, ClientError) as e:
        raise SystemExit(f"[ERROR] Textract call failed: {e}")

def analyze_forms(client, file_bytes):
    try:
        key_map, value_map, block_map = get_kv_map(client, file_bytes)
        kvs = get_kv_relationship(key_map, value_map, block_map)
        return kvs
    except (BotoCoreError, ClientError) as e:
        raise SystemExit(f"[ERROR] Form analysis failed: {e}")

def analyze_tables(client, file_bytes):
    try:
        response = client.analyze_document(
            Document={'Bytes': file_bytes},
            FeatureTypes=['TABLES']
        )
        blocks = response['Blocks']
        tables = []
        for block in blocks:
            if block['BlockType'] == 'TABLE':
                table = {'rows': []}
                if 'Relationships' in block:
                    for relationship in block['Relationships']:
                        if relationship['Type'] == 'CHILD':
                            for cell_id in relationship['Ids']:
                                cell_block = next((b for b in blocks if b['Id'] == cell_id), None)
                                if cell_block and cell_block['BlockType'] == 'CELL':
                                    row_idx = cell_block['RowIndex'] - 1
                                    col_idx = cell_block['ColumnIndex'] - 1
                                    while len(table['rows']) <= row_idx:
                                        table['rows'].append([])
                                    while len(table['rows'][row_idx]) <= col_idx:
                                        table['rows'][row_idx].append('')
                                    table['rows'][row_idx][col_idx] = get_text(cell_block, {b['Id']: b for b in blocks}).strip()
                tables.append(table)
        return tables
    except (BotoCoreError, ClientError) as e:
        raise SystemExit(f"[ERROR] Table analysis failed: {e}")
    
def analyze_queries(client, file_bytes, category: str):
    try:
        if category == 'licence':
            queries_config = {
                'Queries': [
                    {'Text': 'What is the full name?'},
                    {'Text': 'What is the date of birth?'},
                    {'Text': 'What is the expiry date?'},
                    {"Text": "What is the licence validity period?"},
                    {'Text': 'What is the licence number?'},
                    # {'Text': 'What is the string below licence number?'},
                    {"Text": "What is the licence class?"},
                    {'Text': 'What is the address?'},
                ]
            }
        else:
            # TODO: Add more categories as needed
            queries_config = {
                'Queries': [
                    {'Text': 'What is the full name?'},
                    {'Text': 'What is the date of birth?'},
                    {'Text': 'What is the expiry date?'},
                    {'Text': 'What is the document number?'},
                    {'Text': 'What is the address?'}
                ]
            }
        
        response = client.analyze_document(
            Document={'Bytes': file_bytes},
            FeatureTypes=['QUERIES'],
            QueriesConfig=queries_config
        )
        
        blocks = response['Blocks']
        block_map = {block['Id']: block for block in blocks}
        queries = {}
        
        for block in blocks:
            if block['BlockType'] == 'QUERY':
                query_text = block['Query']['Text']
                answer = ''
                if 'Relationships' in block:
                    for relationship in block['Relationships']:
                        if relationship['Type'] == 'ANSWER':
                            for answer_id in relationship['Ids']:
                                answer_block = block_map.get(answer_id)
                                if answer_block and answer_block['BlockType'] == 'QUERY_RESULT':
                                    answer = answer_block.get('Text', '').strip()
                queries[query_text] = answer
        return queries
    except (BotoCoreError, ClientError) as e:
        raise SystemExit(f"[ERROR] Query analysis failed: {e}")
    

# Run from command line with these:
# python textract_enhanced_local.py --file /path/to/input.jpg --region us-east-1 --mode tfbq --category licence
# arguments:
# --file: path to the file (JPEG/PNG/PDF single page)
# --region: AWS region, e.g., us-east-1
# --profile: AWS profile name to use (optional)
# --mode: analysis mode: t(ext), f(orms), b(tables), q(uery) - combine letters like tfbq
# --category: document category for queries: licence, receipt, sop
def main():
    parser = argparse.ArgumentParser(description="Run AWS Textract locally with text and form analysis.")
    parser.add_argument("--file", required=True, type=Path, help="Path to the file file (JPEG/PNG/PDF single page).")
    parser.add_argument("--region", required=False, default="us-east-1", help="AWS region, e.g., us-east-1")
    parser.add_argument("--profile", required=False, default=None, help="AWS profile name to use (optional).")
    parser.add_argument("--mode", required=False, default="t", 
                       help="Analysis mode: t(ext), f(orms), b(tables), q(uery) - combine letters like tfbq")
    parser.add_argument("--category", required=False, default=None, 
                       help="Document category for queries: licence, receipt, sop.")
    args = parser.parse_args()

    # Capture terminal output
    log_output = StringIO()
    
    def log_print(msg):
        print(msg)
        log_output.write(msg + "\n")

    # Print parsed arguments
    log_print(f"[INFO] Using file: {args.file}")
    log_print(f"[INFO] Using region: {args.region}")
    log_print(f"[INFO] Using profile: {args.profile if args.profile else 'default'}")
    log_print(f"[INFO] Using mode: {args.mode}")

    # Check if file exists
    if not args.file.exists():
        log_print(f"[ERROR] File not found: {args.file}", file=sys.stderr)
        sys.exit(2)
    # Validate input file type
    if args.file.suffix.lower() not in [".jpg", ".jpeg", ".png", ".pdf"]:
        log_print(f"[ERROR] Unsupported file type: {args.file.suffix}. Only .jpg, .jpeg, .png, .pdf are allowed.", file=sys.stderr)
        sys.exit(2)
    # Validate if file is smaller than 5 MB
    if args.file.stat().st_size > 5 * 1024 * 1024:
        log_print(f"[ERROR] File size exceeds 5 MB: {args.file.stat().st_size} bytes.", file=sys.stderr)
        sys.exit(2)
    # Validate if document is fewer than 11 pages (only for PDF)
    if args.file.suffix.lower() == ".pdf":
        from PyPDF2 import PdfReader
        try:
            reader = PdfReader(str(args.file))
            if len(reader.pages) > 11:
                log_print(f"[ERROR] PDF document exceeds 11 pages: {len(reader.pages)} pages.", file=sys.stderr)
                sys.exit(2)
        except Exception as e:
            log_print(f"[ERROR] Failed to read PDF file: {e}", file=sys.stderr)
            sys.exit(2)

    mode = args.mode.lower()
    resp, client, file_bytes = detect_document_text(args.file, args.region, args.profile)
    
    # Create log subdirectory
    file_name = args.file.stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    log_subdir = Path("log") / f"{file_name}_{timestamp}"
    log_subdir.mkdir(parents=True, exist_ok=True)

    if 't' in mode:
        log_print("=== TEXT DETECTION ===")
        blocks = resp.get("Blocks", [])
        text_data = []
        for b in blocks:
            if b.get("BlockType") == "LINE":
                text = b.get("Text", "")
                conf = b.get("Confidence", 0.0)
                log_print(f"text = \"{text}\"  | confidence = {conf:.2f}")
                text_data.append({"text": text, "confidence": conf})
        
        with open(log_subdir / "text.json", "w") as f:
            json.dump(text_data, f, indent=2)

    if 'f' in mode:
        log_print("\n=== FORM ANALYSIS ===")
        kvs = analyze_forms(client, file_bytes)
        form_data = dict(kvs)
        for key, value in kvs.items():
            log_print(f"{key}: {value}")
        
        with open(log_subdir / "forms.json", "w") as f:
            json.dump(form_data, f, indent=2)

    if 'b' in mode:
        log_print("\n=== TABLE ANALYSIS ===")
        tables = analyze_tables(client, file_bytes)
        table_data = {"tables": []}
        for i, table in enumerate(tables):
            log_print(f"Table {i+1}:")
            for row in table['rows']:
                log_print("  | " + " | ".join(row) + " |")
            table_data["tables"].append({"table_id": i+1, "rows": table['rows']})
        
        with open(log_subdir / "tables.json", "w") as f:
            json.dump(table_data, f, indent=2)

    if 'q' in mode:
        log_print("\n=== QUERY ANALYSIS ===")
        category = args.category or 'default'
        queries = analyze_queries(client, file_bytes, category)
        for question, answer in queries.items():
            log_print(f"Q: {question}")
            log_print(f"A: {answer}")
            log_print("")
        
        with open(log_subdir / "queries.json", "w") as f:
            json.dump(queries, f, indent=2)
    
    # Save log
    with open(log_subdir / "textract.log", "w") as f:
        f.write(log_output.getvalue())

if __name__ == "__main__":
    main()
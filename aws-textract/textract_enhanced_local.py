#!/usr/bin/env python3
"""
textract_enhanced_local.py — Run Amazon Textract locally with both text detection and form analysis.

Usage:
  python textract_enhanced_local.py --image /path/to/input.jpg --region us-east-1 --mode text
  python textract_enhanced_local.py --image /path/to/form.png --region us-east-1 --mode forms
  # Optionally use a specific AWS profile:
  AWS_PROFILE=myprofile python textract_enhanced_local.py --image input.png --region us-east-1 --mode both

Credentials:
  This script uses standard AWS credential resolution (env vars, shared ~/.aws/ files, or SSO).
"""

import argparse
import sys
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

import boto3
from botocore.exceptions import BotoCoreError, ClientError

def get_kv_map(client, image_bytes):
    response = client.analyze_document(
        Document={'Bytes': image_bytes},
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

def detect_document_text(image_path: Path, region: str, profile: str | None = None):
    session_kwargs = {}
    if profile:
        session_kwargs["profile_name"] = profile
    if region:
        session_kwargs["region_name"] = region

    session = boto3.Session(**session_kwargs)
    client = session.client("textract")

    with image_path.open("rb") as f:
        image_bytes = f.read()

    try:
        resp = client.detect_document_text(Document={"Bytes": image_bytes})
        return resp, client, image_bytes
    except (BotoCoreError, ClientError) as e:
        raise SystemExit(f"[ERROR] Textract call failed: {e}")

def analyze_forms(client, image_bytes):
    try:
        key_map, value_map, block_map = get_kv_map(client, image_bytes)
        kvs = get_kv_relationship(key_map, value_map, block_map)
        return kvs
    except (BotoCoreError, ClientError) as e:
        raise SystemExit(f"[ERROR] Form analysis failed: {e}")

def analyze_tables(client, image_bytes):
    try:
        response = client.analyze_document(
            Document={'Bytes': image_bytes},
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

def main():
    parser = argparse.ArgumentParser(description="Run AWS Textract locally with text and form analysis.")
    parser.add_argument("--image", required=True, type=Path, help="Path to the image file (JPEG/PNG/PDF single page).")
    parser.add_argument("--region", required=False, default="us-east-1", help="AWS region, e.g., us-east-1")
    parser.add_argument("--profile", required=False, default=None, help="AWS profile name to use (optional).")
    parser.add_argument("--mode", required=False, default="t", 
                       help="Analysis mode: t(ext), f(orms), b(tables) - combine letters like tfb")
    args = parser.parse_args()

    if not args.image.exists():
        print(f"[ERROR] Image not found: {args.image}", file=sys.stderr)
        sys.exit(2)

    mode = args.mode.lower()
    resp, client, image_bytes = detect_document_text(args.image, args.region, args.profile)
    
    # Create detection folder
    detection_dir = Path("detection")
    detection_dir.mkdir(exist_ok=True)
    
    image_name = args.image.stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if 't' in mode:
        print("=== TEXT DETECTION ===")
        blocks = resp.get("Blocks", [])
        text_data = []
        for b in blocks:
            if b.get("BlockType") == "LINE":
                text = b.get("Text", "")
                conf = b.get("Confidence", 0.0)
                print(f"text = \"{text}\"  | confidence = {conf:.2f}")
                text_data.append({"text": text, "confidence": conf})
        
        with open(detection_dir / f"{image_name}_t_{timestamp}.json", "w") as f:
            json.dump(text_data, f, indent=2)

    if 'f' in mode:
        print("\n=== FORM ANALYSIS ===")
        kvs = analyze_forms(client, image_bytes)
        form_data = dict(kvs)
        for key, value in kvs.items():
            print(f"{key}: {value}")
        
        with open(detection_dir / f"{image_name}_f_{timestamp}.json", "w") as f:
            json.dump(form_data, f, indent=2)

    if 'b' in mode:
        print("\n=== TABLE ANALYSIS ===")
        tables = analyze_tables(client, image_bytes)
        table_data = {"tables": []}
        for i, table in enumerate(tables):
            print(f"Table {i+1}:")
            for row in table['rows']:
                print("  | " + " | ".join(row) + " |")
            table_data["tables"].append({"table_id": i+1, "rows": table['rows']})
        
        with open(detection_dir / f"{image_name}_b_{timestamp}.json", "w") as f:
            json.dump(table_data, f, indent=2)

if __name__ == "__main__":
    main()
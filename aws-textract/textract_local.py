#!/usr/bin/env python3
"""
textract_local.py — Run Amazon Textract DetectDocumentText locally with your IAM credentials.

Usage:
  python textract_local.py --image /path/to/input.jpg --region ap-south-1
  # Optionally use a specific AWS profile:
  AWS_PROFILE=myprofile python textract_local.py --image input.png --region ap-south-1

Credentials:
  This script uses standard AWS credential resolution (env vars, shared ~/.aws/ files, or SSO).
  - Env vars: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, [AWS_SESSION_TOKEN], AWS_REGION (or pass --region)
  - Shared config: set a profile and export AWS_PROFILE or use the default profile.
"""

import argparse
import sys
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError

def detect_document_text(image_path: Path, region: str, profile: str | None = None):
    # Let boto3 resolve credentials from env or shared config. Honor an explicit profile if given.
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
        return resp
    except (BotoCoreError, ClientError) as e:
        raise SystemExit(f"[ERROR] Textract call failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="Run AWS Textract DetectDocumentText locally.")
    parser.add_argument("--image", required=True, type=Path, help="Path to the image file (JPEG/PNG/PDF single page).")
    parser.add_argument("--region", required=False, default=None, help="AWS region, e.g., ap-south-1")
    parser.add_argument("--profile", required=False, default=None, help="AWS profile name to use (optional).")
    args = parser.parse_args()

    if not args.image.exists():
        print(f"[ERROR] Image not found: {args.image}", file=sys.stderr)
        sys.exit(2)

    resp = detect_document_text(args.image, args.region, args.profile)

    # Print raw response (optional)
    # print(resp)

    # Print only LINE blocks like the Java sample
    blocks = resp.get("Blocks", [])
    for b in blocks:
        if b.get("BlockType") == "LINE":
            text = b.get("Text", "")
            conf = b.get("Confidence", 0.0)
            print(f"text is \"{text}\"  | confidence = {conf:.2f}")

if __name__ == "__main__":
    main()

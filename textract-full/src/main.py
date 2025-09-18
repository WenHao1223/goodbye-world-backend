#!/usr/bin/env python3
"""
Textract Full - Combined CLI for Textract, Bedrock, and Blur Detection
"""

import argparse
import sys
import os
import json
from pathlib import Path
from datetime import datetime

from .textract_enhanced import run_textract
from .logger import log_print
from .bedrock_mapper import run_bedrock_extraction
from .blur_detection import run_blur_detection

def main():
    parser = argparse.ArgumentParser(description="Combined Textract, Bedrock, and Blur Detection CLI")
    parser.add_argument("--file", required=True, type=Path, help="Path to the input file")
    parser.add_argument("--mode", required=False, default="tfbq",
                        help="Analysis mode: t(ext), f(orms), b(tables), q(uery) - combine letters like tfbq")
    parser.add_argument("--category", required=False, default=None,
                        choices=["licence", "receipt", "idcard", "passport"],
                        help="Document category for queries and extraction")
    parser.add_argument("--queries", required=False, default=None,
                        help="Custom queries separated by semicolons (e.g., 'What is the name?;What is the date?')")
    parser.add_argument("--prompt", required=False, default=None,
                        help="Custom prompt for Bedrock AI extraction (overrides category-based prompts)")
    parser.add_argument("--region", required=False, default="us-east-1", help="AWS region")
    parser.add_argument("--profile", required=False, default=None, help="AWS profile name") # False to enable env var usage
    
    args = parser.parse_args()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Either category or queries is required for query mode
    if 'q' in args.mode and not args.category and not args.queries:
        raise SystemExit("[ERROR] Either --category or --queries is required for query mode")

    # Print parsed arguments
    log_print(f"[INFO] Using file: {args.file}")
    log_print(f"[INFO] Using mode: {args.mode}")
    log_print(f"[INFO] Document category: {args.category if args.category else 'N/A'}")
    log_print(f"[INFO] Custom queries: {args.queries if args.queries else 'N/A'}")
    log_print(f"[INFO] Using region: {args.region}")
    log_print(f"[INFO] Using profile: {args.profile if args.profile else 'default'}")

    try:
        # Step 1: Run Textract
        textract_results, log_subdir = run_textract(
            args.file, args.mode, args.category, args.region, args.profile, timestamp, args.queries
        )
        
        # Helper function to ensure JSON serialization
        def make_json_serializable(obj):
            if isinstance(obj, dict):
                return {k: make_json_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_json_serializable(item) for item in obj]
            elif isinstance(obj, bool):
                return bool(obj)  # Explicitly convert to JSON bool
            elif isinstance(obj, (int, float, str, type(None))):
                return obj
            else:
                return str(obj)  # Convert other types to string

        # Step 2: Run Blur Detection (only if text mode is enabled)
        if 't' in args.mode:
            text_data = textract_results.get('text', [])
            blur_results = run_blur_detection(str(args.file), text_data)

            # Save blur analysis results to JSON file
            json_safe_results = make_json_serializable(blur_results)
            blur_file = log_subdir / "blur_analysis.json"
            with open(blur_file, 'w') as f:
                json.dump(json_safe_results, f, indent=2)
        else:
            blur_results = {'overall_assessment': {'is_blurry': False}}
            # Save empty blur analysis for consistency
            json_safe_results = make_json_serializable(blur_results)
            blur_file = log_subdir / "blur_analysis.json"
            with open(blur_file, 'w') as f:
                json.dump(json_safe_results, f, indent=2)
        
        # Step 3: Run Bedrock Extraction (if category or custom prompt provided)
        if args.category or args.prompt:
            # Use current log content for bedrock processing
            from .logger import log_output
            textract_log = log_output.getvalue()

            # Use a default category if only custom prompt is provided
            category = args.category if args.category else "licence"

            extracted_data, output_file = run_bedrock_extraction(
                textract_log, category, args.region, args.profile, args.file.stem, timestamp, args.prompt
            )
        
        log_print("\n=== PROCESSING COMPLETE ===")
        log_print(f"[INFO] Textract results saved to: {log_subdir}")
        if args.category or args.prompt:
            log_print(f"[INFO] Extracted data saved to: {output_file}")
        
        # Summary
        if blur_results['overall_assessment']['is_blurry']:
            log_print("[WARN] Image appears to be blurry - results may be less accurate")
        else:
            log_print("[INFO] Image quality appears good")
        
        # Save complete log
        from .logger import log_output
        with open(log_subdir / "textract.log", "w") as f:
            f.write(log_output.getvalue())
            
    except SystemExit:
        # Save log on SystemExit
        from .logger import log_output
        file_name = args.file.stem
        log_subdir = Path("log") / f"{file_name}_{timestamp}"
        log_subdir.mkdir(parents=True, exist_ok=True)
        with open(log_subdir / "textract.log", "w") as f:
            f.write(log_output.getvalue())
        raise
    except Exception as e:
        log_print(f"[ERROR] Processing failed: {e}")
        
        # Save log even on error
        from .logger import log_output
        file_name = args.file.stem
        log_subdir = Path("log") / f"{file_name}_{timestamp}"
        log_subdir.mkdir(parents=True, exist_ok=True)
        with open(log_subdir / "textract.log", "w") as f:
            f.write(log_output.getvalue())
        
        sys.exit(1)

if __name__ == "__main__":
    main()
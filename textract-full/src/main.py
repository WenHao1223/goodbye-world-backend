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
from .category_detector import detect_document_category

def main():
    parser = argparse.ArgumentParser(description="Combined Textract, Bedrock, and Blur Detection CLI")
    parser.add_argument("--file", required=True, type=Path, help="Path to the input file")
    parser.add_argument("--mode", required=False, default="tfbq",
                        help="Analysis mode: t(ext), f(orms), b(tables), q(uery) - combine letters like tfbq")
    parser.add_argument("--category", required=False, default=None,
                        choices=["idcard", "license", "license-front", "license-back", "tnb", "receipt"],
                        help="Document category for queries and extraction (auto-detected if not provided)")
    parser.add_argument("--queries", required=False, default=None,
                        help="Custom queries separated by semicolons (e.g., 'What is the name?;What is the date?')")
    parser.add_argument("--prompt", required=False, default=None,
                        help="Custom prompt for Bedrock AI extraction (overrides category-based prompts)")
    parser.add_argument("--custom", required=False, default=False, action="store_true",
                        help="Use custom queries and prompts even if category has predefined ones")
    parser.add_argument("--region", required=False, default="us-east-1", help="AWS region")
    parser.add_argument("--profile", required=False, default=None, help="AWS profile name") # False to enable env var usage
    
    args = parser.parse_args()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # For query mode, we need either category (auto-detect if not provided) or custom queries
    if 'q' in args.mode and not args.queries:
        log_print("[INFO] Query mode enabled - will auto-detect category if not provided")

    # Print parsed arguments
    log_print(f"[INFO] Using file: {args.file}")
    log_print(f"[INFO] Using mode: {args.mode}")
    log_print(f"[INFO] Document category: {args.category if args.category else 'Auto-detect'}")
    log_print(f"[INFO] Custom queries: {args.queries if args.queries else 'N/A'}")
    log_print(f"[INFO] Custom mode: {args.custom}")
    log_print(f"[INFO] Using region: {args.region}")
    log_print(f"[INFO] Using profile: {args.profile if args.profile else 'default'}")

    try:
        # Step 1: Run initial Textract (without queries first for auto-detection)
        initial_mode = args.mode.replace('q', '')  # Remove query mode for initial run
        if not initial_mode:
            initial_mode = 'tfb'  # Default to text, forms, tables if only queries requested
        
        textract_results, log_subdir = run_textract(
            args.file, initial_mode, None, args.region, args.profile, timestamp, None
        )
        
        # Step 2: Auto-detect category if needed
        detected_category = None
        if 'q' in args.mode or args.prompt or (not args.category and not args.queries):
            if not args.category:
                detected_category, confidence = detect_document_category(
                    textract_results, args.region, args.profile
                )
                category_to_use = detected_category
                
                # Save detection results
                detection_results = {
                    "detected_category": detected_category,
                    "confidence": confidence,
                    "timestamp": timestamp
                }
                with open(log_subdir / "category_detection.json", 'w') as f:
                    json.dump(detection_results, f, indent=2)
            else:
                category_to_use = args.category
                log_print(f"[INFO] Using provided category: {category_to_use}")
        else:
            category_to_use = args.category
        
        # Step 3: Run queries if needed
        if 'q' in args.mode:
            query_results, _ = run_textract(
                args.file, 'q', category_to_use, args.region, args.profile, timestamp, 
                args.queries, args.custom
            )
            textract_results.update(query_results)
        
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

        # Step 4: Run Blur Detection (only if text mode is enabled)
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
        
        # Step 5: Run Bedrock Extraction (if category detected/provided or custom prompt provided)
        if category_to_use or args.prompt:
            # Use current log content for bedrock processing
            from .logger import log_output
            textract_log = log_output.getvalue()

            # Use detected/provided category or default
            category_for_bedrock = category_to_use if category_to_use else "license"

            extracted_data, output_file = run_bedrock_extraction(
                textract_log, category_for_bedrock, args.region, args.profile, 
                args.file.stem, timestamp, args.prompt, args.custom
            )
        
        log_print("\n=== PROCESSING COMPLETE ===")
        log_print(f"[INFO] Textract results saved to: {log_subdir}")
        if detected_category:
            log_print(f"[INFO] Auto-detected category: {detected_category}")
        if category_to_use or args.prompt:
            log_print(f"[INFO] Extracted data saved to: {output_file}")
        
        # Summary
        if blur_results['overall_assessment']['is_blurry']:
            log_print("[WARN] Image appears to be blurry - results may be less accurate")
        else:
            log_print("[INFO] Image quality appears good")
        
        if detected_category:
            log_print(f"[INFO] Document classified as: {detected_category}")
        
        # Save complete log with category info
        from .logger import log_output
        log_content = log_output.getvalue()
        if detected_category:
            log_content += f"\n\n=== CATEGORY DETECTION ===\nDetected: {detected_category}\n"
        with open(log_subdir / "textract.log", "w") as f:
            f.write(log_content)
            
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
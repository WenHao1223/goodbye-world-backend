#!/usr/bin/env python3
"""
Textract Full - Combined CLI for Textract, Bedrock, and Blur Detection
"""

import argparse
import sys
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
    parser.add_argument("--region", required=False, default="us-east-1", help="AWS region")
    parser.add_argument("--profile", required=True, default=None, help="AWS profile name")
    
    args = parser.parse_args()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Print parsed arguments
    log_print(f"[INFO] Using file: {args.file}")
    log_print(f"[INFO] Using mode: {args.mode}")
    log_print(f"[INFO] Document category: {args.category if args.category else 'N/A'}")
    log_print(f"[INFO] Using region: {args.region}")
    log_print(f"[INFO] Using profile: {args.profile if args.profile else 'default'}")

    try:
        # Step 1: Run Textract
        textract_results, log_subdir = run_textract(
            args.file, args.mode, args.category, args.region, args.profile, timestamp
        )
        
        # Step 2: Run Blur Detection (only if text mode is enabled)
        if 't' in args.mode:
            text_data = textract_results.get('text', [])
            blur_results = run_blur_detection(str(args.file), text_data)
        else:
            blur_results = {'overall_assessment': {'is_blurry': False}}
        
        # Step 3: Run Bedrock Extraction (if category is provided)
        if args.category:
            # Use current log content for bedrock processing
            from .logger import log_output
            textract_log = log_output.getvalue()
            
            extracted_data, output_file = run_bedrock_extraction(
                textract_log, args.category, args.region, args.profile, args.file.stem, timestamp
            )
        
        log_print("\n=== PROCESSING COMPLETE ===")
        log_print(f"[INFO] Textract results saved to: {log_subdir}")
        if args.category:
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
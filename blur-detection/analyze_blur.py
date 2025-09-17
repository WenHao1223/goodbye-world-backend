from blur_detection import BlurDetector, parse_textract_log
import argparse
import os
from datetime import datetime

def log_print(message, log_file_path):
    """Print to console and save to log file"""
    print(message)
    with open(log_file_path, 'a', encoding='utf-8') as f:
        f.write(message + '\n')

def read_textract_log(file_path):
    """Read Textract log file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Textract log file not found: {file_path}")
    except Exception as e:
        raise Exception(f"Error reading file {file_path}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Analyze Textract results for blur detection')
    parser.add_argument('--file', required=True, help='Path to Textract log file')
    args = parser.parse_args()
    
    # Setup log file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_dir = 'log'
    os.makedirs(log_dir, exist_ok=True)
    
    input_filename = os.path.splitext(os.path.basename(args.file))[0]
    log_file_path = os.path.join(log_dir, f'{input_filename}_blur_analysis_{timestamp}.log')
    
    detector = BlurDetector()
    
    try:
        # Read Textract log file
        textract_log_content = read_textract_log(args.file)
        
        # Parse Textract results
        textract_data = parse_textract_log(textract_log_content)
        
        if not textract_data:
            log_print("No Textract data found in the log file", log_file_path)
            return
        
        # Analyze confidence
        analysis = detector.analyze_textract_confidence(textract_data)
        
        log_print(f"[INFO] Analyzing file: {args.file}", log_file_path)
        log_print("=== BLUR ANALYSIS ===\n", log_file_path)
        
        log_print(f"Total text items detected: {analysis['total_items']}", log_file_path)
        log_print(f"Confidence range: {analysis['min_confidence']:.2f}% - {analysis['max_confidence']:.2f}%", log_file_path)
        log_print(f"Median confidence: {analysis['median_confidence']:.2f}%", log_file_path)
        log_print(f"Weighted average: {analysis['weighted_average']:.2f}%", log_file_path)
        log_print(f"Low confidence items: {analysis['low_confidence_count']} ({analysis['low_confidence_percentage']:.1f}%)", log_file_path)
        log_print(f"Quality assessment: {analysis['quality_assessment'].upper()}", log_file_path)
        log_print(f"Likely blurry: {'YES' if analysis['likely_blurry'] else 'NO'}", log_file_path)
        
        log_print("\n=== DETAILED BREAKDOWN ===", log_file_path)
        
        # Show items with lower confidence
        low_conf_items = [item for item in textract_data if item['confidence'] < 99.0]
        if low_conf_items:
            log_print("\nItems with confidence < 99%:", log_file_path)
            for item in sorted(low_conf_items, key=lambda x: x['confidence']):
                log_print(f"  {item['confidence']:.2f}% - '{item['text']}'", log_file_path)
        else:
            log_print("\nAll items have confidence >= 99%", log_file_path)
        
        log_print(f"\n=== RECOMMENDATION ===", log_file_path)
        if analysis['likely_blurry']:
            log_print("⚠️  Image may be blurry - consider retaking", log_file_path)
        else:
            log_print("✅ Image quality appears good based on confidence scores", log_file_path)
            
        log_print(f"\n[INFO] Analysis complete. Log saved to: {log_file_path}", log_file_path)
        
    except Exception as e:
        log_print(f"[ERROR] {str(e)}", log_file_path)

if __name__ == "__main__":
    main()
from blur_detection import BlurDetector, parse_textract_log
import json

# Your actual Textract results
textract_log = """
text = "LESEN HICMAND"  | confidence = 36.07
text = "."  | confidence = 55.19
text = "license"  | confidence = 24.38
text = "MALAYSIA"  | confidence = 99.92
text = "BERKUATKUAI"  | confidence = 67.64
text = "LIM WEN HAD"  | confidence = 82.15
text = "- - - -"  | confidence = 79.10
text = "I 1 I"  | confidence = 60.67
text = "-"  | confidence = 51.04
text = "25/32004"  | confidence = 17.78
text = "I |"  | confidence = 69.07
text = "- -"  | confidence = 92.15
text = "82 DA"  | confidence = 21.73
text = "I I"  | confidence = 69.10
text = "- -"  | confidence = 35.79
text = "- -"  | confidence = 87.33
text = "NO.36. K."  | confidence = 23.91
text = "CORONG SEPULING COADE"  | confidence = 33.95
text = "- - . -"  | confidence = 68.97
text = "- - -"  | confidence = 78.07
text = "AMAN SCRULING -"  | confidence = 47.20
text = "-"  | confidence = 77.64
text = "-"  | confidence = 50.57
text = "PULALIPINAMS"  | confidence = 16.21
text = "I"  | confidence = 81.57
text = "-"  | confidence = 49.75
text = "KELAS LASSE MEMANDO"  | confidence = 28.77
text = "- - -"  | confidence = 79.11
text = "-"  | confidence = 72.47
text = "2"  | confidence = 72.82
text = "-"  | confidence = 60.76
text = "I"  | confidence = 49.11
text = "-"  | confidence = 84.44
text = "-"  | confidence = 82.11
text = "1"  | confidence = 27.05
text = "&"  | confidence = 24.41
text = "all"  | confidence = 85.05
text = "."  | confidence = 25.49
text = "4"  | confidence = 84.73
"""

def main():
    detector = BlurDetector()
    
    # Parse Textract results
    textract_data = parse_textract_log(textract_log)
    
    # Analyze confidence
    analysis = detector.analyze_textract_confidence(textract_data)
    
    print("=== BLUR ANALYSIS FOR YOUR BANK RECEIPT ===\n")
    
    print(f"Total text items detected: {analysis['total_items']}")
    print(f"Confidence range: {analysis['min_confidence']:.2f}% - {analysis['max_confidence']:.2f}%")
    print(f"Median confidence: {analysis['median_confidence']:.2f}%")
    print(f"Weighted average: {analysis['weighted_average']:.2f}%")
    print(f"Low confidence items: {analysis['low_confidence_count']} ({analysis['low_confidence_percentage']:.1f}%)")
    print(f"Quality assessment: {analysis['quality_assessment'].upper()}")
    print(f"Likely blurry: {'YES' if analysis['likely_blurry'] else 'NO'}")
    
    print("\n=== DETAILED BREAKDOWN ===")
    
    # Show items with lower confidence
    low_conf_items = [item for item in textract_data if item['confidence'] < 99.0]
    if low_conf_items:
        print("\nItems with confidence < 99%:")
        for item in sorted(low_conf_items, key=lambda x: x['confidence']):
            print(f"  {item['confidence']:.2f}% - '{item['text']}'")
    
    print(f"\n=== RECOMMENDATION ===")
    if analysis['likely_blurry']:
        print("⚠️  Image may be blurry - consider retaking")
    else:
        print("✅ Image quality appears good based on confidence scores")

if __name__ == "__main__":
    main()
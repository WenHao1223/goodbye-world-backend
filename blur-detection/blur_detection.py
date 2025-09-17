import cv2
import numpy as np
from typing import Dict, List, Tuple
import json

class BlurDetector:
    def __init__(self):
        self.confidence_threshold = 95.0  # Below this is considered low confidence
        self.laplacian_threshold = 100.0  # Below this is considered blurry
        
    def detect_blur_laplacian(self, image_path: str) -> Dict:
        """Detect blur using Laplacian variance method"""
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate Laplacian variance
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        return {
            'method': 'laplacian',
            'score': laplacian_var,
            'is_blurry': laplacian_var < self.laplacian_threshold,
            'quality': 'sharp' if laplacian_var > 200 else 'moderate' if laplacian_var > 100 else 'blurry'
        }
    
    def detect_blur_sobel(self, image_path: str) -> Dict:
        """Detect blur using Sobel edge detection"""
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate Sobel gradients
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        
        # Calculate magnitude
        magnitude = np.sqrt(sobelx**2 + sobely**2)
        sobel_mean = np.mean(magnitude)
        
        return {
            'method': 'sobel',
            'score': sobel_mean,
            'is_blurry': sobel_mean < 50,
            'quality': 'sharp' if sobel_mean > 80 else 'moderate' if sobel_mean > 50 else 'blurry'
        }
    
    def analyze_textract_confidence(self, textract_results: List[Dict]) -> Dict:
        """Analyze Textract confidence scores for blur indication"""
        confidences = [item['confidence'] for item in textract_results]
        
        # Calculate statistics
        min_conf = min(confidences)
        max_conf = max(confidences)
        median_conf = np.median(confidences)
        
        # Count low confidence items
        low_conf_count = sum(1 for c in confidences if c < self.confidence_threshold)
        low_conf_percentage = (low_conf_count / len(confidences)) * 100
        
        # Calculate weighted confidence (give more weight to lower scores)
        weights = [1/c if c > 0 else 1 for c in confidences]
        weighted_avg = np.average(confidences, weights=weights)
        
        return {
            'total_items': len(confidences),
            'min_confidence': min_conf,
            'max_confidence': max_conf,
            'median_confidence': median_conf,
            'weighted_average': weighted_avg,
            'low_confidence_count': low_conf_count,
            'low_confidence_percentage': low_conf_percentage,
            'likely_blurry': low_conf_percentage > 20 or min_conf < 90,
            'quality_assessment': self._assess_quality_from_confidence(median_conf, low_conf_percentage)
        }
    
    def _assess_quality_from_confidence(self, median_conf: float, low_conf_pct: float) -> str:
        """Assess image quality based on confidence metrics"""
        if median_conf > 99 and low_conf_pct < 5:
            return 'excellent'
        elif median_conf > 97 and low_conf_pct < 15:
            return 'good'
        elif median_conf > 95 and low_conf_pct < 25:
            return 'moderate'
        else:
            return 'poor'
    
    def comprehensive_blur_check(self, image_path: str, textract_results: List[Dict] = None) -> Dict:
        """Combine multiple methods for comprehensive blur detection"""
        results = {}
        
        # Image-based detection
        try:
            results['laplacian'] = self.detect_blur_laplacian(image_path)
            results['sobel'] = self.detect_blur_sobel(image_path)
        except Exception as e:
            results['image_analysis_error'] = str(e)
        
        # Textract confidence analysis
        if textract_results:
            results['textract_analysis'] = self.analyze_textract_confidence(textract_results)
        
        # Overall assessment
        blur_indicators = []
        if 'laplacian' in results and results['laplacian']['is_blurry']:
            blur_indicators.append('laplacian')
        if 'sobel' in results and results['sobel']['is_blurry']:
            blur_indicators.append('sobel')
        if 'textract_analysis' in results and results['textract_analysis']['likely_blurry']:
            blur_indicators.append('textract')
        
        results['overall_assessment'] = {
            'is_blurry': len(blur_indicators) >= 2,
            'blur_indicators': blur_indicators,
            'confidence_level': 'high' if len(blur_indicators) >= 2 else 'medium' if len(blur_indicators) == 1 else 'low'
        }
        
        return results

# Example usage with your Textract data
def parse_textract_log(log_content: str) -> List[Dict]:
    """Parse Textract log to extract text and confidence pairs"""
    results = []
    lines = log_content.split('\n')
    
    for line in lines:
        if 'text =' in line and 'confidence =' in line:
            # Extract text and confidence
            parts = line.split('|')
            if len(parts) >= 2:
                text_part = parts[0].strip()
                conf_part = parts[1].strip()
                
                # Extract confidence value
                if 'confidence =' in conf_part:
                    try:
                        confidence = float(conf_part.split('=')[1].strip())
                        text = text_part.split('=')[1].strip().strip('"')
                        results.append({'text': text, 'confidence': confidence})
                    except:
                        continue
    
    return results

if __name__ == "__main__":
    # Example with your data
    detector = BlurDetector()
    
    # Parse your Textract results
    log_content = """
text = "Maybank"  | confidence = 99.89
text = "DuitNow Transfer"  | confidence = 99.91
text = "Successful"  | confidence = 99.95
text = "Reference ID"  | confidence = 99.96
text = "15 Sep 2025, 3:13 PM"  | confidence = 99.75
text = "837356732M"  | confidence = 99.15
text = "Beneficiary name"  | confidence = 99.98
text = "DELLAND PROPERTY MANAGEMENT SDN BHD"  | confidence = 99.97
text = "Beneficiary account number"  | confidence = 99.99
text = "8881 0134 2238 3"  | confidence = 98.05
text = "Receiving bank"  | confidence = 100.00
text = "AmBANK BERHAD"  | confidence = 99.61
text = "Recipient reference"  | confidence = 99.89
text = "0488-MB-MAYBANK22/43"  | confidence = 98.99
text = "Payment details"  | confidence = 99.96
text = "0488-MB LimChoonHeng"  | confidence = 99.44
text = "Amount"  | confidence = 100.00
text = "RM 100.00"  | confidence = 99.63
"""
    
    textract_data = parse_textract_log(log_content)
    confidence_analysis = detector.analyze_textract_confidence(textract_data)
    
    print("Textract Confidence Analysis:")
    print(json.dumps(confidence_analysis, indent=2))
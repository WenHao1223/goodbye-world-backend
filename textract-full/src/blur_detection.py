import cv2
import numpy as np
from typing import Dict, List
import json

class BlurDetector:
    def __init__(self):
        self.confidence_threshold = 95.0
        self.laplacian_threshold = 100.0
        
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
    
    def analyze_textract_confidence(self, textract_results: List[Dict]) -> Dict:
        """Analyze Textract confidence scores for blur indication"""
        confidences = [item['confidence'] for item in textract_results]
        
        # Calculate statistics
        min_conf = min(confidences)
        max_conf = max(confidences)
        median_conf = np.median(confidences)
        
        # Filter extreme outliers and calculate average of remaining
        q1, q3 = np.percentile(confidences, [25, 75])
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        filtered_confidences = [c for c in confidences if lower_bound <= c <= upper_bound]
        avg_conf = np.mean(filtered_confidences) if filtered_confidences else median_conf
        std_conf = np.std(confidences)
        
        # Count low confidence items
        low_conf_count = sum(1 for c in confidences if c < self.confidence_threshold)
        low_conf_percentage = (low_conf_count / len(confidences)) * 100
        
        return {
            'total_items': len(confidences),
            'min_confidence': min_conf,
            'max_confidence': max_conf,
            'median_confidence': median_conf,
            'average_confidence': avg_conf,
            'std_confidence': std_conf,
            'low_confidence_count': low_conf_count,
            'low_confidence_percentage': low_conf_percentage,
            'likely_blurry': median_conf < 85 and avg_conf < 90,
            'quality_assessment': self._assess_quality_from_confidence(median_conf, avg_conf, std_conf)
        }
    
    def _assess_quality_from_confidence(self, median_conf: float, avg_conf: float, std_conf: float) -> str:
        """Assess image quality based on median, average, and standard deviation"""
        # High std indicates inconsistent quality (some very low confidence items)
        if median_conf > 98 and avg_conf > 95 and std_conf < 10:
            return 'excellent'
        elif median_conf > 95 and avg_conf > 90 and std_conf < 15:
            return 'good'
        elif median_conf > 90 and avg_conf > 85 and std_conf < 20:
            return 'moderate'
        else:
            return 'poor'
    
    def comprehensive_blur_check(self, image_path: str, textract_results: List[Dict] = None) -> Dict:
        """Combine multiple methods for comprehensive blur detection"""
        results = {}
        
        # Image-based detection
        try:
            results['laplacian'] = self.detect_blur_laplacian(image_path)
        except Exception as e:
            results['image_analysis_error'] = str(e)
        
        # Textract confidence analysis
        if textract_results:
            results['textract_analysis'] = self.analyze_textract_confidence(textract_results)
        
        # Overall assessment
        blur_indicators = []
        if 'laplacian' in results and results['laplacian']['is_blurry']:
            blur_indicators.append('laplacian')
        if 'textract_analysis' in results and results['textract_analysis']['likely_blurry']:
            blur_indicators.append('textract')
        
        # Determine blur status and confidence level
        is_blurry = False
        confidence_level = 'low'
        
        if 'textract_analysis' in results:
            ta = results['textract_analysis']
            quality = ta['quality_assessment']
            std_conf = ta['std_confidence']
            
            # Determine blur status
            if quality in ['excellent', 'good']:
                is_blurry = False
            elif quality == 'moderate':
                is_blurry = False
            else:  # poor quality
                is_blurry = True
            
            # Confidence level based on standard deviation (consistency)
            if std_conf < 5:  # Very consistent
                confidence_level = 'high'
            elif std_conf < 15:  # Moderately consistent
                confidence_level = 'high' if quality in ['excellent', 'poor'] else 'medium'
            elif std_conf < 25:  # Inconsistent
                confidence_level = 'medium'
            else:  # Very inconsistent (like half-blur)
                confidence_level = 'low'
        
        # Laplacian as secondary indicator only if no textract data
        elif 'laplacian' in blur_indicators:
            is_blurry = True
            confidence_level = 'medium'
        
        results['overall_assessment'] = {
            'is_blurry': is_blurry,
            'blur_indicators': blur_indicators,
            'confidence_level': confidence_level
        }
        
        return results

def run_blur_detection(image_path: str, textract_results: List[Dict] = None):
    from .logger import log_print
    
    detector = BlurDetector()
    blur_analysis = detector.comprehensive_blur_check(image_path, textract_results)
    
    log_print("\n=== BLUR DETECTION ===")
    
    # Print results without JSON serialization
    if 'laplacian' in blur_analysis:
        lap = blur_analysis['laplacian']
        log_print(f"Laplacian score: {lap['score']:.2f} - Quality: {lap['quality']}")
    
    if 'textract_analysis' in blur_analysis:
        ta = blur_analysis['textract_analysis']
        log_print(f"Textract confidence - Median: {ta['median_confidence']:.2f}, Avg: {ta['average_confidence']:.2f}, Std: {ta['std_confidence']:.2f}")
        log_print(f"Quality assessment: {ta['quality_assessment']}")
    
    overall = blur_analysis['overall_assessment']
    log_print(f"Overall: {'BLURRY' if overall['is_blurry'] else 'CLEAR'} (confidence: {overall['confidence_level']})")
    
    return blur_analysis
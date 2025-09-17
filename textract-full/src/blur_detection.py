try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    cv2 = None
    np = None

from typing import Dict, List
import json
import os

class BlurDetector:
    def __init__(self):
        self.confidence_threshold = 95.0
        self.laplacian_threshold = 100.0
        
    def detect_blur_laplacian(self, image_path: str) -> Dict:
        """Detect blur using Laplacian variance method"""
        if not OPENCV_AVAILABLE:
            return {
                'method': 'laplacian',
                'score': 150.0,  # Assume good quality
                'is_blurry': False,
                'quality': 'good'
            }

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
        
        # Optimized blur detection logic
        likely_blurry = (
            # Very low median confidence (most text unreadable)
            median_conf < 80.0 or
            # Very low average confidence (overall poor quality)
            avg_conf < 75.0 or
            # High percentage of very low confidence items (>50% below 85%)
            low_conf_percentage > 50.0 or
            # Extremely high standard deviation with low median (inconsistent + poor)
            (std_conf > 20.0 and median_conf < 85.0)
        )

        return {
            'total_items': len(confidences),
            'min_confidence': min_conf,
            'max_confidence': max_conf,
            'median_confidence': median_conf,
            'average_confidence': avg_conf,
            'std_confidence': std_conf,
            'low_confidence_count': low_conf_count,
            'low_confidence_percentage': low_conf_percentage,
            'likely_blurry': likely_blurry,
            'quality_assessment': self._assess_quality_from_confidence(median_conf, avg_conf, std_conf)
        }
    
    def _assess_quality_from_confidence(self, median_conf: float, avg_conf: float, std_conf: float) -> str:
        """Assess image quality based on median, average, and standard deviation"""
        # Calculate low confidence percentage for better assessment
        if median_conf > 95.0 and avg_conf > 90.0:
            return 'excellent'
        elif median_conf > 90.0 and avg_conf > 85.0:
            return 'good'
        elif median_conf > 85.0 and avg_conf > 80.0:
            return 'fair'
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

    # Check if OpenCV is available
    if not OPENCV_AVAILABLE:
        log_print("\n=== BLUR DETECTION ===")
        log_print("OpenCV not available - using Textract confidence analysis only")

        # Fallback to Textract confidence analysis only
        if textract_results:
            confidences = [item.get('confidence', 0) for item in textract_results]
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                median_confidence = sorted(confidences)[len(confidences) // 2]

                # Calculate standard deviation
                variance = sum((x - avg_confidence) ** 2 for x in confidences) / len(confidences)
                std_confidence = variance ** 0.5

                # Optimized blur detection algorithm
                # Focus on median confidence (more robust) and low confidence percentage
                low_confidence_threshold = 85.0  # Lowered from 90.0
                low_confidence_count = sum(1 for c in confidences if c < low_confidence_threshold)
                low_confidence_percentage = (low_confidence_count / len(confidences)) * 100

                # More sophisticated blur detection
                is_blurry = (
                    # Very low median confidence (most text unreadable)
                    median_confidence < 80.0 or
                    # Very low average confidence (overall poor quality)
                    avg_confidence < 75.0 or
                    # High percentage of very low confidence items (>50% below 85%)
                    low_confidence_percentage > 50.0 or
                    # Extremely high standard deviation with low median (inconsistent + poor)
                    (std_confidence > 20.0 and median_confidence < 85.0)
                )

                # Determine confidence level and quality assessment
                if median_confidence > 95.0 and avg_confidence > 90.0 and low_confidence_percentage < 20.0:
                    confidence_level = "high"
                    quality_assessment = "excellent"
                elif median_confidence > 90.0 and avg_confidence > 85.0 and low_confidence_percentage < 35.0:
                    confidence_level = "high"
                    quality_assessment = "good"
                elif median_confidence > 85.0 and avg_confidence > 80.0 and low_confidence_percentage < 50.0:
                    confidence_level = "medium"
                    quality_assessment = "fair"
                else:
                    confidence_level = "low"
                    quality_assessment = "poor"

                log_print(f"Textract confidence - Median: {median_confidence:.2f}, Avg: {avg_confidence:.2f}, Std: {std_confidence:.2f}")
                log_print(f"Quality assessment: {quality_assessment}")
                log_print(f"Overall: {'BLURRY' if is_blurry else 'CLEAR'} (confidence: {confidence_level})")

                # Calculate additional Textract analysis metrics to match local version
                min_confidence = min(confidences)
                max_confidence = max(confidences)
                # Use the same threshold as in the blur detection logic
                likely_blurry = is_blurry

                return {
                    'laplacian': {
                        'method': 'laplacian',
                        'score': 150.0,  # Default score when OpenCV not available # 0.0+
                        'is_blurry': False,  # Assume not blurry from Laplacian perspective # boolean
                        'quality': 'good' # sharp, moderate, blurry
                    },
                    'textract_analysis': {
                        'total_items': len(confidences),
                        'min_confidence': min_confidence, # 0.0 - 100.0
                        'max_confidence': max_confidence, # 0.0 - 100.0
                        'median_confidence': median_confidence, # 0.0 - 100.0
                        'average_confidence': avg_confidence, # 0.0 - 100.0
                        'std_confidence': std_confidence, # 0.0+
                        'low_confidence_count': low_confidence_count, # int
                        'low_confidence_percentage': low_confidence_percentage, # 0.0 - 100.0
                        'likely_blurry': likely_blurry, # boolean
                        'quality_assessment': quality_assessment # excellent, good, fair, poor
                    },
                    'overall_assessment': {
                        'is_blurry': is_blurry, # boolean
                        'blur_indicators': ['textract'] if is_blurry else [], # Shows which detection methods identified the image as blurry, array that can contain "textract", "laplacian"
                        'confidence_level': confidence_level # high, medium, low
                    }
                }

        # Default fallback
        log_print("No Textract results available - assuming good quality")
        return {
            'laplacian': {
                'method': 'laplacian',
                'score': 150.0,  # Default score when OpenCV not available
                'is_blurry': False,
                'quality': 'good'
            },
            'textract_analysis': {
                'total_items': 0,
                'min_confidence': 0,
                'max_confidence': 0,
                'median_confidence': 0,
                'average_confidence': 0,
                'std_confidence': 0,
                'low_confidence_count': 0,
                'low_confidence_percentage': 0,
                'likely_blurry': False,
                'quality_assessment': 'unknown'
            },
            'overall_assessment': {
                'is_blurry': False,
                'blur_indicators': [],
                'confidence_level': 'low'
            }
        }

    # Full blur detection with OpenCV
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
#!/usr/bin/env python3
"""
Test script for auto-detection functionality
"""

import subprocess
import sys
from pathlib import Path

def test_auto_detection():
    """Test the auto-detection functionality"""
    
    # Test files (assuming they exist in media directory)
    test_files = [
        "media/licence.jpeg",
        # Add other test files as available
    ]
    
    for file_path in test_files:
        if not Path(file_path).exists():
            print(f"Skipping {file_path} - file not found")
            continue
            
        print(f"\n{'='*50}")
        print(f"Testing auto-detection with: {file_path}")
        print(f"{'='*50}")
        
        # Test 1: Auto-detection mode
        print("\n1. Testing auto-detection (no category specified):")
        cmd = ["uv", "run", "python", "cli.py", "--file", file_path, "--mode", "tfbq"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                print("✅ Auto-detection successful")
                # Look for detection results in output
                if "Auto-detected category:" in result.stdout:
                    print("✅ Category detection working")
                else:
                    print("⚠️  Category detection output not found")
            else:
                print(f"❌ Auto-detection failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("❌ Auto-detection timed out")
        except Exception as e:
            print(f"❌ Auto-detection error: {e}")
        
        # Test 2: Custom mode
        print("\n2. Testing custom mode:")
        cmd = ["uv", "run", "python", "cli.py", "--file", file_path, "--mode", "q", 
               "--custom", "--queries", "What is the document type?;What is the main text?"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                print("✅ Custom mode successful")
            else:
                print(f"❌ Custom mode failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("❌ Custom mode timed out")
        except Exception as e:
            print(f"❌ Custom mode error: {e}")

if __name__ == "__main__":
    print("Testing Auto-Detection Functionality")
    print("====================================")
    test_auto_detection()
    print("\nTest completed!")
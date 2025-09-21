#!/usr/bin/env python3
"""
Auto-monitoring AWS Transcribe test - waits until completion without user input
"""

import json
import requests
import time
import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# New us-east-1 endpoints from .env
TRANSCRIBE_API_URL = os.getenv('TRANSCRIBE_API_URL')
TRANSCRIBE_HEALTH_API_URL = os.getenv('TRANSCRIBE_HEALTH_API_URL')
TRANSCRIBE_STATUS_API_URL = os.getenv('TRANSCRIBE_STATUS_API_URL')

def generate_transcript_download_url(transcript_uri):
    """Generate a signed downloadable URL for transcript file"""
    try:
        # Extract bucket and key from S3 URI
        if 's3.us-east-1.amazonaws.com/' in transcript_uri:
            # Format: https://s3.us-east-1.amazonaws.com/bucket-name/file-key
            parts = transcript_uri.replace('https://s3.us-east-1.amazonaws.com/', '').split('/', 1)
            bucket_name = parts[0]
            object_key = parts[1] if len(parts) > 1 else ''
        else:
            print(f"❓ Unexpected S3 URI format: {transcript_uri}")
            return None
        
        print(f"🔗 Generating signed download URL...")
        print(f"   📦 Bucket: {bucket_name}")
        print(f"   📄 File: {object_key}")
        
        # Create S3 client
        s3_client = boto3.client('s3', region_name='us-east-1')
        
        # Generate presigned URL (valid for 1 hour)
        signed_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_key},
            ExpiresIn=3600
        )
        
        return signed_url
        
    except NoCredentialsError:
        print("❌ AWS credentials not found! Cannot generate signed URL.")
        return None
    except ClientError as e:
        print(f"❌ AWS Error generating signed URL: {e}")
        return None
    except Exception as e:
        print(f"💥 Error generating signed URL: {e}")
        return None

def test_health():
    """Test health endpoint"""
    print("🏥 Testing Health Endpoint")
    print("=" * 40)
    
    try:
        response = requests.get(TRANSCRIBE_HEALTH_API_URL, timeout=30)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check Successful!")
            print(f"📄 Response:")
            print(json.dumps(data, indent=2))
            return True
        else:
            print(f"❌ Health check failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Error: {e}")
        return False

def test_transcribe():
    """Test transcription with your S3 file"""
    print("\n🎤 Testing Transcription")
    print("=" * 40)
    
    # Your S3 file - using clean S3 URL (AWS Transcribe cannot use signed URLs)
    s3_url = "https://great-ai-hackathon-uploads-dev.s3.us-east-1.amazonaws.com/sample-audio.m4a"
    
    print(f"📁 S3 URL: {s3_url}")
    print(f"🌐 API URL: {TRANSCRIBE_API_URL}")
    
    payload = {
        "url": s3_url,
        "language": "en-us"
    }
    
    try:
        print(f"\n📡 Starting transcription...")
        response = requests.post(
            TRANSCRIBE_API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Transcription job started successfully!")
            print(f"📄 Response:")
            print(json.dumps(data, indent=2))
            
            job_name = data.get('data', {}).get('job_name')
            if job_name:
                print(f"\n🏷️ Job Name: {job_name}")
                return job_name
            
        else:
            print(f"❌ Transcription failed:")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Error: {e}")
    
    return None

def monitor_job_until_complete(job_name, check_interval=15, max_wait_minutes=10):
    """Monitor a job until completion with automatic polling"""
    print(f"\n🔄 Auto-monitoring job: {job_name}")
    print(f"⏱️ Check interval: {check_interval} seconds")
    print(f"⏰ Max wait time: {max_wait_minutes} minutes")
    print("=" * 50)
    
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    check_count = 0
    
    while True:
        check_count += 1
        elapsed = time.time() - start_time
        
        print(f"\n🔍 Check #{check_count} (elapsed: {elapsed:.0f}s)")
        
        # Check if we've exceeded max wait time
        if elapsed > max_wait_seconds:
            print(f"\n⏰ Timeout reached ({max_wait_minutes} minutes)")
            print(f"💡 Job may still be processing - check manually later")
            break
        
        # Check job status
        try:
            status_url = f"{TRANSCRIBE_STATUS_API_URL}?job_name={job_name}"
            response = requests.get(status_url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                job_data = data.get('data', {})
                status = job_data.get('status', 'Unknown')
                
                print(f"📈 Status: {status}")
                
                if status == 'COMPLETED':
                    print(f"\n🎉 Transcription completed!")
                    transcript = job_data.get('transcript')
                    transcript_uri = job_data.get('transcript_uri')
                    
                    if transcript and not transcript.startswith('Error'):
                        print(f"📜 Transcript: {transcript}")
                    else:
                        print(f"📜 Transcript: {transcript}")
                        if transcript and transcript.startswith('Error') and '403' in transcript:
                            print(f"💡 403 Forbidden error detected - generating downloadable URL...")
                            
                            if transcript_uri:
                                signed_url = generate_transcript_download_url(transcript_uri)
                                if signed_url:
                                    print(f"✅ Downloadable URL generated (valid for 1 hour):")
                                    print(f"🌐 {signed_url}")
                                    print(f"💡 You can:")
                                    print(f"   - Copy this URL into your browser")
                                    print(f"   - Use curl: curl -o transcript.json '{signed_url}'")
                                else:
                                    print(f"❌ Failed to generate signed URL")
                        elif transcript and transcript.startswith('Error'):
                            print(f"💡 Note: There may be a permissions issue reading the transcript file")
                    
                    completion_time = job_data.get('completion_time')
                    if completion_time:
                        print(f"⏱️ Completed at: {completion_time}")
                    
                    if transcript_uri:
                        print(f"🔗 Transcript file: {transcript_uri}")
                    
                    total_time = time.time() - start_time
                    print(f"🕐 Total processing time: {total_time:.0f} seconds")
                    break
                    
                elif status == 'FAILED':
                    print(f"\n❌ Transcription failed!")
                    failure_reason = job_data.get('failure_reason', 'Unknown')
                    print(f"💥 Reason: {failure_reason}")
                    break
                    
                elif status == 'IN_PROGRESS':
                    print(f"⏳ Still processing...")
                    
                else:
                    print(f"❓ Unknown status: {status}")
            else:
                print(f"❌ Status check failed: {response.status_code}")
                
        except Exception as e:
            print(f"💥 Error checking status: {e}")
        
        # Wait before next check
        print(f"😴 Waiting {check_interval} seconds before next check...")
        time.sleep(check_interval)

def main():
    print("🚀 AWS Transcribe Auto-Monitor Test")
    print("=" * 60)
    
    # Test health
    health_ok = test_health()
    
    if health_ok:
        # Test transcription
        job_name = test_transcribe()
        
        if job_name:
            print(f"\n🎯 Job started successfully!")
            print(f"⏳ Monitoring job until completion (no user input required)...")
            
            # Automatically monitor until completion
            monitor_job_until_complete(job_name)
        else:
            print(f"\n❌ Failed to start transcription job")
    else:
        print(f"\n❌ Health check failed - cannot proceed with transcription test")

if __name__ == "__main__":
    main()
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
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# New us-east-1 endpoints from .env
TRANSCRIBE_API_URL = os.getenv('TRANSCRIBE_API_URL')
TRANSCRIBE_HEALTH_API_URL = os.getenv('TRANSCRIBE_HEALTH_API_URL')
TRANSCRIBE_STATUS_API_URL = os.getenv('TRANSCRIBE_STATUS_API_URL')
PROCESS_URL_API_URL = os.getenv('PROCESS_URL_API_URL')

def ensure_output_folder():
    """Create output folder if it doesn't exist"""
    output_folder = "output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"📁 Created output folder: {output_folder}")
    return output_folder

def save_final_output(data, job_name, language="", result_type="transcription"):
    """Save final output to output folder with timestamp"""
    try:
        output_folder = ensure_output_folder()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if language:
            filename = f"{job_name}_{language}_{result_type}_{timestamp}.json"
        else:
            filename = f"{job_name}_{result_type}_{timestamp}.json"
            
        filepath = os.path.join(output_folder, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved final output to: {filepath}")
        return filepath
    except Exception as e:
        print(f"❌ Error saving output: {e}")
        return None

def download_transcript_json(transcript_uri, job_name):
    """Download the full transcript JSON from S3 and save locally"""
    try:
        if not transcript_uri:
            print(f"❌ No transcript URI provided")
            return None
            
        print(f"🔗 Transcript URI: {transcript_uri}")
        
        # Try to get signed URL first
        signed_url = generate_transcript_download_url(transcript_uri)
        if not signed_url:
            print(f"❌ Could not generate signed URL")
            return None
        
        # Download using signed URL
        print(f"📥 Downloading transcript JSON...")
        response = requests.get(signed_url, timeout=30)
        
        if response.status_code == 200:
            transcript_data = response.json()
            
            # Save the full transcript JSON to output folder
            output_folder = ensure_output_folder()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{job_name}_full_transcript_{timestamp}.json"
            filepath = os.path.join(output_folder, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Full transcript JSON saved to: {filepath}")
            
            # Extract and display key information
            if 'results' in transcript_data:
                results = transcript_data['results']
                if 'transcripts' in results and results['transcripts']:
                    full_transcript = results['transcripts'][0].get('transcript', '')
                    print(f"📝 Full Transcript Text:")
                    print(f"   {full_transcript}")
                
                # Show confidence and timing info
                if 'items' in results:
                    total_items = len(results['items'])
                    print(f"📊 Transcript Details:")
                    print(f"   Total words/items: {total_items}")
                    
                    # Calculate average confidence
                    confidences = []
                    for item in results['items']:
                        if 'alternatives' in item and item['alternatives']:
                            conf = item['alternatives'][0].get('confidence')
                            if conf and conf != '0.0':
                                confidences.append(float(conf))
                    
                    if confidences:
                        avg_confidence = sum(confidences) / len(confidences)
                        print(f"   Average confidence: {avg_confidence:.3f}")
                    
                    # Show speaker info if available
                    if 'speaker_labels' in results:
                        speakers = results['speaker_labels'].get('speakers', 0)
                        print(f"   Detected speakers: {speakers}")
            
            return filepath
            
        else:
            print(f"❌ Failed to download transcript: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"💥 Error downloading transcript JSON: {e}")
        return None

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

def test_transcribe_multi_language(s3_url, languages=None):
    """Test transcription with multiple languages simultaneously"""
    if languages is None:
        languages = ["en-us", "zh-cn", "ms-my", "id-id"]
    
    print(f"\n🌍 Testing Multi-Language Transcription")
    print("=" * 50)
    print(f"📁 S3 URL: {s3_url}")
    print(f"🌐 Languages: {', '.join(languages)}")
    print(f"🔄 Starting {len(languages)} transcription jobs...")
    
    jobs = {}
    
    # Start transcription jobs for each language
    for language in languages:
        print(f"\n🚀 Starting transcription for {language}...")
        
        payload = {
            "url": s3_url,
            "language": language
        }
        
        try:
            response = requests.post(
                TRANSCRIBE_API_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                job_name = data.get('data', {}).get('job_name')
                if job_name:
                    jobs[language] = {
                        'job_name': job_name,
                        'status': 'IN_PROGRESS',
                        'data': data
                    }
                    print(f"✅ {language}: Job {job_name} started")
                else:
                    print(f"❌ {language}: No job name returned")
            else:
                print(f"❌ {language}: Failed - {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"💥 {language}: Error - {e}")
    
    if not jobs:
        print(f"❌ No transcription jobs started successfully")
        return None
    
    print(f"\n🎯 Started {len(jobs)} jobs successfully!")
    print(f"⏳ Monitoring all jobs until completion...")
    
    return jobs

def monitor_multi_language_jobs(jobs, check_interval=15, max_wait_minutes=15):
    """Monitor multiple transcription jobs until all complete"""
    if not jobs:
        return
    
    print(f"\n🔄 Auto-monitoring {len(jobs)} jobs:")
    for lang, job_info in jobs.items():
        print(f"   {lang}: {job_info['job_name']}")
    
    print(f"⏱️ Check interval: {check_interval} seconds")
    print(f"⏰ Max wait time: {max_wait_minutes} minutes")
    print("=" * 60)
    
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    check_count = 0
    completed_jobs = {}
    
    while jobs:  # Continue while there are still jobs in progress
        check_count += 1
        elapsed = time.time() - start_time
        
        print(f"\n🔍 Check #{check_count} (elapsed: {elapsed:.0f}s)")
        
        # Check if we've exceeded max wait time
        if elapsed > max_wait_seconds:
            print(f"\n⏰ Timeout reached ({max_wait_minutes} minutes)")
            print(f"💡 {len(jobs)} jobs may still be processing")
            break
        
        # Check status of each job
        completed_this_round = []
        
        for language, job_info in jobs.items():
            job_name = job_info['job_name']
            
            try:
                status_url = f"{TRANSCRIBE_STATUS_API_URL}?job_name={job_name}"
                response = requests.get(status_url, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    job_data = data.get('data', {})
                    status = job_data.get('status', 'Unknown')
                    
                    print(f"📈 {language}: {status}")
                    
                    if status == 'COMPLETED':
                        print(f"🎉 {language}: Transcription completed!")
                        completed_jobs[language] = {
                            'job_name': job_name,
                            'data': data,
                            'language': language
                        }
                        completed_this_round.append(language)
                        
                        # Save final result to output folder
                        save_final_output(data, job_name, language, "final_result")
                        
                        # Show transcript preview
                        transcript = job_data.get('transcript', 'No transcript')
                        if len(transcript) > 100:
                            preview = transcript[:100] + "..."
                        else:
                            preview = transcript
                        print(f"📜 {language}: {preview}")
                        
                        # Try to download full transcript
                        transcript_uri = job_data.get('transcript_uri')
                        if transcript_uri:
                            download_transcript_json(transcript_uri, f"{job_name}_{language}")
                        
                    elif status == 'FAILED':
                        print(f"❌ {language}: Transcription failed!")
                        failure_reason = job_data.get('failure_reason', 'Unknown')
                        print(f"   Reason: {failure_reason}")
                        completed_this_round.append(language)
                        
                    elif status == 'IN_PROGRESS':
                        print(f"⏳ {language}: Still processing...")
                        
                else:
                    print(f"❌ {language}: Status check failed - {response.status_code}")
                    
            except Exception as e:
                print(f"💥 {language}: Error checking status - {e}")
        
        # Remove completed jobs from monitoring
        for lang in completed_this_round:
            jobs.pop(lang, None)
        
        if not jobs:
            print(f"\n🏁 All jobs completed!")
            break
        
        # Wait before next check
        print(f"😴 Waiting {check_interval} seconds before next check...")
        time.sleep(check_interval)
    
    # Summary of results
    print(f"\n📊 Multi-Language Transcription Summary")
    print("=" * 50)
    
    if completed_jobs:
        print(f"✅ Completed Languages: {len(completed_jobs)}")
        
        # Compare transcripts
        print(f"\n📝 Transcript Comparison:")
        for language, job_info in completed_jobs.items():
            transcript = job_info['data'].get('data', {}).get('transcript', 'No transcript')
            if transcript.startswith('Error'):
                print(f"❌ {language}: {transcript}")
            else:
                # Show first 150 characters
                preview = transcript[:150] + "..." if len(transcript) > 150 else transcript
                print(f"🔤 {language}: {preview}")
        
        # Save comparison result
        comparison_data = {
            "comparison_timestamp": datetime.now().isoformat(),
            "languages_tested": list(completed_jobs.keys()),
            "results": {}
        }
        
        for language, job_info in completed_jobs.items():
            comparison_data["results"][language] = {
                "job_name": job_info['job_name'],
                "transcript": job_info['data'].get('data', {}).get('transcript', ''),
                "status": job_info['data'].get('data', {}).get('status', ''),
                "completion_time": job_info['data'].get('data', {}).get('completion_time', '')
            }
        
        # Save comparison result to output folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_final_output(comparison_data, f"multi_language_comparison_{timestamp}", "", "comparison")
        
    total_time = time.time() - start_time
    print(f"🕐 Total processing time: {total_time:.0f} seconds")
    
    return completed_jobs

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
                    
                    # Save the final complete result to output folder
                    save_final_output(data, job_name, "", "final_result")
                    
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
                                    
                                    # Save the signed URL info to output folder
                                    url_data = {
                                        "job_name": job_name,
                                        "signed_url": signed_url,
                                        "transcript_uri": transcript_uri,
                                        "generated_at": datetime.now().isoformat(),
                                        "expires_in": "1 hour"
                                    }
                                    save_final_output(url_data, job_name, "", "signed_url")
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
                    
                    # Try to download the full transcript JSON directly
                    print(f"\n📥 Attempting to download full transcript JSON...")
                    download_transcript_json(transcript_uri, job_name)
                    
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
    
    # Check command line arguments for multi-language mode
    import sys
    
    multi_language_mode = '--multi' in sys.argv or '--multi-language' in sys.argv
    
    if multi_language_mode:
        print("🌍 Multi-Language Mode Enabled")
        
        # Define languages to test (can be customized)
        languages = ["en-us", "zh-cn", "ms-my", "id-id"]
        
        # Allow custom language selection from command line
        if '--languages' in sys.argv:
            try:
                lang_index = sys.argv.index('--languages') + 1
                if lang_index < len(sys.argv):
                    languages = sys.argv[lang_index].split(',')
                    languages = [lang.strip() for lang in languages]
            except:
                pass
        
        print(f"🌐 Testing languages: {', '.join(languages)}")
    
    # Test health first
    health_ok = test_health()
    
    if health_ok:
        # Your S3 file - using clean S3 URL
        s3_url = "https://great-ai-hackathon-uploads-dev.s3.us-east-1.amazonaws.com/sample-audio.m4a"
        
        if multi_language_mode:
            # Multi-language transcription
            jobs = test_transcribe_multi_language(s3_url, languages)
            
            if jobs:
                print(f"\n🎯 {len(jobs)} jobs started successfully!")
                print(f"⏳ Monitoring all jobs until completion...")
                
                # Monitor all jobs until completion
                completed_jobs = monitor_multi_language_jobs(jobs)
                
                if completed_jobs:
                    print(f"\n🎉 Multi-language transcription completed!")
                    print(f"📁 All results saved in log/ folder")
                else:
                    print(f"\n❌ No jobs completed successfully")
            else:
                print(f"\n❌ Failed to start any transcription jobs")
        else:
            # Single language transcription (original behavior)
            job_name = test_transcribe_single(s3_url)
            
            if job_name:
                print(f"\n🎯 Job started successfully!")
                print(f"⏳ Monitoring job until completion (no user input required)...")
                
                # Automatically monitor until completion
                monitor_job_until_complete(job_name)
            else:
                print(f"\n❌ Failed to start transcription job")
    else:
        print(f"\n❌ Health check failed - cannot proceed with transcription test")

def test_transcribe_single(s3_url, language="en-us"):
    """Test transcription with single language (original function)"""
    print(f"\n🎤 Testing Transcription")
    print("=" * 40)
    
    print(f"📁 S3 URL: {s3_url}")
    print(f"🌐 API URL: {TRANSCRIBE_API_URL}")
    print(f"🌐 Language: {language}")
    
    payload = {
        "url": s3_url,
        "language": language
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

if __name__ == "__main__":
    main()
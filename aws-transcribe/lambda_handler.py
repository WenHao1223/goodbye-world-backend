import json
import os
import uuid
import time
import requests
from datetime import datetime
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
from urllib.parse import urlparse

# Initialize AWS clients
# Use environment variable for region, default to us-east-1
aws_region = os.environ.get('AWS_REGION1', 'us-east-1')
transcribe_client = boto3.client('transcribe', region_name=aws_region)
s3_client = boto3.client('s3', region_name=aws_region)

# Supported languages mapping
SUPPORTED_LANGUAGES = {
    'en-us': 'en-US',
    'zh-cn': 'zh-CN', 
    'ms-my': 'ms-MY',
    'id-id': 'id-ID'
}

def lambda_handler(event, context):
    """
    Default handler that routes to specific functions
    """
    # Get the path to determine which handler to use
    path = event.get('path', '')
    method = event.get('httpMethod', '')
    
    if path == '/transcribe' and method == 'POST':
        return transcribe_handler(event, context)
    elif path == '/status' and method == 'GET':
        return status_handler(event, context)
    elif path == '/health' and method == 'GET':
        return health_handler(event, context)
    else:
        return create_response(
            404, 
            "Endpoint not found", 
            "The requested endpoint was not found"
        )

def transcribe_handler(event, context):
    """
    Handle audio/video transcription from S3 URL
    Expected request format:
    {
        "url": "https://s3-bucket-url/audio-file.mp3",
        "language": "en-us" (optional, defaults to "en-us")
    }
    """
    try:
        # Handle OPTIONS requests for CORS
        if event.get('httpMethod') == 'OPTIONS':
            return handle_options()
        
        # Parse request body
        try:
            if 'body' in event:
                if isinstance(event['body'], str):
                    body = json.loads(event['body'])
                else:
                    body = event['body']
            else:
                body = event
        except json.JSONDecodeError:
            return create_response(
                400,
                "Invalid JSON format",
                "Request body must be valid JSON"
            )
        
        # Validate required fields
        url = body.get('url')
        if not url:
            return create_response(
                400,
                "Missing required field",
                "The 'url' field is required"
            )
        
        # Validate URL format
        if not is_valid_s3_url(url):
            return create_response(
                400,
                "Invalid URL format",
                "The provided URL is not a valid S3 downloadable URL"
            )
        
        # Get language (default to en-us)
        language_code = body.get('language', 'en-us').lower()
        if language_code not in SUPPORTED_LANGUAGES:
            return create_response(
                400,
                "Unsupported language",
                f"Language '{language_code}' is not supported. Supported languages: {list(SUPPORTED_LANGUAGES.keys())}"
            )
        
        # Start transcription job
        job_result = start_transcription_job(url, language_code)
        
        if job_result['success']:
            return create_response(
                200,
                "Transcription job started successfully",
                job_result['data']
            )
        else:
            return create_response(
                500,
                "Failed to start transcription job",
                job_result['error']
            )
            
    except Exception as e:
        import traceback
        return create_response(
            500,
            "Internal server error",
            f"An unexpected error occurred: {str(e)}"
        )

def start_transcription_job(media_url: str, language_code: str) -> Dict[str, Any]:
    """
    Start AWS Transcribe job for the given media URL
    """
    try:
        # Convert HTTPS S3 URL to s3:// URI if needed
        s3_uri = convert_to_s3_uri(media_url)
        
        # Generate unique job name
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        job_name = f"transcribe_job_{timestamp}_{uuid.uuid4().hex[:8]}"
        
        # Prepare transcription job parameters
        job_params = {
            'TranscriptionJobName': job_name,
            'LanguageCode': SUPPORTED_LANGUAGES[language_code],
            'Media': {
                'MediaFileUri': s3_uri
            },
            'OutputBucketName': os.environ.get('OUTPUT_S3_BUCKET_NAME'),
            'Settings': {
                'ShowSpeakerLabels': True,
                'MaxSpeakerLabels': 10,
                'ShowAlternatives': True,
                'MaxAlternatives': 2
            }
        }
        
        # Add output bucket name if configured
        output_bucket = os.environ.get('OUTPUT_S3_BUCKET_NAME')
        if output_bucket:
            job_params['OutputBucketName'] = output_bucket
        
        # Start the transcription job
        response = transcribe_client.start_transcription_job(**job_params)
        
        job_data = {
            'job_name': job_name,
            'job_status': response['TranscriptionJob']['TranscriptionJobStatus'],
            'language_code': language_code,
            'media_url': media_url,
            'creation_time': response['TranscriptionJob']['CreationTime'].isoformat(),
            'estimated_completion_time': 'Processing time varies based on audio length'
        }
        
        return {
            'success': True,
            'data': job_data
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        return {
            'success': False,
            'error': f"AWS Transcribe error ({error_code}): {error_message}"
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"Unexpected error: {str(e)}"
        }

def status_handler(event, context):
    """
    Check the status of a transcription job
    """
    try:
        # Handle OPTIONS requests for CORS
        if event.get('httpMethod') == 'OPTIONS':
            return handle_options()
        
        # Get job name from query parameters
        query_params = event.get('queryStringParameters') or {}
        job_name = query_params.get('job_name')
        
        if not job_name:
            return create_response(
                400,
                "Missing required parameter",
                "The 'job_name' query parameter is required"
            )
        
        # Get job status
        job_result = get_transcription_job_status(job_name)
        
        if job_result['success']:
            return create_response(
                200,
                "Job status retrieved successfully",
                job_result['data']
            )
        else:
            return create_response(
                404,
                "Transcription job not found",
                job_result['error']
            )
            
    except Exception as e:
        return create_response(
            500,
            "Internal server error",
            f"An unexpected error occurred: {str(e)}"
        )

def get_transcription_job_status(job_name: str) -> Dict[str, Any]:
    """
    Get the status and results of a transcription job
    """
    try:
        response = transcribe_client.get_transcription_job(
            TranscriptionJobName=job_name
        )
        
        job = response['TranscriptionJob']
        job_status = job['TranscriptionJobStatus']
        
        job_data = {
            'job_name': job_name,
            'status': job_status,
            'language_code': job['LanguageCode'],
            'creation_time': job['CreationTime'].isoformat(),
            'completion_time': job.get('CompletionTime', '').isoformat() if job.get('CompletionTime') else None
        }
        
        # If job is completed, get the transcript
        if job_status == 'COMPLETED':
            transcript_uri = job['Transcript']['TranscriptFileUri']
            transcript_text = get_transcript_text(transcript_uri)
            job_data['transcript'] = transcript_text
            job_data['transcript_uri'] = transcript_uri
        elif job_status == 'FAILED':
            job_data['failure_reason'] = job.get('FailureReason', 'Unknown error')
        
        return {
            'success': True,
            'data': job_data
        }
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'BadRequestException':
            return {
                'success': False,
                'error': f"Transcription job '{job_name}' not found"
            }
        else:
            return {
                'success': False,
                'error': f"AWS error: {e.response['Error']['Message']}"
            }
    except Exception as e:
        return {
            'success': False,
            'error': f"Unexpected error: {str(e)}"
        }

def get_transcript_text(transcript_uri: str) -> str:
    """
    Download and extract transcript text from the transcript file
    """
    try:
        # Download transcript file
        response = requests.get(transcript_uri)
        response.raise_for_status()
        
        transcript_data = response.json()
        
        # Extract the full transcript text
        transcript_text = transcript_data['results']['transcripts'][0]['transcript']
        
        return transcript_text
        
    except Exception as e:
        return f"Error retrieving transcript: {str(e)}"

def is_valid_s3_url(url: str) -> bool:
    """
    Validate if the URL is a valid S3 URL
    """
    try:
        parsed = urlparse(url)
        
        # Check for S3 domain patterns
        s3_patterns = [
            's3.amazonaws.com',
            's3-',
            '.s3.',
            '.s3-'
        ]
        
        return any(pattern in parsed.netloc.lower() for pattern in s3_patterns)
        
    except Exception:
        return False

def health_handler(event, context):
    """
    Health check endpoint
    """
    supported_languages = list(SUPPORTED_LANGUAGES.keys())
    
    return create_response(
        200,
        "Service is healthy",
        {
            'service': 'aws-transcribe-api',
            'supported_languages': supported_languages,
            'timestamp': datetime.now().isoformat(),
            'request_id': context.aws_request_id if context else 'local'
        }
    )

def handle_options():
    """
    Handle OPTIONS requests for CORS preflight
    """
    return {
        'statusCode': 200,
        'headers': get_cors_headers(),
        'body': ''
    }

def get_cors_headers():
    """
    Get CORS headers for responses
    """
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
    }

def create_response(status_code: int, message: str, data: Any) -> Dict[str, Any]:
    """
    Create standardized response format
    """
    response_body = {
        'status': {
            'statusCode': status_code,
            'message': message
        },
        'data': {
            'message': data if isinstance(data, str) else json.dumps(data)
        }
    }
    
    # If data is a dict/object, include it directly in data field
    if isinstance(data, dict):
        response_body['data'] = data
        response_body['data']['message'] = message
    
    return {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': json.dumps(response_body, indent=2, default=str)
    }
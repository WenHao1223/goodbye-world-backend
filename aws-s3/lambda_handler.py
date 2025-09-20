import json
import os
import base64
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
import mimetypes

# Initialize S3 client
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    Default handler that routes to specific functions
    """
    # Get the path to determine which handler to use
    path = event.get('path', '')
    method = event.get('httpMethod', '')
    
    if path == '/upload' and method == 'POST':
        return upload_handler(event, context)
    elif path.startswith('/download/') and method == 'GET':
        return get_download_url_handler(event, context)
    elif path == '/files' and method == 'GET':
        return list_files_handler(event, context)
    elif path == '/health' and method == 'GET':
        return health_handler(event, context)
    else:
        return {
            'statusCode': 404,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Endpoint not found'})
        }

def upload_handler(event, context):
    """
    Handle file upload to S3
    Accepts multipart/form-data or base64 encoded files
    """
    try:
        # Handle OPTIONS requests for CORS
        if event.get('httpMethod') == 'OPTIONS':
            return handle_options()
        
        bucket_name = os.environ.get('S3_BUCKET_NAME')
        if not bucket_name:
            return error_response(500, 'S3_BUCKET_NAME environment variable not set')
        
        # Parse the request
        content_type = event.get('headers', {}).get('content-type', '') or event.get('headers', {}).get('Content-Type', '')
        
        if 'multipart/form-data' in content_type:
            # Handle multipart form data
            result = handle_multipart_upload(event, bucket_name)
        else:
            # Handle JSON with base64 encoded file
            result = handle_json_upload(event, bucket_name)
        
        return result
        
    except Exception as e:
        import traceback
        return error_response(500, f'Upload failed: {str(e)}', traceback.format_exc())

def handle_multipart_upload(event, bucket_name):
    """
    Handle multipart form data upload
    """
    # For multipart, the file content is in the body as base64 when coming through API Gateway
    body = event.get('body', '')
    is_base64 = event.get('isBase64Encoded', False)
    
    if is_base64:
        try:
            # Decode the base64 body
            decoded_body = base64.b64decode(body)
            
            # Parse multipart data (simplified - in production, use a proper multipart parser)
            # For now, assume the entire decoded body is the file content
            file_content = decoded_body
            
            # Generate a unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_extension = '.bin'  # Default extension
            filename = f"upload_{timestamp}_{uuid.uuid4().hex[:8]}{file_extension}"
            
        except Exception as e:
            return error_response(400, f'Failed to decode multipart data: {str(e)}')
    else:
        return error_response(400, 'Multipart data must be base64 encoded')
    
    return upload_to_s3(bucket_name, filename, file_content)

def handle_json_upload(event, bucket_name):
    """
    Handle JSON upload with base64 encoded file
    Expected format:
    {
        "filename": "example.pdf",
        "content": "base64_encoded_content",
        "content_type": "application/pdf"
    }
    """
    try:
        if 'body' in event:
            if isinstance(event['body'], str):
                body = json.loads(event['body'])
            else:
                body = event['body']
        else:
            body = event
        
        filename = body.get('filename')
        content_b64 = body.get('content')
        content_type = body.get('content_type', 'application/octet-stream')
        
        if not filename or not content_b64:
            return error_response(400, 'Missing filename or content in request body')
        
        # Decode base64 content
        try:
            file_content = base64.b64decode(content_b64)
        except Exception as e:
            return error_response(400, f'Invalid base64 content: {str(e)}')
        
        # Generate unique filename to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{timestamp}_{uuid.uuid4().hex[:8]}{ext}"
        
        return upload_to_s3(bucket_name, unique_filename, file_content, content_type)
        
    except json.JSONDecodeError:
        return error_response(400, 'Invalid JSON in request body')
    except Exception as e:
        return error_response(500, f'Failed to process upload: {str(e)}')

def upload_to_s3(bucket_name, filename, file_content, content_type=None):
    """
    Upload file content to S3 bucket
    """
    try:
        # Guess content type if not provided
        if not content_type:
            content_type, _ = mimetypes.guess_type(filename)
            if not content_type:
                content_type = 'application/octet-stream'
        
        # Upload to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=filename,
            Body=file_content,
            ContentType=content_type
        )
        
        # Generate download URL
        expiration = int(os.environ.get('PRESIGNED_URL_EXPIRATION', 3600))
        download_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': filename},
            ExpiresIn=expiration
        )
        
        # Get file size
        file_size = len(file_content)
        
        response_data = {
            'message': 'File uploaded successfully',
            'filename': filename,
            'bucket': bucket_name,
            'size': file_size,
            'content_type': content_type,
            'download_url': download_url,
            'expiration_seconds': expiration,
            'upload_timestamp': datetime.now().isoformat()
        }
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(response_data, indent=2)
        }
        
    except ClientError as e:
        return error_response(500, f'S3 upload failed: {str(e)}')

def get_download_url_handler(event, context):
    """
    Generate a presigned download URL for a file
    """
    try:
        # Handle OPTIONS requests for CORS
        if event.get('httpMethod') == 'OPTIONS':
            return handle_options()
        
        bucket_name = os.environ.get('S3_BUCKET_NAME')
        if not bucket_name:
            return error_response(500, 'S3_BUCKET_NAME environment variable not set')
        
        # Extract file key from path parameters
        file_key = event.get('pathParameters', {}).get('file_key')
        if not file_key:
            return error_response(400, 'File key is required')
        
        # Check if file exists
        try:
            s3_client.head_object(Bucket=bucket_name, Key=file_key)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return error_response(404, 'File not found')
            else:
                return error_response(500, f'Error checking file: {str(e)}')
        
        # Generate presigned URL
        expiration = int(os.environ.get('PRESIGNED_URL_EXPIRATION', 3600))
        download_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': file_key},
            ExpiresIn=expiration
        )
        
        response_data = {
            'download_url': download_url,
            'file_key': file_key,
            'bucket': bucket_name,
            'expiration_seconds': expiration,
            'generated_at': datetime.now().isoformat()
        }
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(response_data, indent=2)
        }
        
    except Exception as e:
        return error_response(500, f'Failed to generate download URL: {str(e)}')

def list_files_handler(event, context):
    """
    List files in the S3 bucket
    """
    try:
        # Handle OPTIONS requests for CORS
        if event.get('httpMethod') == 'OPTIONS':
            return handle_options()
        
        bucket_name = os.environ.get('S3_BUCKET_NAME')
        if not bucket_name:
            return error_response(500, 'S3_BUCKET_NAME environment variable not set')
        
        # Get query parameters
        query_params = event.get('queryStringParameters') or {}
        max_keys = int(query_params.get('limit', 100))
        prefix = query_params.get('prefix', '')
        
        # List objects in bucket
        try:
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
        except ClientError as e:
            return error_response(500, f'Failed to list files: {str(e)}')
        
        files = []
        if 'Contents' in response:
            for obj in response['Contents']:
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'etag': obj['ETag'].strip('"')
                })
        
        response_data = {
            'files': files,
            'count': len(files),
            'bucket': bucket_name,
            'prefix': prefix,
            'is_truncated': response.get('IsTruncated', False)
        }
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(response_data, indent=2, default=str)
        }
        
    except Exception as e:
        return error_response(500, f'Failed to list files: {str(e)}')

def health_handler(event, context):
    """
    Health check endpoint
    """
    bucket_name = os.environ.get('S3_BUCKET_NAME', 'not-configured')
    
    return {
        'statusCode': 200,
        'headers': get_cors_headers(),
        'body': json.dumps({
            'status': 'healthy',
            'service': 's3-upload-api',
            'bucket': bucket_name,
            'timestamp': datetime.now().isoformat(),
            'request_id': context.aws_request_id if context else 'local'
        })
    }

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

def error_response(status_code, message, traceback=None):
    """
    Generate error response
    """
    error_data = {
        'error': message,
        'status_code': status_code,
        'timestamp': datetime.now().isoformat()
    }
    
    if traceback:
        error_data['traceback'] = traceback
    
    return {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': json.dumps(error_data, indent=2)
    }
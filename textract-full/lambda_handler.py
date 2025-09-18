#!/usr/bin/env python3
"""
AWS Lambda handler for textract-full CLI
"""

import json
import base64
import subprocess
import tempfile
import os
from pathlib import Path
import mimetypes


def lambda_handler(event, context):
    """
    AWS Lambda handler for document analysis
    
    Expected event structure:
    {
        "httpMethod": "POST",
        "body": base64-encoded JSON with:
        {
            "file_content": "base64-encoded file content",
            "filename": "original filename",
            "mode": "tfbq" (optional, default: "tfbq"),
            "category": "licence|receipt|idcard|passport" (optional),
            "queries": "custom queries separated by semicolons" (optional),
            "prompt": "custom prompt for Bedrock AI extraction" (optional),
            "region": "us-east-1" (optional, default: "us-east-1")
        }
    }
    """
    
    try:
        # Handle different event formats (API Gateway, direct invoke, etc.)
        if 'httpMethod' in event:
            # API Gateway format
            if event['httpMethod'] != 'POST':
                return {
                    'statusCode': 405,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'POST, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type'
                    },
                    'body': json.dumps({'error': 'Method not allowed'})
                }
            
            # Parse body
            body = event.get('body', '')
            if event.get('isBase64Encoded', False):
                body = base64.b64decode(body).decode('utf-8')
            
            try:
                request_data = json.loads(body)
            except json.JSONDecodeError:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'Invalid JSON in request body'})
                }
        else:
            # Direct invoke format
            request_data = event
        
        # Validate required fields
        if 'file_content' not in request_data or 'filename' not in request_data:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Missing file_content or filename'})
            }
        
        # Extract parameters
        file_content_b64 = request_data['file_content']
        filename = request_data['filename']
        mode = request_data.get('mode', 'tfbq')
        category = request_data.get('category')
        queries = request_data.get('queries')
        prompt = request_data.get('prompt')
        region = request_data.get('region', 'us-east-1')
        
        # Decode file content
        try:
            file_content = base64.b64decode(file_content_b64)
        except Exception as e:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': f'Invalid base64 file content: {str(e)}'})
            }
        
        # Save uploaded file temporarily
        file_suffix = Path(filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as tmp_file:
            tmp_file.write(file_content)
            temp_path = tmp_file.name
        
        try:
            # Set up environment for Lambda
            env = os.environ.copy()
            env['LAMBDA_RUNTIME'] = 'true'  # Flag to indicate Lambda environment

            # Build CLI command (no AWS credentials needed - using Lambda's IAM role)
            cmd = ['python', 'cli.py', '--file', temp_path, '--mode', mode, '--region', region]
            if category:
                cmd.extend(['--category', category])
            if queries:
                cmd.extend(['--queries', queries])
            if prompt:
                cmd.extend(['--prompt', prompt])

            # Run CLI command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__)),  # Current directory
                env=env,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or 'Unknown error'
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': f'Processing failed: {error_msg}',
                        'returncode': result.returncode,
                        'stdout': result.stdout,
                        'stderr': result.stderr
                    })
                }
            
            # Parse output files
            response = {'status': 'success', 'console_output': result.stdout}
            
            # Find latest log directory
            log_dir = Path('/tmp/log')  # Use /tmp in Lambda
            if log_dir.exists():
                latest_log = max(log_dir.glob('*'), key=os.path.getctime)
                
                # Read JSON files
                for json_file in ['text.json', 'forms.json', 'tables.json', 'queries.json', 'blur_analysis.json']:
                    file_path = latest_log / json_file
                    if file_path.exists():
                        with open(file_path) as f:
                            if json_file == 'blur_analysis.json':
                                response['blur_analysis'] = json.load(f)
                            else:
                                response[json_file.replace('.json', '')] = json.load(f)
            
            # Find latest output file (for category-based or custom prompt extraction)
            output_dir = Path('/tmp/output')  # Use /tmp in Lambda
            if output_dir.exists() and (category or prompt):
                output_files = list(output_dir.glob('*.json'))
                if output_files:
                    latest_output = max(output_files, key=os.path.getctime)
                    with open(latest_output) as f:
                        response['extracted_data'] = json.load(f)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(response)
            }
            
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass  # Ignore cleanup errors
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }


def health_handler(event, context):
    """Health check handler"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'status': 'healthy'})
    }


# For local testing
if __name__ == '__main__':
    # Example test event
    test_event = {
        "httpMethod": "POST",
        "body": json.dumps({
            "file_content": "",  # base64 encoded file content
            "filename": "test.pdf",
            "mode": "tfbq",
            "category": "receipt",
            "region": "us-east-1"
        })
    }
    
    result = lambda_handler(test_event, {})
    print(json.dumps(result, indent=2))

#!/usr/bin/env python3
"""
Simple Flask API wrapper for textract-full CLI
"""

from flask import Flask, request, jsonify
import subprocess
import json
from pathlib import Path
import tempfile
import os

app = Flask(__name__)

@app.route('/analyze', methods=['POST'])
def analyze_document():
    try:
        # Get file from request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get parameters
        mode = request.form.get('mode', 'tfbq')
        category = request.form.get('category')
        region = request.form.get('region', 'us-east-1')
        profile = request.form.get('profile')
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            file.save(tmp_file.name)
            temp_path = tmp_file.name
        
        try:
            # Build CLI command
            cmd = ['python', 'cli.py', '--file', temp_path, '--mode', mode, '--region', region]
            if category:
                cmd.extend(['--category', category])
            if profile:
                cmd.extend(['--profile', profile])
            
            # Run CLI command
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
            
            if result.returncode != 0:
                return jsonify({'error': f'Processing failed: {result.stderr}'}), 500
            
            # Parse output files
            response = {'status': 'success', 'console_output': result.stdout}
            
            # Find latest log directory
            log_dir = Path('log')
            if log_dir.exists():
                latest_log = max(log_dir.glob('*'), key=os.path.getctime)
                
                # Read JSON files
                for json_file in ['text.json', 'forms.json', 'tables.json', 'queries.json']:
                    file_path = latest_log / json_file
                    if file_path.exists():
                        with open(file_path) as f:
                            response[json_file.replace('.json', '')] = json.load(f)
            
            # Find latest output file
            output_dir = Path('output')
            if output_dir.exists() and category:
                latest_output = max(output_dir.glob('*.json'), key=os.path.getctime)
                with open(latest_output) as f:
                    response['extracted_data'] = json.load(f)
            
            return jsonify(response)
            
        finally:
            # Clean up temp file
            os.unlink(temp_path)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
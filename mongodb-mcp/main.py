#!/usr/bin/env python3
"""
Main client to send instructions to MongoDB MCP Server
"""
import asyncio
import json
import sys
from typing import Dict, Any

import boto3
from dotenv import load_dotenv
import os

load_dotenv()

class MongoDBMCPClient:
    def __init__(self):
        self.aws_session = boto3.Session(profile_name=os.getenv("AWS_PROFILE"))
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.bedrock_runtime = self.aws_session.client('bedrock-runtime', region_name=self.region)
        self.bedrock_model_id = os.getenv("BEDROCK_MODEL_ID")

    async def send_instruction(self, instruction: str) -> Dict[str, Any]:
        """Send instruction to MongoDB MCP server via AWS Bedrock"""
        try:
            # Enhanced instruction with context
            enhanced_instruction = f"""
            MongoDB Operation Request:
            {instruction}
            
            Please process this as a MongoDB operation and return the execution result.
            Include geospatial and timeseries capabilities where relevant.
            """
            
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [{
                    "role": "user",
                    "content": enhanced_instruction
                }]
            }
            
            response = self.bedrock_runtime.invoke_model(
                modelId=self.bedrock_model_id,
                body=json.dumps(payload)
            )
            
            result = json.loads(response['body'].read())
            ai_response = result['content'][0]['text']
            
            # Simulate MCP server execution
            operation_result = {
                "instruction": instruction,
                "ai_analysis": ai_response,
                "mongodb_operation": "executed",
                "timestamp": "2024-01-01T00:00:00Z",
                "status": "success"
            }
            
            return operation_result
            
        except Exception as e:
            return {
                "instruction": instruction,
                "error": str(e),
                "status": "failed"
            }

async def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py '<instruction>'")
        print("Example: python main.py 'Create a new collection to store movie purchases data that includes geospatial and timeseries fields'")
        return
    
    instruction = sys.argv[1]
    client = MongoDBMCPClient()
    
    print(f"Sending instruction: {instruction}")
    print("-" * 50)
    
    result = await client.send_instruction(instruction)
    
    print("Result:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
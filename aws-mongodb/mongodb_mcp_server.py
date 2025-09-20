#!/usr/bin/env python3
import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import boto3
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

class MongoDBMCPServer:
    def __init__(self):
        self.mongo_client = MongoClient(os.getenv("ATLAS_URI"))
        self.aws_session = boto3.Session(profile_name=os.getenv("AWS_PROFILE"))
        # AWS Lambda automatically provides the region via AWS_REGION1 environment variable
        self.region = os.environ.get('AWS_REGION1', 'us-east-1')
        self.sagemaker_endpoint = os.getenv("SAGEMAKER_ENDPOINT")
        self.bedrock_model_id = os.getenv("BEDROCK_MODEL_ID")
        
        self.sagemaker_runtime = self.aws_session.client('sagemaker-runtime', region_name=self.region)
        self.bedrock_runtime = self.aws_session.client('bedrock-runtime', region_name=self.region)

    async def process_ai_instruction(self, instruction: str) -> Dict[str, Any]:
        """Process natural language instruction using AWS AI services"""
        try:
            # Use Bedrock for instruction processing
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [{
                    "role": "user",
                    "content": f"""Parse this MongoDB instruction and return JSON with operation details:
                    
                    Instruction: {instruction}
                    
                    Return format:
                    {{
                        "operation": "create_collection|insert_document|update_document|find_documents|create_index",
                        "database": "database_name",
                        "collection": "collection_name",
                        "data": {{}},
                        "query": {{}},
                        "options": {{}}
                    }}"""
                }]
            }
            
            response = self.bedrock_runtime.invoke_model(
                modelId=self.bedrock_model_id,
                body=json.dumps(payload)
            )
            
            result = json.loads(response['body'].read())
            content = result['content'][0]['text']
            
            # Extract JSON from response
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != 0:
                return json.loads(content[start:end])
            
        except Exception as e:
            # Fallback to simple parsing
            return self._simple_parse_instruction(instruction)
    
    def _simple_parse_instruction(self, instruction: str) -> Dict[str, Any]:
        """Simple fallback instruction parsing"""
        instruction_lower = instruction.lower()
        
        if "create" in instruction_lower and "collection" in instruction_lower:
            return {
                "operation": "create_collection",
                "database": os.getenv("ATLAS_DB_NAME"),
                "collection": "new_collection",
                "options": {"timeseries": True, "geospatial": True}
            }
        elif "insert" in instruction_lower:
            return {
                "operation": "insert_document",
                "database": os.getenv("ATLAS_DB_NAME"),
                "collection": "documents",
                "data": {"timestamp": datetime.utcnow(), "processed": True}
            }
        
        return {"operation": "unknown", "error": "Could not parse instruction"}

    async def execute_mongodb_operation(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MongoDB operation based on parsed instruction"""
        try:
            db_name = operation_data.get("database", os.getenv("ATLAS_DB_NAME"))
            collection_name = operation_data.get("collection", "default")
            operation = operation_data.get("operation")
            
            db = self.mongo_client[db_name]
            collection = db[collection_name]
            
            if operation == "create_collection":
                options = operation_data.get("options", {})
                if options.get("timeseries"):
                    db.create_collection(collection_name, timeseries={"timeField": "timestamp"})
                else:
                    db.create_collection(collection_name)
                
                # Create geospatial index if requested
                if options.get("geospatial"):
                    collection.create_index([("location", "2dsphere")])
                
                return {"success": True, "message": f"Collection {collection_name} created"}
            
            elif operation == "insert_document":
                data = operation_data.get("data", {})
                if not data.get("timestamp"):
                    data["timestamp"] = datetime.utcnow()
                
                result = collection.insert_one(data)
                return {"success": True, "inserted_id": str(result.inserted_id)}
            
            elif operation == "find_documents":
                query = operation_data.get("query", {})
                docs = list(collection.find(query).limit(10))
                for doc in docs:
                    doc["_id"] = str(doc["_id"])
                return {"success": True, "documents": docs}
            
            elif operation == "update_document":
                query = operation_data.get("query", {})
                update = operation_data.get("data", {})
                result = collection.update_many(query, {"$set": update})
                return {"success": True, "modified_count": result.modified_count}
            
            return {"success": False, "error": f"Unknown operation: {operation}"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

app = Server("mongodb-mcp-server")

@app.list_tools()
async def handle_list_tools() -> List[Tool]:
    return [
        Tool(
            name="execute_mongodb_instruction",
            description="Execute MongoDB operations using natural language instructions via AWS AI",
            inputSchema={
                "type": "object",
                "properties": {
                    "instruction": {
                        "type": "string",
                        "description": "Natural language instruction for MongoDB operation"
                    }
                },
                "required": ["instruction"]
            }
        ),
        Tool(
            name="direct_mongodb_operation",
            description="Execute direct MongoDB operation with structured data",
            inputSchema={
                "type": "object",
                "properties": {
                    "operation": {"type": "string"},
                    "database": {"type": "string"},
                    "collection": {"type": "string"},
                    "data": {"type": "object"},
                    "query": {"type": "object"}
                },
                "required": ["operation"]
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    server = MongoDBMCPServer()
    
    if name == "execute_mongodb_instruction":
        instruction = arguments.get("instruction", "")
        
        # Process instruction with AI
        operation_data = await server.process_ai_instruction(instruction)
        
        # Execute MongoDB operation
        result = await server.execute_mongodb_operation(operation_data)
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "instruction": instruction,
                "parsed_operation": operation_data,
                "result": result
            }, indent=2, default=str)
        )]
    
    elif name == "direct_mongodb_operation":
        result = await server.execute_mongodb_operation(arguments)
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, default=str)
        )]
    
    return [TextContent(type="text", text="Unknown tool")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mongodb-mcp-server",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
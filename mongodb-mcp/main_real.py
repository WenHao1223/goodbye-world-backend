#!/usr/bin/env python3
import asyncio
import json
import sys
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

class RealMongoDBClient:
    def __init__(self):
        self.mongo_client = MongoClient(os.getenv("ATLAS_URI"))
    
    def parse_instruction(self, instruction: str) -> dict:
        """Parse natural language instruction"""
        instruction_lower = instruction.lower()
        
        if "create" in instruction_lower and "collection" in instruction_lower:
            # Extract collection name from instruction
            if "movie" in instruction_lower and "purchase" in instruction_lower:
                collection_name = "moviePurchases"
            else:
                collection_name = "new_collection"
            
            return {
                "operation": "create_collection",
                "database": "hackathon_db",
                "collection": collection_name,
                "options": {
                    "timeseries": "timeseries" in instruction_lower or "time" in instruction_lower,
                    "geospatial": "geospatial" in instruction_lower or "location" in instruction_lower
                }
            }
        elif "create" in instruction_lower and ("document" in instruction_lower or "movie" in instruction_lower or "sample" in instruction_lower):
            # Extract number if specified
            import re
            numbers = re.findall(r'\d+', instruction)
            count = int(numbers[0]) if numbers else 1
            
            return {
                "operation": "insert_multiple",
                "database": "hackathon_db",
                "collection": "moviePurchases",
                "count": count
            }
        elif "insert" in instruction_lower:
            return {
                "operation": "insert_document",
                "database": "hackathon_db", 
                "collection": "moviePurchases",
                "data": {
                    "title": "Sample Movie",
                    "purchaseDate": datetime.utcnow(),
                    "location": {"type": "Point", "coordinates": [-74.0060, 40.7128]},
                    "price": 12.99
                }
            }
        elif "find" in instruction_lower or "search" in instruction_lower:
            # Extract search criteria
            query = {}
            
            # Look for title searches
            if "title" in instruction_lower:
                import re
                # Extract words after "title of"
                title_match = re.search(r'title\s+of\s+(\w+)', instruction_lower)
                if title_match:
                    query["title"] = {"$regex": title_match.group(1), "$options": "i"}
            
            # Look for specific movie names
            movies = ["inception", "matrix", "interstellar", "avatar", "titanic", "avengers", "star wars"]
            for movie in movies:
                if movie in instruction_lower:
                    query["title"] = {"$regex": movie, "$options": "i"}
                    break
            
            return {
                "operation": "find_documents",
                "database": "hackathon_db",
                "collection": "moviePurchases",
                "query": query
            }
        
        return {"operation": "unknown", "error": "Could not parse instruction"}
    
    def execute_operation(self, operation_data: dict) -> dict:
        """Execute MongoDB operation"""
        try:
            db_name = operation_data.get("database", "hackathon_db")
            collection_name = operation_data.get("collection", "default")
            operation = operation_data.get("operation")
            
            db = self.mongo_client[db_name]
            
            if operation == "create_collection":
                options = operation_data.get("options", {})
                
                # Check if collection already exists
                if collection_name in db.list_collection_names():
                    return {"success": False, "message": f"Collection {collection_name} already exists"}
                
                if options.get("timeseries"):
                    db.create_collection(collection_name, timeseries={"timeField": "purchaseDate"})
                else:
                    db.create_collection(collection_name)
                
                collection = db[collection_name]
                
                # Create geospatial index if requested
                if options.get("geospatial"):
                    collection.create_index([("location", "2dsphere")])
                
                return {"success": True, "message": f"Collection {collection_name} created with timeseries={options.get('timeseries')} and geospatial={options.get('geospatial')}"}
            
            elif operation == "insert_document":
                collection = db[collection_name]
                data = operation_data.get("data", {})
                result = collection.insert_one(data)
                return {"success": True, "inserted_id": str(result.inserted_id)}
            
            elif operation == "insert_multiple":
                collection = db[collection_name]
                count = operation_data.get("count", 1)
                
                movies = [
                    "Inception", "The Matrix", "Interstellar", "Avatar", "Titanic",
                    "The Avengers", "Star Wars", "Jurassic Park", "The Lion King", "Frozen"
                ]
                
                documents = []
                for i in range(count):
                    doc = {
                        "title": movies[i % len(movies)],
                        "purchaseDate": datetime.utcnow(),
                        "location": {
                            "type": "Point", 
                            "coordinates": [-74.0060 + i*0.01, 40.7128 + i*0.01]
                        },
                        "price": round(9.99 + i*2.5, 2),
                        "userId": f"user_{i+1}"
                    }
                    documents.append(doc)
                
                result = collection.insert_many(documents)
                return {"success": True, "inserted_count": len(result.inserted_ids), "inserted_ids": [str(id) for id in result.inserted_ids]}
            
            elif operation == "find_documents":
                collection = db[collection_name]
                query = operation_data.get("query", {})
                docs = list(collection.find(query).limit(10))
                for doc in docs:
                    doc["_id"] = str(doc["_id"])
                return {"success": True, "count": len(docs), "documents": docs}
            
            return {"success": False, "error": f"Unknown operation: {operation}"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

def main():
    if len(sys.argv) < 2:
        print("Usage: python main_real.py '<instruction>'")
        print("Examples:")
        print("  python main_real.py 'Create a new collection to store movie purchases data that includes geospatial and timeseries fields'")
        print("  python main_real.py 'Insert a sample movie purchase document'")
        print("  python main_real.py 'Find all movie purchases'")
        return
    
    instruction = sys.argv[1]
    client = RealMongoDBClient()
    
    print(f"Executing instruction: {instruction}")
    print("-" * 50)
    
    # Parse instruction
    operation_data = client.parse_instruction(instruction)
    print(f"Parsed operation: {json.dumps(operation_data, indent=2, default=str)}")
    print("-" * 50)
    
    # Execute operation
    result = client.execute_operation(operation_data)
    print(f"Result: {json.dumps(result, indent=2, default=str)}")

if __name__ == "__main__":
    main()
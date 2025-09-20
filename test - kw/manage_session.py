import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("ATLAS_URI")
DB_NAME = os.getenv("ATLAS_DB_NAME", "chat")

# Connect to MongoDB Atlas
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
sessions = db["session"]

def get_session(session_id: str):
    return sessions.find_one({"session_id": session_id})

def update_session(session_id: str, data: dict):
    sessions.update_one(
        {"session_id": session_id},
        {"$set": data},
        upsert=True
    )

def delete_session(session_id: str):
    sessions.delete_one({"session_id": session_id})

# Example usage:
session_id = "user123"
session_data = get_session(session_id)
print(session_data)

for doc in sessions.find():
    print(doc)
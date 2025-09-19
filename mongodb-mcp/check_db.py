#!/usr/bin/env python3
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("ATLAS_URI"))
db = client["hackathon_db"]

print("Collections in hackathon_db:")
for collection_name in db.list_collection_names():
    print(f"  - {collection_name}")
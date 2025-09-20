#!/usr/bin/env python3
import json
import sys
import re
from datetime import datetime, timedelta
from pymongo import MongoClient
import os
import boto3

# Load environment variables only if not in Lambda
if not os.getenv('LAMBDA_RUNTIME'):
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

class GovernmentServiceClient:
    def __init__(self):
        self.mongo_client = MongoClient(os.getenv("ATLAS_URI"))
        self.db = self.mongo_client[os.getenv("ATLAS_DB_NAME", "greataihackathon")]
        # AWS Lambda automatically provides the region via AWS_REGION1 environment variable
        # If not available, fall back to us-east-1
        region = os.environ.get('AWS_REGION1', 'us-east-1')
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)
    
    def parse_instruction(self, instruction: str) -> dict:
        """Parse natural language instruction using AWS Bedrock"""
        import time
        import random
        
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries + 1):
            try:
                prompt = f"""Parse Malaysian government database instruction. Return ONLY valid JSON.

CRITICAL PATTERN RULE: 041223070745 (12 consecutive digits) = identity_no field, NEVER license_number!

Instruction: "{instruction}"

Database Schemas:

accounts: {{
    "beneficiary_name": "string",
    "beneficiary_account": "string", 
    "service": "TNB|JPJ",
    "qr_link": "string",
    "active": boolean
}}

licenses: {{
    "full_name": "string",
    "identity_no": "12-digit string (e.g. 011223071234)",
    "date_of_birth": "YYYY-MM-DD",
    "nationality": "string",
    "license_number": "format: 7digits space 8chars (e.g. 1234567 AbCdEfGh)",
    "license_classes": ["array of strings - A|B|B1|B2|C|D|DA|E|E1|E2|F|G|H|I"],
    "valid_from": "YYYY-MM-DD",
    "valid_to": "YYYY-MM-DD",
    "address": "string",
    "status": "active|expired|suspended"
}}

tnb: {{
    "bill": {{
        "akaun": {{
            "no_akaun": "12-digit account number",
            "no_kontrak": "string",
            "deposit": "number",
            "no_invois": "string",
            "name": "string",
            "address": "string"
        }},
        "meta": {{
            "bil_semasa": {{
                "jumlah": "number",
                "tarikh_bil": "DD-MM-YYYY",
                "bayar_sebelum": "DD-MM-YYYY"
            }}
        }}
    }},
    "status": "paid|unpaid|overdue",
    "pembayaran": {{
        "jumlah": "number",
        "tarikh_bayar": "DD-MM-YYYY",
        "kaedah": "string",
        "rujukan": "string"
    }}
}}

transactions: {{
    "transaction_id": "string",
    "reference_id": "string",
    "transaction_date": "YYYY-MM-DD",
    "transaction_type": "string",
    "amount": "number",
    "currency": "string",
    "fees": "number",
    "status": "string",
    "sender_bank": "string",
    "sender_account": "string",
    "sender_name": "string",
    "beneficiary_bank": "string",
    "beneficiary_account": "string",
    "beneficiary_name": "string",
    "service_type": "JPJ" | "TNB" | "Other",
    "bill_reference": "string",
    "payment_details": "string",
    "notes": "string",
    "created_at": "YYYY-MM-DD"
}}

INTELLIGENT FIELD MAPPING:

ANALYZE INTENT AND CONTEXT:
1. Identify the main action (find, update, create)
2. Determine the target entity (license, TNB bill, account, transaction)
3. Extract relevant numbers and their patterns
4. Map to appropriate fields based on context

NUMBER PATTERN RECOGNITION - CRITICAL:
- Pattern: 12 consecutive digits (like 041223070745) in license context → ALWAYS identity_no field
- Pattern: 7digits space 8alphanumeric (like "1234567 AbCdEfGh") → license_number field
- Pattern: 12 consecutive digits + TNB context → account_no field
- Keyword "account" + number → account_no field

IMPORTANT: 041223070745 = 12 digits = identity_no (NOT license_number)

CRITICAL EXAMPLE: "Extend 2 years licence 041223070745" MUST use identity_no field!

CONTEXT KEYWORDS:
- Account: "account", "service", "beneficiary", "find account", "account from", "service account"
- License: "license", "licence", "driving", "extend", "renew", "validity"  
- TNB: "tnb", "bill", "owe", "debt", "payment", "paid"
- Transaction: "transaction", "payment", "receipt", "reference"

PRIORITY RULES:
1. If query contains "account" as the main entity (e.g., "find account", "account from") → collection: "accounts"
2. If query contains "bill" or payment context with TNB → collection: "tnb"
3. If query contains license-related keywords → collection: "licenses"
4. If query contains transaction-related keywords → collection: "transactions"

SEMANTIC PATTERNS - Use similar intent and structure:

TNB QUERIES:
- Intent: Find/check TNB bills or debt → collection: "tnb", operation: "find"
- Intent: Find UNPAID TNB bills → collection: "tnb", operation: "find", status_filter: "unpaid"
- Intent: Update TNB payment only → collection: "tnb", operation: "update", special_logic: "tnb_payment"
- Intent: Update TNB payment AND create transaction → collection: "tnb", operation: "update", special_logic: "tnb_payment_with_transaction"
- Numbers: 12 digits in TNB context → account_no field (simple format: {{"account_no": "number"}})
- Keywords: "and record transaction", "and create transaction" → use tnb_payment_with_transaction
- TNB + transaction keywords: "TNB" + ("transaction details" OR "beneficiary_name" OR "reference_id") → use tnb_payment_with_transaction
- When TNB context + JSON transaction details provided → ALWAYS use tnb_payment_with_transaction and extract all transaction fields
- Keywords: "unpaid", "outstanding", "not paid" → add status_filter: "unpaid"

CRITICAL: TNB queries use simple account_no format, NOT nested bill.akaun.no_akaun structure!

TNB TRANSACTION DETECTION RULES:
- TNB bill update + detailed transaction info → use tnb_payment_with_transaction
- Keywords: "TNB bill" + "transaction details" → tnb_payment_with_transaction
- Pattern: "Update TNB" + JSON with transaction fields → tnb_payment_with_transaction
- Context: TNB account number + beneficiary details → tnb_payment_with_transaction

CRITICAL AMOUNT FIELD RULE:
- NEVER include both "payment_amount" and "amount" fields in the same response
- Use "payment_amount" for TNB payment operations (tnb_payment, tnb_payment_with_transaction)
- Use "amount" for transaction creation operations (create_transaction, process_payment)
- If JSON contains amount, extract it ONCE into the appropriate field based on operation type

JPJ QUERIES:
- Intent: Create JPJ transaction → collection: "transactions", operation: "create", special_logic: "create_transaction"
- Keywords: "JPJ account", "to JPJ" → service_type: "JPJ"
- Intent: Payment to JPJ with transaction creation → create_transaction with service_type JPJ

LICENSE QUERIES:
- Intent: Find/search license → collection: "licenses", operation: "find"
- Intent: Extend/renew license → collection: "licenses", operation: "update", special_logic: "license_extend"
- Numbers: 12 consecutive digits (like 041223070745) → MUST BE identity_no field, NEVER license_number
- Numbers: 7digits space 8chars (like "1234567 AbCdEfGh") → MUST BE license_number field

CRITICAL: 041223070745 is 12 consecutive digits = identity_no, NOT license_number!

TRANSACTION OPERATIONS:
- Intent: Create new transaction → collection: "transactions", operation: "create", special_logic: "create_transaction"
- Intent: Process payment receipt → special_logic: "process_payment"
- Intent: Create transaction AND update TNB bill → special_logic: "process_payment"
- Keywords: "create transaction", "transaction record", "DuitNow transaction" → use create_transaction
- Keywords: "update TNB bill if applicable", "update TNB bill", "if applicable" → use process_payment

CRITICAL: "Create transaction" ALWAYS needs collection: "transactions", operation: "create", special_logic: "create_transaction"

ACCOUNT QUERIES:
- Intent: Find service accounts → collection: "accounts", operation: "find"
- Keywords: "account from", "account for", "find account", "service account" → collection: "accounts"
- Keywords: "TNB service", "JPJ service" → filter by service field
- Context: When user specifically mentions "account" as the main entity → ALWAYS use accounts collection

EXAMPLES - FOLLOW EXACTLY:
- "Search license for 041223070745" → 12 digits = identity → {{"collection": "licenses", "operation": "find", "query": {{"identity_no": "041223070745"}}}}
- "Extend 3 years licence 041223070745" → 12 digits = identity → {{"collection": "licenses", "operation": "update", "query": {{"identity_no": "041223070745"}}, "special_logic": "license_extend", "extend_years": 3}}
- "Search license for 1234567 AbCdEfGh" → 7digits+space+8chars → {{"collection": "licenses", "operation": "find", "query": {{"license_number": "1234567 AbCdEfGh"}}}}
- "Extend 2 years licence 1234567 AbCdEfGh" → 7digits+space+8chars → {{"collection": "licenses", "operation": "update", "query": {{"license_number": "1234567 AbCdEfGh"}}, "special_logic": "license_extend", "extend_years": 2}}
- "Update TNB bill 220001234521 paid RM 45.67 reference 837356732M" → TNB payment → {{"collection": "tnb", "operation": "update", "query": {{"account_no": "220001234521"}}, "special_logic": "tnb_payment", "payment_amount": 45.67, "reference_no": "837356732M"}}
- "Update TNB bill 220001234513 paid full today using Online Banking" → Full payment without reference → {{"collection": "tnb", "operation": "update", "query": {{"account_no": "220001234513"}}, "special_logic": "tnb_payment", "reference_no": "MANUAL_PAYMENT"}}
- "Update TNB bill 220001234513 paid RM 45.67 via DuitNow reference 837356732M" → TNB payment → {{"collection": "tnb", "operation": "update", "query": {{"account_no": "220001234513"}}, "special_logic": "tnb_payment", "payment_amount": 45.67, "reference_no": "837356732M"}}
- "Update TNB bill 220001234513 paid RM 45.67 via DuitNow reference 837356732M and record transaction" → TNB + Transaction → {{"collection": "tnb", "operation": "update", "query": {{"account_no": "220001234513"}}, "special_logic": "tnb_payment_with_transaction", "payment_amount": 45.67, "reference_no": "837356732M"}}
- "Update TNB bill 220001234513 paid RM 100.00 via Maybank with transaction details: beneficiary_name Tenaga Nasional, reference_id OLB20250918003" → TNB + Transaction Details → {{"collection": "tnb", "operation": "update", "query": {{"account_no": "220001234513"}}, "special_logic": "tnb_payment_with_transaction", "payment_amount": 100.0, "reference_no": "OLB20250918003", "beneficiary_name": "Tenaga Nasional", "receiving_bank": "Maybank"}}
- "Update TNB bill 220001234513 with transaction details JSON containing amount RM 60.00" → TNB + Transaction → {{"collection": "tnb", "operation": "update", "query": {{"account_no": "220001234513"}}, "special_logic": "tnb_payment_with_transaction", "payment_amount": 60.0, "reference_no": "OLB20250918003"}}
- "Find latest unpaid TNB bills for account number 220001234513" → Find unpaid only → {{"collection": "tnb", "operation": "find", "query": {{"account_no": "220001234513"}}, "status_filter": "unpaid"}}
- "Create DuitNow transaction: reference 837356732M, RM 40.00, Jabatan Pengangkutan Jalan Malaysia, account 5123456789012345, Maybank, license renewal, recipient ref 0488-MB-MAYBANK22/43" → Detailed transaction → {{"collection": "transactions", "operation": "create", "special_logic": "create_transaction", "reference_id": "837356732M", "amount": 40.00, "beneficiary_name": "Jabatan Pengangkutan Jalan Malaysia", "beneficiary_account": "5123456789012345", "receiving_bank": "Maybank", "payment_details": "license renewal", "recipient_reference": "0488-MB-MAYBANK22/43", "service_type": "JPJ"}}
- "Create transaction record via DuitNow with transaction details: beneficiary_name Jabatan Pengangkutan, reference_id 837356732M, amount RM 40.00" → Transaction via DuitNow → {{"collection": "transactions", "operation": "create", "special_logic": "create_transaction", "reference_id": "837356732M", "amount": 40.00, "beneficiary_name": "Jabatan Pengangkutan", "service_type": "JPJ"}}
- "DuitNow payment 837356732M of RM 100.00 to JPJ account 220001234513 and create transaction record" → JPJ Transaction → {{"collection": "transactions", "operation": "create", "special_logic": "create_transaction", "reference_id": "837356732M", "amount": 100.00, "service_type": "JPJ"}}
- "Create transaction and update TNB bill 220001234513 if applicable" → Process Payment → {{"collection": "transactions", "operation": "create", "special_logic": "process_payment", "reference_id": "837356732M", "amount": 100.00, "bill_reference": "220001234513", "beneficiary_name": "DELLAND PROPERTY MANAGEMENT SDN BHD"}}
- "Find account from TNB service" → Find TNB account → {{"collection": "accounts", "operation": "find", "query": {{"service": "TNB"}}}}
- "Find account from JPJ service" → Find JPJ account → {{"collection": "accounts", "operation": "find", "query": {{"service": "JPJ"}}}}
- "Find all accounts" → Find all accounts → {{"collection": "accounts", "operation": "find", "query": {{}}}}
- "Get service account details" → Find accounts → {{"collection": "accounts", "operation": "find", "query": {{}}}}

SPECIAL LOGIC TRIGGERS:
- license_extend: When intent is to extend/renew license validity
- tnb_payment: When intent is to update TNB bill with payment information only
- tnb_payment_with_transaction: When intent is to update TNB bill AND create transaction record
- create_transaction: When intent is to create new transaction record only
- process_payment: When intent is to process payment receipt with multiple details

Return JSON format:
{{
    "collection": "accounts|licenses|tnb|transactions",
    "operation": "find|update|create",
    "query": {{"field": "value"}},
    "status_filter": "unpaid|paid|partial",
    "special_logic": "license_extend|tnb_payment|tnb_payment_with_transaction|create_transaction|process_payment",
    "extend_years": number,
    "reference_no": "string",
    "payment_amount": number,
    "reference_id": "string",
    "amount": number,
    "beneficiary_name": "string",
    "beneficiary_account": "string",
    "receiving_bank": "string",
    "payment_details": "string",
    "recipient_reference": "string",
    "transaction_date": "string",
    "successful_timestamp": "string",
    "service_type": "string"
}}

CRITICAL: ALWAYS include collection, operation, and special_logic fields in the response!"""

                response = self.bedrock.invoke_model(
                    modelId=os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0'),
                    body=json.dumps({
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 300,
                        "messages": [{"role": "user", "content": prompt}]
                    })
                )
                
                result = json.loads(response['body'].read())
                content = result['content'][0]['text'].strip()
                
                # Extract JSON from response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    parsed = json.loads(content[json_start:json_end])
                    return parsed
                
                return {"collection": "unknown", "operation": "unknown", "error": "Could not parse JSON from response"}
            
            except Exception as e:
                if "ThrottlingException" in str(e) and attempt < max_retries:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"Rate limited, retrying in {delay:.1f} seconds... (attempt {attempt + 1}/{max_retries + 1})")
                    time.sleep(delay)
                    continue
                
                print(f"Bedrock error: {e}")
                return {"collection": "unknown", "operation": "unknown", "error": str(e)}
        
        return {"collection": "unknown", "operation": "unknown", "error": "Max retries exceeded"}
    
    def execute_operation(self, operation_data: dict) -> dict:
        """Execute MongoDB operation"""
        try:
            collection_name = operation_data.get("collection")
            operation = operation_data.get("operation")
            query = operation_data.get("query", {})
            special_logic = operation_data.get("special_logic")
            

            
            if not collection_name or collection_name not in ["accounts", "licenses", "tnb", "transactions"]:
                return {"success": False, "error": "Invalid collection"}
            
            collection = self.db[collection_name]
            
            if operation == "find":
                
                # Handle TNB bill query structure
                if collection_name == "tnb" and "account_no" in query:
                    tnb_query = {"bill.akaun.no_akaun": query["account_no"]}
                    
                    # Check if we need to filter by unpaid status specifically
                    if operation_data.get("status_filter") == "unpaid":
                        tnb_query["status"] = "unpaid"
                    
                    query = tnb_query
                
                docs = list(collection.find(query).limit(10))
                for doc in docs:
                    doc["_id"] = str(doc["_id"])
                
                # License suspension check
                if collection_name == "licenses" and docs:
                    for doc in docs:
                        if doc.get("status") == "suspended":
                            return {
                                "success": True,
                                "documents": docs,
                                "warning": "License suspended. Please visit physical branch."
                            }
                
                return {"success": True, "count": len(docs), "documents": docs}
            
            elif operation == "update":
                if special_logic == "license_extend":
                    return self._handle_license_extend(operation_data)
                elif special_logic == "tnb_payment":
                    return self._handle_tnb_payment(operation_data)
                elif special_logic == "tnb_payment_with_transaction":
                    return self._handle_tnb_payment_with_transaction(operation_data)
                else:
                    update_data = operation_data.get("update_data", {})
                    result = collection.update_one(query, {"$set": update_data})
                    return {"success": True, "modified_count": result.modified_count}
            
            elif operation == "create":
                if special_logic == "create_transaction":
                    return self._handle_create_transaction(operation_data)
                elif special_logic == "process_payment":
                    return self._handle_process_payment(operation_data)
                else:
                    create_data = operation_data.get("create_data", {})
                    result = collection.insert_one(create_data)
                    return {"success": True, "inserted_id": str(result.inserted_id)}
            
            return {"success": False, "error": f"Unknown operation: {operation}"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_license_extend(self, operation_data: dict) -> dict:
        """Handle license extension"""
        query = operation_data.get("query", {})
        extend_years = operation_data.get("extend_years", 2)
        
        # Validate extend_years is integer between 1-10
        try:
            extend_years = int(extend_years)
            if extend_years < 1 or extend_years > 10:
                return {"success": False, "error": "License validity can only be extended from 1 to 10 years"}
        except (ValueError, TypeError):
            return {"success": False, "error": "License extension years must be a valid integer between 1-10"}
        
        license_doc = self.db.licenses.find_one(query)
        if not license_doc:
            return {"success": False, "error": "License not found"}
        
        if license_doc.get("status") == "suspended":
            return {"success": False, "error": "License suspended. Please visit physical branch."}
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        if license_doc.get("status") == "expired":
            new_valid_from = today
            new_valid_to = (datetime.now() + timedelta(days=365 * extend_years)).strftime("%Y-%m-%d")
        else:
            current_valid_to = datetime.strptime(license_doc["valid_to"], "%Y-%m-%d")
            new_valid_from = license_doc["valid_from"]
            new_valid_to = (current_valid_to + timedelta(days=365 * extend_years)).strftime("%Y-%m-%d")
        
        result = self.db.licenses.update_one(
            query,
            {"$set": {"valid_from": new_valid_from, "valid_to": new_valid_to, "status": "active"}}
        )
        
        # Retrieve the updated document
        updated_license = self.db.licenses.find_one(query)
        if updated_license:
            updated_license["_id"] = str(updated_license["_id"])
        
        return {
            "success": True, 
            "message": f"License extended to {new_valid_to}", 
            "modified_count": result.modified_count,
            "documents": {
                "licenses": updated_license
            }
        }
    
    def _handle_tnb_payment(self, operation_data: dict) -> dict:
        """Handle TNB payment"""
        query = operation_data.get("query", {})
        reference_no = operation_data.get("reference_no", "MANUAL_PAYMENT")
        payment_amount = operation_data.get("payment_amount")
        today = datetime.now().strftime("%Y-%m-%d")
        
        if "account_no" in query:
            query = {"bill.akaun.no_akaun": query["account_no"]}
        
        tnb_doc = self.db.tnb.find_one(query)
        if not tnb_doc:
            return {"success": False, "error": "TNB bill not found"}
        
        if tnb_doc.get("pembayaran") is not None:
            return {"success": False, "error": "Bill already has payment record. No further updates allowed."}
        
        bill_amount = tnb_doc.get("bill", {}).get("meta", {}).get("bil_semasa", {}).get("jumlah", 0)
        
        # Priority: payment_amount > JSON amount > full bill amount
        if payment_amount:
            final_amount = payment_amount
        else:
            # Check if amount is provided in operation_data (from JSON)
            json_amount = operation_data.get("amount")
            if json_amount:
                final_amount = json_amount
            else:
                final_amount = bill_amount
                
        new_status = "paid" if final_amount >= bill_amount else "partial"
        
        result = self.db.tnb.update_one(
            query,
            {"$set": {
                "status": new_status,
                "pembayaran": {
                    "jumlah": final_amount,
                    "tarikh_bayar": today,
                    "kaedah": "Online Banking",
                    "rujukan": reference_no
                }
            }}
        )
        
        # Retrieve the updated TNB bill document
        updated_tnb_doc = self.db.tnb.find_one(query)
        if updated_tnb_doc:
            updated_tnb_doc["_id"] = str(updated_tnb_doc["_id"])
        
        return {
            "success": True, 
            "message": f"Payment of RM{final_amount} updated", 
            "modified_count": result.modified_count,
            "documents": {
                "tnb": updated_tnb_doc
            }
        }
    
    def _handle_create_transaction(self, operation_data: dict) -> dict:
        """Handle transaction creation"""
        reference_id = operation_data.get("reference_id")
        amount = operation_data.get("amount")
        service_type = operation_data.get("service_type", "Other")
        # Use provided transaction_date or default to today
        transaction_date = operation_data.get("transaction_date") or operation_data.get("successful_timestamp")
        if transaction_date:
            # Parse provided date and convert to ISO format
            try:
                if "T" in transaction_date:
                    today = transaction_date
                else:
                    # Handle formats like "15 Sep 2025, 3:13 PM"
                    parsed_date = datetime.strptime(transaction_date, "%d %b %Y, %I:%M %p")
                    today = parsed_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            except:
                today = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            today = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Use provided transaction details or lookup from accounts
        beneficiary_name = operation_data.get("beneficiary_name")
        beneficiary_account = operation_data.get("beneficiary_account")
        receiving_bank = operation_data.get("receiving_bank")
        payment_details = operation_data.get("payment_details")
        
        # If no beneficiary details provided, lookup from accounts collection
        if not beneficiary_name and service_type in ["TNB", "JPJ"]:
            account_doc = self.db.accounts.find_one({"service": service_type})
            if account_doc:
                beneficiary_name = account_doc.get("beneficiary_name")
                beneficiary_account = account_doc.get("beneficiary_account")
                receiving_bank = account_doc.get("beneficiary_bank")
        
        transaction_doc = {
            "transaction_id": f"TXN_{reference_id}",
            "reference_id": reference_id,
            "transaction_date": today,
            "transaction_type": "Payment",
            "amount": amount,
            "currency": "MYR",
            "fees": 0.0,
            "status": "Successful",
            "sender_bank": "Unknown",
            "sender_account": "Unknown",
            "sender_name": "Unknown",
            "beneficiary_bank": receiving_bank or "Unknown",
            "beneficiary_account": beneficiary_account or "Unknown",
            "beneficiary_name": beneficiary_name or "Unknown",
            "service_type": "JPJ" if "JPJ" in (beneficiary_name or "") or "Jabatan Pengangkutan" in (beneficiary_name or "") else service_type,
            "bill_reference": "",
            "payment_details": payment_details or f"Payment to {beneficiary_name or service_type}",
            "notes": operation_data.get("recipient_reference", ""),
            "created_at": today
        }
        
        result = self.db.transactions.insert_one(transaction_doc)
        
        # Add the _id to the document for response
        transaction_doc["_id"] = str(result.inserted_id)
        
        return {
            "success": True, 
            "message": f"Transaction {reference_id} created", 
            "inserted_id": str(result.inserted_id),
            "documents": {
                "transactions": transaction_doc
            }
        }
    
    def _handle_process_payment(self, operation_data: dict) -> dict:
        """Handle payment processing with TNB bill check"""
        reference_id = operation_data.get("reference_id")
        amount = operation_data.get("amount")
        beneficiary_name = operation_data.get("beneficiary_name")
        beneficiary_account = operation_data.get("beneficiary_account", "Unknown")
        bill_reference = operation_data.get("bill_reference")
        # Use provided transaction_date or default to today
        transaction_date = operation_data.get("transaction_date") or operation_data.get("successful_timestamp")
        if transaction_date:
            try:
                if "T" in transaction_date:
                    today = transaction_date
                else:
                    parsed_date = datetime.strptime(transaction_date, "%d %b %Y, %I:%M %p")
                    today = parsed_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            except:
                today = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            today = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Check TNB bill if bill_reference is provided
        if bill_reference:
            tnb_doc = self.db.tnb.find_one({"bill.akaun.no_akaun": bill_reference})
            if tnb_doc and tnb_doc.get("pembayaran") is not None:
                return {"success": False, "error": f"TNB bill {bill_reference} already has payment record. No further updates allowed."}
        
        transaction_doc = {
            "transaction_id": f"TXN_{reference_id}",
            "reference_id": reference_id,
            "transaction_date": today,
            "transaction_type": "Payment Receipt",
            "amount": amount,
            "currency": "MYR",
            "fees": 0.0,
            "status": "Successful",
            "sender_bank": "Unknown",
            "sender_account": "Unknown",
            "sender_name": "Unknown",
            "beneficiary_bank": "Unknown",
            "beneficiary_account": beneficiary_account,
            "beneficiary_name": beneficiary_name,
            "service_type": "Government Services",
            "bill_reference": bill_reference or "",
            "payment_details": f"Payment processed for {beneficiary_name}",
            "notes": "",
            "created_at": today
        }
        
        result = self.db.transactions.insert_one(transaction_doc)
        
        # Update TNB bill if applicable and pembayaran is null
        if bill_reference and tnb_doc:
            bill_amount = tnb_doc.get("bill", {}).get("meta", {}).get("bil_semasa", {}).get("jumlah", 0)
            new_status = "paid" if amount >= bill_amount else "partial"
            
            self.db.tnb.update_one(
                {"bill.akaun.no_akaun": bill_reference},
                {"$set": {
                    "status": new_status,
                    "pembayaran": {
                        "jumlah": amount,
                        "tarikh_bayar": today,
                        "kaedah": "Online Banking",
                        "rujukan": reference_id
                    }
                }}
            )
            
            # Get the updated TNB document and created transaction
            updated_tnb = self.db.tnb.find_one({"bill.akaun.no_akaun": bill_reference})
            created_transaction = self.db.transactions.find_one({"_id": result.inserted_id})
            
            return {
                "success": True, 
                "message": f"Payment {reference_id} processed and TNB bill {bill_reference} updated", 
                "inserted_id": str(result.inserted_id),
                "documents": {
                    "transactions": created_transaction,
                    "tnb": updated_tnb
                }
            }
        
        # Get the created transaction
        created_transaction = self.db.transactions.find_one({"_id": result.inserted_id})
        
        return {
            "success": True, 
            "message": f"Payment {reference_id} processed", 
            "inserted_id": str(result.inserted_id),
            "documents": {
                "transactions": created_transaction
            }
        }
    
    def _handle_tnb_payment_with_transaction(self, operation_data: dict) -> dict:
        """Handle TNB payment update and create transaction record"""
        # First update TNB payment
        tnb_result = self._handle_tnb_payment(operation_data)
        if not tnb_result.get("success"):
            return tnb_result
        
        # Get TNB account details from accounts collection
        tnb_account = self.db.accounts.find_one({"service": "TNB"})
        
        # Then create transaction record
        reference_id = operation_data.get("reference_no", "MANUAL_PAYMENT")
        
        # Priority: payment_amount > JSON amount > 0
        payment_amount = operation_data.get("payment_amount")
        if payment_amount:
            amount = payment_amount
        else:
            # Use JSON amount if payment_amount not provided
            json_amount = operation_data.get("amount")
            amount = json_amount if json_amount else 0
            
        account_no = operation_data.get("query", {}).get("account_no", "Unknown")
        # Use provided transaction_date or default to today
        transaction_date = operation_data.get("transaction_date") or operation_data.get("successful_timestamp")
        if transaction_date:
            try:
                if "T" in transaction_date:
                    today = transaction_date
                else:
                    parsed_date = datetime.strptime(transaction_date, "%d %b %Y, %I:%M %p")
                    today = parsed_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            except:
                today = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            today = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        transaction_doc = {
            "transaction_id": f"TXN_{reference_id}",
            "reference_id": reference_id,
            "transaction_date": today,
            "transaction_type": "Payment",
            "amount": amount,
            "currency": "MYR",
            "fees": 0.0,
            "status": "Successful",
            "sender_bank": "Unknown",
            "sender_account": "Unknown",
            "sender_name": "Unknown",
            "beneficiary_bank": operation_data.get("receiving_bank") or (tnb_account.get("beneficiary_bank", "Unknown") if tnb_account else "Unknown"),
            "beneficiary_account": operation_data.get("beneficiary_account") or (tnb_account.get("beneficiary_account", account_no) if tnb_account else account_no),
            "beneficiary_name": operation_data.get("beneficiary_name") or (tnb_account.get("beneficiary_name", "Tenaga Nasional Berhad") if tnb_account else "Tenaga Nasional Berhad"),
            "service_type": "TNB",
            "bill_reference": account_no,
            "payment_details": operation_data.get("payment_details") or f"TNB bill payment for account {account_no}",
            "notes": operation_data.get("recipient_reference", ""),
            "created_at": today
        }
        
        transaction_result = self.db.transactions.insert_one(transaction_doc)
        
        # Retrieve the updated TNB bill document
        tnb_query = {"bill.akaun.no_akaun": account_no}
        updated_tnb_doc = self.db.tnb.find_one(tnb_query)
        if updated_tnb_doc:
            updated_tnb_doc["_id"] = str(updated_tnb_doc["_id"])
        
        # Add the _id to the transaction document for response
        transaction_doc["_id"] = str(transaction_result.inserted_id)
        
        return {
            "success": True,
            "message": f"TNB payment updated and transaction {reference_id} created",
            "tnb_update": tnb_result,
            "transaction_id": str(transaction_result.inserted_id),
            "documents": {
                "tnb": updated_tnb_doc,
                "transactions": transaction_doc
            }
        }
    


def main():
    client = GovernmentServiceClient()
    
    if len(sys.argv) >= 2:
        instruction = sys.argv[1]
        execute_instruction(client, instruction)
    else:
        print("Government Services Database Client (Bedrock AI)")
        print("Type 'exit' or 'quit' to stop")
        print("-" * 50)
        
        while True:
            try:
                print("Enter instruction (Ctrl+Z for multi-line, then Enter):")
                lines = []
                while True:
                    try:
                        line = input("" if not lines else "... ")
                        lines.append(line)
                    except EOFError:
                        break
                    except KeyboardInterrupt:
                        if lines:
                            print("\nMulti-line input cancelled")
                            lines = []
                            break
                        else:
                            print("\nGoodbye!")
                            return
                
                instruction = " ".join(lines).strip()
                if instruction.lower() in ['exit', 'quit', 'q']:
                    break
                if instruction:
                    execute_instruction(client, instruction)
                    print()
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break

def execute_instruction(client, instruction):
    print(f"Executing: {instruction}")
    print("-" * 50)
    
    operation_data = client.parse_instruction(instruction)
    print(f"Parsed: {json.dumps(operation_data, indent=2, default=str)}")
    print("-" * 50)
    
    result = client.execute_operation(operation_data)
    print(f"Result: {json.dumps(result, indent=2, default=str)}")

if __name__ == "__main__":
    main()
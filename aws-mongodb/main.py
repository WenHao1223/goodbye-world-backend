#!/usr/bin/env python3
import json
import sys
import re
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import boto3

load_dotenv()

class GovernmentServiceClient:
    def __init__(self):
        self.mongo_client = MongoClient(os.getenv("ATLAS_URI"))
        self.db = self.mongo_client[os.getenv("ATLAS_DB_NAME", "greataihackathon")]
        self.bedrock = boto3.client('bedrock-runtime', region_name=os.getenv('AWS_REGION', 'us-east-1'))
    
    def parse_instruction(self, instruction: str) -> dict:
        """Parse natural language instruction using AWS Bedrock"""
        try:
            prompt = f"""Parse Malaysian government database instruction. Return ONLY valid JSON.

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
        "cara": "string",
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

CONTEXT KEYWORDS:
- License: "license", "licence", "driving", "extend", "renew", "validity"
- TNB: "tnb", "bill", "owe", "debt", "payment", "paid"
- Transaction: "transaction", "payment", "receipt", "reference"
- Account: "account", "service", "beneficiary"

SEMANTIC PATTERNS - Use similar intent and structure:

TNB QUERIES:
- Intent: Find/check TNB bills or debt → collection: "tnb", operation: "find"
- Intent: Update TNB payment only → collection: "tnb", operation: "update", special_logic: "tnb_payment"
- Intent: Update TNB payment AND create transaction → collection: "tnb", operation: "update", special_logic: "tnb_payment_with_transaction"
- Numbers: 12 digits in TNB context → account_no field (simple format: {{"account_no": "number"}})
- Keywords: "and record transaction", "and create transaction" → use tnb_payment_with_transaction

CRITICAL: TNB queries use simple account_no format, NOT nested bill.akaun.no_akaun structure!

LICENSE QUERIES:
- Intent: Find/search license → collection: "licenses", operation: "find"
- Intent: Extend/renew license → collection: "licenses", operation: "update", special_logic: "license_extend"
- Numbers: 12 consecutive digits (like 041223070745) → MUST BE identity_no field, NEVER license_number
- Numbers: 7digits space 8chars (like "1234567 AbCdEfGh") → MUST BE license_number field

CRITICAL: 041223070745 is 12 consecutive digits = identity_no, NOT license_number!

TRANSACTION OPERATIONS:
- Intent: Create new transaction → collection: "transactions", operation: "create", special_logic: "create_transaction"
- Intent: Process payment receipt → special_logic: "process_payment"

ACCOUNT QUERIES:
- Intent: Find service accounts → collection: "accounts", operation: "find"

EXAMPLES - FOLLOW EXACTLY:
- "Search license for 041223070745" → 12 digits = identity → {{"collection": "licenses", "operation": "find", "query": {{"identity_no": "041223070745"}}}}
- "Extend 3 years licence 041223070745" → 12 digits = identity → {{"collection": "licenses", "operation": "update", "query": {{"identity_no": "041223070745"}}, "special_logic": "license_extend", "extend_years": 3}}
- "Search license for 1234567 AbCdEfGh" → 7digits+space+8chars → {{"collection": "licenses", "operation": "find", "query": {{"license_number": "1234567 AbCdEfGh"}}}}
- "Extend 2 years licence 1234567 AbCdEfGh" → 7digits+space+8chars → {{"collection": "licenses", "operation": "update", "query": {{"license_number": "1234567 AbCdEfGh"}}, "special_logic": "license_extend", "extend_years": 2}}
- "Update TNB bill 220001234521 paid RM 45.67 reference 837356732M" → TNB payment → {{"collection": "tnb", "operation": "update", "query": {{"account_no": "220001234521"}}, "special_logic": "tnb_payment", "payment_amount": 45.67, "reference_no": "837356732M"}}
- "Update TNB bill 220001234513 paid RM 45.67 via DuitNow reference 837356732M" → TNB payment → {{"collection": "tnb", "operation": "update", "query": {{"account_no": "220001234513"}}, "special_logic": "tnb_payment", "payment_amount": 45.67, "reference_no": "837356732M"}}
- "Update TNB bill 220001234513 paid RM 45.67 via DuitNow reference 837356732M and record transaction" → TNB + Transaction → {{"collection": "tnb", "operation": "update", "query": {{"account_no": "220001234513"}}, "special_logic": "tnb_payment_with_transaction", "payment_amount": 45.67, "reference_no": "837356732M"}}

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
    "special_logic": "license_extend|tnb_payment|tnb_payment_with_transaction|create_transaction|process_payment",
    "extend_years": number,
    "reference_no": "string",
    "payment_amount": number,
    "reference_id": "string",
    "amount": number,
    "beneficiary_name": "string",
    "beneficiary_account": "string"
}}"""

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
            print(f"Bedrock error: {e}")
            return {"collection": "unknown", "operation": "unknown", "error": str(e)}
    
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
                    query = {"bill.akaun.no_akaun": query["account_no"]}
                
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
        
        return {"success": True, "message": f"License extended to {new_valid_to}", "modified_count": result.modified_count}
    
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
        
        if tnb_doc.get("status") == "paid":
            return {"success": False, "error": "Bill already paid"}
        
        bill_amount = tnb_doc.get("bill", {}).get("meta", {}).get("bil_semasa", {}).get("jumlah", 0)
        final_amount = payment_amount if payment_amount else bill_amount
        new_status = "paid" if final_amount >= bill_amount else "partial"
        
        result = self.db.tnb.update_one(
            query,
            {"$set": {
                "status": new_status,
                "pembayaran": {
                    "jumlah": final_amount,
                    "tarikh_bayar": today,
                    "cara": "Online Banking",
                    "rujukan": reference_no
                }
            }}
        )
        
        return {"success": True, "message": f"Payment of RM{final_amount} updated", "modified_count": result.modified_count}
    
    def _handle_create_transaction(self, operation_data: dict) -> dict:
        """Handle transaction creation"""
        reference_id = operation_data.get("reference_id")
        amount = operation_data.get("amount")
        beneficiary_name = operation_data.get("beneficiary_name")
        service_type = operation_data.get("service_type", "TNB" if "TNB" in str(beneficiary_name).upper() or "TNB" in str(beneficiary_name).upper() else "Other")
        today = datetime.now().strftime("%Y-%m-%d")
        
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
            "beneficiary_bank": "Unknown",
            "beneficiary_account": "Unknown",
            "beneficiary_name": beneficiary_name,
            "service_type": service_type,
            "bill_reference": "",
            "payment_details": f"Transaction for {beneficiary_name}",
            "notes": "",
            "created_at": today
        }
        
        result = self.db.transactions.insert_one(transaction_doc)
        return {"success": True, "message": f"Transaction {reference_id} created", "inserted_id": str(result.inserted_id)}
    
    def _handle_process_payment(self, operation_data: dict) -> dict:
        """Handle payment processing"""
        reference_id = operation_data.get("reference_id")
        amount = operation_data.get("amount")
        beneficiary_name = operation_data.get("beneficiary_name")
        beneficiary_account = operation_data.get("beneficiary_account", "Unknown")
        today = datetime.now().strftime("%Y-%m-%d")
        
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
            "bill_reference": "",
            "payment_details": f"Payment processed for {beneficiary_name}",
            "notes": "",
            "created_at": today
        }
        
        result = self.db.transactions.insert_one(transaction_doc)
        return {"success": True, "message": f"Payment {reference_id} processed", "inserted_id": str(result.inserted_id)}
    
    def _handle_tnb_payment_with_transaction(self, operation_data: dict) -> dict:
        """Handle TNB payment update and create transaction record"""
        # First update TNB payment
        tnb_result = self._handle_tnb_payment(operation_data)
        if not tnb_result.get("success"):
            return tnb_result
        
        # Then create transaction record
        reference_id = operation_data.get("reference_no", "MANUAL_PAYMENT")
        amount = operation_data.get("payment_amount", 0)
        account_no = operation_data.get("query", {}).get("account_no", "Unknown")
        
        transaction_data = {
            "reference_id": reference_id,
            "amount": amount,
            "beneficiary_name": "Tenaga Nasional Berhad",
            "beneficiary_account": account_no,
            "service_type": "TNB"
        }
        
        transaction_result = self._handle_create_transaction(transaction_data)
        
        return {
            "success": True,
            "message": f"TNB payment updated and transaction {reference_id} created",
            "tnb_update": tnb_result,
            "transaction_created": transaction_result
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
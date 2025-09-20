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
    
    def parse_instruction(self, instruction: str) -> dict:
        """Parse natural language instruction using AWS Bedrock"""
        # Force fallback since AI keeps mapping incorrectly
        return self._fallback_parse(instruction)
        
        try:
            bedrock = boto3.client('bedrock-runtime', region_name=os.getenv('AWS_REGION', 'us-east-1'))
            
            prompt = f"""Parse Malaysian government database instruction. Return only JSON.

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

IMPORTANT FIELD MAPPING RULES:
- If searching for 12 consecutive digits (e.g. 011223071234) → use identity_no field
- If searching for format "7digits space 8chars" (e.g. 1234567 AbCdEfGh) → use license_number field

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
            }},
            "butiran": {{
                "tunggakan": "number",
                "caj_semasa": "number",
                "penggenapan": "number"
            }},
            "bil_terdahulu": {{
                "jumlah": "number",
                "tarikh_bil": "DD-MM-YYYY"
            }},
            "bayaran_akhir": {{
                "jumlah": "number",
                "tarikh_bayar": "DD-MM-YYYY"
            }},
            "jenis_bacaan": "string"
        }},
        "tarif": {{
            "tempoh": {{
                "dari": "DD-MM-YYYY",
                "hingga": "DD-MM-YYYY",
                "hari": "number"
            }},
            "jenis": "string",
            "faktor_prorata": "number",
            "blok": [{{"kWh": "number", "kadar": "number", "jumlah": "number"}}],
            "jumlah_kWh": "number",
            "jumlah_amaun": "number"
        }},
        "caj": {{
            "kegunaan": {{
                "tidak_kena_ST": {{"kWh": "number", "RM": "number"}},
                "kena_ST": {{"kWh": "number", "RM": "number"}},
                "jumlah": {{"kWh": "number", "RM": "number"}}
            }},
            "service_tax": "number",
            "kwtbb": "number"
        }},
        "meter": {{
            "no_meter": "number",
            "bacaan_dahulu": "number",
            "bacaan_semasa": "number",
            "kegunaan": "number",
            "unit": "string"
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
    "service_type": "string",
    "bill_reference": "string",
    "payment_details": "string",
    "notes": "string",
    "created_at": "YYYY-MM-DD"
}}

SPECIAL LOGIC:
- For license extension updates, use special_logic: "license_extend" and include extend_years
- For TNB payment updates, use special_logic: "tnb_payment" and include reference_no

MANDATORY FIELD MAPPING - NO EXCEPTIONS:

STEP 1: COUNT DIGITS IN THE NUMBER
STEP 2: APPLY RULE STRICTLY

RULE 1: If you find EXACTLY 12 consecutive digits (no spaces, no letters) → MUST use "identity_no" field
RULE 2: If you find 7 digits + space + 8 alphanumeric characters → MUST use "license_number" field

EXAMPLES - FOLLOW EXACTLY:
- "Search license for 041223070745" → Count digits: 0-4-1-2-2-3-0-7-0-7-4-5 = 12 digits → {{"identity_no": "041223070745"}}
- "Search license for 1234567 AbCdEfGh" → Pattern: 7digits+space+8chars → {{"license_number": "1234567 AbCdEfGh"}}

NEVER split 12-digit numbers. NEVER use license_number for 12 consecutive digits.

TNB BILL QUERIES:
- For TNB bills, account numbers are stored in "bill.akaun.no_akaun" field
- Example: "Find TNB bill 220001234513" → {{"bill.akaun.no_akaun": "220001234513"}}

Return:
{{
    "collection": "collection_name",
    "operation": "find|update",
    "query": {{"field": "value"}},
    "special_logic": "license_extend|tnb_payment" (if applicable),
    "extend_years": number (for license extension),
    "reference_no": "string" (for TNB payment)
}}"""

            response = bedrock.invoke_model(
                modelId=os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0'),
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 200,
                    "messages": [{"role": "user", "content": prompt}]
                })
            )
            
            result = json.loads(response['body'].read())
            content = result['content'][0]['text'].strip()
            
            # Extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(content[json_start:json_end])
            
            # Force fallback since AI mapping is incorrect
            return self._fallback_parse(instruction)
            
        except Exception as e:
            print(f"Bedrock failed: {e}")
            return self._fallback_parse(instruction)
        
        # Force fallback since AI still maps incorrectly despite explicit instructions
        return self._fallback_parse(instruction)
    
    def _fallback_parse(self, instruction: str) -> dict:
        """Fallback parsing if Bedrock fails"""
        instruction_lower = instruction.lower()
        
        # Extract 12-digit numbers (identity numbers) - must be exactly 12 consecutive digits
        identity_match = re.search(r'\b\d{12}\b', instruction)
        # Extract license format (digits + space + letters) - must be exactly 7 digits + space + 8 alphanumeric
        license_format_match = re.search(r'\b\d{7}\s+[A-Za-z0-9]{8}\b', instruction)
        
        if "licen" in instruction_lower:
            if ("update" in instruction_lower or "extend" in instruction_lower or "renew" in instruction_lower) and ("year" in instruction_lower):
                years_match = re.search(r'(\d+)\s*years?', instruction_lower)
                extend_years = int(years_match.group(1)) if years_match else 2
                if identity_match:
                    return {"collection": "licenses", "operation": "update", "query": {"identity_no": identity_match.group()}, "special_logic": "license_extend", "extend_years": extend_years}
                elif license_format_match:
                    return {"collection": "licenses", "operation": "update", "query": {"license_number": license_format_match.group()}, "special_logic": "license_extend", "extend_years": extend_years}
            elif identity_match:  # 12-digit number = identity_no
                return {"collection": "licenses", "operation": "find", "query": {"identity_no": identity_match.group()}}
            elif license_format_match:  # License format = license_number
                return {"collection": "licenses", "operation": "find", "query": {"license_number": license_format_match.group()}}
            else:
                # If no specific number found, don't guess - return unknown
                pass
        
        # Check TNB bills first (more specific)
        if "tnb" in instruction_lower and ("bill" in instruction_lower or "owe" in instruction_lower or "debt" in instruction_lower or ("account" in instruction_lower and identity_match)):
            if "update" in instruction_lower and "paid" in instruction_lower:
                ref_match = re.search(r'OLB\d+', instruction)
                amount_match = re.search(r'rm\s*(\d+(?:\.\d{2})?)', instruction_lower)
                if identity_match:
                    reference_no = ref_match.group() if ref_match else "MANUAL_PAYMENT"
                    payment_amount = float(amount_match.group(1)) if amount_match else None
                    return {"collection": "tnb", "operation": "update", "query": {"account_no": identity_match.group()}, "special_logic": "tnb_payment", "reference_no": reference_no, "payment_amount": payment_amount}
            elif identity_match:
                return {"collection": "tnb", "operation": "find", "query": {"account_no": identity_match.group()}}
        
        # Check service accounts (less specific)
        if "account" in instruction_lower and ("tnb" in instruction_lower or "jpj" in instruction_lower) and not identity_match:
            service = "TNB" if "tnb" in instruction_lower else "JPJ"
            return {"collection": "accounts", "operation": "find", "query": {"service": service}}
        
        # Transaction creation patterns
        if "create" in instruction_lower and "transaction" in instruction_lower:
            ref_match = re.search(r'reference\s+([A-Za-z0-9]+)', instruction)
            amount_match = re.search(r'rm\s*(\d+(?:\.\d{2})?)', instruction_lower)
            beneficiary_match = re.search(r'beneficiary\s+(.+)', instruction, re.IGNORECASE)
            
            if ref_match and amount_match and beneficiary_match:
                return {
                    "collection": "transactions", 
                    "operation": "create", 
                    "special_logic": "create_transaction",
                    "reference_id": ref_match.group(1),
                    "amount": float(amount_match.group(1)),
                    "beneficiary_name": beneficiary_match.group(1).strip()
                }
        
        # Payment processing patterns
        if "process" in instruction_lower and ("payment" in instruction_lower or "receipt" in instruction_lower):
            ref_match = re.search(r'reference\s+([A-Za-z0-9]+)', instruction)
            amount_match = re.search(r'rm\s*(\d+(?:\.\d{2})?)', instruction_lower)
            beneficiary_match = re.search(r'beneficiary\s+(.+?)(?:\s+account|$)', instruction, re.IGNORECASE)
            account_match = re.search(r'account\s+(\d+)', instruction)
            
            if ref_match and amount_match and beneficiary_match:
                return {
                    "collection": "transactions", 
                    "operation": "create", 
                    "special_logic": "process_payment",
                    "reference_id": ref_match.group(1),
                    "amount": float(amount_match.group(1)),
                    "beneficiary_name": beneficiary_match.group(1).strip(),
                    "beneficiary_account": account_match.group(1) if account_match else None
                }
        
        # Generic update/find detection
        if ("update" in instruction_lower or "renew" in instruction_lower) and identity_match:
            if "licen" in instruction_lower:
                years_match = re.search(r'(\d+)\s*years?', instruction_lower)
                extend_years = int(years_match.group(1)) if years_match else 2
                return {"collection": "licenses", "operation": "update", "query": {"identity_no": identity_match.group()}, "special_logic": "license_extend", "extend_years": extend_years}
        
        return {"collection": "unknown", "operation": "unknown", "error": "Could not parse instruction"}
    
    def execute_operation(self, operation_data: dict) -> dict:
        """Execute MongoDB operation dynamically"""
        try:
            collection_name = operation_data.get("collection")
            operation = operation_data.get("operation")
            query = operation_data.get("query", {})
            special_logic = operation_data.get("special_logic")
            
            if not collection_name or collection_name not in ["accounts", "licenses", "tnb", "transactions"]:
                # Try fallback parsing
                fallback_data = self._fallback_parse(str(operation_data))
                if fallback_data.get("collection") != "unknown":
                    return self.execute_operation(fallback_data)
                return {"success": False, "error": "Invalid collection"}
            
            collection = self.db[collection_name]
            
            if operation == "find":
                # Handle special TNB bill query structure
                if collection_name == "tnb" and "account_no" in query:
                    query = {"bill.akaun.no_akaun": query["account_no"]}
                
                docs = list(collection.find(query).limit(10))
                for doc in docs:
                    doc["_id"] = str(doc["_id"])
                
                # Special license suspension check
                if collection_name == "licenses" and docs:
                    for doc in docs:
                        if doc.get("status") == "suspended":
                            return {
                                "success": True,
                                "documents": docs,
                                "warning": "This user's license is suspended and cannot update its validity. Please go to nearby physical branch to process."
                            }
                
                return {"success": True, "count": len(docs), "documents": docs}
            
            elif operation == "update":
                if special_logic == "license_extend":
                    return self._handle_license_extend(operation_data)
                elif special_logic == "tnb_payment":
                    return self._handle_tnb_payment(operation_data)
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
            
            # Try fallback if operation not recognized
            fallback_data = self._fallback_parse(str(operation_data))
            if fallback_data.get("operation") != "unknown":
                return self.execute_operation(fallback_data)
            return {"success": False, "error": f"Unknown operation: {operation}"}
            
        except Exception as e:
            print(f"Execution error: {e}")
            return {"success": False, "error": str(e)}
    
    def _handle_license_extend(self, operation_data: dict) -> dict:
        """Handle license validity extension"""
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
        """Handle TNB bill payment update"""
        query = operation_data.get("query", {})
        reference_no = operation_data.get("reference_no")
        payment_amount = operation_data.get("payment_amount")
        today = datetime.now().strftime("%Y-%m-%d")
        
        if "account_no" in query:
            query = {"bill.akaun.no_akaun": query["account_no"]}
        
        # Get bill details
        tnb_doc = self.db.tnb.find_one(query)
        if not tnb_doc:
            return {"success": False, "error": "TNB bill not found"}
        
        current_status = tnb_doc.get("status", "unpaid")
        
        # If bill is already paid, do not allow any updates
        if current_status == "paid":
            return {"success": False, "error": "Bill is already paid. No further updates allowed."}
        
        # Use specified amount or full bill amount
        bill_amount = tnb_doc.get("bill", {}).get("meta", {}).get("bil_semasa", {}).get("jumlah", 0)
        final_amount = payment_amount if payment_amount is not None else bill_amount
        
        # Determine status based on payment amount
        new_status = "paid" if final_amount >= bill_amount else "partial"
        
        # Update payment details
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
        
        return {"success": True, "message": f"Payment of RM{final_amount} updated with reference {reference_no}", "modified_count": result.modified_count}
    
    def _handle_create_transaction(self, operation_data: dict) -> dict:
        """Handle transaction record creation"""
        reference_id = operation_data.get("reference_id")
        amount = operation_data.get("amount")
        beneficiary_name = operation_data.get("beneficiary_name")
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
            "service_type": "Government Services",
            "bill_reference": "",
            "payment_details": f"Transaction created for {beneficiary_name}",
            "notes": "",
            "created_at": today
        }
        
        result = self.db.transactions.insert_one(transaction_doc)
        return {"success": True, "message": f"Transaction {reference_id} created", "inserted_id": str(result.inserted_id)}
    
    def _handle_process_payment(self, operation_data: dict) -> dict:
        """Handle payment receipt processing"""
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
        return {"success": True, "message": f"Payment receipt {reference_id} processed", "inserted_id": str(result.inserted_id)}

def main():
    client = GovernmentServiceClient()
    
    if len(sys.argv) >= 2:
        # Single command mode
        instruction = sys.argv[1]
        execute_instruction(client, instruction)
    else:
        # Interactive mode
        print("Government Services Database Client")
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
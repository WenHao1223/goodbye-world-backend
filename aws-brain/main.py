#!/usr/bin/env python3
import json
import sys
import re
import uuid
import requests
import logging
from datetime import datetime, timedelta
from pymongo import MongoClient
import os
import boto3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('aws-brain')

# Load environment variables only if not in Lambda
if not os.getenv('LAMBDA_RUNTIME'):
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

class IntentClassifier:
    """
    Main class for intent classification and session management
    """
    
    def __init__(self):
        """
        Initialize the intent classifier with MongoDB and Bedrock connections
        """
        logger.info("🚀 Initializing IntentClassifier...")
        
        try:
            self.mongo_client = MongoClient(os.getenv("ATLAS_URI"))
            self.db = self.mongo_client[os.getenv("ATLAS_DB_NAME", "greataihackathon")]
            logger.info(f"✅ MongoDB connected to database: {os.getenv('ATLAS_DB_NAME', 'greataihackathon')}")
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {str(e)}")
            raise
        
        # AWS Lambda automatically provides the region via AWS_REGION1 environment variable
        # If not available, fall back to us-east-1
        region = os.environ.get('AWS_REGION1', 'us-east-1')
        try:
            self.bedrock = boto3.client('bedrock-runtime', region_name=region)
            logger.info(f"✅ AWS Bedrock client initialized for region: {region}")
        except Exception as e:
            logger.error(f"❌ AWS Bedrock connection failed: {str(e)}")
            raise
        
        # Document extraction service URL
        self.textract_service_url = "https://wdetiko31e.execute-api.us-east-1.amazonaws.com/dev/analyze"
        logger.info(f"📄 Textract service URL configured: {self.textract_service_url}")
        
        logger.info("🎯 IntentClassifier initialization completed successfully")
    
    def process_request(self, request_data: dict) -> dict:
        """
        Process the incoming request and determine the appropriate response
        
        Args:
            request_data (dict): Request data containing userId, sessionId, message, etc.
            
        Returns:
            dict: Response with id, reply, sessionId, attachments
        """
        logger.info("=" * 80)
        logger.info("🎯 NEW REQUEST FROM LAYER I")
        logger.info("=" * 80)
        logger.info(f"📥 Request received: {json.dumps(request_data, indent=2)}")
        
        try:
            user_id = request_data.get('user_id')
            session_id = request_data.get('session_id')
            message = request_data.get('message')
            created_at = request_data.get('created_at')
            attachment_url = request_data.get('attachment_url', [])
            
            logger.info(f"👤 User ID: {user_id}")
            logger.info(f"🔗 Session ID: {session_id}")
            logger.info(f"💬 Message: {message}")
            logger.info(f"📎 Attachments: {attachment_url}")
            
            # Generate response ID
            response_id = str(uuid.uuid4())
            logger.info(f"🆔 Generated Response ID: {response_id}")
            
            # Determine intent based on conditions
            intent_type = None
            response = None
            
            if attachment_url and len(attachment_url) > 0:
                # Intent: detect_file
                intent_type = "detect_file"
                logger.info("🔍 INTENT DETECTED: detect_file (attachment provided)")
                response = self.handle_detect_file(user_id, session_id, message, attachment_url, response_id)
            
            elif session_id == "(new-session)":
                # Intent: first_time_connection
                intent_type = "first_time_connection"
                logger.info("🆕 INTENT DETECTED: first_time_connection (new session)")
                response = self.handle_first_time_connection(user_id, message, response_id)
            
            elif self.is_conversation_ending(message):
                # Intent: new_connection
                intent_type = "new_connection"
                logger.info("👋 INTENT DETECTED: new_connection (conversation ending)")
                response = self.handle_new_connection(user_id, session_id, message, response_id)
            
            else:
                # Regular conversation - classify intent using Bedrock
                intent_type = "regular_conversation"
                logger.info("💬 INTENT DETECTED: regular_conversation (bedrock classification)")
                response = self.handle_regular_conversation(user_id, session_id, message, response_id)
            
            logger.info("=" * 80)
            logger.info("📤 RESPONSE TO LAYER I")
            logger.info("=" * 80)
            logger.info(f"🎯 Intent Type: {intent_type}")
            logger.info(f"📥 Response: {json.dumps(response, indent=2)}")
            logger.info("=" * 80)
            
            return response
                
        except Exception as e:
            logger.error(f"❌ Error in process_request: {str(e)}")
            error_response = {
                'id': str(uuid.uuid4()),
                'reply': f'Sorry, I encountered an error: {str(e)}',
                'sessionId': request_data.get('session_id', 'error'),
                'attachments': []
            }
            logger.info(f"📤 Error Response: {json.dumps(error_response, indent=2)}")
            return error_response
    
    def handle_first_time_connection(self, user_id: str, message: str, response_id: str) -> dict:
        """
        Handle first time connection with sessionId = "(new-session)"
        """
        logger.info("🆕 Processing FIRST_TIME_CONNECTION intent")
        logger.info(f"👤 User ID: {user_id}")
        logger.info(f"💬 First message: {message}")
        
        # Generate new session ID
        new_session_id = str(uuid.uuid4())
        logger.info(f"🆔 Generated new session ID: {new_session_id}")
        
        # Store session in chat database
        chat_collection = self.db.chat
        chat_doc = {
            'userId': user_id,
            'sessionId': new_session_id,
            'createdAt': datetime.now().isoformat(),
            'messages': [{
                'id': response_id,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'type': 'user'
            }],
            'status': 'active'
        }
        
        try:
            insert_result = chat_collection.insert_one(chat_doc)
            logger.info(f"✅ Session stored in MongoDB chat collection. Document ID: {insert_result.inserted_id}")
        except Exception as e:
            logger.error(f"❌ Failed to store session in MongoDB: {str(e)}")
        
        # Generate welcome response
        reply = "Hello! Welcome to the government services assistant. How can I help you today?"
        logger.info(f"💬 Generated welcome reply: {reply}")
        
        response = {
            'id': response_id,
            'reply': reply,
            'sessionId': new_session_id,
            'attachments': []
        }
        
        logger.info("✅ FIRST_TIME_CONNECTION intent processing completed")
        return response
    
    def handle_new_connection(self, user_id: str, current_session_id: str, message: str, response_id: str) -> dict:
        """
        Handle conversation ending and create new session
        """
        logger.info("👋 Processing NEW_CONNECTION intent (conversation ending)")
        logger.info(f"👤 User ID: {user_id}")
        logger.info(f"🔗 Current session ID: {current_session_id}")
        logger.info(f"💬 Ending message: {message}")
        
        # Close current session
        try:
            update_result = self.db.chat.update_one(
                {'userId': user_id, 'sessionId': current_session_id},
                {'$set': {'status': 'closed', 'closedAt': datetime.now().isoformat()}}
            )
            logger.info(f"✅ Closed current session. Modified count: {update_result.modified_count}")
        except Exception as e:
            logger.error(f"❌ Failed to close session in MongoDB: {str(e)}")
        
        # Generate new session ID
        new_session_id = str(uuid.uuid4())
        logger.info(f"🆔 Generated new session ID: {new_session_id}")
        
        # Create new session
        chat_doc = {
            'userId': user_id,
            'sessionId': new_session_id,
            'createdAt': datetime.now().isoformat(),
            'messages': [{
                'id': response_id,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'type': 'user'
            }],
            'status': 'active'
        }
        
        try:
            insert_result = self.db.chat.insert_one(chat_doc)
            logger.info(f"✅ New session stored in MongoDB. Document ID: {insert_result.inserted_id}")
        except Exception as e:
            logger.error(f"❌ Failed to create new session in MongoDB: {str(e)}")
        
        # Generate farewell and new conversation response
        reply = "Thank you for using our service! I'm here to help with a new request. What can I assist you with?"
        logger.info(f"💬 Generated farewell reply: {reply}")
        
        response = {
            'id': response_id,
            'reply': reply,
            'sessionId': new_session_id,
            'attachments': []
        }
        
        logger.info("✅ NEW_CONNECTION intent processing completed")
        return response
    
    def handle_detect_file(self, user_id: str, session_id: str, message: str, attachment_url: list, response_id: str) -> dict:
        """
        Handle file detection using textract service
        """
        logger.info("🔍 Processing DETECT_FILE intent")
        logger.info(f"👤 User ID: {user_id}")
        logger.info(f"🔗 Session ID: {session_id}")
        logger.info(f"💬 Message: {message}")
        logger.info(f"📎 Attachment URLs: {attachment_url}")
        
        try:
            # Call document extraction service
            logger.info("📞 Calling Layer III - Document Extraction Service")
            logger.info(f"🌐 Service URL: {self.textract_service_url}")
            
            request_payload = {
                'file_url': attachment_url[0] if attachment_url else ''
            }
            logger.info(f"📤 Request to textract service: {json.dumps(request_payload, indent=2)}")
            
            response = requests.post(self.textract_service_url, json=request_payload, timeout=30)
            logger.info(f"📥 Textract service response status: {response.status_code}")
            
            if response.status_code == 200:
                extraction_result = response.json()
                logger.info(f"✅ Textract service response: {json.dumps(extraction_result, indent=2)}")
                
                detected_category = extraction_result.get('category', 'unknown')
                extracted_data = extraction_result.get('extracted_data', {})
                logger.info(f"🏷️ Detected category: {detected_category}")
                logger.info(f"📊 Extracted data: {json.dumps(extracted_data, indent=2)}")
                
                # Store result to chat database
                logger.info("💾 Storing extraction result to MongoDB chat collection")
                try:
                    update_result = self.db.chat.update_one(
                        {'userId': user_id, 'sessionId': session_id},
                        {
                            '$push': {
                                'messages': {
                                    'id': response_id,
                                    'message': message,
                                    'timestamp': datetime.now().isoformat(),
                                    'type': 'user',
                                    'attachment_url': attachment_url,
                                    'detected_category': detected_category,
                                    'extraction_result': extraction_result
                                }
                            }
                        }
                    )
                    logger.info(f"✅ Stored to chat collection. Modified count: {update_result.modified_count}")
                except Exception as e:
                    logger.error(f"❌ Failed to store to chat collection: {str(e)}")
                
                # Check for unique identities and store to user database
                if extracted_data:
                    logger.info("🔍 Checking for unique identities in extracted data")
                    self.store_user_identities(user_id, extracted_data)
                
                # Generate response based on detected category
                reply = self.generate_file_detection_response(detected_category, extracted_data)
                logger.info(f"💬 Generated reply: {reply}")
                
                response_data = {
                    'id': response_id,
                    'reply': reply,
                    'sessionId': session_id,
                    'attachments': [{
                        'type': 'extraction_result',
                        'category': detected_category,
                        'data': extracted_data
                    }]
                }
                
                logger.info("✅ DETECT_FILE intent processing completed successfully")
                return response_data
            else:
                logger.error(f"❌ Textract service returned error status: {response.status_code}")
                logger.error(f"❌ Response text: {response.text}")
                
                error_response = {
                    'id': response_id,
                    'reply': 'Sorry, I had trouble processing your document. Please try again.',
                    'sessionId': session_id,
                    'attachments': []
                }
                return error_response
                
        except Exception as e:
            logger.error(f"❌ Error in handle_detect_file: {str(e)}")
            error_response = {
                'id': response_id,
                'reply': f'Sorry, I encountered an error while processing your document: {str(e)}',
                'sessionId': session_id,
                'attachments': []
            }
            return error_response
    
    def handle_regular_conversation(self, user_id: str, session_id: str, message: str, response_id: str) -> dict:
        """
        Handle regular conversation using Bedrock for intent classification
        """
        logger.info("💬 Processing REGULAR_CONVERSATION intent")
        logger.info(f"👤 User ID: {user_id}")
        logger.info(f"🔗 Session ID: {session_id}")
        logger.info(f"💬 Message: {message}")
        
        try:
            # Classify intent using Bedrock
            logger.info("🤖 Calling Layer III - AWS Bedrock for intent classification")
            intent_result = self.classify_intent_with_bedrock(message)
            logger.info(f"✅ Bedrock classification result: {json.dumps(intent_result, indent=2)}")
            
            # Update chat with user message
            logger.info("💾 Storing conversation to MongoDB chat collection")
            try:
                update_result = self.db.chat.update_one(
                    {'userId': user_id, 'sessionId': session_id},
                    {
                        '$push': {
                            'messages': {
                                'id': response_id,
                                'message': message,
                                'timestamp': datetime.now().isoformat(),
                                'type': 'user',
                                'intent': intent_result.get('intent', 'unknown')
                            }
                        }
                    }
                )
                logger.info(f"✅ Stored to chat collection. Modified count: {update_result.modified_count}")
            except Exception as e:
                logger.error(f"❌ Failed to store to chat collection: {str(e)}")
            
            # Generate response based on intent
            reply = self.generate_intent_response(intent_result, message)
            logger.info(f"💬 Generated reply: {reply}")
            
            response_data = {
                'id': response_id,
                'reply': reply,
                'sessionId': session_id,
                'attachments': []
            }
            
            logger.info("✅ REGULAR_CONVERSATION intent processing completed")
            return response_data
            
        except Exception as e:
            logger.error(f"❌ Error in handle_regular_conversation: {str(e)}")
            error_response = {
                'id': response_id,
                'reply': 'I understand you want assistance. Could you please provide more details about what you need help with?',
                'sessionId': session_id,
                'attachments': []
            }
            return error_response
    
    def is_conversation_ending(self, message: str) -> bool:
        """
        Check if the message indicates conversation ending
        """
        ending_keywords = [
            'thank you', 'thanks', 'goodbye', 'bye', 'cancel', 'stop', 
            'exit', 'quit', 'end conversation', 'that\'s all', 'no more questions'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in ending_keywords)
    
    def classify_intent_with_bedrock(self, message: str) -> dict:
        """
        Use AWS Bedrock to classify the intent of the message
        """
        logger.info("🤖 Starting Bedrock intent classification")
        logger.info(f"💬 Message to classify: {message}")
        
        prompt = f"""Classify the intent of this government service request message. Return ONLY valid JSON.

Message: "{message}"

Available intents and their descriptions:
- license_inquiry: Questions about driving license, license application, license renewal, license status
- tnb_inquiry: Questions about TNB bills, electricity bills, TNB account, power bills
- jpj_inquiry: Questions about JPJ services, vehicle registration, road tax
- account_inquiry: Questions about service accounts, account details, account management
- payment_inquiry: Questions about payments, transactions, payment status, payment methods
- document_inquiry: Questions about required documents, document verification
- general_inquiry: General questions about government services
- greeting: Greetings, introductions, how are you messages
- unknown: Cannot determine intent from the message

Return JSON format:
{{
    "intent": "intent_name",
    "confidence": 0.95,
    "category": "government_service_category",
    "suggested_actions": ["action1", "action2"]
}}"""

        try:
            bedrock_model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
            logger.info(f"🤖 Using Bedrock model: {bedrock_model_id}")
            
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 200,
                "messages": [{"role": "user", "content": prompt}]
            }
            logger.info(f"📤 Bedrock request body: {json.dumps(request_body, indent=2)}")
            
            response = self.bedrock.invoke_model(
                modelId=bedrock_model_id,
                body=json.dumps(request_body)
            )
            
            result = json.loads(response['body'].read())
            logger.info(f"📥 Raw Bedrock response: {json.dumps(result, indent=2)}")
            
            content = result['content'][0]['text'].strip()
            logger.info(f"📄 Bedrock content: {content}")
            
            # Extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                parsed = json.loads(content[json_start:json_end])
                logger.info(f"✅ Parsed intent result: {json.dumps(parsed, indent=2)}")
                return parsed
            
            logger.warning("⚠️ Could not extract JSON from Bedrock response")
            return {"intent": "unknown", "confidence": 0.0, "category": "unknown", "suggested_actions": []}
            
        except Exception as e:
            logger.error(f"❌ Bedrock classification error: {str(e)}")
            return {"intent": "unknown", "confidence": 0.0, "category": "unknown", "error": str(e)}
    
    def store_user_identities(self, user_id: str, extracted_data: dict):
        """
        Store unique identities to user database
        """
        logger.info("🔍 Processing user identities extraction")
        logger.info(f"👤 User ID: {user_id}")
        logger.info(f"📊 Extracted data: {json.dumps(extracted_data, indent=2)}")
        
        identity_fields = ['identity_no', 'license_no', 'account_no', 'license_number']
        
        user_identities = {}
        for field in identity_fields:
            if field in extracted_data and extracted_data[field]:
                user_identities[field] = extracted_data[field]
                logger.info(f"🆔 Found identity - {field}: {extracted_data[field]}")
        
        if user_identities:
            logger.info(f"💾 Storing identities to user database: {json.dumps(user_identities, indent=2)}")
            
            try:
                # Update or create user record
                update_result = self.db.user.update_one(
                    {'userId': user_id},
                    {
                        '$set': {
                            'userId': user_id,
                            'lastUpdated': datetime.now().isoformat(),
                            **user_identities
                        }
                    },
                    upsert=True
                )
                logger.info(f"✅ User identities stored. Modified count: {update_result.modified_count}, Upserted ID: {update_result.upserted_id}")
            except Exception as e:
                logger.error(f"❌ Failed to store user identities: {str(e)}")
        else:
            logger.info("ℹ️ No unique identities found in extracted data")
    
    def generate_file_detection_response(self, category: str, extracted_data: dict) -> str:
        """
        Generate response based on detected file category
        """
        if category == 'license':
            return "I've detected a driving license document. I can help you with license-related services like renewal, status check, or information updates."
        elif category == 'tnb_bill':
            return "I've detected a TNB electricity bill. I can help you check your bill status, payment history, or process payments."
        elif category == 'bank_statement':
            return "I've detected a bank statement. I can help you with transaction verification or payment processing."
        else:
            return f"I've processed your document (category: {category}). How can I assist you with this document?"
    
    def generate_intent_response(self, intent_result: dict, original_message: str) -> str:
        """
        Generate response based on classified intent
        """
        intent = intent_result.get('intent', 'unknown')
        
        responses = {
            'license_inquiry': "I can help you with driving license services. Would you like to check license status, apply for renewal, or get information about license requirements?",
            'tnb_inquiry': "I can assist you with TNB electricity bill services. Would you like to check your bill status, view payment history, or process a payment?",
            'jpj_inquiry': "I can help you with JPJ vehicle services. Would you like information about vehicle registration, road tax, or other JPJ services?",
            'account_inquiry': "I can help you with service account information. Which service account would you like to inquire about?",
            'payment_inquiry': "I can assist you with payment-related services. Would you like to check payment status, process a payment, or view transaction history?",
            'document_inquiry': "I can help you with document requirements and verification. Which service or document type are you asking about?",
            'greeting': "Hello! I'm here to help you with government services. How can I assist you today?",
            'general_inquiry': "I'm here to help you with various government services including licensing, bills, and payments. What specific service do you need assistance with?",
            'unknown': "I understand you need assistance. Could you please provide more details about which government service you'd like help with? I can assist with driving licenses, TNB bills, JPJ services, and more."
        }
        
        return responses.get(intent, responses['unknown'])

    def classify_intent(self, user_input: str) -> dict:
        """
        Legacy method for backward compatibility
        """
        return self.classify_intent_with_bedrock(user_input)
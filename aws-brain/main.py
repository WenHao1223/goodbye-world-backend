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

# Configure logging for CloudWatch
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # Force reconfiguration
)
logger = logging.getLogger('aws-brain')

# Also ensure logs go to stdout for Lambda CloudWatch
import sys
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

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
            self.db = self.mongo_client[os.getenv("ATLAS_DB_NAME", "chat")]
            logger.info(f"✅ MongoDB connected to database: {os.getenv('ATLAS_DB_NAME', 'chat')}")
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
    
    def prepare_ocr_payload(self, attachment: list) -> dict:
        """
        Prepare OCR API payload from attachment data - downloads file and converts to base64
        
        Args:
            attachment (list): Attachment data with URL:
                - Format: [{'url': 'http://...', 'type': 'image/jpeg', 'name': 'file.jpg'}]
        
        Returns:
            dict: Payload for OCR API with base64 'file' field
        """
        logger.info("🔧 Preparing OCR API payload from attachment")
        
        if not attachment or len(attachment) == 0:
            logger.warning("⚠️ No attachment provided")
            return {'file_content': '', 'filename': ''}
        
        attachment_item = attachment[0]
        file_url = attachment_item.get('url', '')
        filename = attachment_item.get('name', 'unknown.jpg')
        
        logger.info(f"📎 Processing attachment - filename: {filename}")
        logger.info(f"🌐 File URL: {file_url[:100]}...")
        print(f"📎 Processing attachment - filename: {filename}")
        print(f"🌐 File URL: {file_url[:100]}...")
        
        if not file_url:
            logger.error("❌ No URL provided in attachment")
            return {'file_content': '', 'filename': filename}
        
        try:
            # Download the file from the URL
            logger.info("📥 Downloading file from URL...")
            print("📥 Downloading file from URL...")
            
            import base64
            response = requests.get(file_url, timeout=30)
            response.raise_for_status()
            
            # Convert to base64
            file_content_base64 = base64.b64encode(response.content).decode('utf-8')
            
            logger.info(f"✅ File downloaded and converted to base64")
            logger.info(f"📏 Original file size: {len(response.content)} bytes")
            logger.info(f"📏 Base64 content length: {len(file_content_base64)} characters")
            
            print(f"✅ File downloaded and converted to base64")
            print(f"📏 Original file size: {len(response.content)} bytes")
            print(f"📏 Base64 content length: {len(file_content_base64)} characters")
            
            # Prepare payload for OCR API
            payload = {
                'file_content': file_content_base64,
                'filename': filename
            }
            
            logger.info(f"✅ OCR payload prepared with base64 content")
            logger.info(f"📋 Payload structure: file_content({len(file_content_base64)} chars) + filename({filename})")
            print(f"📋 OCR payload: file_content({len(file_content_base64)} chars) + filename({filename})")
            return payload
            
        except Exception as e:
            logger.error(f"❌ Error downloading/converting file: {str(e)}")
            print(f"❌ Error downloading/converting file: {str(e)}")
            return {'file_content': '', 'filename': filename, 'error': str(e)}
    
    def get_iso_timestamp(self) -> str:
        """
        Get current timestamp in ISO format (UTC)
        """
        from datetime import timezone
        return datetime.now(timezone.utc).isoformat()
    
    def ensure_collection_indexes(self, collection_name: str):
        """
        Ensure proper indexes are created for the WhatsApp number collection
        """
        try:
            collection = self.db[collection_name]
            # Create index on userId and sessionId for faster queries
            collection.create_index([("userId", 1), ("sessionId", 1)])
            collection.create_index([("createdAt", 1)])
            logger.info(f"✅ Indexes ensured for collection '{collection_name}'")
        except Exception as e:
            logger.warning(f"⚠️ Could not create indexes for collection '{collection_name}': {str(e)}")
    
    def process_request(self, request_data: dict) -> dict:
        """
        Process the incoming request and determine the appropriate response
        
        Args:
            request_data (dict): Request data containing userId, sessionId, message, etc.
            
        Returns:
            dict: Response with messageId, message, sessionId, attachment
        """
        logger.info("=" * 80)
        logger.info("🎯 NEW REQUEST FROM LAYER I")
        logger.info("=" * 80)
        logger.info(f"📥 Request received: {json.dumps(request_data, indent=2)}")
        
        # Print to stdout for CloudWatch visibility
        print("=" * 80)
        print("🎯 NEW REQUEST FROM LAYER I")
        print("=" * 80)
        print(f"📥 Request received: {json.dumps(request_data, indent=2)}")
        
        try:
            user_id = request_data.get('user_id')
            session_id = request_data.get('session_id')
            message = request_data.get('message', '')
            created_at = request_data.get('created_at')
            attachment = request_data.get('attachment', [])
            
            # If message is empty but attachment is provided, use a default message
            if not message and attachment and len(attachment) > 0:
                message = "Document uploaded"
                logger.info("📎 Empty message with attachment - using default message: 'Document uploaded'")
            
            logger.info(f"👤 User ID: {user_id}")
            logger.info(f"🔗 Session ID: {session_id}")
            logger.info(f"💬 Message: {message}")
            logger.info(f"📎 attachment: {attachment}")
            
            # Generate response ID (messageId)
            message_id = str(uuid.uuid4())
            logger.info(f"🆔 Generated Message ID (messageId): {message_id}")
            
            # Determine intent based on conditions
            intent_type = None
            response = None
            
            if attachment and len(attachment) > 0:
                # Intent: detect_file (direct document processing)
                intent_type = "detect_file"
                logger.info("🔍 INTENT DETECTED: detect_file (attachment provided)")
                print("🔍 INTENT DETECTED: detect_file (attachment provided)")  # CloudWatch visibility
                response = self.handle_document_processing_with_confirmation(user_id, session_id, message, attachment, message_id)
            
            elif session_id == "(new-session)":
                # Intent: first_time_connection
                intent_type = "first_time_connection"
                logger.info("🆕 INTENT DETECTED: first_time_connection (new session)")
                print("🆕 INTENT DETECTED: first_time_connection (new session)")  # CloudWatch visibility
                response = self.handle_first_time_connection(user_id, message, message_id)
            
            elif self.is_greeting_message(message):
                # Intent: greeting_new_session (user said hi/hello - start new session)
                intent_type = "greeting_new_session"
                logger.info("👋 INTENT DETECTED: greeting_new_session (user said greeting)")
                print("👋 INTENT DETECTED: greeting_new_session (user said greeting)")  # CloudWatch visibility
                response = self.handle_new_connection(user_id, session_id, message, message_id)
            
            elif self.is_conversation_ending(message):
                # Intent: new_connection
                intent_type = "new_connection"
                logger.info("👋 INTENT DETECTED: new_connection (conversation ending)")
                print("👋 INTENT DETECTED: new_connection (conversation ending)")  # CloudWatch visibility
                response = self.handle_new_connection(user_id, session_id, message, message_id)
            
            elif self.is_user_awaiting_document_upload(user_id, session_id) and not self.is_exit_or_restart_command(message):
                # User is awaiting document upload but trying to do something else - enforce document upload
                intent_type = "enforce_document_upload"
                logger.info("🔒 INTENT DETECTED: enforce_document_upload (user must upload document)")
                print("🔒 INTENT DETECTED: enforce_document_upload (user must upload document)")  # CloudWatch visibility
                response = self.handle_enforce_document_upload(user_id, session_id, message, message_id)
            
            else:
                # Regular conversation - classify intent using Bedrock
                intent_type = "regular_conversation"
                logger.info("💬 INTENT DETECTED: regular_conversation (bedrock classification)")
                print("💬 INTENT DETECTED: regular_conversation (bedrock classification)")  # CloudWatch visibility
                response = self.handle_regular_conversation(user_id, session_id, message, message_id)
            
            logger.info("=" * 80)
            logger.info("📤 RESPONSE TO LAYER I")
            logger.info("=" * 80)
            logger.info(f"🎯 Intent Type: {intent_type}")
            logger.info(f"📥 Response: {json.dumps(response, indent=2)}")
            logger.info("=" * 80)
            
            # Print to stdout for CloudWatch visibility
            print("=" * 80)
            print("📤 RESPONSE TO LAYER I")
            print("=" * 80)
            print(f"🎯 Intent Type: {intent_type}")
            print(f"📥 Response: {json.dumps(response, indent=2)}")
            print("=" * 80)
            
            return response
                
        except Exception as e:
            logger.error(f"❌ Error in process_request: {str(e)}")
            print(f"❌ ERROR in process_request: {str(e)}")  # CloudWatch visibility
            
            error_response = {
                'messageId': str(uuid.uuid4()),
                'message': f'Sorry, I encountered an error: {str(e)}',
                'sessionId': request_data.get('session_id', 'error'),
                'attachment': [],
                'createdAt': self.get_iso_timestamp()
            }
            logger.info(f"📤 Error Response: {json.dumps(error_response, indent=2)}")
            print(f"📤 ERROR Response: {json.dumps(error_response, indent=2)}")  # CloudWatch visibility
            return error_response
    
    def handle_first_time_connection(self, user_id: str, message: str, message_id: str) -> dict:
        """
        Handle first time connection with sessionId = "(new-session)"
        """
        logger.info("🆕 Processing FIRST_TIME_CONNECTION intent")
        logger.info(f"👤 User ID: {user_id}")
        logger.info(f"💬 First message: {message}")
        
        # Generate new session ID
        new_session_id = str(uuid.uuid4())
        logger.info(f"🆔 Generated new session ID: {new_session_id}")
        
        # Store session in user-specific collection in chat database
        # Use userId as collection name (e.g., "60123456789")
        collection_name = user_id
        chat_collection = self.db[collection_name]
        logger.info(f"💾 Using collection: {collection_name}")
        
        # Ensure indexes exist for this collection
        self.ensure_collection_indexes(collection_name)
        
        chat_doc = {
            'userId': user_id,
            'sessionId': new_session_id,
            'createdAt': self.get_iso_timestamp(),
            'messages': [{
                'messageId': message_id,
                'message': message,
                'timestamp': self.get_iso_timestamp(),
                'type': 'user'
            }],
            'status': 'active'
        }
        
        try:
            insert_result = chat_collection.insert_one(chat_doc)
            logger.info(f"✅ Session stored in MongoDB collection '{collection_name}'. Document ID: {insert_result.inserted_id}")
        except Exception as e:
            logger.error(f"❌ Failed to store session in MongoDB collection '{collection_name}': {str(e)}")
        
        # Generate welcome response
        reply = "Hello! Welcome to the government services assistant. How can I help you today?"
        logger.info(f"💬 Generated welcome reply: {reply}")
        
        response = {
            'messageId': message_id,
            'message': reply,
            'sessionId': new_session_id,
            'attachment': [],
            'createdAt': self.get_iso_timestamp()
        }
        
        logger.info("✅ FIRST_TIME_CONNECTION intent processing completed")
        return response
    
    def handle_new_connection(self, user_id: str, current_session_id: str, message: str, message_id: str) -> dict:
        """
        Handle conversation ending and create new session
        """
        logger.info("👋 Processing NEW_CONNECTION intent (conversation ending)")
        logger.info(f"👤 User ID: {user_id}")
        logger.info(f"🔗 Current session ID: {current_session_id}")
        logger.info(f"💬 Ending message: {message}")
        
        # Close current session in user-specific collection
        collection_name = user_id
        chat_collection = self.db[collection_name]
        logger.info(f"💾 Using collection: {collection_name}")
        
        try:
            update_result = chat_collection.update_one(
                {'userId': user_id, 'sessionId': current_session_id},
                {'$set': {'status': 'closed', 'closedAt': self.get_iso_timestamp()}}
            )
            logger.info(f"✅ Closed current session in collection '{collection_name}'. Modified count: {update_result.modified_count}")
        except Exception as e:
            logger.error(f"❌ Failed to close session in MongoDB collection '{collection_name}': {str(e)}")
        
        # Generate new session ID
        new_session_id = str(uuid.uuid4())
        logger.info(f"🆔 Generated new session ID: {new_session_id}")
        
        # Create new session
        chat_doc = {
            'userId': user_id,
            'sessionId': new_session_id,
            'createdAt': self.get_iso_timestamp(),
            'messages': [{
                'messageId': message_id,
                'message': message,
                'timestamp': self.get_iso_timestamp(),
                'type': 'user'
            }],
            'status': 'active'
        }
        
        try:
            insert_result = chat_collection.insert_one(chat_doc)
            logger.info(f"✅ New session stored in MongoDB collection '{collection_name}'. Document ID: {insert_result.inserted_id}")
        except Exception as e:
            logger.error(f"❌ Failed to create new session in MongoDB collection '{collection_name}': {str(e)}")
        
        # Generate farewell and new conversation response
        reply = "Thank you for using our service! I'm here to help with a new request. What can I assist you with?"
        logger.info(f"💬 Generated farewell reply: {reply}")
        
        response = {
            'messageId': message_id,
            'message': reply,
            'sessionId': new_session_id,
            'attachment': [],
            'createdAt': self.get_iso_timestamp()
        }
        
        logger.info("✅ NEW_CONNECTION intent processing completed")
        return response
    
    def handle_detect_file(self, user_id: str, session_id: str, message: str, attachment: list, message_id: str) -> dict:
        """
        Handle file detection using textract service with blur detection and data confirmation
        """
        logger.info("🔍 Processing DETECT_FILE intent")
        logger.info(f"👤 User ID: {user_id}")
        logger.info(f"🔗 Session ID: {session_id}")
        logger.info(f"💬 Message: {message}")
        logger.info(f"📎 Attachment: {attachment}")
        
        try:
            # Call document extraction service
            logger.info("📞 Calling Layer III - Document Extraction Service")
            logger.info(f"🌐 Service URL: {self.textract_service_url}")
            
            # Handle both URL-based attachments and direct file content
            request_payload = self.prepare_ocr_payload(attachment)
            logger.info(f"📤 Request to textract service: {json.dumps(request_payload, indent=2)}")
            print(f"📤 OCR API Request payload: {json.dumps(request_payload, indent=2)}")  # Enhanced logging
            
            response = requests.post(self.textract_service_url, json=request_payload, timeout=30)
            logger.info(f"📥 Textract service response status: {response.status_code}")
            print(f"📥 OCR API Response status: {response.status_code}")  # Enhanced logging
            
            if response.status_code == 200:
                extraction_result = response.json()
                logger.info(f"✅ Textract service response received")
                print(f"✅ OCR API Success response sample: {json.dumps(extraction_result, indent=2)[:500]}...")  # Enhanced logging
                
                # Check for blur analysis
                blur_analysis = extraction_result.get('blur_analysis', {})
                overall_assessment = blur_analysis.get('overall_assessment', {})
                is_blurry = overall_assessment.get('is_blurry', False)
                
                logger.info(f"📷 Image blur analysis - Is blurry: {is_blurry}")
                
                if is_blurry:
                    # Ask user to reupload due to blur
                    logger.info("⚠️ Image detected as blurry, requesting reupload")
                    
                    blur_response = {
                        'messageId': message_id,
                        'message': 'The image you uploaded appears to be blurry or unclear. Please take a clearer photo and upload it again for better processing.',
                        'sessionId': session_id,
                        'attachment': [],
                        'createdAt': self.get_iso_timestamp()
                    }
                    return blur_response
                
                # Extract key information
                detected_category = extraction_result.get('category_detection', {}).get('detected_category', 'unknown')
                extracted_data = extraction_result.get('extracted_data', {})
                
                logger.info(f"🏷️ Detected category: {detected_category}")
                logger.info(f"📊 Extracted data: {json.dumps(extracted_data, indent=2)}")
                
                # Store result to user-specific collection
                collection_name = user_id
                chat_collection = self.db[collection_name]
                logger.info(f"💾 Storing extraction result to MongoDB collection '{collection_name}'")
                
                try:
                    update_result = chat_collection.update_one(
                        {'userId': user_id, 'sessionId': session_id},
                        {
                            '$push': {
                                'messages': {
                                    'messageId': message_id,
                                    'message': message,
                                    'timestamp': self.get_iso_timestamp(),
                                    'type': 'user',
                                    'attachment': attachment,
                                    'detected_category': detected_category,
                                    'extraction_result': extraction_result,
                                    'extracted_data': extracted_data
                                }
                            },
                            '$set': {
                                'extracted_data': extracted_data,  # Store at session level too
                                'document_category': detected_category
                            },
                            '$unset': {
                                'awaiting_document_upload': '',  # Clear awaiting state since document is uploaded
                                'document_prompt_sent': ''
                            }
                        }
                    )
                    logger.info(f"✅ Stored to collection '{collection_name}' and cleared awaiting document state. Modified count: {update_result.modified_count}")
                except Exception as e:
                    logger.error(f"❌ Failed to store to collection '{collection_name}': {str(e)}")
                
                # Check for unique identities and store to user database
                if extracted_data:
                    logger.info("🔍 Checking for unique identities in extracted data")
                    self.store_user_identities(user_id, extracted_data)
                
                # Generate confirmation message with extracted key data
                confirmation_message = self.generate_data_confirmation_message(detected_category, extracted_data)
                logger.info(f"💬 Generated confirmation message: {confirmation_message}")
                
                response_data = {
                    'messageId': message_id,
                    'message': confirmation_message,
                    'sessionId': session_id,
                    'attachment': [{
                        'type': 'extraction_result',
                        'category': detected_category,
                        'data': extracted_data
                    }],
                    'createdAt': self.get_iso_timestamp()
                }
                
                logger.info("✅ DETECT_FILE intent processing completed successfully")
                return response_data
            else:
                logger.error(f"❌ Textract service returned error status: {response.status_code}")
                logger.error(f"❌ Response text: {response.text}")
                print(f"❌ OCR API Error status: {response.status_code}")  # Enhanced logging
                print(f"❌ OCR API Error response: {response.text}")  # Enhanced logging
                
                error_response = {
                    'messageId': message_id,
                    'message': 'Sorry, I had trouble processing your document. Please try again.',
                    'sessionId': session_id,
                    'attachment': [],
                    'createdAt': self.get_iso_timestamp()
                }
                return error_response
                
        except Exception as e:
            logger.error(f"❌ Error in handle_detect_file: {str(e)}")
            error_response = {
                'messageId': message_id,
                'message': f'Sorry, I encountered an error while processing your document: {str(e)}',
                'sessionId': session_id,
                'attachment': [],
                'createdAt': self.get_iso_timestamp()
            }
            return error_response
    
    def handle_regular_conversation(self, user_id: str, session_id: str, message: str, message_id: str) -> dict:
        """
        Handle regular conversation using Bedrock for intent classification
        """
        logger.info("💬 Processing REGULAR_CONVERSATION intent")
        logger.info(f"👤 User ID: {user_id}")
        logger.info(f"🔗 Session ID: {session_id}")
        logger.info(f"💬 Message: {message}")
        
        try:
            collection_name = user_id
            chat_collection = self.db[collection_name]
            logger.info(f"💾 Processing conversation for MongoDB collection '{collection_name}'")
            
            # PRIORITY CHECK: Handle verified license documents that need renewal process
            current_session = chat_collection.find_one({'userId': user_id, 'sessionId': session_id})
            if current_session:
                is_validated = current_session.get('isValidate', False)
                document_category = current_session.get('document_category', '')
                awaiting_year_selection = current_session.get('awaiting_year_selection', False)
                awaiting_payment = current_session.get('awaiting_payment_receipt', False)
                
                logger.info(f"🔍 Priority check - isValidate: {is_validated}, category: {document_category}, awaiting_year: {awaiting_year_selection}, awaiting_payment: {awaiting_payment}")
                
                # If document is verified and it's a license, prioritize renewal flow
                if is_validated and document_category == 'license':
                    logger.info("🎯 PRIORITY: Verified license document - checking renewal flow")
                    
                    # Check if user is selecting years
                    if awaiting_year_selection:
                        logger.info("📅 User is in year selection flow")
                        year_result = self.handle_year_selection(user_id, session_id, message, message_id, chat_collection)
                        if year_result:
                            return year_result
                    
                    # Check if user is confirming again (they said "yes" but already verified)
                    confirmation_keywords = ['yes', 'correct', 'confirm', 'ok', 'okay', 'right', 'true', 'accurate']
                    is_confirming = any(keyword in message.lower() for keyword in confirmation_keywords)
                    
                    if is_confirming and not awaiting_year_selection and not awaiting_payment:
                        logger.info("🔄 User confirming again - directing to year selection")
                        
                        # Mark as awaiting year selection
                        try:
                            chat_collection.update_one(
                                {'userId': user_id, 'sessionId': session_id},
                                {'$set': {'awaiting_year_selection': True}}
                            )
                        except Exception as e:
                            logger.error(f"❌ Failed to mark as awaiting year selection: {str(e)}")
                        
                        return {
                            'messageId': message_id,
                            'message': """✅ **License Information Confirmed!**

� **License Renewal Process**

How many years would you like to extend your driving license validity?

**Available Options:**
• 1️⃣ **1 Year** - RM 30.00
• 2️⃣ **2 Years** - RM 60.00  
• 3️⃣ **3 Years** - RM 90.00
• 4️⃣ **4 Years** - RM 120.00
• 5️⃣ **5 Years** - RM 150.00

Please reply with the number of years you want to extend (e.g., "2 years" or just "2").""",
                            'sessionId': session_id,
                            'attachment': [],
                            'createdAt': self.get_iso_timestamp()
                        }
                
                # Handle verified IC/Identity Card documents
                elif is_validated and document_category in ['identity_card', 'ic', 'mykad']:
                    logger.info("🎯 PRIORITY: Verified IC document - offering services")
                    
                    confirmation_keywords = ['yes', 'correct', 'confirm', 'ok', 'okay', 'right', 'true', 'accurate']
                    is_confirming = any(keyword in message.lower() for keyword in confirmation_keywords)
                    
                    if is_confirming:
                        logger.info("🆔 User confirmed IC - offering available services")
                        
                        extracted_data = current_session.get('data', {}) or current_session.get('extracted_data', {})
                        full_name = extracted_data.get('full_name', extracted_data.get('name', 'Unknown'))
                        
                        return {
                            'messageId': message_id,
                            'message': f"""✅ **Identity Confirmed!**

👤 **Verified Identity:** {full_name}

🏛️ **Available Government Services:**

🚗 **JPJ Services:**
• License Renewal
• Vehicle Registration
• Road Tax Payment

💡 **TNB Services:**
• Bill Payment
• Account Verification

📋 **Other Services:**
• Document Verification
• Account Inquiries

**What service would you like to proceed with?**

Please tell me which service you need, for example:
• "I want to renew my license"
• "I want to pay my TNB bill"
• "Check my account status"

I'm here to help with your government service needs! 🤝""",
                            'sessionId': session_id,
                            'attachment': [],
                            'createdAt': self.get_iso_timestamp()
                        }
                
                # Handle other verified documents
                elif is_validated and extracted_data:
                    logger.info("🎯 PRIORITY: Verified document - offering general services")
                    
                    confirmation_keywords = ['yes', 'correct', 'confirm', 'ok', 'okay', 'right', 'true', 'accurate']
                    is_confirming = any(keyword in message.lower() for keyword in confirmation_keywords)
                    
                    if is_confirming:
                        logger.info("📄 User confirmed document - offering available services")
                        
                        return {
                            'messageId': message_id,
                            'message': """✅ **Document Information Confirmed!**

🏛️ **Available Government Services:**

🚗 **JPJ Services:**
• License Renewal
• Vehicle Registration

💡 **TNB Services:**
• Bill Payment
• Account Services

📋 **General Services:**
• Document Processing
• Account Verification

**What would you like to do next?**

Please tell me which service you need, for example:
• "I want to renew my license"
• "I want to pay my TNB bill"
• "Help with document verification"

How can I assist you today? 🤝""",
                            'sessionId': session_id,
                            'attachment': [],
                            'createdAt': self.get_iso_timestamp()
                        }
            
            # Classify intent using Bedrock
            logger.info("🤖 Calling Layer III - AWS Bedrock for intent classification")
            intent_result = self.classify_intent_with_bedrock(message)
            logger.info(f"✅ Bedrock classification result: {json.dumps(intent_result, indent=2)}")
            
            # Extract topic from intent result
            topic = intent_result.get('topic', None)
            intent_name = intent_result.get('intent', 'unknown')
            
            # Check if topic is detected and different from current session
            current_session_id = session_id
            
            # Skip topic management for check_context intent to avoid session changes
            if topic and intent_name != 'check_context':
                logger.info(f"🏷️ Topic detected: {topic}")
                
                # Check current session document
                current_session = chat_collection.find_one({'userId': user_id, 'sessionId': session_id})
                
                if current_session:
                    # Check if session has topic field at document level
                    session_has_topic = 'topic' in current_session
                    current_session_topic = current_session.get('topic', None)
                    
                    logger.info(f"📋 Current session has topic field: {session_has_topic}")
                    logger.info(f"📋 Current session topic: {current_session_topic}")
                    
                    # Only create new session if:
                    # 1. Session has topic field AND 
                    # 2. New topic is different from current topic
                    if session_has_topic and current_session_topic != topic:
                        # Create new session for different topic
                        new_session_id = str(uuid.uuid4())
                        logger.info(f"🆔 Creating new session for different topic '{current_session_topic}' → '{topic}': {new_session_id}")
                        
                        # Close current session
                        try:
                            chat_collection.update_one(
                                {'userId': user_id, 'sessionId': session_id},
                                {'$set': {'status': 'closed', 'closedAt': self.get_iso_timestamp()}}
                            )
                            logger.info(f"✅ Closed previous session: {session_id}")
                        except Exception as e:
                            logger.error(f"❌ Failed to close previous session: {str(e)}")
                        
                        # Create new session document with topic
                        new_session_doc = {
                            'userId': user_id,
                            'sessionId': new_session_id,
                            'createdAt': self.get_iso_timestamp(),
                            'topic': topic,  # Store topic at session level
                            'messages': [{
                                'messageId': message_id,
                                'message': message,
                                'timestamp': self.get_iso_timestamp(),
                                'type': 'user',
                                'intent': intent_name,
                                'topic': topic
                            }],
                            'status': 'active'
                        }
                        
                        try:
                            insert_result = chat_collection.insert_one(new_session_doc)
                            logger.info(f"✅ Created new session document with topic. Document ID: {insert_result.inserted_id}")
                            current_session_id = new_session_id
                        except Exception as e:
                            logger.error(f"❌ Failed to create new session document: {str(e)}")
                            current_session_id = session_id  # Fall back to original session
                    
                    elif not session_has_topic:
                        # Session has no topic field, add topic to existing session
                        logger.info(f"ℹ️ Adding topic '{topic}' to session without topic field: {session_id}")
                        try:
                            message_doc = {
                                'messageId': message_id,
                                'message': message,
                                'timestamp': self.get_iso_timestamp(),
                                'type': 'user',
                                'intent': intent_name,
                                'topic': topic
                            }
                            
                            update_result = chat_collection.update_one(
                                {'userId': user_id, 'sessionId': session_id},
                                {
                                    '$push': {'messages': message_doc},
                                    '$set': {'topic': topic}  # Add topic to session level
                                }
                            )
                            logger.info(f"✅ Added topic and message to existing session. Modified count: {update_result.modified_count}")
                        except Exception as e:
                            logger.error(f"❌ Failed to add topic to existing session: {str(e)}")
                    
                    else:
                        # Same topic, continue current session
                        logger.info(f"ℹ️ Same topic '{topic}', continuing current session: {session_id}")
                        try:
                            message_doc = {
                                'messageId': message_id,
                                'message': message,
                                'timestamp': self.get_iso_timestamp(),
                                'type': 'user',
                                'intent': intent_name,
                                'topic': topic
                            }
                            
                            update_result = chat_collection.update_one(
                                {'userId': user_id, 'sessionId': session_id},
                                {'$push': {'messages': message_doc}}
                            )
                            logger.info(f"✅ Added message to existing session with same topic. Modified count: {update_result.modified_count}")
                        except Exception as e:
                            logger.error(f"❌ Failed to add message to existing session: {str(e)}")
                else:
                    # Session doesn't exist, create new session with topic
                    logger.info(f"ℹ️ Session not found, creating new session with topic '{topic}': {session_id}")
                    new_session_doc = {
                        'userId': user_id,
                        'sessionId': session_id,
                        'createdAt': self.get_iso_timestamp(),
                        'topic': topic,
                        'messages': [{
                            'messageId': message_id,
                            'message': message,
                            'timestamp': self.get_iso_timestamp(),
                            'type': 'user',
                            'intent': intent_name,
                            'topic': topic
                        }],
                        'status': 'active'
                    }
                    
                    try:
                        insert_result = chat_collection.insert_one(new_session_doc)
                        logger.info(f"✅ Created new session document with topic. Document ID: {insert_result.inserted_id}")
                    except Exception as e:
                        logger.error(f"❌ Failed to create new session document: {str(e)}")
            else:
                # No topic detected OR check_context intent, continue current session without topic changes
                if intent_name == 'check_context':
                    logger.info("ℹ️ Check context intent - continuing current session without topic management")
                else:
                    logger.info("ℹ️ No topic detected, continuing current session")
                
                try:
                    message_doc = {
                        'messageId': message_id,
                        'message': message,
                        'timestamp': self.get_iso_timestamp(),
                        'type': 'user',
                        'intent': intent_name
                    }
                    
                    # Only add topic to message if it's not check_context intent
                    if intent_name != 'check_context' and topic:
                        message_doc['topic'] = topic
                    
                    update_result = chat_collection.update_one(
                        {'userId': user_id, 'sessionId': session_id},
                        {'$push': {'messages': message_doc}}
                    )
                    logger.info(f"✅ Added message to current session. Modified count: {update_result.modified_count}")
                except Exception as e:
                    logger.error(f"❌ Failed to add message to current session: {str(e)}")
            
            # Check if specific intents require document upload
            requires_document_upload = intent_name in ['renew_license', 'pay_tnb_bill']
            document_already_uploaded = self.check_document_uploaded_in_session(user_id, current_session_id, intent_name)
            
            # Check if user was previously awaiting document upload
            current_session = chat_collection.find_one({'userId': user_id, 'sessionId': current_session_id})
            awaiting_document = current_session.get('awaiting_document_upload') if current_session else None
            
            # Handle document_upload intent specifically
            if intent_name == 'document_upload':
                logger.info("📄 Handling document_upload intent")
                reply = self.handle_document_upload_intent(user_id, current_session_id, message, message_id)['message']
            
            # Handle check_context intent for context-less confirmations
            elif intent_name == 'check_context':
                logger.info("🔍 Handling check_context intent - looking up recent document data")
                context_result = self.check_recent_document_context(user_id, current_session_id)
                reply = context_result.get('message', 'I need more context to assist you properly.')
                
                # If we found context and user is confirming, update validation status
                if context_result.get('has_context') and context_result.get('requires_confirmation'):
                    try:
                        chat_collection.update_one(
                            {'userId': user_id, 'sessionId': current_session_id},
                            {'$set': {'isValidate': True, 'confirmation_timestamp': self.get_iso_timestamp()}}
                        )
                        logger.info("✅ Context found - marked document as validated")
                    except Exception as e:
                        logger.error(f"❌ Failed to mark document as validated: {str(e)}")
                
                # Note: check_context intent should NOT start a new session, context restoration
                # is handled within the check_recent_document_context method by updating current session
            
            elif requires_document_upload and not document_already_uploaded:
                # Prompt user to upload document for these specific intents
                logger.info(f"📎 Intent '{intent_name}' requires document upload - prompting user")
                reply = self.generate_document_upload_prompt(intent_name)
                
                # Mark session as awaiting document upload
                try:
                    chat_collection.update_one(
                        {'userId': user_id, 'sessionId': current_session_id},
                        {'$set': {'awaiting_document_upload': intent_name, 'document_prompt_sent': True}}
                    )
                    logger.info(f"✅ Session marked as awaiting document upload for intent: {intent_name}")
                except Exception as e:
                    logger.error(f"❌ Failed to mark session as awaiting document: {str(e)}")
            
            elif awaiting_document and awaiting_document != intent_name:
                # User changed intent while awaiting document upload, clear the awaiting state
                logger.info(f"🔄 User changed intent from '{awaiting_document}' to '{intent_name}' - clearing awaiting state")
                try:
                    chat_collection.update_one(
                        {'userId': user_id, 'sessionId': current_session_id},
                        {'$unset': {'awaiting_document_upload': '', 'document_prompt_sent': ''}}
                    )
                    logger.info("✅ Cleared awaiting document upload state")
                except Exception as e:
                    logger.error(f"❌ Failed to clear awaiting state: {str(e)}")
                
                # Generate normal response for the new intent
                reply = self.generate_intent_response(intent_result, message)
            
            elif awaiting_document == intent_name and not document_already_uploaded:
                # User is still on the same intent but hasn't uploaded document
                reply = f"I'm still waiting for you to upload the required document for {intent_name}. Please upload the document so I can assist you further."
                logger.info(f"⏳ Reminding user to upload document for intent: {intent_name}")
            
            elif awaiting_document and not document_already_uploaded:
                # User is awaiting document upload - only allow exit commands or enforce document upload
                if self.is_exit_or_restart_command(message):
                    logger.info(f"🚪 User wants to exit/restart while awaiting document upload")
                    # Clear awaiting state and process exit command
                    try:
                        chat_collection.update_one(
                            {'userId': user_id, 'sessionId': current_session_id},
                            {'$unset': {'awaiting_document_upload': '', 'document_prompt_sent': ''}}
                        )
                        logger.info("✅ Cleared awaiting document upload state for exit command")
                    except Exception as e:
                        logger.error(f"❌ Failed to clear awaiting state: {str(e)}")
                    
                    # Process the exit/restart command
                    reply = self.generate_intent_response(intent_result, message)
                else:
                    # Enforce document upload - reject other intents
                    awaiting_intent = awaiting_document
                    reply = f"""🚨 **Document Upload Required**

I'm still waiting for you to upload the required document for **{awaiting_intent}**.

📎 **You must upload a document to continue with this service.**

**Options:**
• 📸 Upload the required document now
• 🚪 Say "exit", "bye", or "cancel" to stop this process
• 🔄 Say "restart" to begin a new conversation

Please upload your document or use one of the exit commands above."""
                    logger.info(f"🔒 Enforcing document upload for awaiting intent: {awaiting_intent}")
            
            else:
                # Check if this is a license renewal confirmation or year selection
                license_renewal_response = self.handle_license_renewal_flow(user_id, current_session_id, message, intent_result, message_id)
                if license_renewal_response:
                    logger.info("🔄 License renewal flow handled - returning response")
                    reply = license_renewal_response['message']
                else:
                    # Check if this is a TNB bill payment confirmation
                    tnb_bill_response = self.handle_tnb_bill_flow(user_id, current_session_id, message, intent_result, message_id)
                    if tnb_bill_response:
                        logger.info("� TNB bill flow handled - returning response")
                        reply = tnb_bill_response['message']
                    else:
                        logger.info("�🔄 License renewal flow returned None - checking for manual override")
                        
                        # Priority check: Handle verified documents before manual override
                        current_session = chat_collection.find_one({'userId': user_id, 'sessionId': current_session_id})
                        if current_session:
                            extracted_data = current_session.get('data', {}) or current_session.get('extracted_data', {})
                            document_category = current_session.get('document_category', '')
                            is_validated = current_session.get('isValidate', False)
                            confirmation_keywords = ['yes', 'correct', 'confirm', 'ok', 'okay', 'right', 'true', 'accurate']
                            is_confirming = any(keyword in message.lower() for keyword in confirmation_keywords)
                            
                            # DEBUG: Log session state for troubleshooting
                            logger.info(f"🔍 DEBUG Session State:")
                            logger.info(f"   📂 document_category: '{document_category}'")
                            logger.info(f"   ✅ is_validated: {is_validated}")
                            logger.info(f"   🎯 is_confirming: {is_confirming}")
                            logger.info(f"   📄 has_extracted_data: {bool(extracted_data)}")
                            logger.info(f"   💬 message: '{message}'")
                            
                            # Priority check: If document is already verified and user is confirming, handle appropriately
                            # Check for IC documents with broader matching
                            ic_categories = ['ic', 'identity_card', 'mykad', 'malaysian_ic', 'identity_document', 'national_id', 'identification_card']
                            is_ic_document = any(ic_cat in document_category.lower() for ic_cat in ic_categories)
                            
                            if is_validated and is_ic_document and is_confirming:
                                logger.info("🎯 Priority check: IC document already verified, directing to license renewal")
                                reply = """✅ **IC Information Already Confirmed!**

🔄 **License Renewal Process**

How many years would you like to extend your driving license validity?

**Available Options:**
• 1️⃣ **1 Year** - RM 30.00
• 2️⃣ **2 Years** - RM 60.00  
• 3️⃣ **3 Years** - RM 90.00
• 4️⃣ **4 Years** - RM 120.00
• 5️⃣ **5 Years** - RM 150.00

Please reply with the number of years you want to extend (e.g., "2 years" or just "2")."""

                                # Mark session as awaiting year selection for license renewal
                                try:
                                    chat_collection.update_one(
                                        {'userId': user_id, 'sessionId': current_session_id},
                                        {
                                            '$set': {
                                                'awaiting_year_selection': True,
                                                'license_confirmed': True,
                                                'verification_timestamp': self.get_iso_timestamp()
                                            }
                                        }
                                    )
                                    logger.info("✅ IC verified - session marked as awaiting year selection for license renewal")
                                except Exception as e:
                                    logger.error(f"❌ Failed to mark session as awaiting year selection: {str(e)}")
                            elif is_validated and document_category == 'license' and is_confirming:
                                logger.info("🎯 Priority check: License document already verified, offering next-step services")
                                reply = """✅ **License Information Already Confirmed!**

🎯 **Next Step Services**

Your driving license information is already verified. What would you like to do next?

🔄 **License Renewal:**
• Extend license validity (1-5 years)
• Quick renewal process
• Secure payment options

💡 **Other Services:**
• TNB Bill Payment
• Government Account Services
• License Status Check

Please let me know which service you need assistance with."""
                            elif is_validated and document_category == 'tnb_bill' and is_confirming:
                                logger.info("🎯 Priority check: TNB bill document already verified, offering next-step services")
                                reply = """✅ **TNB Bill Information Already Confirmed!**

🎯 **Next Step Services**

Your TNB bill information is already verified. What would you like to do next?

💡 **Bill Payment:**
• Make payment to verified account
• Check payment status
• Payment receipt verification

🚗 **Other Services:**
• Driving License Renewal
• Government Account Services
• License Status Check

Please let me know which service you need assistance with."""
                            # Manual override: if user is confirming and we have unverified data, force the verification
                            elif document_category == 'license' and extracted_data and is_confirming and not is_validated:
                                logger.info("🚨 MANUAL OVERRIDE: Forcing license renewal year selection")
                                
                                # Mark session as verified and awaiting year selection
                                try:
                                    chat_collection.update_one(
                                        {'userId': user_id, 'sessionId': current_session_id},
                                        {
                                            '$set': {
                                                'isValidate': True,  # User confirmed document
                                                'awaiting_year_selection': True, 
                                                'license_confirmed': True,
                                                'verification_timestamp': self.get_iso_timestamp()
                                            }
                                        }
                                    )
                                    logger.info("✅ Session marked as verified and awaiting year selection (manual override)")
                                except Exception as e:
                                    logger.error(f"❌ Failed to mark session as verified: {str(e)}")
                                
                                reply = """✅ **License Information Confirmed!**

🔄 **License Renewal Process**

How many years would you like to extend your driving license validity?

**Available Options:**
• 1️⃣ **1 Year** - RM 30.00
• 2️⃣ **2 Years** - RM 60.00  
• 3️⃣ **3 Years** - RM 90.00
• 4️⃣ **4 Years** - RM 120.00
• 5️⃣ **5 Years** - RM 150.00

Please reply with the number of years you want to extend (e.g., "2 years" or just "2")."""
                            elif document_category == 'tnb_bill' and extracted_data and is_confirming and not is_validated:
                                logger.info("🚨 MANUAL OVERRIDE: TNB bill payment confirmation")
                                
                                # Mark session as verified and get TNB payment accounts
                                try:
                                    chat_collection.update_one(
                                        {'userId': user_id, 'sessionId': current_session_id},
                                        {
                                            '$set': {
                                                'isValidate': True,  # User confirmed document
                                                'verification_timestamp': self.get_iso_timestamp()
                                            }
                                        }
                                    )
                                    logger.info("✅ TNB bill marked as verified (manual override)")
                                except Exception as e:
                                    logger.error(f"❌ Failed to mark TNB bill as verified: {str(e)}")
                                
                                # Get TNB beneficiary accounts
                                bill_amount = extracted_data.get('bill_amount', extracted_data.get('amount_due', 'Not found'))
                                account_number = extracted_data.get('account_number', extracted_data.get('tnb_account_number', 'Not found'))
                                
                                beneficiary_info = self.get_beneficiary_accounts("TNB")
                                
                                if beneficiary_info and beneficiary_info.get('success'):
                                    accounts_info = self.format_beneficiary_accounts(beneficiary_info.get('documents', []))
                                    
                                    reply = f"""✅ **TNB Bill Information Confirmed!**

💡 **TNB Bill Payment**

📋 **Bill Details:**
• Account Number: {account_number}
• Amount Due: {bill_amount}

💳 **Payment Account Options:**

{accounts_info}

📸 **Next Step:** 
After making payment to any of the above accounts, take a clear photo of your payment receipt and send it to me for verification.

I'll verify the payment amount matches your bill amount before confirming the payment."""
                                else:
                                    reply = f"""✅ **TNB Bill Information Confirmed!**

💡 **TNB Bill Payment**

📋 **Bill Details:**
• Account Number: {account_number}
• Amount Due: {bill_amount}

💳 **Payment Instructions:**
Please make payment for your TNB bill.

📸 **Next Step:** 
After making payment, take a clear photo of your payment receipt and send it to me for verification."""
                            # Check for IC documents with broader matching (manual override)
                            elif is_ic_document and extracted_data and is_confirming and not is_validated:
                                logger.info("🚨 MANUAL OVERRIDE: IC information confirmation")
                                
                                # Mark session as verified
                                try:
                                    chat_collection.update_one(
                                        {'userId': user_id, 'sessionId': current_session_id},
                                        {
                                            '$set': {
                                                'isValidate': True,  # User confirmed document
                                                'verification_timestamp': self.get_iso_timestamp()
                                            }
                                        }
                                    )
                                    logger.info("✅ IC information marked as verified (manual override)")
                                except Exception as e:
                                    logger.error(f"❌ Failed to mark IC as verified: {str(e)}")
                                
                                reply = """✅ **IC Information Confirmed!**

🔄 **License Renewal Process**

How many years would you like to extend your driving license validity?

**Available Options:**
• 1️⃣ **1 Year** - RM 30.00
• 2️⃣ **2 Years** - RM 60.00  
• 3️⃣ **3 Years** - RM 90.00
• 4️⃣ **4 Years** - RM 120.00
• 5️⃣ **5 Years** - RM 150.00

Please reply with the number of years you want to extend (e.g., "2 years" or just "2")."""

                                # Mark session as awaiting year selection for license renewal
                                try:
                                    chat_collection.update_one(
                                        {'userId': user_id, 'sessionId': current_session_id},
                                        {
                                            '$set': {
                                                'isValidate': True,  # User confirmed document
                                                'awaiting_year_selection': True,
                                                'license_confirmed': True,
                                                'verification_timestamp': self.get_iso_timestamp()
                                            }
                                        }
                                    )
                                    logger.info("✅ IC information marked as verified and awaiting year selection (manual override)")
                                except Exception as e:
                                    logger.error(f"❌ Failed to mark IC as verified and awaiting year selection: {str(e)}")
                            # Catch-all for any document confirmation that doesn't match specific patterns
                            elif extracted_data and is_confirming and document_category:
                                logger.info(f"🎯 Generic document confirmation detected for category: {document_category}")
                                
                                # Mark as verified and direct to license renewal as default
                                try:
                                    chat_collection.update_one(
                                        {'userId': user_id, 'sessionId': current_session_id},
                                        {
                                            '$set': {
                                                'isValidate': True,  # User confirmed document
                                                'awaiting_year_selection': True,
                                                'license_confirmed': True,
                                                'verification_timestamp': self.get_iso_timestamp()
                                            }
                                        }
                                    )
                                    logger.info("✅ Generic document marked as verified and directing to license renewal")
                                except Exception as e:
                                    logger.error(f"❌ Failed to mark generic document as verified: {str(e)}")
                                
                                reply = """✅ **Document Information Confirmed!**

🔄 **License Renewal Process**

How many years would you like to extend your driving license validity?

**Available Options:**
• 1️⃣ **1 Year** - RM 30.00
• 2️⃣ **2 Years** - RM 60.00  
• 3️⃣ **3 Years** - RM 90.00
• 4️⃣ **4 Years** - RM 120.00
• 5️⃣ **5 Years** - RM 150.00

Please reply with the number of years you want to extend (e.g., "2 years" or just "2")."""
                            else:
                                # Generate normal response based on intent
                                reply = self.generate_intent_response(intent_result, message)
                        else:
                            # Generate normal response based on intent
                            reply = self.generate_intent_response(intent_result, message)
            
            logger.info(f"💬 Generated reply: {reply}")
            
            response_data = {
                'messageId': message_id,
                'message': reply,
                'sessionId': current_session_id,  # Use current or new session ID
                'attachment': [],
                'createdAt': self.get_iso_timestamp()
            }
            
            logger.info("✅ REGULAR_CONVERSATION intent processing completed")
            return response_data
            
        except Exception as e:
            logger.error(f"❌ Error in handle_regular_conversation: {str(e)}")
            error_response = {
                'messageId': message_id,
                'message': 'I understand you want assistance. Could you please provide more details about what you need help with?',
                'sessionId': session_id,
                'attachment': [],
                'createdAt': self.get_iso_timestamp()
            }
            return error_response
    
    def handle_license_renewal_flow(self, user_id: str, session_id: str, message: str, intent_result: dict, message_id: str) -> dict:
        """
        Handle license renewal confirmation and year selection flow
        """
        logger.info("🔄 Checking license renewal flow")
        logger.info(f"📝 Input message: '{message}'")
        logger.info(f"🤖 Intent result: {json.dumps(intent_result, indent=2)}")
        
        try:
            collection_name = user_id
            chat_collection = self.db[collection_name]
            
            # Get current session to check for extracted license data
            current_session = chat_collection.find_one({'userId': user_id, 'sessionId': session_id})
            if not current_session:
                logger.info("❌ No current session found")
                return None
            
            # Check if session has extracted license data and user is confirming
            extracted_data = current_session.get('data', {}) or current_session.get('extracted_data', {})
            document_category = current_session.get('document_category', '')
            is_validated = current_session.get('isValidate', False)
            
            logger.info(f"📊 Extracted data: {json.dumps(extracted_data, indent=2)}")
            logger.info(f"🏷️ Document category: '{document_category}'")
            logger.info(f"✅ Is validated: {is_validated}")
            
            # Check if user is confirming license data
            confirmation_keywords = ['yes', 'correct', 'confirm', 'ok', 'okay', 'right', 'true', 'accurate', 'proper']
            is_confirming = any(keyword in message.lower() for keyword in confirmation_keywords)
            
            logger.info(f"✅ Is confirming: {is_confirming}")
            logger.info(f"📋 Has license data: {bool(extracted_data)}")
            logger.info(f"📄 Is license category: {document_category == 'license'}")
            
            # Enhanced condition check for license confirmation
            if document_category == 'license' and extracted_data and is_confirming and not is_validated:
                # User confirmed license data, mark as verified and ask for extension years
                logger.info("✅ User confirmed license data - marking as verified and asking for extension years")
                
                # Mark session as verified and awaiting year selection
                try:
                    chat_collection.update_one(
                        {'userId': user_id, 'sessionId': session_id},
                        {
                            '$set': {
                                'isValidate': True,  # User confirmed document
                                'awaiting_year_selection': True,
                                'license_confirmed': True,
                                'verification_timestamp': self.get_iso_timestamp()
                            }
                        }
                    )
                    logger.info("✅ Session marked as verified and awaiting year selection")
                except Exception as e:
                    logger.error(f"❌ Failed to mark session as verified: {str(e)}")
                
                year_selection_message = """✅ **License Information Confirmed!**

🔄 **License Renewal Process**

How many years would you like to extend your driving license validity?

**Available Options:**
• 1️⃣ **1 Year** - RM 30.00
• 2️⃣ **2 Years** - RM 60.00  
• 3️⃣ **3 Years** - RM 90.00
• 4️⃣ **4 Years** - RM 120.00
• 5️⃣ **5 Years** - RM 150.00

Please reply with the number of years you want to extend (e.g., "2 years" or just "2")."""

                return {
                    'messageId': message_id,
                    'message': year_selection_message,
                    'sessionId': session_id,
                    'attachment': [],
                    'createdAt': self.get_iso_timestamp()
                }
            
            # Check if user is selecting years
            awaiting_year_selection = current_session.get('awaiting_year_selection', False)
            if awaiting_year_selection:
                return self.handle_year_selection(user_id, session_id, message, message_id, chat_collection)
            
            # Check if user is uploading payment receipt
            awaiting_payment = current_session.get('awaiting_payment_receipt', False)
            if awaiting_payment:
                # This will be handled by the document processing flow
                return None
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error in license renewal flow: {str(e)}")
            return None
    
    def handle_tnb_bill_flow(self, user_id: str, session_id: str, message: str, intent_result: dict, message_id: str) -> dict:
        """
        Handle TNB bill payment confirmation flow
        """
        logger.info("💡 Checking TNB bill flow")
        logger.info(f"📝 Input message: '{message}'")
        logger.info(f"🤖 Intent result: {json.dumps(intent_result, indent=2)}")
        
        try:
            collection_name = user_id
            chat_collection = self.db[collection_name]
            
            # Get current session to check for extracted TNB bill data
            current_session = chat_collection.find_one({'userId': user_id, 'sessionId': session_id})
            if not current_session:
                logger.info("❌ No current session found")
                return None
            
            # Check if session has extracted TNB bill data and user is confirming
            extracted_data = current_session.get('data', {}) or current_session.get('extracted_data', {})
            document_category = current_session.get('document_category', '')
            is_validated = current_session.get('isValidate', False)
            
            logger.info(f"📊 Extracted data: {json.dumps(extracted_data, indent=2)}")
            logger.info(f"🏷️ Document category: '{document_category}'")
            logger.info(f"✅ Is validated: {is_validated}")
            
            # Check if user is confirming TNB bill data
            confirmation_keywords = ['yes', 'correct', 'confirm', 'ok', 'okay', 'right', 'true', 'accurate', 'proper']
            is_confirming = any(keyword in message.lower() for keyword in confirmation_keywords)
            
            logger.info(f"✅ Is confirming: {is_confirming}")
            logger.info(f"📋 Has TNB bill data: {bool(extracted_data)}")
            logger.info(f"📄 Is TNB bill category: {document_category == 'tnb_bill'}")
            
            # Enhanced condition check for TNB bill confirmation
            if document_category == 'tnb_bill' and extracted_data and is_confirming and not is_validated:
                # User confirmed TNB bill data, mark as verified and show payment accounts
                logger.info("✅ User confirmed TNB bill data - marking as verified and showing payment accounts")
                
                # Mark session as verified
                try:
                    chat_collection.update_one(
                        {'userId': user_id, 'sessionId': session_id},
                        {
                            '$set': {
                                'isValidate': True,  # User confirmed document
                                'verification_timestamp': self.get_iso_timestamp()
                            }
                        }
                    )
                    logger.info("✅ TNB bill session marked as verified")
                except Exception as e:
                    logger.error(f"❌ Failed to mark TNB bill session as verified: {str(e)}")
                
                # Get bill details
                bill_amount = extracted_data.get('bill_amount', extracted_data.get('amount_due', 'Not found'))
                account_number = extracted_data.get('account_number', extracted_data.get('tnb_account_number', 'Not found'))
                customer_name = extracted_data.get('customer_name', extracted_data.get('full_name', 'Not found'))
                
                # Call MongoDB MCP API to get TNB beneficiary accounts
                logger.info("🌐 Calling MongoDB MCP API to get TNB beneficiary accounts")
                beneficiary_info = self.get_beneficiary_accounts("TNB")
                
                if beneficiary_info and beneficiary_info.get('success'):
                    # Generate payment message with beneficiary account details
                    accounts_info = self.format_beneficiary_accounts(beneficiary_info.get('documents', []))
                    
                    payment_message = f"""✅ **TNB Bill Information Confirmed!**

💡 **TNB Bill Payment**

📋 **Bill Details:**
• Customer Name: {customer_name}
• Account Number: {account_number}
• Amount Due: {bill_amount}

💳 **Payment Account Options:**

{accounts_info}

📸 **Next Step:** 
After making payment to any of the above accounts, take a clear photo of your payment receipt and send it to me for verification.

I'll verify the payment amount matches your bill amount before confirming the payment."""
                else:
                    # Fallback if API fails
                    payment_message = f"""✅ **TNB Bill Information Confirmed!**

💡 **TNB Bill Payment**

📋 **Bill Details:**
• Customer Name: {customer_name}
• Account Number: {account_number}
• Amount Due: {bill_amount}

💳 **Payment Instructions:**
Please make payment for your TNB bill amount: {bill_amount}

📸 **Next Step:** 
After making payment, take a clear photo of your payment receipt and send it to me for verification."""

                return {
                    'messageId': message_id,
                    'message': payment_message,
                    'sessionId': session_id,
                    'attachment': [],
                    'createdAt': self.get_iso_timestamp()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error in TNB bill flow: {str(e)}")
            return None

    def handle_year_selection(self, user_id: str, session_id: str, message: str, message_id: str, chat_collection) -> dict:
        """
        Handle year selection for license renewal
        """
        logger.info("📅 Processing year selection")
        
        try:
            # Extract number of years from message
            import re
            year_match = re.search(r'(\d+)', message.lower())
            
            if not year_match:
                # Invalid year selection
                retry_message = """❌ **Invalid Selection**

Please specify the number of years you want to extend your license.

**Available Options:**
• 1️⃣ **1 Year** - RM 30.00
• 2️⃣ **2 Years** - RM 60.00  
• 3️⃣ **3 Years** - RM 90.00
• 4️⃣ **4 Years** - RM 120.00
• 5️⃣ **5 Years** - RM 150.00

Please reply with just the number (e.g., "2" or "3")."""

                return {
                    'messageId': message_id,
                    'message': retry_message,
                    'sessionId': session_id,
                    'attachment': [],
                    'createdAt': self.get_iso_timestamp()
                }
            
            years = int(year_match.group(1))
            
            # Validate years (1-5)
            if years < 1 or years > 5:
                invalid_message = """❌ **Invalid Number of Years**

Please select between 1 to 5 years only.

**Available Options:**
• 1️⃣ **1 Year** - RM 30.00
• 2️⃣ **2 Years** - RM 60.00  
• 3️⃣ **3 Years** - RM 90.00
• 4️⃣ **4 Years** - RM 120.00
• 5️⃣ **5 Years** - RM 150.00"""

                return {
                    'messageId': message_id,
                    'message': invalid_message,
                    'sessionId': session_id,
                    'attachment': [],
                    'createdAt': self.get_iso_timestamp()
                }
            
            # Calculate payment amount
            amount = years * 30
            
            logger.info(f"✅ User selected {years} years, amount: RM {amount}")
            
            # Save year selection and amount to session
            try:
                chat_collection.update_one(
                    {'userId': user_id, 'sessionId': session_id},
                    {
                        '$set': {
                            'renewal_years': years,
                            'payment_amount': amount,
                            'awaiting_payment_receipt': True
                        },
                        '$unset': {'awaiting_year_selection': ''}
                    }
                )
                logger.info(f"✅ Saved renewal selection: {years} years, RM {amount}")
            except Exception as e:
                logger.error(f"❌ Failed to save year selection: {str(e)}")
            
            # Call MongoDB MCP API to get JPJ beneficiary accounts
            logger.info("🌐 Calling MongoDB MCP API to get JPJ beneficiary accounts")
            beneficiary_info = self.get_beneficiary_accounts("JPJ")
            
            if beneficiary_info and beneficiary_info.get('success'):
                # Generate payment message with beneficiary account details
                accounts_info = self.format_beneficiary_accounts(beneficiary_info.get('documents', []))
                
                payment_message = f"""✅ **License Renewal Selected**

📋 **Your Selection:**
• Extension Period: **{years} year{'s' if years > 1 else ''}**
• Payment Amount: **RM {amount:.2f}**

💳 **Payment Account Options:**

{accounts_info}

📸 **Next Step:** 
After making payment to any of the above accounts, take a clear photo of your payment receipt and send it to me for verification.

I'll verify the payment amount matches **RM {amount:.2f}** before proceeding with your license renewal."""
            else:
                # Fallback if API fails
                payment_message = f"""✅ **License Renewal Selected**

📋 **Your Selection:**
• Extension Period: **{years} year{'s' if years > 1 else ''}**
• Payment Amount: **RM {amount:.2f}**

💳 **Payment Instructions:**
Please make payment of **RM {amount:.2f}** for your license renewal.

📸 **Next Step:** 
After making payment, take a clear photo of your payment receipt and send it to me for verification.

I'll verify the payment amount matches RM {amount:.2f} before proceeding with your license renewal."""

            return {
                'messageId': message_id,
                'message': payment_message,
                'sessionId': session_id,
                'attachment': [],
                'createdAt': self.get_iso_timestamp()
            }
            
        except Exception as e:
            logger.error(f"❌ Error in year selection: {str(e)}")
            return {
                'messageId': message_id,
                'message': 'Sorry, there was an error processing your year selection. Please try again.',
                'sessionId': session_id,
                'attachment': [],
                'createdAt': self.get_iso_timestamp()
            }
    
    def get_beneficiary_accounts(self, service: str) -> dict:
        """
        Get beneficiary accounts from MongoDB MCP API
        """
        logger.info(f"🌐 Getting beneficiary accounts for service: {service}")
        
        try:
            # MongoDB MCP API endpoint
            api_url = "https://xlxakmb2sf.execute-api.us-east-1.amazonaws.com/dev/mongodb-mcp"
            
            # Create human language instruction
            instruction = f"find accounts with service from {service}"
            
            payload = {
                "instruction": instruction
            }
            
            logger.info(f"📤 MongoDB MCP API request: {json.dumps(payload, indent=2)}")
            print(f"🌐 MongoDB MCP API Request: {json.dumps(payload, indent=2)}")
            
            response = requests.post(api_url, json=payload, timeout=30)
            logger.info(f"📥 MongoDB MCP API response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ MongoDB MCP API success: {json.dumps(result, indent=2)}")
                print(f"✅ MongoDB MCP API Response: {json.dumps(result, indent=2)}")
                return result
            else:
                logger.error(f"❌ MongoDB MCP API error: {response.status_code} - {response.text}")
                print(f"❌ MongoDB MCP API Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error calling MongoDB MCP API: {str(e)}")
            return None
    
    def format_beneficiary_accounts(self, accounts: list) -> str:
        """
        Format beneficiary account information for display
        """
        if not accounts:
            return "⚠️ **No payment accounts found**"
        
        formatted_accounts = []
        
        for i, account in enumerate(accounts, 1):
            beneficiary_name = account.get('beneficiary_name', 'Unknown')
            beneficiary_account = account.get('beneficiary_account', 'Unknown')
            beneficiary_bank = account.get('beneficiary_bank', 'Unknown')
            qr_link = account.get('qr_link', '')
            
            account_info = f"""**{i}. {beneficiary_name}**
💳 Account: `{beneficiary_account}`
🏦 Bank: {beneficiary_bank}"""
            
            if qr_link:
                account_info += f"\n📱 QR Code: [Payment QR]({qr_link})"
            
            formatted_accounts.append(account_info)
        
        return "\n\n".join(formatted_accounts)

    def handle_document_upload_intent(self, user_id: str, session_id: str, message: str, message_id: str) -> dict:
        """
        Handle document_upload intent - when user mentions uploading a document but hasn't attached one yet
        """
        logger.info("📄 Processing DOCUMENT_UPLOAD intent")
        logger.info(f"👤 User ID: {user_id}")
        logger.info(f"🔗 Session ID: {session_id}")
        logger.info(f"💬 Message: {message}")
        
        # Prompt user to upload the document
        upload_prompt = """I'm ready to help you process your document! 📋

Please upload your document by taking a clear photo and sending it to me. I can process various types of documents including:

📸 **Driving License** - for license renewals and verification
📸 **TNB Bills** - for bill payments and account verification  
📸 **IC (Identity Card)** - for identity verification
📸 **Other Government Documents** - for various services

Please ensure the photo is clear and all text is readable for accurate processing."""

        collection_name = user_id
        chat_collection = self.db[collection_name]
        
        try:
            # Add message to session
            message_doc = {
                'messageId': message_id,
                'message': message,
                'timestamp': self.get_iso_timestamp(),
                'type': 'user',
                'intent': 'document_upload'
            }
            
            update_result = chat_collection.update_one(
                {'userId': user_id, 'sessionId': session_id},
                {
                    '$push': {'messages': message_doc},
                    '$set': {'awaiting_document_upload': 'document_upload', 'document_prompt_sent': True}
                }
            )
            logger.info(f"✅ Added document upload intent message and marked session as awaiting document. Modified count: {update_result.modified_count}")
        except Exception as e:
            logger.error(f"❌ Failed to update session for document upload intent: {str(e)}")
        
        response_data = {
            'messageId': message_id,
            'message': upload_prompt,
            'sessionId': session_id,
            'attachment': [],
            'createdAt': self.get_iso_timestamp()
        }
        
        logger.info("✅ DOCUMENT_UPLOAD intent processing completed")
        return response_data

    def handle_document_processing_with_confirmation(self, user_id: str, session_id: str, message: str, attachment: list, message_id: str) -> dict:
        """
        Handle document processing with OCR API call and Bedrock confirmation generation
        """
        logger.info("🔍 Processing DOCUMENT with OCR API and Bedrock confirmation")
        logger.info(f"👤 User ID: {user_id}")
        logger.info(f"🔗 Session ID: {session_id}")
        logger.info(f"💬 Message: {message}")
        logger.info(f"📎 Attachment: {attachment}")
        
        try:
            # Step 1: Call OCR document extraction service
            logger.info("📞 Calling OCR Document Extraction API")
            logger.info(f"🌐 Service URL: {self.textract_service_url}")
            
            # Handle both URL-based attachments and direct file content
            request_payload = self.prepare_ocr_payload(attachment)
            logger.info(f"📤 Request to OCR API: {json.dumps(request_payload, indent=2)}")
            print(f"📤 OCR API Request payload: {json.dumps(request_payload, indent=2)}")  # Enhanced logging
            
            response = requests.post(self.textract_service_url, json=request_payload, timeout=30)
            logger.info(f"📥 OCR API response status: {response.status_code}")
            print(f"📥 OCR API Response status: {response.status_code}")  # Enhanced logging
            
            if response.status_code == 200:
                extraction_result = response.json()
                logger.info(f"✅ OCR API response received")
                print(f"✅ OCR API Success response sample: {json.dumps(extraction_result, indent=2)[:500]}...")  # Enhanced logging
                
                # Check for blur analysis
                blur_analysis = extraction_result.get('blur_analysis', {})
                overall_assessment = blur_analysis.get('overall_assessment', {})
                is_blurry = overall_assessment.get('is_blurry', False)
                
                logger.info(f"📷 Image blur analysis - Is blurry: {is_blurry}")
                
                if is_blurry:
                    # Ask user to reupload due to blur
                    logger.info("⚠️ Image detected as blurry, requesting reupload")
                    
                    blur_response = {
                        'messageId': message_id,
                        'message': 'The image you uploaded appears to be blurry or unclear. Please take a clearer photo and upload it again for better processing.',
                        'sessionId': session_id,
                        'attachment': [],
                        'createdAt': self.get_iso_timestamp()
                    }
                    return blur_response
                
                # Step 2: Extract key information
                detected_category = extraction_result.get('category_detection', {}).get('detected_category', 'unknown')
                extracted_data = extraction_result.get('extracted_data', {})
                
                logger.info(f"🏷️ Detected category: {detected_category}")
                logger.info(f"📊 Extracted data: {json.dumps(extracted_data, indent=2)}")
                
                # Step 3: Store result to MongoDB with "data" field
                collection_name = user_id
                chat_collection = self.db[collection_name]
                logger.info(f"💾 Storing extraction result to MongoDB collection '{collection_name}' for session '{session_id}'")
                
                try:
                    update_result = chat_collection.update_one(
                        {'userId': user_id, 'sessionId': session_id},
                        {
                            '$push': {
                                'messages': {
                                    'messageId': message_id,
                                    'message': message,
                                    'timestamp': self.get_iso_timestamp(),
                                    'type': 'user',
                                    'attachment': attachment,
                                    'detected_category': detected_category,
                                    'extraction_result': extraction_result,
                                    'extracted_data': extracted_data,
                                    'intent': 'document_processing'
                                }
                            },
                            '$set': {
                                'data': extracted_data,  # Store as "data" field as requested
                                'extracted_data': extracted_data,  # Keep both for compatibility
                                'document_category': detected_category,
                                'last_document_processed': self.get_iso_timestamp(),
                                'isValidate': False  # Set to False when attachment is sent, True when user confirms
                            },
                            '$unset': {
                                'awaiting_document_upload': '',  # Clear awaiting state since document is uploaded
                                'document_prompt_sent': ''
                            }
                        }
                    )
                    logger.info(f"✅ Stored to collection '{collection_name}' with 'data' field, set isValidate=False, and cleared awaiting document state. Modified count: {update_result.modified_count}")
                except Exception as e:
                    logger.error(f"❌ Failed to store to collection '{collection_name}': {str(e)}")
                
                # Step 4: Store user identities if found
                if extracted_data:
                    logger.info("🔍 Checking for unique identities in extracted data")
                    self.store_user_identities(user_id, extracted_data)
                
                # Step 5: Check if this is a payment receipt for license renewal
                if detected_category == 'receipt':
                    receipt_verification_result = self.verify_payment_receipt(user_id, session_id, extracted_data, chat_collection)
                    if receipt_verification_result:
                        return receipt_verification_result
                
                # Step 6: Use Bedrock to generate confirmation question
                logger.info("🤖 Calling Bedrock to generate confirmation question")
                confirmation_message = self.generate_bedrock_confirmation_question(detected_category, extracted_data)
                logger.info(f"💬 Generated Bedrock confirmation message: {confirmation_message}")
                
                response_data = {
                    'messageId': message_id,
                    'message': confirmation_message,
                    'sessionId': session_id,
                    'attachment': [{
                        'type': 'extraction_result',
                        'category': detected_category,
                        'data': extracted_data,
                        'processing_timestamp': self.get_iso_timestamp(),
                        'requires_confirmation': True
                    }],
                    'createdAt': self.get_iso_timestamp()
                }
                
                logger.info("✅ DOCUMENT processing with confirmation completed successfully")
                return response_data
            else:
                logger.error(f"❌ OCR API returned error status: {response.status_code}")
                logger.error(f"❌ Response text: {response.text}")
                print(f"❌ OCR API Error status: {response.status_code}")  # Enhanced logging
                print(f"❌ OCR API Error response: {response.text}")  # Enhanced logging
                
                error_response = {
                    'messageId': message_id,
                    'message': 'Sorry, I had trouble processing your document. Please try uploading it again.',
                    'sessionId': session_id,
                    'attachment': [],
                    'createdAt': self.get_iso_timestamp()
                }
                return error_response
                
        except Exception as e:
            logger.error(f"❌ Error in document processing with confirmation: {str(e)}")
            error_response = {
                'messageId': message_id,
                'message': f'Sorry, I encountered an error while processing your document: {str(e)}',
                'sessionId': session_id,
                'attachment': [],
                'createdAt': self.get_iso_timestamp()
            }
            return error_response

    def generate_bedrock_confirmation_question(self, category: str, extracted_data: dict) -> str:
        """
        Use Bedrock to generate a natural confirmation question based on extracted data
        """
        logger.info("🤖 Generating Bedrock confirmation question")
        logger.info(f"📋 Category: {category}")
        logger.info(f"📊 Extracted data: {json.dumps(extracted_data, indent=2)}")
        
        # Create a prompt for Bedrock to generate confirmation question
        prompt = f"""You are a government services assistant. A user has uploaded a {category} document and OCR has extracted the following information:

Document Type: {category}
Extracted Data: {json.dumps(extracted_data, indent=2)}

Generate a friendly, professional confirmation message that:
1. Acknowledges the document was processed successfully
2. Lists the key extracted information in a clear, readable format
3. Asks the user to confirm if the information is correct
4. Provides clear options for "Yes, correct" or "No, needs correction"

Make the message conversational and easy to understand. Use emojis appropriately. Format the extracted data in a clean, organized way with bullet points.

Return only the confirmation message text, no JSON or code blocks."""

        try:
            bedrock_model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
            logger.info(f"🤖 Using Bedrock model for confirmation: {bedrock_model_id}")
            
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}]
            }
            logger.info(f"📤 Bedrock confirmation request: {json.dumps(request_body, indent=2)}")
            
            response = self.bedrock.invoke_model(
                modelId=bedrock_model_id,
                body=json.dumps(request_body)
            )
            
            result = json.loads(response['body'].read())
            logger.info(f"📥 Raw Bedrock confirmation response: {json.dumps(result, indent=2)}")
            
            confirmation_text = result['content'][0]['text'].strip()
            logger.info(f"✅ Generated confirmation question: {confirmation_text}")
            
            return confirmation_text
            
        except Exception as e:
            logger.error(f"❌ Bedrock confirmation generation error: {str(e)}")
            # Fallback to manual confirmation if Bedrock fails
            return self.generate_fallback_confirmation_message(category, extracted_data)
    
    def generate_fallback_confirmation_message(self, category: str, extracted_data: dict) -> str:
        """
        Generate fallback confirmation message if Bedrock fails
        """
        logger.info(f"📝 Generating fallback confirmation for category: {category}")
        
        # Format extracted data into readable bullets
        data_points = []
        for key, value in extracted_data.items():
            if value and str(value).strip():
                formatted_key = key.replace('_', ' ').title()
                data_points.append(f"• {formatted_key}: {value}")
        
        data_text = '\n'.join(data_points) if data_points else "• No specific data extracted"
        
        fallback_message = f"""✅ **Document Successfully Processed!**

📋 **Document Type:** {category.title()}

**Extracted Information:**
{data_text}

🔍 **Please confirm:** Is the information above correct?

**Reply with:**
• ✅ "Yes" or "Correct" - if the information is accurate
• ❌ "No" or "Wrong" - if something needs to be corrected

I'll proceed with the next steps once you confirm the details."""
        
        logger.info(f"📄 Generated fallback confirmation message")
        return fallback_message

    def verify_payment_receipt(self, user_id: str, session_id: str, extracted_data: dict, chat_collection) -> dict:
        """
        Verify payment receipt for license renewal
        """
        logger.info("💳 Verifying payment receipt for license renewal")
        
        try:
            # Get current session to check if awaiting payment
            current_session = chat_collection.find_one({'userId': user_id, 'sessionId': session_id})
            if not current_session:
                logger.info("ℹ️ No current session found")
                return None
            
            awaiting_payment = current_session.get('awaiting_payment_receipt', False)
            if not awaiting_payment:
                logger.info("ℹ️ Not awaiting payment receipt")
                return None
            
            # Get expected payment amount
            expected_amount = current_session.get('payment_amount', 0)
            renewal_years = current_session.get('renewal_years', 0)
            
            logger.info(f"💰 Expected payment: RM {expected_amount}, Years: {renewal_years}")
            
            # Extract amount from receipt
            receipt_amount_str = extracted_data.get('amount', '')
            logger.info(f"📄 Receipt amount string: {receipt_amount_str}")
            
            # Parse amount from receipt (handle different formats)
            import re
            amount_match = re.search(r'RM\s*(\d+(?:\.\d{2})?)', receipt_amount_str.replace(',', ''))
            
            if not amount_match:
                # Try alternative parsing
                amount_match = re.search(r'(\d+(?:\.\d{2})?)', receipt_amount_str.replace(',', '').replace('RM', ''))
            
            if not amount_match:
                verification_failed_message = f"""❌ **Payment Verification Failed**

I couldn't extract the payment amount from your receipt. 

**Expected Amount:** RM {expected_amount:.2f}
**Receipt Amount:** {receipt_amount_str}

Please ensure your receipt clearly shows the payment amount and try uploading again."""

                return {
                    'messageId': str(uuid.uuid4()),
                    'message': verification_failed_message,
                    'sessionId': session_id,
                    'attachment': [],
                    'createdAt': self.get_iso_timestamp()
                }
            
            receipt_amount = float(amount_match.group(1))
            logger.info(f"💰 Parsed receipt amount: RM {receipt_amount}")
            
            # Verify payment amount matches
            if abs(receipt_amount - expected_amount) < 0.01:  # Allow small floating point differences
                logger.info("✅ Payment amount verified - proceeding with license renewal")
                
                # Clear payment awaiting state and mark as verified
                try:
                    chat_collection.update_one(
                        {'userId': user_id, 'sessionId': session_id},
                        {
                            '$set': {
                                'payment_verified': True,
                                'receipt_data': extracted_data,
                                'verification_timestamp': self.get_iso_timestamp()
                            },
                            '$unset': {'awaiting_payment_receipt': ''}
                        }
                    )
                    logger.info("✅ Payment verification completed and saved")
                except Exception as e:
                    logger.error(f"❌ Failed to save payment verification: {str(e)}")
                
                # Process license renewal with government database
                renewal_result = self.process_license_renewal(user_id, session_id, current_session)
                
                if renewal_result['success']:
                    success_message = f"""✅ **Payment Verified & License Renewed!**

💳 **Payment Details:**
• Amount Paid: RM {receipt_amount:.2f}
• Expected: RM {expected_amount:.2f}
• Status: ✅ **VERIFIED**

📋 **License Renewal:**
• Extension Period: {renewal_years} year{'s' if renewal_years > 1 else ''}
• Status: ✅ **COMPLETED**

🏛️ **Government Database:**
• Update Status: ✅ **SUCCESSFUL**
• Processing ID: {renewal_result.get('processing_id', 'N/A')}

Your driving license validity has been successfully extended. Thank you for using our service! 🎉"""
                else:
                    error_message = f"""✅ **Payment Verified**

💳 **Payment Status:** ✅ Verified (RM {receipt_amount:.2f})

⚠️ **License Renewal Issue:**
There was an issue updating the government database. 

**Error:** {renewal_result.get('error', 'Unknown error')}

Please contact customer service with your payment receipt for manual processing."""

                return {
                    'messageId': str(uuid.uuid4()),
                    'message': success_message if renewal_result['success'] else error_message,
                    'sessionId': session_id,
                    'attachment': [],
                    'createdAt': self.get_iso_timestamp()
                }
            
            else:
                # Payment amount mismatch
                mismatch_message = f"""❌ **Payment Amount Mismatch**

💳 **Payment Verification:**
• Expected Amount: **RM {expected_amount:.2f}**
• Receipt Amount: **RM {receipt_amount:.2f}**
• Difference: RM {abs(receipt_amount - expected_amount):.2f}

**Required:** Please make payment of exactly **RM {expected_amount:.2f}** for {renewal_years} year{'s' if renewal_years > 1 else ''} license extension.

📸 **Next Step:** Upload the correct payment receipt showing RM {expected_amount:.2f}."""

                return {
                    'messageId': str(uuid.uuid4()),
                    'message': mismatch_message,
                    'sessionId': session_id,
                    'attachment': [],
                    'createdAt': self.get_iso_timestamp()
                }
            
        except Exception as e:
            logger.error(f"❌ Error in payment verification: {str(e)}")
            return {
                'messageId': str(uuid.uuid4()),
                'message': 'Sorry, there was an error verifying your payment. Please try uploading your receipt again.',
                'sessionId': session_id,
                'attachment': [],
                'createdAt': self.get_iso_timestamp()
            }
    
    def process_license_renewal(self, user_id: str, session_id: str, session_data: dict) -> dict:
        """
        Process license renewal by calling MongoDB MCP API
        """
        logger.info("🏛️ Processing license renewal with government database")
        
        try:
            # Extract IC number from previous license data
            extracted_data = session_data.get('data', {}) or session_data.get('extracted_data', {})
            ic_number = extracted_data.get('identity_no', 'Unknown')
            renewal_years = session_data.get('renewal_years', 1)
            
            logger.info(f"📄 Processing renewal for IC: {ic_number}, Years: {renewal_years}")
            
            # Create instruction for MongoDB MCP API
            instruction = f"Extend validity of {renewal_years} years for licence with ic {ic_number}"
            
            logger.info(f"📤 Sending instruction to MongoDB MCP: {instruction}")
            
            # Call MongoDB MCP API
            api_url = "https://xlxakmb2sf.execute-api.us-east-1.amazonaws.com/dev/mongodb-mcp"
            
            payload = {
                "instruction": instruction
            }
            
            logger.info(f"🌐 Calling MongoDB MCP API: {api_url}")
            print(f"🌐 MongoDB MCP API Request: {json.dumps(payload, indent=2)}")
            
            response = requests.post(api_url, json=payload, timeout=30)
            logger.info(f"📥 MongoDB MCP API response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ MongoDB MCP API success: {json.dumps(result, indent=2)}")
                print(f"✅ MongoDB MCP API Response: {json.dumps(result, indent=2)}")
                
                # Generate processing ID for tracking
                processing_id = f"LR{datetime.now().strftime('%Y%m%d%H%M%S')}{ic_number[-4:]}"
                
                return {
                    'success': True,
                    'result': result,
                    'processing_id': processing_id,
                    'instruction': instruction
                }
            else:
                logger.error(f"❌ MongoDB MCP API error: {response.status_code} - {response.text}")
                print(f"❌ MongoDB MCP API Error: {response.status_code} - {response.text}")
                
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code} - {response.text}",
                    'instruction': instruction
                }
                
        except Exception as e:
            logger.error(f"❌ Error in license renewal processing: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def handle_document_detection_with_api(self, user_id: str, session_id: str, message: str, attachment: list, message_id: str) -> dict:
        """
        Handle document detection using the API when a document is actually uploaded
        """
        logger.info("🔍 Processing DOCUMENT_DETECTION with API")
        logger.info(f"👤 User ID: {user_id}")
        logger.info(f"🔗 Session ID: {session_id}")
        logger.info(f"💬 Message: {message}")
        logger.info(f"📎 Attachment: {attachment}")
        
        try:
            # Call document extraction service
            logger.info("📞 Calling Document Extraction API")
            logger.info(f"🌐 Service URL: {self.textract_service_url}")
            
            # Handle both URL-based attachments and direct file content
            request_payload = self.prepare_ocr_payload(attachment)
            logger.info(f"📤 Request to API: {json.dumps(request_payload, indent=2)}")
            print(f"📤 OCR API Request payload: {json.dumps(request_payload, indent=2)}")  # Enhanced logging
            
            response = requests.post(self.textract_service_url, json=request_payload, timeout=30)
            logger.info(f"📥 API response status: {response.status_code}")
            print(f"📥 OCR API Response status: {response.status_code}")  # Enhanced logging
            
            if response.status_code == 200:
                extraction_result = response.json()
                logger.info(f"✅ API response received")
                print(f"✅ OCR API Success response sample: {json.dumps(extraction_result, indent=2)[:500]}...")  # Enhanced logging
                
                # Check for blur analysis
                blur_analysis = extraction_result.get('blur_analysis', {})
                overall_assessment = blur_analysis.get('overall_assessment', {})
                is_blurry = overall_assessment.get('is_blurry', False)
                
                logger.info(f"📷 Image blur analysis - Is blurry: {is_blurry}")
                
                if is_blurry:
                    # Ask user to reupload due to blur
                    logger.info("⚠️ Image detected as blurry, requesting reupload")
                    
                    blur_response = {
                        'messageId': message_id,
                        'message': 'The image you uploaded appears to be blurry or unclear. Please take a clearer photo and upload it again for better processing.',
                        'sessionId': session_id,
                        'attachment': [],
                        'createdAt': self.get_iso_timestamp()
                    }
                    return blur_response
                
                # Extract key information
                detected_category = extraction_result.get('category_detection', {}).get('detected_category', 'unknown')
                extracted_data = extraction_result.get('extracted_data', {})
                
                logger.info(f"🏷️ Detected category: {detected_category}")
                logger.info(f"📊 Extracted data: {json.dumps(extracted_data, indent=2)}")
                
                # Store result to user-specific collection based on current session_id
                collection_name = user_id
                chat_collection = self.db[collection_name]
                logger.info(f"💾 Storing extraction result to MongoDB collection '{collection_name}' for session '{session_id}'")
                
                try:
                    update_result = chat_collection.update_one(
                        {'userId': user_id, 'sessionId': session_id},
                        {
                            '$push': {
                                'messages': {
                                    'messageId': message_id,
                                    'message': message,
                                    'timestamp': self.get_iso_timestamp(),
                                    'type': 'user',
                                    'attachment': attachment,
                                    'detected_category': detected_category,
                                    'extraction_result': extraction_result,
                                    'extracted_data': extracted_data,
                                    'intent': 'document_detection'
                                }
                            },
                            '$set': {
                                'extracted_data': extracted_data,  # Store at session level
                                'document_category': detected_category,
                                'last_document_processed': self.get_iso_timestamp()
                            },
                            '$unset': {
                                'awaiting_document_upload': '',  # Clear awaiting state since document is uploaded
                                'document_prompt_sent': ''
                            }
                        }
                    )
                    logger.info(f"✅ Stored to collection '{collection_name}' and cleared awaiting document state. Modified count: {update_result.modified_count}")
                except Exception as e:
                    logger.error(f"❌ Failed to store to collection '{collection_name}': {str(e)}")
                
                # Check for unique identities and store to user database
                if extracted_data:
                    logger.info("🔍 Checking for unique identities in extracted data")
                    self.store_user_identities(user_id, extracted_data)
                
                # Generate success message with detected category
                success_message = f"""✅ **Document Successfully Processed!**

📋 **Detection Results:**
• Document Type: {detected_category.title()}
• Processing Status: Completed
• Data Extracted: ✅

I've successfully extracted the information from your {detected_category} document. The data has been stored securely and is ready for use.

How would you like to proceed with this document? I can help you with:
🔄 Process transactions
📋 Verify information  
📞 Access related services"""

                logger.info(f"💬 Generated success message for category: {detected_category}")
                
                response_data = {
                    'messageId': message_id,
                    'message': success_message,
                    'sessionId': session_id,
                    'attachment': [{
                        'type': 'extraction_result',
                        'category': detected_category,
                        'data': extracted_data,
                        'processing_timestamp': self.get_iso_timestamp()
                    }],
                    'createdAt': self.get_iso_timestamp()
                }
                
                logger.info("✅ DOCUMENT_DETECTION processing completed successfully")
                return response_data
            else:
                logger.error(f"❌ API returned error status: {response.status_code}")
                logger.error(f"❌ Response text: {response.text}")
                print(f"❌ OCR API Error status: {response.status_code}")  # Enhanced logging
                print(f"❌ OCR API Error response: {response.text}")  # Enhanced logging
                
                error_response = {
                    'messageId': message_id,
                    'message': 'Sorry, I had trouble processing your document. Please try uploading it again.',
                    'sessionId': session_id,
                    'attachment': [],
                    'createdAt': self.get_iso_timestamp()
                }
                return error_response
                
        except Exception as e:
            logger.error(f"❌ Error in document detection API call: {str(e)}")
            error_response = {
                'messageId': message_id,
                'message': f'Sorry, I encountered an error while processing your document: {str(e)}',
                'sessionId': session_id,
                'attachment': [],
                'createdAt': self.get_iso_timestamp()
            }
            return error_response

    def check_document_uploaded_in_session(self, user_id: str, session_id: str, intent_name: str) -> bool:
        """
        Check if a document has been uploaded in the current session for the specific intent
        OR if we've already prompted the user for this intent
        """
        logger.info(f"🔍 Checking if document uploaded for intent '{intent_name}' in session {session_id}")
        
        try:
            collection_name = user_id
            chat_collection = self.db[collection_name]
            
            # Find session and check for document uploads
            session_doc = chat_collection.find_one({'userId': user_id, 'sessionId': session_id})
            
            if session_doc:
                # Check if we've already prompted for this specific intent
                awaiting_document = session_doc.get('awaiting_document_upload')
                if awaiting_document == intent_name:
                    logger.info(f"ℹ️ Already prompted for document upload for intent '{intent_name}'")
                    return True  # Consider as "handled" to avoid re-prompting
                
                # Check if any message in this session has an attachment (document upload)
                messages = session_doc.get('messages', [])
                for message in messages:
                    if message.get('attachment') and len(message.get('attachment', [])) > 0:
                        logger.info(f"✅ Document found in session for intent '{intent_name}'")
                        return True
                
                # Also check if session has extraction_result or extracted_data
                if session_doc.get('extracted_data') or session_doc.get('extraction_result'):
                    logger.info(f"✅ Extracted data found in session for intent '{intent_name}'")
                    return True
            
            logger.info(f"❌ No document found in session for intent '{intent_name}'")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking document upload status: {str(e)}")
            return False
    
    def generate_document_upload_prompt(self, intent_name: str) -> str:
        """
        Generate specific prompts for document upload based on intent
        """
        logger.info(f"📝 Generating document upload prompt for intent: {intent_name}")
        
        prompts = {
            'renew_license': """I can help you renew your driving license! 📋

To proceed with the renewal, I need to verify your identity and current license details. Please upload one of the following documents:

📸 **Option 1:** Your current driving license (photo of the front side)
📸 **Option 2:** Your IC (Identity Card) - front side

Please take a clear photo and send it to me. I'll extract the necessary information to process your license renewal.""",
            
            'pay_tnb_bill': """I can help you pay your TNB electricity bill! ⚡

To process your bill payment, I need to verify your account details and bill information. Please upload:

📸 **TNB Bill Document:** Take a photo of your TNB bill (the upper portion showing your account number and amount due)

Please ensure the photo is clear and all important details are visible. I'll extract the account information to help you with the payment process."""
        }
        
        return prompts.get(intent_name, f"To proceed with '{intent_name}', please upload the required document.")

    def is_user_awaiting_document_upload(self, user_id: str, session_id: str) -> bool:
        """
        Check if user is currently awaiting document upload
        """
        try:
            collection_name = user_id
            chat_collection = self.db[collection_name]
            
            session_doc = chat_collection.find_one({'userId': user_id, 'sessionId': session_id})
            if session_doc:
                awaiting_document = session_doc.get('awaiting_document_upload')
                return awaiting_document is not None
            return False
        except Exception as e:
            logger.error(f"❌ Error checking awaiting document status: {str(e)}")
            return False
    
    def handle_enforce_document_upload(self, user_id: str, session_id: str, message: str, message_id: str) -> dict:
        """
        Enforce document upload when user is awaiting document but trying to do something else
        """
        logger.info("🔒 Processing ENFORCE_DOCUMENT_UPLOAD")
        logger.info(f"👤 User ID: {user_id}")
        logger.info(f"🔗 Session ID: {session_id}")
        logger.info(f"💬 Message: {message}")
        
        # Get the awaiting intent
        collection_name = user_id
        chat_collection = self.db[collection_name]
        
        try:
            session_doc = chat_collection.find_one({'userId': user_id, 'sessionId': session_id})
            awaiting_intent = session_doc.get('awaiting_document_upload', 'unknown') if session_doc else 'unknown'
            
            logger.info(f"📋 User is awaiting document upload for intent: {awaiting_intent}")
            
            enforcement_message = f"""🚨 **Document Upload Required**

I'm still waiting for you to upload the required document for **{awaiting_intent}**.

📎 **You must upload a document to continue with this service.**

**Your options:**
• 📸 **Upload the required document now** - Take a clear photo and send it
• 🚪 **Exit commands:** Say "exit", "bye", "cancel", or "stop" 
• 🔄 **Restart:** Say "restart" or "new conversation"
• 👋 **Start fresh:** Say "hello", "hi", "good morning", etc. (starts new session)

⚠️ All other requests will be ignored until you upload the document or use one of the options above."""

            # Add this interaction to session
            try:
                message_doc = {
                    'messageId': message_id,
                    'message': message,
                    'timestamp': self.get_iso_timestamp(),
                    'type': 'user',
                    'intent': 'blocked_awaiting_document',
                    'awaiting_for': awaiting_intent
                }
                
                chat_collection.update_one(
                    {'userId': user_id, 'sessionId': session_id},
                    {'$push': {'messages': message_doc}}
                )
                logger.info(f"✅ Added blocked message to session for awaiting intent: {awaiting_intent}")
            except Exception as e:
                logger.error(f"❌ Failed to add blocked message to session: {str(e)}")
            
            response_data = {
                'messageId': message_id,
                'message': enforcement_message,
                'sessionId': session_id,
                'attachment': [],
                'createdAt': self.get_iso_timestamp()
            }
            
            logger.info("✅ ENFORCE_DOCUMENT_UPLOAD processing completed")
            return response_data
            
        except Exception as e:
            logger.error(f"❌ Error in handle_enforce_document_upload: {str(e)}")
            error_response = {
                'messageId': message_id,
                'message': 'Please upload the required document to continue, or say "exit" to cancel.',
                'sessionId': session_id,
                'attachment': [],
                'createdAt': self.get_iso_timestamp()
            }
            return error_response

    def is_exit_or_restart_command(self, message: str) -> bool:
        """
        Check if the message is an exit, bye, restart command (no longer includes greetings)
        """
        exit_keywords = [
            'exit', 'bye', 'goodbye', 'cancel', 'stop', 'quit', 'end', 'abort',
            'restart', 'reset', 'start over', 'begin again', 'new conversation'
        ]
        
        message_lower = message.lower().strip()
        return any(keyword in message_lower for keyword in exit_keywords)

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
    
    def is_greeting_message(self, message: str) -> bool:
        """
        Check if the message is a greeting that should start a new session
        """
        greeting_keywords = [
            'hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon',
            'good evening', 'morning', 'afternoon', 'evening', 'hola', 'howdy'
        ]
        
        message_lower = message.lower().strip()
        # Check if message starts with or is exactly a greeting
        return any(
            message_lower.startswith(keyword) or message_lower == keyword 
            for keyword in greeting_keywords
        )
    
    def classify_intent_with_bedrock(self, message: str) -> dict:
        """
        Use AWS Bedrock to classify the intent of the message and determine topic
        """
        logger.info("🤖 Starting Bedrock intent classification")
        logger.info(f"💬 Message to classify: {message}")
        
        prompt = f"""Classify the intent of this government service request message. Return ONLY valid JSON.

Message: "{message}"

Available intents and their descriptions:
- renew_license: User wants to renew their driving license
- pay_tnb_bill: User wants to pay TNB electricity bill
- document_upload: User is uploading or sharing a document for processing
- license_inquiry: Questions about driving license, license application, license status
- tnb_inquiry: Questions about TNB bills, electricity bills, TNB account, power bills
- jpj_inquiry: Questions about JPJ services, vehicle registration, road tax
- account_inquiry: Questions about service accounts, account details, account management
- payment_inquiry: Questions about payments, transactions, payment status, payment methods
- document_inquiry: Questions about required documents, document verification
- general_inquiry: General questions about government services
- greeting: Greetings, introductions, how are you messages
- check_context: Simple confirmations like "yes", "correct", "ok" without clear context that need database lookup
- unknown: Cannot determine intent from the message

For specific topics, map the intent to these topics:
- renew_license → topic: "renew license"
- pay_tnb_bill → topic: "pay tnb bill"
- document_upload → topic: "document processing"
- check_context → topic: "context verification"

Return JSON format:
{{
    "intent": "intent_name",
    "confidence": 0.95,
    "category": "government_service_category",
    "topic": "specific_topic_name",
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
        
        # Updated identity fields to match new API response
        identity_fields = [
            'identity_no', 'license_number', 'account_number', 'tnb_account_number',
            'license_no', 'account_no', 'full_name'
        ]
        
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
                            'lastUpdated': self.get_iso_timestamp(),
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
    
    def generate_data_confirmation_message(self, category: str, extracted_data: dict) -> str:
        """
        Generate confirmation message with extracted key data for user verification
        """
        logger.info(f"📝 Generating confirmation message for category: {category}")
        
        if category == 'license':
            # Extract key license information
            full_name = extracted_data.get('full_name', 'Not found')
            identity_no = extracted_data.get('identity_no', 'Not found')
            license_number = extracted_data.get('license_number', 'Not found')
            
            confirmation_msg = f"""I've successfully processed your driving license. Please confirm the following details:

📋 **Extracted Information:**
• Full Name: {full_name}
• Identity Number: {identity_no}
• License Number: {license_number}

Is this information correct? Please reply "Yes" to confirm or "No" if any details need correction."""
            
            logger.info(f"📄 License confirmation generated for: {full_name}")
            return confirmation_msg
            
        elif category == 'tnb_bill':
            # Extract key TNB bill information
            account_number = extracted_data.get('account_number', extracted_data.get('tnb_account_number', 'Not found'))
            customer_name = extracted_data.get('customer_name', extracted_data.get('full_name', 'Not found'))
            bill_amount = extracted_data.get('bill_amount', extracted_data.get('amount_due', 'Not found'))
            
            confirmation_msg = f"""I've successfully processed your TNB bill. Please confirm the following details:

📋 **Extracted Information:**
• Customer Name: {customer_name}
• TNB Account Number: {account_number}
• Bill Amount: {bill_amount}

Is this information correct? Please reply "Yes" to confirm or "No" if any details need correction."""
            
            logger.info(f"💡 TNB bill confirmation generated for account: {account_number}")
            return confirmation_msg
            
        else:
            # Generic confirmation for other document types
            key_fields = []
            
            # Look for common identity fields
            if 'full_name' in extracted_data:
                key_fields.append(f"• Full Name: {extracted_data['full_name']}")
            if 'identity_no' in extracted_data:
                key_fields.append(f"• Identity Number: {extracted_data['identity_no']}")
            if 'account_number' in extracted_data:
                key_fields.append(f"• Account Number: {extracted_data['account_number']}")
            
            if key_fields:
                confirmation_msg = f"""I've successfully processed your document. Please confirm the following details:

📋 **Extracted Information:**
{chr(10).join(key_fields)}

Is this information correct? Please reply "Yes" to confirm or "No" if any details need correction."""
            else:
                confirmation_msg = f"I've processed your document (category: {category}). The document has been analyzed and stored. How can I assist you further?"
            
            logger.info(f"📄 Generic confirmation generated for category: {category}")
            return confirmation_msg

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
    
    def check_recent_document_context(self, user_id: str, session_id: str) -> dict:
        """
        Check MongoDB chat database for recent document data across all sessions to provide context for confirmation
        """
        logger.info("🔍 Checking recent document context from MongoDB across all sessions")
        logger.info(f"👤 User ID: {user_id}")
        logger.info(f"🔗 Current Session ID: {session_id}")
        
        try:
            collection_name = user_id
            chat_collection = self.db[collection_name]
            logger.info(f"💾 Checking collection: {collection_name}")
            
            # First check current session
            current_session = chat_collection.find_one({'userId': user_id, 'sessionId': session_id})
            
            # Then search for the most recent session with document data
            recent_session_with_data = chat_collection.find_one(
                {
                    'userId': user_id,
                    '$or': [
                        {'data': {'$exists': True, '$ne': {}}},
                        {'extracted_data': {'$exists': True, '$ne': {}}}
                    ]
                },
                sort=[('last_document_processed', -1), ('createdAt', -1)]
            )
            
            logger.info(f"📋 Found recent session with data: {bool(recent_session_with_data)}")
            
            if recent_session_with_data:
                # Extract document data from the most recent session with data
                extracted_data = recent_session_with_data.get('data', {}) or recent_session_with_data.get('extracted_data', {})
                document_category = recent_session_with_data.get('document_category', '')
                topic = recent_session_with_data.get('topic', '')
                is_validated = recent_session_with_data.get('isValidate', False)
                session_with_data_id = recent_session_with_data.get('sessionId', '')
                
                logger.info(f"📄 Found document category: '{document_category}'")
                logger.info(f"🏷️ Session topic: '{topic}'")
                logger.info(f"✅ Document validated: {is_validated}")
                logger.info(f"� Session with data ID: '{session_with_data_id}'")
                logger.info(f"📊 Extracted data keys: {list(extracted_data.keys())}")
                
                # Check if we have license renewal topic with ID/license number
                if topic == 'renew license' and extracted_data:
                    id_number = extracted_data.get('id_number', extracted_data.get('ic_number', extracted_data.get('identity_number', '')))
                    license_number = extracted_data.get('license_number', extracted_data.get('license_no', ''))
                    full_name = extracted_data.get('full_name', extracted_data.get('name', 'Not found'))
                    
                    logger.info(f"🆔 Found ID number: '{id_number}'")
                    logger.info(f"🪪 Found license number: '{license_number}'")
                    
                    if id_number or license_number:
                        logger.info("🎯 License renewal context found with ID/license - proceeding to payment accounts")
                        
                        # Get JPJ beneficiary accounts using MCP API
                        try:
                            beneficiary_info = self.get_beneficiary_accounts("JPJ")
                            logger.info(f"💳 Beneficiary accounts response: {beneficiary_info}")
                            
                            if beneficiary_info and beneficiary_info.get('success'):
                                accounts_info = self.format_beneficiary_accounts(beneficiary_info.get('documents', []))
                                
                                # Update current session with license renewal context
                                try:
                                    chat_collection.update_one(
                                        {'userId': user_id, 'sessionId': session_id},
                                        {
                                            '$set': {
                                                'topic': 'renew license',
                                                'document_category': document_category,
                                                'data': extracted_data,
                                                'isValidate': True,
                                                'awaiting_year_selection': True,
                                                'license_confirmed': True,
                                                'context_restored_from': session_with_data_id,
                                                'context_restoration_timestamp': self.get_iso_timestamp()
                                            }
                                        }
                                    )
                                    logger.info("✅ Current session updated with license renewal context")
                                except Exception as e:
                                    logger.error(f"❌ Failed to update current session with context: {str(e)}")
                                
                                message = f"""✅ **License Renewal Context Found!**

👤 **Name:** {full_name}
🆔 **ID Number:** {id_number}
{f'🪪 **License Number:** {license_number}' if license_number else ''}

🔄 **License Renewal Process**

How many years would you like to extend your driving license validity?

**Available Options:**
• 1️⃣ **1 Year** - RM 30.00
• 2️⃣ **2 Years** - RM 60.00  
• 3️⃣ **3 Years** - RM 90.00
• 4️⃣ **4 Years** - RM 120.00
• 5️⃣ **5 Years** - RM 150.00

Please reply with the number of years you want to extend (e.g., "2 years" or just "2")."""
                                
                                return {
                                    'has_context': True,
                                    'context_type': 'license_renewal_ready',
                                    'document_category': document_category,
                                    'extracted_data': extracted_data,
                                    'message': message,
                                    'requires_confirmation': False,
                                    'ready_for_payment': True
                                }
                            else:
                                logger.error("❌ Failed to get beneficiary accounts")
                                message = f"""✅ **License Renewal Context Found!**

👤 **Name:** {full_name}
🆔 **ID Number:** {id_number}
{f'🪪 **License Number:** {license_number}' if license_number else ''}

🔄 **License Renewal Process**

How many years would you like to extend your driving license validity?

**Available Options:**
• 1️⃣ **1 Year** - RM 30.00
• 2️⃣ **2 Years** - RM 60.00  
• 3️⃣ **3 Years** - RM 90.00
• 4️⃣ **4 Years** - RM 120.00
• 5️⃣ **5 Years** - RM 150.00

Please reply with the number of years you want to extend (e.g., "2 years" or just "2")."""
                                
                                return {
                                    'has_context': True,
                                    'context_type': 'license_renewal_ready',
                                    'document_category': document_category,
                                    'extracted_data': extracted_data,
                                    'message': message,
                                    'requires_confirmation': False
                                }
                        except Exception as e:
                            logger.error(f"❌ Error getting beneficiary accounts: {str(e)}")
                
                # Handle other document types that need confirmation
                if extracted_data and document_category and not is_validated:
                    logger.info("📋 Found unvalidated document data - generating confirmation request")
                    
                    # Update current session with found context
                    try:
                        chat_collection.update_one(
                            {'userId': user_id, 'sessionId': session_id},
                            {
                                '$set': {
                                    'document_category': document_category,
                                    'data': extracted_data,
                                    'topic': topic if topic else document_category,
                                    'context_restored_from': session_with_data_id,
                                    'context_restoration_timestamp': self.get_iso_timestamp()
                                }
                            }
                        )
                        logger.info("✅ Current session updated with found document context")
                    except Exception as e:
                        logger.error(f"❌ Failed to update current session with context: {str(e)}")
                    
                    # Generate confirmation message based on document type
                    if document_category == 'license':
                        full_name = extracted_data.get('full_name', extracted_data.get('name', 'Not found'))
                        license_number = extracted_data.get('license_number', extracted_data.get('license_no', 'Not found'))
                        expiry_date = extracted_data.get('expiry_date', extracted_data.get('valid_until', 'Not found'))
                        
                        confirmation_message = f"""📄 **Driving License Information Found**

👤 **Name:** {full_name}
🆔 **License Number:** {license_number}
📅 **Expiry Date:** {expiry_date}

❓ **Is this information correct?**

Please reply with "yes" or "correct" if the information is accurate, or "no" if you need to upload a different document."""
                    
                    elif document_category == 'tnb_bill':
                        account_number = extracted_data.get('account_number', extracted_data.get('tnb_account_number', 'Not found'))
                        bill_amount = extracted_data.get('bill_amount', extracted_data.get('amount_due', 'Not found'))
                        due_date = extracted_data.get('due_date', extracted_data.get('payment_due_date', 'Not found'))
                        
                        confirmation_message = f"""💡 **TNB Bill Information Found**

🔢 **Account Number:** {account_number}
💰 **Bill Amount:** {bill_amount}
📅 **Due Date:** {due_date}

❓ **Is this information correct?**

Please reply with "yes" or "correct" if the information is accurate, or "no" if you need to upload a different document."""
                    
                    elif document_category in ['ic', 'identity_card', 'mykad', 'idcard']:
                        ic_number = extracted_data.get('ic_number', extracted_data.get('id_number', extracted_data.get('identity_number', 'Not found')))
                        full_name = extracted_data.get('full_name', extracted_data.get('name', 'Not found'))
                        
                        confirmation_message = f"""🆔 **IC Information Found**

👤 **Name:** {full_name}
🔢 **IC Number:** {ic_number}

❓ **Is this information correct?**

Please reply with "yes" or "correct" if the information is accurate, or "no" if you need to upload a different document."""
                    
                    else:
                        # Generic document confirmation
                        confirmation_message = f"""📄 **Document Information Found ({document_category})**

I found your previous {document_category} document information.

❓ **Is this information correct?**

Please reply with "yes" or "correct" if the information is accurate, or "no" if you need to upload a different document."""
                    
                    return {
                        'has_context': True,
                        'context_type': 'needs_confirmation',
                        'document_category': document_category,
                        'extracted_data': extracted_data,
                        'message': confirmation_message,
                        'requires_confirmation': True
                    }
                
                # If document is already validated, provide next steps
                elif extracted_data and document_category and is_validated:
                    logger.info("✅ Found validated document data - providing next steps")
                    
                    # Update current session with validated context
                    try:
                        chat_collection.update_one(
                            {'userId': user_id, 'sessionId': session_id},
                            {
                                '$set': {
                                    'document_category': document_category,
                                    'data': extracted_data,
                                    'topic': topic if topic else document_category,
                                    'isValidate': True,
                                    'context_restored_from': session_with_data_id,
                                    'context_restoration_timestamp': self.get_iso_timestamp()
                                }
                            }
                        )
                        logger.info("✅ Current session updated with validated document context")
                    except Exception as e:
                        logger.error(f"❌ Failed to update current session with context: {str(e)}")
                    
                    if document_category == 'license' or topic == 'renew license':
                        message = """✅ **License Information Already Confirmed!**

🔄 **License Renewal Process**

How many years would you like to extend your driving license validity?

**Available Options:**
• 1️⃣ **1 Year** - RM 30.00
• 2️⃣ **2 Years** - RM 60.00  
• 3️⃣ **3 Years** - RM 90.00
• 4️⃣ **4 Years** - RM 120.00
• 5️⃣ **5 Years** - RM 150.00

Please reply with the number of years you want to extend (e.g., "2 years" or just "2")."""
                    
                    elif document_category in ['ic', 'identity_card', 'mykad', 'idcard']:
                        message = """✅ **IC Information Already Confirmed!**

🔄 **License Renewal Process**

How many years would you like to extend your driving license validity?

**Available Options:**
• 1️⃣ **1 Year** - RM 30.00
• 2️⃣ **2 Years** - RM 60.00  
• 3️⃣ **3 Years** - RM 90.00
• 4️⃣ **4 Years** - RM 120.00
• 5️⃣ **5 Years** - RM 150.00

Please reply with the number of years you want to extend (e.g., "2 years" or just "2")."""
                    
                    elif document_category == 'tnb_bill':
                        message = """✅ **TNB Bill Information Already Confirmed!**

💡 **Next Steps for Bill Payment**

Your TNB bill information is confirmed. To proceed with payment, I'll provide you with the payment account details.

Please wait while I retrieve the payment information for you."""
                    
                    else:
                        message = f"""✅ **Document Information Already Confirmed!**

Your {document_category} document has been validated. What would you like to do next?

🏛️ **Available Services:**
• License Renewal
• TNB Bill Payment
• Account Services

Please let me know how I can assist you further."""
                    
                    return {
                        'has_context': True,
                        'context_type': 'already_validated',
                        'document_category': document_category,
                        'extracted_data': extracted_data,
                        'message': message,
                        'requires_confirmation': False,
                        'is_validated': True
                    }
            
            # No recent document context found across any session
            logger.info("ℹ️ No recent document context found across all sessions")
            return {
                'has_context': False,
                'context_type': 'no_context',
                'message': """🤔 **Need More Context**

I don't have any recent document information to confirm. 

📎 **To get started:**
• Upload your IC or driving license for license renewal
• Upload your TNB bill for bill payment
• Or tell me specifically what service you need

How can I help you today?"""
            }
                
        except Exception as e:
            logger.error(f"❌ Error checking document context: {str(e)}")
            return {
                'has_context': False,
                'context_type': 'error',
                'message': "I encountered an error while checking your recent documents. Please upload a document or tell me what service you need."
            }
    
    def generate_intent_response(self, intent_result: dict, original_message: str) -> str:
        """
        Generate response based on classified intent with validation requests
        """
        intent = intent_result.get('intent', 'unknown')
        
        responses = {
            'renew_license': "I can help you renew your driving license. To proceed with the renewal and verify your identity, please upload a photo of your IC (Identity Card) or current driving license. This will help me validate your details and assist you better.",
            'pay_tnb_bill': "I can assist you with paying your TNB electricity bill. To proceed with the payment and verify your account, please take a photo of the upper part of your TNB bill (showing your account details and amount due). This will help me process your payment accurately.",
            'document_upload': "I'm ready to process your document! Please upload a clear photo of your document and I'll extract the information for you.",
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
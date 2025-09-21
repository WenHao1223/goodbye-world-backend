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
            message = request_data.get('message')
            created_at = request_data.get('created_at')
            attachment = request_data.get('attachment', [])
            
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
                response = self.handle_document_detection_with_api(user_id, session_id, message, attachment, message_id)
            
            elif session_id == "(new-session)":
                # Intent: first_time_connection
                intent_type = "first_time_connection"
                logger.info("🆕 INTENT DETECTED: first_time_connection (new session)")
                print("🆕 INTENT DETECTED: first_time_connection (new session)")  # CloudWatch visibility
                response = self.handle_first_time_connection(user_id, message, message_id)
            
            elif self.is_conversation_ending(message):
                # Intent: new_connection
                intent_type = "new_connection"
                logger.info("👋 INTENT DETECTED: new_connection (conversation ending)")
                print("👋 INTENT DETECTED: new_connection (conversation ending)")  # CloudWatch visibility
                response = self.handle_new_connection(user_id, session_id, message, message_id)
            
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
        
        # Store session in WhatsApp number-specific collection
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
        
        # Close current session in WhatsApp number-specific collection
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
            
            # Extract URL from attachment object
            file_url = attachment[0].get('url', '') if attachment and len(attachment) > 0 else ''
            
            request_payload = {
                'file_url': file_url
            }
            logger.info(f"📤 Request to textract service: {json.dumps(request_payload, indent=2)}")
            
            response = requests.post(self.textract_service_url, json=request_payload, timeout=30)
            logger.info(f"📥 Textract service response status: {response.status_code}")
            
            if response.status_code == 200:
                extraction_result = response.json()
                logger.info(f"✅ Textract service response received")
                
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
                
                # Store result to WhatsApp number-specific collection
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
            # Classify intent using Bedrock
            logger.info("🤖 Calling Layer III - AWS Bedrock for intent classification")
            intent_result = self.classify_intent_with_bedrock(message)
            logger.info(f"✅ Bedrock classification result: {json.dumps(intent_result, indent=2)}")
            
            # Extract topic from intent result
            topic = intent_result.get('topic', None)
            intent_name = intent_result.get('intent', 'unknown')
            
            collection_name = user_id
            chat_collection = self.db[collection_name]
            logger.info(f"💾 Processing conversation for MongoDB collection '{collection_name}'")
            
            # Check if topic is detected and different from current session
            current_session_id = session_id
            
            if topic:
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
                # No topic detected, continue current session
                logger.info("ℹ️ No topic detected, continuing current session")
                try:
                    message_doc = {
                        'messageId': message_id,
                        'message': message,
                        'timestamp': self.get_iso_timestamp(),
                        'type': 'user',
                        'intent': intent_name
                    }
                    
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
            
            # Extract URL from attachment object
            file_url = attachment[0].get('url', '') if attachment and len(attachment) > 0 else ''
            
            request_payload = {
                'file_url': file_url
            }
            logger.info(f"📤 Request to API: {json.dumps(request_payload, indent=2)}")
            
            response = requests.post(self.textract_service_url, json=request_payload, timeout=30)
            logger.info(f"📥 API response status: {response.status_code}")
            
            if response.status_code == 200:
                extraction_result = response.json()
                logger.info(f"✅ API response received")
                
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
                
                # Store result to WhatsApp number-specific collection based on current session_id
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
- unknown: Cannot determine intent from the message

For specific topics, map the intent to these topics:
- renew_license → topic: "renew license"
- pay_tnb_bill → topic: "pay tnb bill"
- document_upload → topic: "document processing"

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
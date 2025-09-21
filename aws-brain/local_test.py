import jsonimport json

from datetime import datetime, timezonefrom datetime import datetime, timezone

from main import IntentClassifierfrom main import IntentClassifier



def get_iso_timestamp() -> str:def get_iso_timestamp() -> str:

    """    """

    Get current timestamp in ISO format (UTC)    Get current timestamp in ISO format (UTC)

    """    """

    return datetime.now(timezone.utc).isoformat()    return datetime.now(timezone.utc).isoformat()



def test_local():def test_local():

    """    """

    Test the intent classifier locally including new document_upload intent    Test the intent classifier locally

    """    """

    classifier = IntentClassifier()    classifier = IntentClassifier()

        

    # Test cases for different intents including session management and document upload prompts    # Test cases for different intents including session management and document upload prompts

    current_time = get_iso_timestamp()    current_time = get_iso_timestamp()

    test_requests = [    test_requests = [

        {        {

            'user_id': 'test_user_123',            'user_id': 'test_user_123',

            'session_id': '(new-session)',            'session_id': '(new-session)',

            'message': 'Hello, I need help',            'message': 'Hello, I need help',

            'created_at': current_time,            'created_at': current_time,

            'attachment': []            'attachment': []

        },        },

        {        {

            'user_id': 'test_user_123',            'user_id': 'test_user_123',

            'session_id': 'session_123',            'session_id': 'session_123',

            'message': 'I want to check my driving license status',  # No topic            'message': 'I want to check my driving license status',  # No topic

            'created_at': current_time,            'created_at': current_time,

            'attachment': []            'attachment': []

        },        },

        {        {

            'user_id': 'test_user_123',            'user_id': 'test_user_123',

            'session_id': 'session_123',  # Same session            'session_id': 'session_123',  # Same session

            'message': 'I want to renew my license',  # New topic: "renew license" - should create new session AND prompt for document            'message': 'I want to renew my license',  # New topic: "renew license" - should create new session AND prompt for document

            'created_at': current_time,            'created_at': current_time,

            'attachment': []            'attachment': []

        },        },

        {        {

            'user_id': 'test_user_123',            'user_id': 'test_user_123',

            'session_id': 'session_456',  # This will be updated to new session ID from previous request            'session_id': 'session_456',  # This will be updated to new session ID from previous request

            'message': 'How much does license renewal cost?',  # Same topic: "renew license" - should remind about document upload            'message': 'How much does license renewal cost?',  # Same topic: "renew license" - should remind about document upload

            'created_at': current_time,            'created_at': current_time,

            'attachment': []            'attachment': []

        },        },

        {        {

            'user_id': 'test_user_123',            'user_id': 'test_user_123',

            'session_id': 'session_456',  # This will be updated            'session_id': 'session_456',  # This will be updated

            'message': 'I need to pay my TNB bill',  # New topic: "pay tnb bill" - should create new session AND prompt for document            'message': 'I need to pay my TNB bill',  # New topic: "pay tnb bill" - should create new session AND prompt for document

            'created_at': current_time,            'created_at': current_time,

            'attachment': []            'attachment': []

        },        },

        {        {

            'user_id': 'test_user_123',            'user_id': 'test_user_123',

            'session_id': 'session_789',  # This will be updated            'session_id': 'session_789',  # This will be updated

            'message': 'What is my TNB account balance?',  # Same topic: "pay tnb bill" - should remind about document upload            'message': 'What is my TNB account balance?',  # Same topic: "pay tnb bill" - should remind about document upload

            'created_at': current_time,            'created_at': current_time,

            'attachment': []            'attachment': []

        },        },

        {        {

            'user_id': 'test_user_123',            'user_id': 'test_user_123',

            'session_id': 'session_101',            'session_id': 'session_101',

            'message': 'Thank you for your help, goodbye',  # Conversation ending            'message': 'Thank you for your help, goodbye',  # Conversation ending

            'created_at': current_time,            'created_at': current_time,

            'attachment': []            'attachment': []

        },        },

        # Test case for renew_license with document upload after prompt        # Test case for renew_license with document upload after prompt

        {        {

            'user_id': 'test_user_doc_1',            'user_id': 'test_user_doc_1',

            'session_id': '(new-session)',            'session_id': '(new-session)',

            'message': 'I want to renew my driving license',  # Should prompt for document            'message': 'I want to renew my driving license',  # Should prompt for document

            'created_at': current_time,            'created_at': current_time,

            'attachment': []            'attachment': []

        },        },

        {        {

            'user_id': 'test_user_doc_1',            'user_id': 'test_user_doc_1',

            'session_id': 'session_doc_1',  # Will be updated from previous response            'session_id': 'session_doc_1',  # Will be updated from previous response

            'message': 'Here is my license document',            'message': 'Here is my license document',

            'created_at': current_time,            'created_at': current_time,

            'attachment': [{            'attachment': [{

                'url': 'https://example.com/license.jpg',                'url': 'https://example.com/license.jpg',

                'type': 'image/jpeg',                'type': 'image/jpeg',

                'name': 'license.jpg'                'name': 'license.jpg'

            }]            }]

        },        },

        # Test case for pay_tnb_bill with document upload after prompt        # Test case for pay_tnb_bill with document upload after prompt

        {        {

            'user_id': 'test_user_doc_2',            'user_id': 'test_user_doc_2',

            'session_id': '(new-session)',            'session_id': '(new-session)',

            'message': 'I need to pay my TNB electricity bill',  # Should prompt for document            'message': 'I need to pay my TNB electricity bill',  # Should prompt for document

            'created_at': current_time,            'created_at': current_time,

            'attachment': []            'attachment': []

        },        },

        {        {

            'user_id': 'test_user_doc_2',            'user_id': 'test_user_doc_2',

            'session_id': 'session_doc_2',  # Will be updated from previous response            'session_id': 'session_doc_2',  # Will be updated from previous response

            'message': 'Here is my TNB bill',            'message': 'Here is my TNB bill',

            'created_at': current_time,            'created_at': current_time,

            'attachment': [{            'attachment': [{

                'url': 'https://example.com/tnb_bill.jpg',                'url': 'https://example.com/tnb_bill.jpg',

                'type': 'image/jpeg',                'type': 'image/jpeg',

                'name': 'tnb_bill.jpg'                'name': 'tnb_bill.jpg'

            }]            }]

        },        },

        # Test case for intent change while awaiting document        # Test case for intent change while awaiting document

        {        {

            'user_id': 'test_user_change',            'user_id': 'test_user_change',

            'session_id': '(new-session)',            'session_id': '(new-session)',

            'message': 'I want to renew my license',  # Should prompt for document            'message': 'I want to renew my license',  # Should prompt for document

            'created_at': current_time,            'created_at': current_time,

            'attachment': []            'attachment': []

        },        },

        {        {

            'user_id': 'test_user_change',            'user_id': 'test_user_change',

            'session_id': 'session_change',            'session_id': 'session_change',

            'message': 'Actually, I want to pay my TNB bill instead',  # Should change intent and clear awaiting state            'message': 'Actually, I want to pay my TNB bill instead',  # Should change intent and clear awaiting state

            'created_at': current_time,            'created_at': current_time,

            'attachment': []            'attachment': []

        },        }

        # Test case for new document_upload intent    ]

        {    

            'user_id': 'test_user_doc_intent',    print("Testing Intent Classifier with Validation Requests")

            'session_id': '(new-session)',    print("=" * 60)

            'message': 'I have a document to upload',  # Should detect document_upload intent    

            'created_at': current_time,    for i, request_data in enumerate(test_requests, 1):

            'attachment': []        print(f"\nTest Case {i}:")

        },        print(f"Input: {json.dumps(request_data, indent=2)}")

        {        try:

            'user_id': 'test_user_doc_intent',            result = classifier.process_request(request_data)

            'session_id': 'session_doc_intent',            print(f"Result: {json.dumps(result, indent=2)}")

            'message': 'Here is my document',            

            'created_at': current_time,            # Highlight validation requests

            'attachment': [{            message_text = result.get('message', '')

                'url': 'https://example.com/document.jpg',            if 'upload a photo' in message_text or 'take a photo' in message_text:

                'type': 'image/jpeg',                print("🔐 VALIDATION REQUEST DETECTED!")

                'name': 'document.jpg'                if 'IC' in message_text or 'license' in message_text:

            }]                    print("📄 → User should upload IC or driving license")

        },                elif 'TNB bill' in message_text:

        # Test case for document upload with potential blur detection                    print("📋 → User should snap upper part of TNB bill")

        {            

            'user_id': 'test_user_blur',            # Highlight blur detection

            'session_id': '(new-session)',            if 'blurry' in message_text or 'unclear' in message_text:

            'message': 'Process this document please',                print("� BLUR DETECTED - Reupload requested!")

            'created_at': current_time,            

            'attachment': [{            # Highlight confirmation requests

                'url': 'https://example.com/blurry_document.jpg',            if 'confirm the following details' in message_text:

                'type': 'image/jpeg',                print("✅ DATA CONFIRMATION REQUEST!")

                'name': 'blurry_document.jpg'                if 'License Number' in message_text:

            }]                    print("🆔 → License data extracted and awaiting confirmation")

        },                elif 'TNB Account Number' in message_text:

        # Test case for document_upload intent without attachment                    print("💡 → TNB bill data extracted and awaiting confirmation")

        {            

            'user_id': 'test_user_upload_intent',            # Check for new document upload prompts

            'session_id': '(new-session)',            if 'upload one of the following documents' in message_text or 'Please upload:' in message_text:

            'message': 'I want to upload my documents for processing',  # Should trigger document_upload intent                print("📎 NEW DOCUMENT UPLOAD PROMPT DETECTED!")

            'created_at': current_time,                if 'driving license' in message_text or 'IC' in message_text:

            'attachment': []                    print("🆔 → User should upload driving license or IC for renewal")

        }                elif 'TNB bill' in message_text:

    ]                    print("💡 → User should upload TNB bill for payment processing")

                

    print("Testing Intent Classifier with Document Upload Intent")            # Check for document awaiting reminders

    print("=" * 60)            if 'still waiting for you to upload' in message_text:

                    print("⏳ DOCUMENT UPLOAD REMINDER!")

    for i, request_data in enumerate(test_requests, 1):                print("📁 → User hasn't uploaded required document yet")

        print(f"\nTest Case {i}:")        except Exception as e:

        print(f"Input: {json.dumps(request_data, indent=2)}")            print(f"Error: {str(e)}")

        try:

            result = classifier.process_request(request_data)def test_lambda_locally():

            print(f"Result: {json.dumps(result, indent=2)}")    """

                Test the lambda handler locally

            # Highlight document upload prompts (new flow)    """

            message_text = result.get('message', '')    from lambda_handler import lambda_handler

            if 'upload one of the following documents' in message_text or 'Please upload:' in message_text:    

                print("📎 DOCUMENT UPLOAD PROMPT DETECTED!")    test_event = {

                if 'driving license' in message_text or 'IC' in message_text:        'body': json.dumps({

                    print("🆔 → User should upload driving license or IC for renewal")            'userId': 'test_user_123',

                elif 'TNB bill' in message_text:            'sessionId': '(new-session)',

                    print("💡 → User should upload TNB bill for payment processing")            'message': 'I want to apply for a driving license',

                        'createdAt': get_iso_timestamp(),

            # Highlight new document_upload intent prompts            'attachment': []

            elif "I'm ready to help you process your document" in message_text or "Please upload your document by taking a clear photo" in message_text:        }),

                print("📄 NEW DOCUMENT_UPLOAD INTENT DETECTED!")        'httpMethod': 'POST'

                print("📤 → User expressed intent to upload documents")    }

                

            # Highlight document awaiting reminders    try:

            elif 'still waiting for you to upload' in message_text:        result = lambda_handler(test_event, None)

                print("⏳ DOCUMENT UPLOAD REMINDER!")        print("\nLambda Handler Test Result:")

                print("📁 → User hasn't uploaded required document yet")        print(json.dumps(result, indent=2))

                except Exception as e:

            # Highlight validation requests (legacy)        print(f"Lambda Handler Error: {str(e)}")

            elif 'upload a photo' in message_text or 'take a photo' in message_text:

                print("🔐 VALIDATION REQUEST DETECTED!")if __name__ == "__main__":

                if 'IC' in message_text or 'license' in message_text:    test_local()

                    print("📄 → User should upload IC or driving license")    test_lambda_locally()
                elif 'TNB bill' in message_text:
                    print("📋 → User should snap upper part of TNB bill")
            
            # Highlight successful document processing
            elif 'Document Successfully Processed!' in message_text:
                print("✅ DOCUMENT PROCESSING SUCCESS!")
                if 'license' in message_text.lower():
                    print("🆔 → License document processed successfully")
                elif 'tnb' in message_text.lower():
                    print("💡 → TNB bill processed successfully")
                else:
                    print("📄 → Document processed successfully")
            
            # Highlight blur detection
            if 'blurry' in message_text or 'unclear' in message_text:
                print("📸 BLUR DETECTED - Reupload requested!")
            
            # Highlight confirmation requests
            if 'confirm the following details' in message_text:
                print("✅ DATA CONFIRMATION REQUEST!")
                if 'License Number' in message_text:
                    print("🆔 → License data extracted and awaiting confirmation")
                elif 'TNB Account Number' in message_text:
                    print("💡 → TNB bill data extracted and awaiting confirmation")
            
            # Check for new document upload prompts
            if 'upload one of the following documents' in message_text or 'Please upload:' in message_text:
                print("📎 NEW DOCUMENT UPLOAD PROMPT DETECTED!")
                if 'driving license' in message_text or 'IC' in message_text:
                    print("🆔 → User should upload driving license or IC for renewal")
                elif 'TNB bill' in message_text:
                    print("💡 → User should upload TNB bill for payment processing")
            
            # Check for document awaiting reminders
            if 'still waiting for you to upload' in message_text:
                print("⏳ DOCUMENT UPLOAD REMINDER!")
                print("📁 → User hasn't uploaded required document yet")
        except Exception as e:
            print(f"Error: {str(e)}")

def test_lambda_locally():
    """
    Test the lambda handler locally
    """
    from lambda_handler import lambda_handler
    
    test_event = {
        'body': json.dumps({
            'userId': 'test_user_123',
            'sessionId': '(new-session)',
            'message': 'I want to upload my documents',
            'createdAt': get_iso_timestamp(),
            'attachment': []
        }),
        'httpMethod': 'POST'
    }
    
    try:
        result = lambda_handler(test_event, None)
        print("\nLambda Handler Test Result:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Lambda Handler Error: {str(e)}")

if __name__ == "__main__":
    test_local()
    test_lambda_locally()
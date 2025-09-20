import boto3
import json
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

class IntentChatbot:
    """
    A simple chatbot to classify user intent using AWS Bedrock.
    """
    def __init__(self):
        """
        Initializes the Bedrock client.
        """
        # Set up the AWS Bedrock client
        self.bedrock = boto3.client(
            'bedrock-runtime', 
            region_name=os.getenv('AWS_REGION', 'ap-southeast-2')
        )
        self.model_id = os.getenv(
            'BEDROCK_MODEL_ID', 
            'anthropic.claude-3-haiku-20240307-v1:0'
        )

    def get_intent(self, user_input: str) -> str:
        """
        Gets the user's intent from their input.

        Args:
            user_input: The text entered by the user.

        Returns:
            A string representing the intent ('renew_license', 'pay_summon', or 'others').
        """
        # This prompt is highly specific to ensure the AI only returns one of the three intents.
        prompt = f"""You are an intent classification AI. Your only job is to classify the user's request into one of the following three categories: 'renew_license', 'pay_summon', or 'others'.

- Use 'renew_license' for any requests about renewing, extending, or checking the validity of a driving license.
- Use 'pay_summon' for any requests about paying fines, traffic tickets, or summons (saman).
- Use 'others' for anything else, including greetings or general questions.

Do not respond with a sentence. Your output must be ONLY one of the three category names.

User request: "{user_input}"

Classification:"""

        try:
            # Create the payload for the Bedrock API call
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 10,
                "temperature": 0,
                "messages": [{"role": "user", "content": prompt}]
            }

            # Invoke the model
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(payload)
            )

            # Parse the response to get the generated text
            result = json.loads(response['body'].read())
            intent = result['content'][0]['text'].strip()

            # Final check to ensure the output is one of the valid intents
            if intent in ['renew_license', 'pay_summon', 'others']:
                return intent
            else:
                return 'others'

        except Exception as e:
            print(f"Error calling Bedrock API: {e}")
            return "others"

def main():
    """
    Main function to run the chatbot in the terminal.
    """
    chatbot = IntentChatbot()
    print("Simple Intent Chatbot")
    print("Enter your request, or type 'exit' to quit.")
    print("-" * 30)

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Bot: Goodbye!")
            break
        
        # Get the intent from the user's input
        intent = chatbot.get_intent(user_input)
        
        # Print the identified intent
        print(f"Bot (Intent): {intent}")

if __name__ == "__main__":
    main()

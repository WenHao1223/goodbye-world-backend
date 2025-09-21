import boto3
import json
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

class AIModel:
    """
    A reusable class to interact with an AWS Bedrock foundation model.
    This class is initialized once and can be used for various tasks
    by providing different prompts.
    """
    def __init__(self):
        """
        Initializes the Bedrock runtime client. This connection is created
        only once when an instance of this class is made.
        """
        self.bedrock = boto3.client(
            'bedrock-runtime',
            region_name=os.getenv('AWS_REGION', 'ap-southeast-2')
        )
        self.model_id = os.getenv(
            'BEDROCK_MODEL_ID',
            'anthropic.claude-3-haiku-20240307-v1:0'
        )

    def invoke(self, prompt: str, max_tokens: int = 10) -> str:
        """
        Invokes the Bedrock model with a specific prompt.

        Args:
            prompt: The full prompt string to send to the model.
            max_tokens: The maximum number of tokens for the model to generate.

        Returns:
            The text response from the model, or "Error" if something went wrong.
        """
        try:
            # The payload sent to the model includes the prompt and parameters.
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": 0,  # 0 for deterministic results
                "messages": [{"role": "user", "content": prompt}]
            }

            # The actual API call to the Bedrock service.
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(payload)
            )

            # Parse the response to extract the generated text.
            result = json.loads(response['body'].read())
            return result['content'][0]['text'].strip()

        except Exception as e:
            print(f"Error calling Bedrock API: {e}")
            return "Error"

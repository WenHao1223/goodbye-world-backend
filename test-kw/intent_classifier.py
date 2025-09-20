import boto3
import json
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# ...existing code...

def build_intent_prompt(user_input: str) -> str:
    """
    Builds a prompt for intent classification to be used with an AI model.

    Args:
        user_input: The text entered by the user.

    Returns:
        The prompt string for intent classification.
    """
    return f"""You are an intent classification AI. Your only job is to classify the user's request into one of the following three categories: 'renew_license', 'pay_summon', or 'others'.

- Use 'renew_license' for any requests about renewing, extending, or checking the validity of a driving license.
- Use 'pay_summon' for any requests about paying fines, traffic tickets, or summons (saman).
- Use 'others' for anything else, including greetings, chit-chat, or questions not related to licenses or summons.

Do not respond with a sentence. Your output must be ONLY one of the three category names.

User request: "{user_input}"

Classification:"""





















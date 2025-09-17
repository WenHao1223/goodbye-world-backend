# python check-bedrock-models.py --profile greataihackathon-personal --region us-east-1

import boto3
import argparse

def list_available_models(region, profile=None):
    session_kwargs = {"region_name": region}
    if profile:
        session_kwargs["profile_name"] = profile
    
    session = boto3.Session(**session_kwargs)
    bedrock = session.client("bedrock")
    
    try:
        response = bedrock.list_foundation_models()
        print(f"Available models in {region}:")
        for model in response['modelSummaries']:
            print(f"- {model['modelId']} ({model['modelName']})")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--profile", default=None)
    args = parser.parse_args()
    
    list_available_models(args.region, args.profile)
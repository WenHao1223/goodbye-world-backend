import os, json
import boto3
from dotenv import load_dotenv

load_dotenv()

# AWS Lambda automatically provides the region via AWS_REGION1 environment variable
REGION = os.environ.get('AWS_REGION1', 'ap-southeast-1')
PROFILE = os.getenv("AWS_PROFILE")

def build_body(model_id: str) -> tuple[bytes, str, str]:
    low = model_id.lower()
    if "anthropic" in low:
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 10,
            "messages": [{"role": "user", "content": "Say 'ok'."}],
        }
        return json.dumps(body).encode("utf-8"), "application/json", "application/json"
    if "nova" in low:
        body = {
            "messages": [{"role": "user", "content": [{"text": "Say ok."}]}],
            "inferenceConfig": {"max_new_tokens": 10},
        }
        return json.dumps(body).encode("utf-8"), "application/json", "application/json"
    if "titan" in low and ("text" in low or "express" in low):
        body = {"inputText": "Say ok.", "textGenerationConfig": {"maxTokenCount": 10}}
        return json.dumps(body).encode("utf-8"), "application/json", "application/json"
    raise ValueError("Unsupported model for test")

def is_invokable_model_id(mid: str) -> bool:
    if ":28k" in mid or ":200k" in mid:
        return False
    if "embed" in mid.lower():
        return False
    return True

def check_bedrock_models():
    print(f"Checking Bedrock models in region: {REGION}")
    print("-" * 60)

    session = boto3.Session(profile_name=PROFILE) if PROFILE else boto3.Session()
    bedrock = session.client("bedrock", region_name=REGION)
    rt = session.client("bedrock-runtime", region_name=REGION)
    
    # Check quotas
    print("Checking Bedrock quotas:")
    try:
        service_quotas = session.client('service-quotas', region_name=REGION)
        bedrock_quotas = service_quotas.list_service_quotas(ServiceCode='bedrock')
        
        for quota in bedrock_quotas['Quotas']:
            if any(word in quota['QuotaName'].lower() for word in ['on-demand', 'request', 'token', 'throughput']):
                print(f"  {quota['QuotaName']}: {quota['Value']} {quota.get('Unit', '')}")
                
    except Exception as e:
        print(f"  Could not retrieve quotas: {str(e)[:50]}...")

    # List models
    resp = bedrock.list_foundation_models()
    summaries = resp.get("modelSummaries", [])
    print("\nAll available models:")
    for m in summaries:
        mid = m["modelId"]
        status = m.get("modelLifecycle", {}).get("status", "N/A")
        inf = ",".join(m.get("inferenceTypesSupported", [])) or "N/A"
        print(f"  {mid}\n    Status: {status}\n    Inference: {inf}\n")

    # Map modelId -> whether it needs profiles
    needs_profile = {}
    for m in summaries:
        mid = m["modelId"]
        types = m.get("inferenceTypesSupported", []) or []
        needs_profile[mid] = ("PROVISIONED" in types) and ("ON_DEMAND" not in types)

    # Index inference profiles
    profiles_by_model = {}
    try:
        next_token = None
        while True:
            kw = {"maxResults": 100}
            if next_token:
                kw["nextToken"] = next_token
            prof = bedrock.list_inference_profiles(**kw)
            for p in prof.get("inferenceProfiles", []):
                for assoc in p.get("modelAssociations", []):
                    mid = assoc.get("modelId")
                    if not mid:
                        continue
                    profiles_by_model.setdefault(mid, []).append(p["inferenceProfileId"])
            next_token = prof.get("nextToken")
            if not next_token:
                break
    except Exception as e:
        print(f"Could not list inference profiles: {e}")

    print("Testing model access:")
    for m in summaries:
        mid = m["modelId"]

        if not is_invokable_model_id(mid):
            print(f"  [SKIP] {mid} - Not directly invokable")
            continue

        try:
            body, ctype, accept = build_body(mid)
        except ValueError:
            print(f"  [SKIP] {mid} - Unsupported in test")
            continue

        try:
            if needs_profile.get(mid):
                prof_ids = profiles_by_model.get(mid, [])
                if not prof_ids:
                    print(f"  [NO] {mid} - Requires Inference Profile (none found)")
                    continue
                rt.invoke_model(
                    inferenceProfileIdentifier=prof_ids[0],
                    body=body,
                    contentType=ctype,
                    accept=accept,
                )
            else:
                rt.invoke_model(
                    modelId=mid,
                    body=body,
                    contentType=ctype,
                    accept=accept,
                )
            print(f"  [OK] {mid} - ACCESSIBLE")
        except Exception as e:
            msg = str(e)
            if "AccessDenied" in msg:
                print(f"  [NO] {mid} - NO ACCESS")
            elif "ThrottlingException" in msg:
                print(f"  [THROTTLED] {mid} - RATE LIMITED")
            elif "ValidationException" in msg and "on-demand throughput isn't supported" in msg:
                print(f"  [NO] {mid} - Needs Inference Profile")
            elif "ResourceNotFoundException" in msg:
                print(f"  [??] {mid} - Not found")
            else:
                print(f"  [??] {mid} - ERROR: {msg[:50]}...")

if __name__ == "__main__":
    check_bedrock_models()
import os, json
import boto3
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("AWS_REGION", "ap-southeast-1")
PROFILE = os.getenv("AWS_PROFILE")

# Very small test prompts per provider
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
        # When using inference profiles for Nova, the messages format is supported.
        body = {
            "messages": [{"role": "user", "content": [{"text": "Say ok."}]}],
            "inferenceConfig": {"max_new_tokens": 10},
        }
        return json.dumps(body).encode("utf-8"), "application/json", "application/json"
    if "titan" in low and ("text" in low or "express" in low):
        body = {"inputText": "Say ok.", "textGenerationConfig": {"maxTokenCount": 10}}
        return json.dumps(body).encode("utf-8"), "application/json", "application/json"
    # Skip embeddings and anything unknown here
    raise ValueError("Unsupported model for test")

def is_invokable_model_id(mid: str) -> bool:
    # Skip context-size variants like :28k/:200k and embeddings
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

    # 1) List models
    resp = bedrock.list_foundation_models()
    summaries = resp.get("modelSummaries", [])
    print("All available models:")
    for m in summaries:
        mid = m["modelId"]
        status = m.get("modelLifecycle", {}).get("status", "N/A")
        inf = ",".join(m.get("inferenceTypesSupported", [])) or "N/A"
        print(f"  {mid}\n    Status: {status}\n    Inference: {inf}\n")

    # 2) Map modelId -> whether it needs profiles
    needs_profile = {}
    for m in summaries:
        mid = m["modelId"]
        types = m.get("inferenceTypesSupported", []) or []
        needs_profile[mid] = ("PROVISIONED" in types) and ("ON_DEMAND" not in types)

    # 3) Index inference profiles (so we can try them automatically)
    profiles_by_model = {}
    next_token = None
    while True:
        kw = {"maxResults": 100}
        if next_token:
            kw["nextToken"] = next_token
        prof = bedrock.list_inference_profiles(**kw)
        for p in prof.get("inferenceProfiles", []):
            # Each profile lists one or more associated model IDs
            for assoc in p.get("modelAssociations", []):
                mid = assoc.get("modelId")
                if not mid:
                    continue
                profiles_by_model.setdefault(mid, []).append(p["inferenceProfileId"])
        next_token = prof.get("nextToken")
        if not next_token:
            break

    print("Testing model access:")
    for m in summaries:
        mid = m["modelId"]

        # Skip non-invokable IDs
        if not is_invokable_model_id(mid):
            print(f"  [SKIP] {mid} - Not directly invokable (variant/embedding).")
            continue

        # Build provider-specific body
        try:
            body, ctype, accept = build_body(mid)
        except ValueError:
            print(f"  [SKIP] {mid} - Unsupported in quick test harness.")
            continue

        try:
            if needs_profile.get(mid):
                prof_ids = profiles_by_model.get(mid, [])
                if not prof_ids:
                    print(f"  [NO] {mid} - Requires Inference Profile (none found).")
                    continue
                # Try the first available profile
                rt.invoke_model(
                    inferenceProfileIdentifier=prof_ids[0],
                    body=body,
                    contentType=ctype,
                    accept=accept,
                )
            else:
                # On-demand is supported
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
                print(f"  [NO] {mid} - NO ACCESS (grant in Console)")
            elif "ValidationException" in msg and "on-demand throughput isn’t supported" in msg:
                print(f"  [NO] {mid} - Needs Inference Profile (provisioned).")
            elif "ResourceNotFoundException" in msg:
                print(f"  [??] {mid} - Not found (wrong ID or region/profile).")
            else:
                print(f"  [??] {mid} - ERROR: {msg}")

if __name__ == "__main__":
    check_bedrock_models()
import os, json
import boto3
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("AWS_REGION", "ap-southeast-1")
PROFILE = os.getenv("AWS_PROFILE")

# Very small test prompts per provider
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
        # When using inference profiles for Nova, the messages format is supported.
        body = {
            "messages": [{"role": "user", "content": [{"text": "Say ok."}]}],
            "inferenceConfig": {"max_new_tokens": 10},
        }
        return json.dumps(body).encode("utf-8"), "application/json", "application/json"
    if "titan" in low and ("text" in low or "express" in low):
        body = {"inputText": "Say ok.", "textGenerationConfig": {"maxTokenCount": 10}}
        return json.dumps(body).encode("utf-8"), "application/json", "application/json"
    # Skip embeddings and anything unknown here
    raise ValueError("Unsupported model for test")

def is_invokable_model_id(mid: str) -> bool:
    # Skip context-size variants like :28k/:200k and embeddings
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

    # 1) List models
    resp = bedrock.list_foundation_models()
    summaries = resp.get("modelSummaries", [])
    print("All available models:")
    for m in summaries:
        mid = m["modelId"]
        status = m.get("modelLifecycle", {}).get("status", "N/A")
        inf = ",".join(m.get("inferenceTypesSupported", [])) or "N/A"
        print(f"  {mid}\n    Status: {status}\n    Inference: {inf}\n")

    # 2) Map modelId -> whether it needs profiles
    needs_profile = {}
    for m in summaries:
        mid = m["modelId"]
        types = m.get("inferenceTypesSupported", []) or []
        needs_profile[mid] = ("PROVISIONED" in types) and ("ON_DEMAND" not in types)

    # 3) Index inference profiles (so we can try them automatically)
    profiles_by_model = {}
    next_token = None
    while True:
        kw = {"maxResults": 100}
        if next_token:
            kw["nextToken"] = next_token
        prof = bedrock.list_inference_profiles(**kw)
        for p in prof.get("inferenceProfiles", []):
            # Each profile lists one or more associated model IDs
            for assoc in p.get("modelAssociations", []):
                mid = assoc.get("modelId")
                if not mid:
                    continue
                profiles_by_model.setdefault(mid, []).append(p["inferenceProfileId"])
        next_token = prof.get("nextToken")
        if not next_token:
            break

    print("Testing model access:")
    for m in summaries:
        mid = m["modelId"]

        # Skip non-invokable IDs
        if not is_invokable_model_id(mid):
            print(f"  [SKIP] {mid} - Not directly invokable (variant/embedding).")
            continue

        # Build provider-specific body
        try:
            body, ctype, accept = build_body(mid)
        except ValueError:
            print(f"  [SKIP] {mid} - Unsupported in quick test harness.")
            continue

        try:
            if needs_profile.get(mid):
                prof_ids = profiles_by_model.get(mid, [])
                if not prof_ids:
                    print(f"  [NO] {mid} - Requires Inference Profile (none found).")
                    continue
                # Try the first available profile
                rt.invoke_model(
                    inferenceProfileIdentifier=prof_ids[0],
                    body=body,
                    contentType=ctype,
                    accept=accept,
                )
            else:
                # On-demand is supported
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
                print(f"  [NO] {mid} - NO ACCESS (grant in Console)")
            elif "ValidationException" in msg and "on-demand throughput isn’t supported" in msg:
                print(f"  [NO] {mid} - Needs Inference Profile (provisioned).")
            elif "ResourceNotFoundException" in msg:
                print(f"  [??] {mid} - Not found (wrong ID or region/profile).")
            else:
                print(f"  [??] {mid} - ERROR: {msg}")

if __name__ == "__main__":
    check_bedrock_models()
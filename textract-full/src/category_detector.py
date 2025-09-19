#!/usr/bin/env python3
"""
Category Detector - Auto-detect document category based on text, forms, and tables
"""

import json
import boto3
from typing import Dict, List, Optional, Tuple
from .logger import log_print

def detect_document_category(textract_results: Dict, region: str, profile: Optional[str] = None) -> Tuple[str, float]:
    """
    Auto-detect document category using Bedrock AI based on textract results
    Returns: (category, confidence_score)
    """
    
    # Prepare content for analysis
    content_parts = []
    
    # Add text content
    if 'text' in textract_results:
        text_content = " ".join([item['text'] for item in textract_results['text']])
        content_parts.append(f"TEXT: {text_content}")
    
    # Add form content
    if 'forms' in textract_results:
        form_content = " ".join([f"{k}: {str(v)}" for k, v in textract_results['forms'].items()])
        content_parts.append(f"FORMS: {form_content}")
    
    # Add table content
    if 'tables' in textract_results:
        table_content = ""
        for table in textract_results['tables'].get('tables', []):
            for row in table.get('rows', []):
                table_content += " ".join(row) + " "
        content_parts.append(f"TABLES: {table_content}")
    
    combined_content = "\n".join(content_parts)
    
    # Use Bedrock to classify the document
    session_kwargs = {"region_name": region}
    if profile:
        session_kwargs["profile_name"] = profile
    
    session = boto3.Session(**session_kwargs)
    bedrock = session.client("bedrock-runtime")
    
    classification_prompt = """Analyze the following document content and classify it into one of these categories:
- license: Driver's license, driving permit, or similar identification with driving privileges
- receipt: Purchase receipt, invoice, bill, or transaction record from retail stores
- bank-receipt: Bank transaction receipt, ATM receipt, or bank statement
- idcard: Identity card, national ID, employee ID, or general identification document
- passport: Passport or travel document

- For confidence scores, use the following scale:
    - 0.0 to 0.4: Low confidence
    - 0.4 to 0.7: Medium confidence
    - 0.7 to 1.0: High confidence

Return your response as JSON with this exact format:
{
  "category": "one of: license, receipt, bank-receipt, idcard, passport",
  "confidence": {
    "level": "one of: low, medium, high",
    "score": "floating point number between 0.0 and 1.0"
  },
  "reasoning": "brief explanation of why this category was chosen"
}

Document content to analyze:"""

    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 200,
        "temperature": 0,
        "messages": [
            {
                "role": "user",
                "content": f"{classification_prompt}\n\n{combined_content}"
            }
        ]
    }

    try:
        resp = bedrock.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0", 
            body=json.dumps(payload)
        )
        result = json.loads(resp["body"].read())
        raw_text = result["content"][0]["text"]
        
        # Extract JSON from response
        json_start = raw_text.find('{')
        json_end = raw_text.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            classification = json.loads(raw_text[json_start:json_end])
            category = classification.get('category', 'license')
            # Handle both old and new confidence formats
            if isinstance(classification.get('confidence'), dict):
                confidence_score = classification['confidence'].get('score', 0.5)
            else:
                confidence_score = classification.get('confidence', 0.5)
            
            reasoning = classification.get('reasoning', 'Auto-detected')
            
            log_print(f"[INFO] Auto-detected category: {category} (confidence: {confidence_score:.2f})")
            log_print(f"[INFO] Reasoning: {reasoning}")
            
            return category, confidence_score
        
    except Exception as e:
        log_print(f"[WARN] Category detection failed: {e}")
    
    # Fallback to license if detection fails
    log_print("[INFO] Using fallback category: license")
    return "license", 0.5
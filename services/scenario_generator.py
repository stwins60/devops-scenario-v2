import random
import uuid
import json
import os
import logging
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LANGUAGES = ["Python", "Node.js", "Java", "Go"]
ISSUE_TYPES = ["CI deployment failure", "Docker issue", "Kubernetes misconfig", "Database connection logic"]
DIFFICULTIES = ["Easy", "Medium", "Hard"]

# Initialize Bedrock client. Boto3 explicitly uses AWS credentials from .env
try:
    bedrock_client = boto3.client(
        'bedrock-runtime', 
        region_name=os.getenv('AWS_REGION', 'us-east-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
except Exception as e:
    logger.error(f"Failed to initialize AWS Bedrock client: {e}")
    bedrock_client = None

def generate_scenario_data():
    lang = random.choice(LANGUAGES)
    issue = random.choice(ISSUE_TYPES)
    diff = random.choice(DIFFICULTIES)
    
    return generate_specific_scenario(lang, issue, diff)

def generate_specific_scenario(lang, issue, diff):
    use_mock = os.getenv("USE_MOCK_GENERATOR", "false").lower() == "true"
    
    if bedrock_client and not use_mock:
        try:
            return generate_from_bedrock(lang, issue, diff)
        except Exception as e:
            logger.error(f"Bedrock generation failed: {e}. Falling back to mock data.")
            return generate_mock_scenario(lang, issue, diff)
    else:
        return generate_mock_scenario(lang, issue, diff)

def generate_from_bedrock(lang, issue, diff):
    prompt = f"""
You are an expert DevOps engineer and instructor. Create a training scenario for a student.
Generate a scenario where a {lang} application has a {issue} issue. The difficulty should be {diff}.

Return your response strictly as a JSON object with the following keys:
- "title": A short, catchy title (e.g., "{lang} - {issue}")
- "description": A paragraph describing the problem context for the student.
- "code_snippet": The broken application code, Dockerfile, or configuration file as a string. Include comments indicating where the bug MIGHT be, or leave subtle clues.
- "tags": A list of up to 3 relevant strings.

Ensure the code has an actual bug, missing config, or logic error that the user needs to fix.
Return ONLY the raw JSON object. Do not include markdown formatting like ```json.
Ensure all newlines within the code_snippet are properly escaped as \\n.
"""

    model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
    
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "temperature": 0.7,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    response = bedrock_client.invoke_model(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(payload)
    )
    
    response_body = json.loads(response.get('body').read())
    content = response_body.get('content', [])[0].get('text', '')
    
    # Safely parse JSON in case the model wraps it in markdown
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.endswith("```"):
        content = content[:-3]
        
    generated_data = json.loads(content.strip(), strict=False)
    
    return {
        "id": str(uuid.uuid4())[:8],
        "title": generated_data.get("title", f"{lang} - {issue}"),
        "language": lang,
        "difficulty": diff,
        "issue_type": issue,
        "description": generated_data.get("description", "A DevOps issue occurred. Please fix it."),
        "code_snippet": generated_data.get("code_snippet", "// Error generating code"),
        "tags": generated_data.get("tags", [lang.lower(), "devops"])
    }

def generate_mock_scenario(lang, issue, diff):
    description = f"You are tasked with fixing a {issue.lower()} in a {lang} application. The application recently started failing in the production environment."
    return {
        "id": str(uuid.uuid4())[:8],
        "title": f"[MOCK] {lang} - {issue}",
        "language": lang,
        "difficulty": diff,
        "issue_type": issue,
        "description": description,
        "code_snippet": f"// Mock Code block for {lang}\n// {issue} issue present.\n// Please connect AWS to see true AI generated configurations.",
        "tags": [lang.lower(), issue.split()[0].lower(), "devops"]
    }

import os
import json
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

def analyze_regulatory_change(old_text: str, new_text: str) -> dict:
    endpoint = os.getenv("FOUNDRY_MODEL_ENDPOINT")
    key = os.getenv("FOUNDRY_MODEL_KEY")
    deployment = os.getenv("FOUNDRY_MODEL_DEPLOYMENT")

    if not endpoint:
        raise ValueError("FOUNDRY_MODEL_ENDPOINT missing")
    if not key:
        raise ValueError("FOUNDRY_MODEL_KEY missing")
    if not deployment:
        raise ValueError("FOUNDRY_MODEL_DEPLOYMENT missing")

    # ✅ Azure OpenAI client
    client = AzureOpenAI(
        api_key=key,
        azure_endpoint=endpoint,
        api_version="2024-05-01-preview"
    )

    prompt = f"""
Compare OLD and NEW regulation.

Return ONLY valid JSON with:
what_changed, business_impact, risk_level, affected_teams,
recommended_actions, confidence_score.

OLD:
{old_text}

NEW:
{new_text}
"""

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "Return only valid JSON. No markdown."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=1000,
        response_format={"type": "json_object"}  # 🔥 important
    )

    content = response.choices[0].message.content

    return json.loads(content)
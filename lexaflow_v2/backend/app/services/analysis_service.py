import json
import re
from difflib import SequenceMatcher

from openai import AzureOpenAI

from backend.app.core.config import settings
from backend.app.schemas import ActionRecommendation, AnalysisResult


def _azure_enabled() -> bool:
    return all(
        [
            settings.azure_openai_endpoint,
            settings.azure_openai_key,
            settings.azure_openai_deployment,
        ]
    )


def _coerce_action(item: object) -> ActionRecommendation:
    if isinstance(item, dict):
        action = str(item.get("action", "")).strip()
        if not action:
            action = "Review regulation delta and document required controls."
        return ActionRecommendation(
            action=action,
            owner=str(item.get("owner", "Compliance Team")),
            priority=str(item.get("priority", "Medium")).title(),
            due_days=int(item.get("due_days", 7)),
        )

    return ActionRecommendation(
        action=str(item) or "Review regulation delta and document required controls.",
        owner="Compliance Team",
        priority="Medium",
        due_days=7,
    )


def _normalize_analysis(payload: dict) -> AnalysisResult:
    actions_raw = payload.get("recommended_actions", [])
    if not isinstance(actions_raw, list):
        actions_raw = [actions_raw]

    normalized = {
        "what_changed": payload.get("what_changed", {}),
        "business_impact": payload.get("business_impact", {}),
        "risk_level": str(payload.get("risk_level", "medium")).lower(),
        "affected_teams": payload.get("affected_teams", []),
        "recommended_actions": [_coerce_action(item) for item in actions_raw],
        "confidence_score": float(payload.get("confidence_score", 0.8)),
    }

    if not isinstance(normalized["affected_teams"], list):
        normalized["affected_teams"] = [str(normalized["affected_teams"])]

    return AnalysisResult.model_validate(normalized)


def _extract_sentence_deltas(old_text: str, new_text: str) -> tuple[list[str], list[str]]:
    split_pattern = re.compile(r"[.\n]+")
    old_sentences = [item.strip() for item in split_pattern.split(old_text) if item.strip()]
    new_sentences = [item.strip() for item in split_pattern.split(new_text) if item.strip()]

    old_set = set(old_sentences)
    new_set = set(new_sentences)

    added = [sentence for sentence in new_sentences if sentence not in old_set][:5]
    removed = [sentence for sentence in old_sentences if sentence not in new_set][:5]
    return added, removed


def _extract_review_frequency_change(old_text: str, new_text: str) -> dict | None:
    pattern = re.compile(r"\b\d+\s*(?:year|years|month|months)\b", re.IGNORECASE)
    old_match = pattern.search(old_text)
    new_match = pattern.search(new_text)
    if not old_match or not new_match:
        return None

    if old_match.group(0).lower() == new_match.group(0).lower():
        return None

    return {"old": old_match.group(0), "new": new_match.group(0)}


def _fallback_analysis(old_text: str, new_text: str) -> AnalysisResult:
    similarity = SequenceMatcher(a=old_text, b=new_text).ratio()
    change_ratio = round((1.0 - similarity) * 100, 2)

    added, removed = _extract_sentence_deltas(old_text, new_text)
    frequency_change = _extract_review_frequency_change(old_text, new_text)

    what_changed: dict[str, object] = {
        "change_ratio_percent": change_ratio,
        "added_requirements": added,
        "removed_or_modified_requirements": removed,
    }
    if frequency_change:
        what_changed["review_frequency"] = frequency_change

    risk_level = "medium"
    if frequency_change or "must" in new_text.lower() or "required" in new_text.lower():
        risk_level = "high"
    elif change_ratio < 3:
        risk_level = "low"

    business_impact = {
        "operations": "Process updates are required to align SOPs with the latest regulation text.",
        "compliance": "Control evidence and review cadence should be revalidated.",
        "technology": "Systems may need updates if new audit or logging requirements were introduced.",
    }

    recommendations = [
        ActionRecommendation(
            action="Review and update KYC policy documentation for the latest regulatory wording.",
            owner="Compliance Team",
            priority="High" if risk_level == "high" else "Medium",
            due_days=7,
        ),
        ActionRecommendation(
            action="Validate monitoring controls and implement any missing audit evidence steps.",
            owner="Risk Management Team",
            priority="Medium",
            due_days=10,
        ),
    ]

    if frequency_change:
        recommendations.insert(
            0,
            ActionRecommendation(
                action=f"Update review cadence from {frequency_change['old']} to {frequency_change['new']} in operational workflows.",
                owner="Operations Team",
                priority="High",
                due_days=5,
            ),
        )

    return AnalysisResult(
        what_changed=what_changed,
        business_impact=business_impact,
        risk_level=risk_level,
        affected_teams=["Compliance", "Risk Management", "Operations", "IT"],
        recommended_actions=recommendations,
        confidence_score=0.72,
    )


def _azure_analysis(old_text: str, new_text: str) -> AnalysisResult:
    client = AzureOpenAI(
        api_key=settings.azure_openai_key,
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
    )

    prompt = f"""
Compare OLD and NEW regulation text.

Return only valid JSON with keys:
what_changed, business_impact, risk_level, affected_teams, recommended_actions, confidence_score.

recommended_actions must be a list of objects with keys:
action, owner, priority, due_days.

OLD:
{old_text}

NEW:
{new_text}
"""

    response = client.chat.completions.create(
        model=settings.azure_openai_deployment,
        messages=[
            {"role": "system", "content": "You are a compliance analyst. Return JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=1200,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content or "{}"
    payload = json.loads(content)
    return _normalize_analysis(payload)


def analyze_regulatory_change(old_text: str, new_text: str) -> AnalysisResult:
    if _azure_enabled():
        try:
            return _azure_analysis(old_text, new_text)
        except Exception:
            return _fallback_analysis(old_text, new_text)
    return _fallback_analysis(old_text, new_text)



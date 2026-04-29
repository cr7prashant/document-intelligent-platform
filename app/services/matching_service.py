import json
import logging
from abc import ABC, abstractmethod
import httpx
from app.config import settings
from app.models.envelope import Envelope, MatchResult, Decision
from app.models.matching import CatalogItem
from app.services.audit_service import append_audit

log = logging.getLogger(__name__)

CATALOG = [
    CatalogItem(hs_code="8471.30.0100", description="portable digital automatic data processing machine under 10kg", category="electronics", restricted=False, typical_weight_kg=2.5),
    CatalogItem(hs_code="8517.62.0050", description="telephone sets, including smartphones", category="electronics", restricted=False, typical_weight_kg=0.3),
    CatalogItem(hs_code="9403.60.8081", description="wooden furniture for dining rooms", category="furniture", restricted=False, typical_weight_kg=15.0),
    CatalogItem(hs_code="3004.90.9290", description="medicaments for therapeutic use", category="pharmaceuticals", restricted=True, typical_weight_kg=0.5),
    CatalogItem(hs_code="8703.23.0190", description="passenger motor vehicle with spark-ignition engine", category="automotive", restricted=False, typical_weight_kg=1400.0),
    CatalogItem(hs_code="0805.10.0020", description="oranges, fresh", category="produce", restricted=False, typical_weight_kg=0.2),
    CatalogItem(hs_code="6110.30.3053", description="sweaters of man-made fibers", category="apparel", restricted=False, typical_weight_kg=0.4),
    CatalogItem(hs_code="8471.50.0150", description="desktop computer processing unit", category="electronics", restricted=False, typical_weight_kg=8.0),
]


class LLMClient(ABC):
    @abstractmethod
    async def match_commodity(self, description: str, catalog: list[CatalogItem]) -> dict:
        pass


class GroqClient(LLMClient):
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self.timeout = settings.LLM_TIMEOUT

    async def match_commodity(self, description, catalog):
        catalog_json = [item.model_dump() for item in catalog]
        prompt = f"""You are a commodity classification assistant.
Given the product description: "{description}"
And this reference catalog:
{json.dumps(catalog_json, indent=2)}

Return ONLY a JSON object with these fields:
- "matched_code": best matching HS code from catalog, or "" if none
- "confidence": float 0.0-1.0
- "rationale": short explanation
No other text."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "response_format": {"type": "json_object"}
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers, json=body
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]
            parsed = json.loads(raw)
            return {
                "matched_code": parsed.get("matched_code", ""),
                "confidence": float(parsed.get("confidence", 0.0)),
                "rationale": parsed.get("rationale", "")
            }


class MockLLMClient(LLMClient):

    async def match_commodity(self, description, catalog):
        desc = description.lower()
        for item in catalog:
            if any(w in desc for w in item.description.lower().split()):
                return {
                    "matched_code": item.hs_code,
                    "confidence": 0.85,
                    "rationale": f"keyword match: '{item.description}'"
                }
        return {"matched_code": "", "confidence": 0.2, "rationale": "no match in catalog"}


def get_client():
    # return MockLLMClient() here to skip real API calls
    return GroqClient()


async def run_matching(envelope, llm_client):
    threshold = envelope.processing_instructions.confidence_threshold
    code = envelope.extraction.get("commodity_code")
    desc = envelope.extraction.get("commodity_desc")

    if code and code.confidence >= threshold:
        envelope.matching_results = MatchResult(
            source="catalog_exact", fallback_used=False,
            rationale="code confidence is fine, skipping LLM",
            match_confidence=1.0
        )
        append_audit(envelope, "matching", "match", "skipped", {"reason": "above_threshold"})
        return envelope

    if not desc or not desc.value:
        envelope.matching_results = MatchResult(
            source="no_match", fallback_used=False,
            rationale="no description to fall back on", match_confidence=0.0
        )
        _force_hitl(envelope)
        append_audit(envelope, "matching", "match", "failed", {"reason": "no_description"})
        return envelope

    try:
        result = await llm_client.match_commodity(desc.value, CATALOG)
        match = MatchResult(
            matched_code=result.get("matched_code", ""),
            match_confidence=result.get("confidence", 0.0),
            rationale=result.get("rationale", ""),
            fallback_used=True, source="llm_match"
        )
        append_audit(envelope, "matching", "match", "success", {"llm_result": result})
    except Exception as e:
        log.error("llm failed: %s", e)
        match = MatchResult(
            source="no_match", fallback_used=False,
            rationale=f"LLM error: {e}", match_confidence=0.0
        )
        _force_hitl(envelope)
        append_audit(envelope, "matching", "match", "error", {"error": str(e)})

    envelope.matching_results = match

    if match.match_confidence < 0.70:
        _force_hitl(envelope)
        append_audit(envelope, "matching", "confidence_override", "info",
                     {"confidence": match.match_confidence})

    return envelope


def _force_hitl(envelope):
    if envelope.decision is None:
        envelope.decision = Decision(route="hitl_review")
    else:
        envelope.decision.route = "hitl_review"
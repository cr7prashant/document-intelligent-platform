from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ExtractedField(BaseModel):
    value: str
    confidence: float


class ProcessingInstructions(BaseModel):
    workflow: str
    confidence_threshold: float
    hitl_on_failure: bool


class ValidationResult(BaseModel):
    passed: bool
    failed_fields: list[dict[str, str]] = []


class MatchResult(BaseModel):
    matched_code: str | None = None
    match_confidence: float = 0.0
    rationale: str = ""
    fallback_used: bool
    source: Literal["catalog_exact", "llm_match", "no_match"]


class Decision(BaseModel):
    route: Literal["auto_approve", "hitl_review", "rejected"] = "hitl_review"


class AuditEntry(BaseModel):
    timestamp: datetime
    service: str
    action: str
    envelope_id: str
    result: str
    details: dict = {}


class Envelope(BaseModel):
    envelope_id: str
    schema_version: str
    tenant: dict[str, str]
    document: dict
    extraction: dict[str, ExtractedField]
    processing_instructions: ProcessingInstructions
    validation_results: ValidationResult | None = None
    matching_results: MatchResult | None = None
    decision: Decision | None = None
    audit: list[AuditEntry] = []
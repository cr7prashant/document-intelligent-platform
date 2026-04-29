import logging

from fastapi import APIRouter, Depends, HTTPException

from app.models.envelope import Envelope, MatchResult
from app.services.validation_service import check_schema, validate
from app.services.matching_service import LLMClient, run_matching
from app.services.audit_service import append_audit
from app.api.dependencies import get_client_dep

router = APIRouter()
log = logging.getLogger(__name__)


@router.post("/process", response_model=Envelope)
async def process_endpoint(envelope: Envelope, llm: LLMClient = Depends(get_client_dep)):
    log.info("[%s] starting pipeline", envelope.envelope_id)

    errors = check_schema(envelope)
    if errors:
        raise HTTPException(422, detail={"errors": errors})

    # step 1: validate
    decision, vr = validate(envelope)
    envelope.decision = decision
    envelope.validation_results = vr
    append_audit(envelope, "validation", "validate",
                 "pass" if vr.passed else "fail",
                 {"failed_fields": vr.failed_fields, "route": decision.route})

    # step 2: match (only when commodity code confidence is low)
    threshold = envelope.processing_instructions.confidence_threshold
    code = envelope.extraction.get("commodity_code")

    if code and code.confidence < threshold:
        log.info("[%s] low commodity confidence, matching", envelope.envelope_id)
        envelope = await run_matching(envelope, llm)
    else:
        envelope.matching_results = MatchResult(
            source="catalog_exact", fallback_used=False,
            rationale="code confidence sufficient", match_confidence=1.0
        )
        append_audit(envelope, "matching", "match", "skipped", {"reason": "not_needed"})

    log.info("[%s] done, route=%s", envelope.envelope_id, envelope.decision.route)
    return envelope
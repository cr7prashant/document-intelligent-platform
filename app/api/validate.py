import logging

from fastapi import APIRouter, HTTPException

from app.models.envelope import Envelope
from app.services.validation_service import check_schema, validate
from app.services.audit_service import append_audit

router = APIRouter()
log = logging.getLogger(__name__)


@router.post("/validate", response_model=Envelope)
async def validate_endpoint(envelope: Envelope):
    log.info("[%s] validating", envelope.envelope_id)

    errors = check_schema(envelope)
    if errors:
        raise HTTPException(422, detail={"errors": errors})

    decision, result = validate(envelope)
    envelope.decision = decision
    envelope.validation_results = result

    append_audit(envelope, "validation", "validate",
                 "pass" if result.passed else "fail",
                 {"failed_fields": result.failed_fields, "route": decision.route})

    log.info("[%s] route=%s", envelope.envelope_id, decision.route)
    return envelope
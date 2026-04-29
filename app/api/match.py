import logging

from fastapi import APIRouter, Depends

from app.models.envelope import Envelope
from app.services.matching_service import LLMClient, run_matching
from app.api.dependencies import get_client_dep

router = APIRouter()
log = logging.getLogger(__name__)


@router.post("/match", response_model=Envelope)
async def match_endpoint(envelope: Envelope, llm: LLMClient = Depends(get_client_dep)):
    log.info("[%s] running commodity match", envelope.envelope_id)
    envelope = await run_matching(envelope, llm)
    return envelope
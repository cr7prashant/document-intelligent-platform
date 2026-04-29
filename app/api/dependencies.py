from app.services.matching_service import get_client, LLMClient


def get_client_dep() -> LLMClient:
    return get_client()
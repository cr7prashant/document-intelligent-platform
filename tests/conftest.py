import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.matching_service import MockLLMClient
from app.api.dependencies import get_client_dep


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_llm():
    return MockLLMClient()


@pytest.fixture(autouse=True)
def _override_llm(mock_llm):
    app.dependency_overrides[get_client_dep] = lambda: mock_llm
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def envelope():
    return {
        "envelope_id": "test_001",
        "schema_version": "envelope-v1",
        "tenant": {"id": "test", "name": "Test Co"},
        "document": {"type": "shipping_manifest", "filename": "test.pdf", "page_count": 1},
        "extraction": {
            "shipment_id": {"value": "SHP123", "confidence": 0.95},
            "recipient_name": {"value": "Acme Corp", "confidence": 0.90},
            "commodity_code": {"value": "8471.30.0100", "confidence": 0.94},
            "commodity_desc": {"value": "laptop computer", "confidence": 0.96},
            "ship_date": {"value": "2026-04-01", "confidence": 0.99}
        },
        "processing_instructions": {
            "workflow": "manifest-v1",
            "confidence_threshold": 0.80,
            "hitl_on_failure": True
        },
        "validation_results": None,
        "matching_results": None,
        "decision": None,
        "audit": []
    }
def test_happy_path(client, envelope):
    resp = client.post("/process", json=envelope)
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"]["route"] == "auto_approve"
    assert data["matching_results"]["source"] == "catalog_exact"
    assert len(data["audit"]) >= 2


def test_low_confidence_recipient(client, envelope):
    envelope["extraction"]["recipient_name"]["confidence"] = 0.70
    resp = client.post("/process", json=envelope)
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"]["route"] == "hitl_review"
    assert not data["validation_results"]["passed"]


def test_low_commodity_triggers_llm(client, envelope):
    envelope["extraction"]["commodity_code"]["confidence"] = 0.60
    resp = client.post("/process", json=envelope)
    assert resp.status_code == 200
    data = resp.json()
    assert data["matching_results"]["source"] == "llm_match"
    assert data["matching_results"]["matched_code"]


def test_bad_envelope_422(client):
    bad = {
        "envelope_id": "bad",
        "extraction": {},
        "processing_instructions": {"confidence_threshold": 0.8, "hitl_on_failure": True}
    }
    assert client.post("/process", json=bad).status_code == 422


def test_llm_failure_graceful(client, envelope, monkeypatch):
    async def boom(*a, **kw):
        raise Exception("LLM timeout")

    from app.services.matching_service import MockLLMClient
    monkeypatch.setattr(MockLLMClient, "match_commodity", boom)

    envelope["extraction"]["commodity_code"]["confidence"] = 0.60
    resp = client.post("/process", json=envelope)
    assert resp.status_code == 200
    data = resp.json()
    assert data["matching_results"]["source"] == "no_match"
    assert data["decision"]["route"] == "hitl_review"
    assert any(e["details"].get("error") for e in data["audit"] if e["service"] == "matching")


def test_missing_extraction_fields_422(client, envelope):
    del envelope["extraction"]["shipment_id"]
    del envelope["extraction"]["recipient_name"]
    resp = client.post("/process", json=envelope)
    assert resp.status_code == 422
    assert "errors" in resp.json()["detail"]
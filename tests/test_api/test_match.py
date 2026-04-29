def test_low_confidence_triggers_llm(client, envelope):
    envelope["extraction"]["commodity_code"]["confidence"] = 0.60
    resp = client.post("/match", json=envelope)
    assert resp.status_code == 200
    data = resp.json()
    assert data["matching_results"]["source"] == "llm_match"
    assert data["matching_results"]["fallback_used"] is True
    assert data["matching_results"]["matched_code"]


def test_high_confidence_skips_llm(client, envelope):
    resp = client.post("/match", json=envelope)
    assert resp.status_code == 200
    assert resp.json()["matching_results"]["source"] == "catalog_exact"


def test_llm_failure(client, envelope, monkeypatch):
    async def boom(*a, **kw):
        raise Exception("timeout")

    from app.services.matching_service import MockLLMClient
    monkeypatch.setattr(MockLLMClient, "match_commodity", boom)

    envelope["extraction"]["commodity_code"]["confidence"] = 0.60
    resp = client.post("/match", json=envelope)
    assert resp.status_code == 200
    data = resp.json()
    assert data["matching_results"]["source"] == "no_match"
    assert data["decision"]["route"] == "hitl_review"
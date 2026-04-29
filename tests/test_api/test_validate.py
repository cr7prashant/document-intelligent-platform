def test_valid_envelope(client, envelope):
    resp = client.post("/validate", json=envelope)
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"]["route"] == "auto_approve"
    assert data["validation_results"]["passed"] is True
    assert len(data["audit"]) >= 1


def test_low_confidence(client, envelope):
    envelope["extraction"]["recipient_name"]["confidence"] = 0.70
    resp = client.post("/validate", json=envelope)
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"]["route"] == "hitl_review"
    assert not data["validation_results"]["passed"]
    assert any(f["field"] == "recipient_name" for f in data["validation_results"]["failed_fields"])


def test_future_date(client, envelope):
    envelope["extraction"]["ship_date"]["value"] = "2099-01-01"
    resp = client.post("/validate", json=envelope)
    data = resp.json()
    assert data["decision"]["route"] == "hitl_review"
    assert any(f["field"] == "ship_date" for f in data["validation_results"]["failed_fields"])


def test_old_date(client, envelope):
    envelope["extraction"]["ship_date"]["value"] = "2020-01-01"
    resp = client.post("/validate", json=envelope)
    data = resp.json()
    assert data["decision"]["route"] == "hitl_review"
    assert any("old" in f["reason"] for f in data["validation_results"]["failed_fields"])


def test_rejected_when_no_hitl(client, envelope):
    envelope["processing_instructions"]["hitl_on_failure"] = False
    envelope["extraction"]["recipient_name"]["confidence"] = 0.50
    resp = client.post("/validate", json=envelope)
    assert resp.json()["decision"]["route"] == "rejected"


def test_missing_fields_422(client, envelope):
    del envelope["extraction"]["shipment_id"]
    del envelope["extraction"]["recipient_name"]
    resp = client.post("/validate", json=envelope)
    assert resp.status_code == 422
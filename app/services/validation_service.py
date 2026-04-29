from datetime import date, datetime

from app.models.envelope import Envelope, ValidationResult, Decision


def check_schema(envelope):
    errors = []
    ext = envelope.extraction

    if "shipment_id" not in ext or not ext["shipment_id"].value:
        errors.append({"field": "shipment_id", "reason": "missing or empty"})
    if "recipient_name" not in ext or not ext["recipient_name"].value:
        errors.append({"field": "recipient_name", "reason": "missing or empty"})

    has_code = "commodity_code" in ext and ext["commodity_code"].value
    has_desc = "commodity_desc" in ext and ext["commodity_desc"].value
    if not has_code and not has_desc:
        errors.append({"field": "commodity_code/commodity_desc", "reason": "need at least one"})

    return errors


def validate(envelope):
    failed = []
    threshold = envelope.processing_instructions.confidence_threshold
    ext = envelope.extraction

    for name, field in ext.items():
        if field.confidence < threshold:
            failed.append({"field": name, "reason": f"confidence {field.confidence} below {threshold}"})

    if "ship_date" in ext:
        try:
            d = datetime.strptime(ext["ship_date"].value, "%Y-%m-%d").date()
            today = date.today()
            if d > today:
                failed.append({"field": "ship_date", "reason": "date is in the future"})
            elif (today - d).days > 365:
                failed.append({"field": "ship_date", "reason": f"too old ({(today - d).days} days)"})
        except ValueError:
            failed.append({"field": "ship_date", "reason": "bad date format"})

    if not failed:
        route = "auto_approve"
    elif envelope.processing_instructions.hitl_on_failure:
        route = "hitl_review"
    else:
        route = "rejected"

    return Decision(route=route), ValidationResult(passed=not failed, failed_fields=failed)
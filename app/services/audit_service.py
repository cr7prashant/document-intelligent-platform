from datetime import datetime, UTC

from app.models.envelope import AuditEntry


def append_audit(envelope, service: str, action: str, result: str, details: dict = None):
    # just stick an audit log on the envelope
    envelope.audit.append(AuditEntry(
        timestamp=datetime.now(UTC),
        service=service,
        action=action,
        envelope_id=envelope.envelope_id,
        result=result,
        details=details or {}
    ))
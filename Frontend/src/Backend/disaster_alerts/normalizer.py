import hashlib

from .models import DisasterAlert


def create_alert_id(
    source: str,
    alert_type: str,
    state: str,
    district: str,
    issued_at: str,
    description: str,
) -> str:
    """
    Create a stable unique ID for an alert.

    The same alert received again from the same source
    will produce the same ID.
    """

    raw = "|".join(
        [
            source or "",
            alert_type or "",
            state or "",
            district or "",
            issued_at or "",
            description or "",
        ]
    )

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


def normalize_alert(
    *,
    source: str,
    authority: str,
    alert_type: str,
    severity: str,
    state: str = None,
    district: str = None,
    affected_area: str = None,
    issued_at: str = None,
    expires_at: str = None,
    description: str = "",
    status: str = "Active",
    source_url: str = None,
) -> DisasterAlert:
    """
    Convert source-specific alert information
    into the common VayuNetra DisasterAlert format.
    """

    alert_id = create_alert_id(
        source=source,
        alert_type=alert_type,
        state=state,
        district=district,
        issued_at=issued_at,
        description=description,
    )

    return DisasterAlert(
        id=alert_id,
        source=source,
        authority=authority,
        alert_type=alert_type,
        severity=severity,
        state=state,
        district=district,
        affected_area=affected_area,
        issued_at=issued_at,
        expires_at=expires_at,
        description=description,
        status=status,
        source_url=source_url,
    )
import hashlib

from models import DisasterAlert


def create_alert_id(
    source,
    alert_type,
    state,
    district,
    issued_at,
    headline,
):
    """
    Create a stable internal ID for an alert.
    """

    raw = "|".join([
        source or "",
        alert_type or "",
        state or "",
        district or "",
        issued_at or "",
        headline or "",
    ])

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


def normalize_alert(
    *,
    source,
    authority,
    alert_type,
    category=None,
    severity=None,
    urgency=None,
    certainty=None,
    state=None,
    district=None,
    affected_area=None,
    issued_at=None,
    effective_at=None,
    onset_at=None,
    expires_at=None,
    headline=None,
    instruction=None,
    status=None,
    message_type=None,
    source_url=None,
    polygon_url=None,
):
    """
    Convert source-specific alert information
    into the common DisasterAlert structure.
    """

    alert_id = create_alert_id(
        source,
        alert_type,
        state,
        district,
        issued_at,
        headline,
    )

    return DisasterAlert(
        id=alert_id,
        source=source,
        authority=authority,
        alert_type=alert_type,

        category=category,
        severity=severity,
        urgency=urgency,
        certainty=certainty,

        state=state,
        district=district,
        affected_area=affected_area,

        issued_at=issued_at,
        effective_at=effective_at,
        onset_at=onset_at,
        expires_at=expires_at,

        headline=headline,
        instruction=instruction,

        status=status,
        message_type=message_type,

        source_url=source_url,
        polygon_url=polygon_url,
    )
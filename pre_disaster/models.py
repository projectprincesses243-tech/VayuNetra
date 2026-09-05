from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class DisasterAlert:
    id: str
    source: str
    authority: str
    alert_type: str

    category: Optional[str] = None
    severity: Optional[str] = None
    urgency: Optional[str] = None
    certainty: Optional[str] = None

    state: Optional[str] = None
    district: Optional[str] = None
    affected_area: Optional[str] = None

    issued_at: Optional[str] = None
    effective_at: Optional[str] = None
    onset_at: Optional[str] = None
    expires_at: Optional[str] = None

    headline: Optional[str] = None
    instruction: Optional[str] = None

    status: Optional[str] = None
    message_type: Optional[str] = None

    source_url: Optional[str] = None
    polygon_url: Optional[str] = None

    def to_dict(self):
        return asdict(self)
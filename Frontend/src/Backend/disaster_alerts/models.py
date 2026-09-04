from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class DisasterAlert:

    # ---------------------------------------------
    # INTERNAL IDENTIFICATION
    # ---------------------------------------------

    id: str


    # ---------------------------------------------
    # GOVERNMENT SOURCE
    # ---------------------------------------------

    source: str
    authority: str


    # ---------------------------------------------
    # ALERT / ISSUE
    # ---------------------------------------------

    alert_type: str

    category: Optional[str] = None
    severity: Optional[str] = None
    urgency: Optional[str] = None
    certainty: Optional[str] = None


    # ---------------------------------------------
    # LOCATION
    # ---------------------------------------------

    state: Optional[str] = None
    district: Optional[str] = None
    affected_area: Optional[str] = None


    # ---------------------------------------------
    # TIME
    # ---------------------------------------------

    issued_at: Optional[str] = None
    effective_at: Optional[str] = None
    onset_at: Optional[str] = None
    expires_at: Optional[str] = None


    # ---------------------------------------------
    # GOVERNMENT MESSAGE
    # ---------------------------------------------

    headline: Optional[str] = None
    description: Optional[str] = None
    instruction: Optional[str] = None


    # ---------------------------------------------
    # ALERT STATUS
    # ---------------------------------------------

    status: Optional[str] = None
    message_type: Optional[str] = None


    # ---------------------------------------------
    # OFFICIAL SOURCE
    # ---------------------------------------------

    source_url: Optional[str] = None
    polygon_url: Optional[str] = None


    # ---------------------------------------------
    # CONVERT TO DICTIONARY
    # ---------------------------------------------

    def to_dict(self):
        return asdict(self)
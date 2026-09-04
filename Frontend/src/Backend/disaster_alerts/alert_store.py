from typing import Dict, List
from datetime import datetime, timezone

from .config import MAX_ALERTS
from .models import DisasterAlert


class AlertStore:

    def __init__(self):
        self.alerts: Dict[str, DisasterAlert] = {}

    def add(self, alert: DisasterAlert):
        self.alerts[alert.id] = alert

        if len(self.alerts) > MAX_ALERTS:
            oldest_id = next(iter(self.alerts))
            del self.alerts[oldest_id]

    def add_many(self, alerts: List[DisasterAlert]):
        for alert in alerts:
            self.add(alert)

    def get_all(self) -> List[DisasterAlert]:
        return list(self.alerts.values())

    def get_active(self) -> List[DisasterAlert]:

        active_alerts = []

        for alert in self.alerts.values():

            # CAP "Actual" means this is a real official alert.
            # "Active" is also accepted for sources that use that status.
            if alert.status:
                status = alert.status.strip().lower()

                if status not in ["actual", "active"]:
                    continue

            # If the government provides an expiry time,
            # do not show the alert after it has expired.
            if alert.expires_at:

                try:
                    expiry = datetime.fromisoformat(
                        alert.expires_at
                    )

                    now = datetime.now(
                        timezone.utc
                    )

                    if expiry.tzinfo is None:
                        expiry = expiry.replace(
                            tzinfo=timezone.utc
                        )

                    if expiry <= now:
                        continue

                except ValueError:
                    # If the government timestamp cannot be parsed,
                    # keep the alert rather than silently deleting it.
                    pass

            active_alerts.append(alert)

        return active_alerts
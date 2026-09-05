from datetime import datetime, timezone


class AlertStore:
    def __init__(self):
        self.alerts = {}

    def add(self, alert):
        """
        Add or update an alert using its unique ID.
        """
        self.alerts[alert.id] = alert

    def add_many(self, alerts):
        """
        Add multiple alerts to the store.
        """
        for alert in alerts:
            self.add(alert)

    def get_all(self):
        """
        Return all stored alerts.
        """
        return list(self.alerts.values())

    def get_active(self):
        """
        Return alerts that are still active.

        CAP commonly uses 'Actual' for genuine alerts,
        so both 'Actual' and 'Active' are accepted here.
        Expired alerts are excluded when an expiry time
        is available.
        """

        active_alerts = []

        for alert in self.alerts.values():

            # Ignore non-real/test alerts when status is supplied.
            if alert.status:
                status = alert.status.strip().lower()

                if status not in ("actual", "active"):
                    continue

            # Remove expired alerts.
            if alert.expires_at:
                try:
                    expiry = datetime.fromisoformat(
                        alert.expires_at
                    )

                    if expiry.tzinfo is None:
                        expiry = expiry.replace(
                            tzinfo=timezone.utc
                        )

                    now = datetime.now(timezone.utc)

                    if expiry <= now:
                        continue

                except ValueError:
                    # If the date cannot be parsed,
                    # keep the alert rather than deleting
                    # potentially valid government data.
                    pass

            active_alerts.append(alert)

        return active_alerts
class AlertDeduplicator:
    def __init__(self):
        self.seen_ids = set()

    def is_new(self, alert):
        """
        Return True only if this alert
        has not been processed before.
        """

        if alert.id in self.seen_ids:
            return False

        self.seen_ids.add(alert.id)
        return True

    def filter_new(self, alerts):
        """
        Keep only alerts that have not
        been seen previously.
        """

        return [
            alert
            for alert in alerts
            if self.is_new(alert)
        ]
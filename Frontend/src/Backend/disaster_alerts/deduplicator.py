from typing import Iterable, List

from .models import DisasterAlert


class AlertDeduplicator:
    """
    Prevents the same alert from being processed repeatedly.
    """

    def __init__(self):
        self.seen_ids = set()

    def is_new(self, alert: DisasterAlert) -> bool:
        """
        Return True only if this alert has not been seen before.
        """

        if alert.id in self.seen_ids:
            return False

        self.seen_ids.add(alert.id)

        return True

    def filter_new(
        self,
        alerts: Iterable[DisasterAlert],
    ) -> List[DisasterAlert]:
        """
        Return only alerts that have not been processed before.
        """

        new_alerts = []

        for alert in alerts:
            if self.is_new(alert):
                new_alerts.append(alert)

        return new_alerts
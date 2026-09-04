import time

from .alert_store import AlertStore
from .config import ALERT_CHECK_INTERVAL_SECONDS
from .deduplicator import AlertDeduplicator

from .sources.sachet import fetch_sachet_alerts


class AlertScheduler:
    """
    Coordinates periodic checking of government
    disaster-alert sources.
    """

    def __init__(self):
        self.store = AlertStore()
        self.deduplicator = AlertDeduplicator()

        # Government sources will be added here
        # as their official machine-readable
        # endpoints are verified.
        self.sources = [
            ("SACHET", fetch_sachet_alerts),
        ]

    def check_sources(self):
        """
        Check every configured source once.
        """

        newly_detected = []

        for source_name, fetch_function in self.sources:

            try:
                alerts = fetch_function()

                new_alerts = (
                    self.deduplicator.filter_new(
                        alerts
                    )
                )

                self.store.add_many(
                    new_alerts
                )

                newly_detected.extend(
                    new_alerts
                )

                print(
                    f"[{source_name}] "
                    f"received={len(alerts)} "
                    f"new={len(new_alerts)}"
                )

            except Exception as error:

                print(
                    f"[{source_name}] "
                    f"failed: {error}"
                )

        return newly_detected

    def run_forever(self):
        """
        Continuously check configured sources.
        """

        while True:

            self.check_sources()

            time.sleep(
                ALERT_CHECK_INTERVAL_SECONDS
            )
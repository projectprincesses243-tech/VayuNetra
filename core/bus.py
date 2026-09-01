"""
The event bus. Modules announce things here instead of calling each other.
"""

from collections import defaultdict


class EventBus:
    def __init__(self):
        self._subscribers = defaultdict(list)
        self.log = []
        self.tick = 0

    def subscribe(self, event_name, callback):
        """Register a function to run whenever event_name is published."""
        self._subscribers[event_name].append(callback)

    def publish(self, event_name, payload=None):
        """Announce that something happened."""
        payload = payload or {}
        self.log.append({
            "tick":    self.tick,
            "event":   event_name,
            "payload": payload,
        })
        # list() so a callback can safely subscribe during iteration
        for callback in list(self._subscribers[event_name]):
            callback(payload)

    def recent(self, n=20):
        """Last n events - the dashboard event log reads this."""
        return self.log[-n:]

    def count(self, event_name):
        """How many times this event fired. Analytics uses this."""
        return sum(1 for e in self.log if e["event"] == event_name)

    def reset(self):
        """
        Wipe all state between experiment runs.

        Must clear subscribers too - a new Mission re-subscribes on creation,
        so without this each run would fire every previous run's handlers.
        Mutates in place rather than rebinding, so modules that already
        imported BUS keep pointing at the same live object.
        """
        self._subscribers.clear()
        self.log.clear()
        self.tick = 0


# One shared instance for the whole program.
# Every module does:  from core.bus import BUS
BUS = EventBus()
"""
VayuNetra Pre-Disaster Integration Bridge

Purpose:
Translate external government disaster alerts
into a Digital Twin compatible scenario.

This file isolates:
    External Alert System
                |
                |
          Digital Twin

No core simulation module is modified.
"""


from dataclasses import dataclass


@dataclass
class DisasterScenario:
    """
    Internal VayuNetra representation
    of an incoming disaster situation.
    """

    hazard: str
    severity: str
    priority: str
    affected_area: str


    def to_dict(self):

        return {
            "hazard": self.hazard,
            "severity": self.severity,
            "priority": self.priority,
            "affected_area": self.affected_area,
        }



class PreDisasterBridge:
    """
    Adapter between:
        Government Alert APIs
                |
                |
        VayuNetra Digital Twin
    """


    def __init__(self):

        self.current_scenario = None



    def update_from_alert(self, alert):

        """
        Convert external alert JSON
        into VayuNetra scenario.
        """

        severity = alert.get(
            "severity",
            "UNKNOWN"
        )


        if severity in [
            "Severe",
            "Extreme",
            "HIGH"
        ]:
            priority = "HIGH"

        elif severity in [
            "Moderate"
        ]:
            priority = "MEDIUM"

        else:
            priority = "LOW"



        self.current_scenario = DisasterScenario(

            hazard=alert.get(
                "alert_type",
                "UNKNOWN"
            ),

            severity=severity,

            priority=priority,

            affected_area=alert.get(
                "affected_area",
                "UNKNOWN"
            )

        )


        return self.current_scenario



    def get_scenario(self):

        return self.current_scenario
    
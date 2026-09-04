import os
import requests

from ..models import DisasterAlert


# Official IMD district warning API
IMD_DISTRICT_WARNING_URL = os.getenv(
    "IMD_DISTRICT_WARNING_URL",
    "https://api.imd.gov.in/api/v1/districtwarning",
)

# API key/token supplied through environment variables.
# Leave empty until you have valid IMD API credentials.
IMD_API_KEY = os.getenv(
    "IMD_API_KEY",
    "",
)


# IMD warning colour → VayuNetra severity
IMD_SEVERITY_MAP = {
    "1": "Red",
    "2": "Orange",
    "3": "Yellow",
    "4": "Green",
    "red": "Red",
    "orange": "Orange",
    "yellow": "Yellow",
    "green": "Green",
}


def _get_severity(value):
    """
    Convert an IMD warning colour/code into
    VayuNetra severity.
    """

    if value is None:
        return "Unknown"

    value = str(value).strip().lower()

    return IMD_SEVERITY_MAP.get(
        value,
        str(value).title(),
    )


def _get_warning_text(value):
    """
    Safely convert an IMD warning value into text.
    """

    if value is None:
        return ""

    if isinstance(value, list):
        return ", ".join(
            str(item)
            for item in value
            if item is not None
        )

    if isinstance(value, dict):
        return ", ".join(
            f"{key}: {val}"
            for key, val in value.items()
        )

    return str(value).strip()


def _parse_district_warning(item):
    """
    Convert one IMD district-warning record
    into a VayuNetra DisasterAlert.
    """

    if not isinstance(item, dict):
        return None

    district = (
        item.get("District")
        or item.get("district")
        or item.get("DISTRICT")
    )

    if not district:
        return None

    alerts = []

    # IMD provides warning information for multiple days.
    for day_number in range(1, 6):

        day_key = f"Day_{day_number}"
        color_key = f"Day{day_number}_Color"

        warning_text = _get_warning_text(
            item.get(day_key)
        )

        color = item.get(color_key)

        # Some responses may use slightly different
        # capitalization/naming.
        if color is None:
            color = item.get(
                f"Day_{day_number}_Color"
            )

        if not warning_text and color is None:
            continue

        severity = _get_severity(color)

        if not warning_text:
            warning_text = (
                f"IMD Day {day_number} "
                f"{severity} warning"
            )

        alert_id = (
            f"IMD-{district}-"
            f"DAY{day_number}-"
            f"{warning_text}"
        )

        alerts.append(
            DisasterAlert(
                id=alert_id,
                source="IMD",
                authority=(
                    "India Meteorological "
                    "Department"
                ),
                alert_type=(
                    f"Weather Warning - "
                    f"Day {day_number}"
                ),
                severity=severity,
                state=None,
                district=str(district),
                affected_area=str(district),
                issued_at=None,
                expires_at=None,
                description=warning_text,
                status="Active",
                source_url=(
                    "https://api.imd.gov.in/"
                ),
            )
        )

    return alerts


def fetch_imd_alerts():
    """
    Fetch district-wise warnings from the
    official IMD API.

    Returns:
        list[DisasterAlert]
    """

    headers = {
        "Accept": "application/json",
    }

    # Add authentication only when configured.
    if IMD_API_KEY:
        headers["Authorization"] = (
            f"Bearer {IMD_API_KEY}"
        )

    try:

        response = requests.get(
            IMD_DISTRICT_WARNING_URL,
            headers=headers,
            timeout=20,
        )

        # Authentication/access problem.
        if response.status_code in (
            401,
            403,
        ):
            print(
                "[IMD] API authentication "
                "or access is required."
            )

            return []

        response.raise_for_status()

        data = response.json()

        # IMD may return the records directly
        # or inside a common data/results field.
        if isinstance(data, list):

            records = data

        elif isinstance(data, dict):

            records = (
                data.get("data")
                or data.get("results")
                or data.get("Data")
                or []
            )

        else:

            records = []

        alerts = []

        for item in records:

            parsed_alerts = (
                _parse_district_warning(item)
            )

            if parsed_alerts:
                alerts.extend(
                    parsed_alerts
                )

        print(
            f"[IMD] Received "
            f"{len(alerts)} warning records."
        )

        return alerts

    except requests.RequestException as error:

        print(
            f"[IMD] Network/API error: "
            f"{error}"
        )

        return []

    except ValueError as error:

        print(
            f"[IMD] Invalid JSON response: "
            f"{error}"
        )

        return []

    except Exception as error:

        print(
            f"[IMD] Unexpected error: "
            f"{error}"
        )

        return []
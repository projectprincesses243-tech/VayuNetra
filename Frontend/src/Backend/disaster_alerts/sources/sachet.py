import os
import re
import html
import requests
import xml.etree.ElementTree as ET

from ..models import DisasterAlert


# =================================================
# OFFICIAL NDMA SACHET RSS FEED
# =================================================

SACHET_RSS_URL = os.getenv(
    "SACHET_RSS_URL",
    "https://sachet.ndma.gov.in/cap_public_website/rss/rss_india.xml",
)


# =================================================
# CAP XML NAMESPACE
# =================================================

CAP_NAMESPACE = {
    "cap": "urn:oasis:names:tc:emergency:cap:1.2"
}


# =================================================
# TEXT CLEANING
# =================================================

def _clean_text(value):

    if value is None:
        return ""

    value = html.unescape(str(value))

    value = re.sub(
        r"<[^>]+>",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


# =================================================
# CAP TEXT
# =================================================

def _find_text(element, tag_name):

    child = element.find(
        f"cap:{tag_name}",
        CAP_NAMESPACE
    )

    if child is None:
        return ""

    return _clean_text(
        child.text or ""
    )


# =================================================
# PREFERRED INFO BLOCK
# =================================================

def _get_preferred_info(root):

    info_blocks = root.findall(
        "cap:info",
        CAP_NAMESPACE
    )

    if not info_blocks:
        return None

    # Prefer English government information
    for info in info_blocks:

        language = _find_text(
            info,
            "language"
        ).lower()

        if language.startswith("en"):
            return info

    return info_blocks[0]


# =================================================
# EXTRACT STATE
# =================================================

def _extract_state(area_description):

    if not area_description:
        return None

    # Example:
    #
    # Districts of Uttarakhand
    #
    # -> Uttarakhand

    match = re.search(
        r"\b(?:districts?|areas?|parts?)\s+of\s+(.+)$",
        area_description,
        flags=re.IGNORECASE
    )

    if match:

        state = match.group(1).strip(
            " ,.-"
        )

        return state or None

    return None


# =================================================
# EXTRACT DISTRICT
# =================================================

def _extract_districts(headline):

    if not headline:
        return None

    # -------------------------------------------------
    # Exact pattern for headlines such as:
    #
    # "... over Dehradun, Haridwar, Pauri Garhwal,
    # and Tehri Garhwal districts in the next 3 hours."
    # -------------------------------------------------

    match = re.search(
        r"\bover\s+(.+?)\s+districts?\b",
        headline,
        flags=re.IGNORECASE
    )

    if match:

        district_text = match.group(1).strip()

        # Convert:
        #
        # A, B, C, and D
        #
        # to:
        #
        # A, B, C, D

        district_text = re.sub(
            r",?\s+and\s+",
            ", ",
            district_text,
            flags=re.IGNORECASE
        )

        district_text = district_text.strip(
            " ,.-"
        )

        if district_text:
            return district_text

    return None


# =================================================
# PARSE CAP XML
# =================================================

def _parse_cap_xml(
    xml_content,
    fallback_link=None
):

    try:

        root = ET.fromstring(
            xml_content
        )

    except ET.ParseError as error:

        print(
            f"[SACHET] CAP XML parsing error: {error}"
        )

        return None


    # =================================================
    # ALERT LEVEL
    # =================================================

    identifier = _find_text(
        root,
        "identifier"
    )

    sender = _find_text(
        root,
        "sender"
    )

    sent = _find_text(
        root,
        "sent"
    )

    status = _find_text(
        root,
        "status"
    )

    message_type = _find_text(
        root,
        "msgType"
    )


    # =================================================
    # INFO
    # =================================================

    info = _get_preferred_info(
        root
    )

    if info is None:

        print(
            "[SACHET] No CAP info block found."
        )

        return None


    category = _find_text(
        info,
        "category"
    )

    event = _find_text(
        info,
        "event"
    )

    urgency = _find_text(
        info,
        "urgency"
    )

    severity = _find_text(
        info,
        "severity"
    )

    certainty = _find_text(
        info,
        "certainty"
    )

    effective = _find_text(
        info,
        "effective"
    )

    onset = _find_text(
        info,
        "onset"
    )

    expires = _find_text(
        info,
        "expires"
    )

    headline = _find_text(
        info,
        "headline"
    )

    description = _find_text(
        info,
        "description"
    )

    instruction = _find_text(
        info,
        "instruction"
    )


    # =================================================
    # AREA
    # =================================================

    area_blocks = info.findall(
        "cap:area",
        CAP_NAMESPACE
    )

    affected_areas = []

    polygon_urls = []

    state = None


    for area in area_blocks:

        area_description = _find_text(
            area,
            "areaDesc"
        )

        if area_description:

            affected_areas.append(
                area_description
            )

            detected_state = _extract_state(
                area_description
            )

            if detected_state:

                state = detected_state


        # ---------------------------------------------
        # Polygon URL
        # ---------------------------------------------

        for parameter in area.findall(
            "cap:parameter",
            CAP_NAMESPACE
        ):

            value_name = _find_text(
                parameter,
                "valueName"
            )

            value = _find_text(
                parameter,
                "value"
            )

            if (
                value_name.lower()
                == "polygon url"
                and value
            ):

                polygon_urls.append(
                    value
                )


    # =================================================
    # DISTRICT
    # =================================================

    district = _extract_districts(
        headline
    )


    # =================================================
    # AFFECTED AREA
    # =================================================

    affected_area = None

    if affected_areas:

        affected_area = "; ".join(
            affected_areas
        )


    # =================================================
    # ISSUE
    # =================================================

    alert_type = (
        event
        or headline
        or "Government Disaster Alert"
    )


    # =================================================
    # ID
    # =================================================

    if identifier:

        alert_id = (
            f"SACHET-{identifier}"
        )

    else:

        alert_id = (
            f"SACHET-{sent}-"
            f"{alert_type}-"
            f"{affected_area}"
        )


    # =================================================
    # CREATE ALERT
    # =================================================

    return DisasterAlert(

        id=alert_id,

        source="NDMA SACHET",

        authority=(
            sender
            or "Government Disaster Authority"
        ),

        alert_type=alert_type,

        category=(
            category
            or None
        ),

        severity=(
            severity
            or None
        ),

        urgency=(
            urgency
            or None
        ),

        certainty=(
            certainty
            or None
        ),

        state=state,

        district=district,

        affected_area=affected_area,

        issued_at=(
            sent
            or None
        ),

        effective_at=(
            effective
            or None
        ),

        onset_at=(
            onset
            or None
        ),

        expires_at=(
            expires
            or None
        ),

        headline=(
            headline
            or None
        ),

        description=(
            description
            or None
        ),

        instruction=(
            instruction
            or None
        ),

        status=(
            status
            or None
        ),

        message_type=(
            message_type
            or None
        ),

        source_url=(
            fallback_link
            or "https://sachet.ndma.gov.in/"
        ),

        polygon_url=(
            polygon_urls[0]
            if polygon_urls
            else None
        ),
    )


# =================================================
# FETCH CAP XML
# =================================================

def _fetch_cap_xml(link):

    if not link:
        return None

    try:

        response = requests.get(
            link,
            timeout=20,
            headers={
                "User-Agent": "VayuNetra/1.0",
                "Accept": (
                    "application/xml, "
                    "text/xml"
                ),
            },
        )

        response.raise_for_status()

        return response.content

    except requests.RequestException as error:

        print(
            f"[SACHET] CAP request failed: {error}"
        )

        return None


# =================================================
# RSS TEXT
# =================================================

def _get_rss_text(
    element,
    tag_name
):

    child = element.find(
        tag_name
    )

    if child is None:
        return ""

    return child.text or ""


# =================================================
# FETCH SACHET
# =================================================

def fetch_sachet_alerts():

    try:

        response = requests.get(
            SACHET_RSS_URL,
            timeout=20,
            headers={
                "User-Agent": "VayuNetra/1.0",
                "Accept": (
                    "application/rss+xml, "
                    "application/xml, "
                    "text/xml"
                ),
            },
        )

        response.raise_for_status()

        root = ET.fromstring(
            response.content
        )

        alerts = []


        for item in root.iter(
            "item"
        ):

            title = _clean_text(
                _get_rss_text(
                    item,
                    "title"
                )
            )

            description = _clean_text(
                _get_rss_text(
                    item,
                    "description"
                )
            )

            pub_date = _clean_text(
                _get_rss_text(
                    item,
                    "pubDate"
                )
            )

            link = _clean_text(
                _get_rss_text(
                    item,
                    "link"
                )
            )

            guid = _clean_text(
                _get_rss_text(
                    item,
                    "guid"
                )
            )


            # ---------------------------------------------
            # Get detailed CAP XML
            # ---------------------------------------------

            cap_xml = _fetch_cap_xml(
                link
            )


            alert = None


            if cap_xml:

                alert = _parse_cap_xml(
                    cap_xml,
                    fallback_link=link
                )


            # ---------------------------------------------
            # Fallback RSS alert
            # ---------------------------------------------

            if alert is None:

                if not title and not description:
                    continue


                alert_id = (
                    f"SACHET-{guid}"
                    if guid
                    else (
                        f"SACHET-{title}-"
                        f"{pub_date}"
                    )
                )


                alert = DisasterAlert(

                    id=alert_id,

                    source="NDMA SACHET",

                    authority=(
                        "National Disaster "
                        "Management Authority"
                    ),

                    alert_type=(
                        title
                        or "Government Disaster Alert"
                    ),

                    category=None,

                    severity=None,

                    urgency=None,

                    certainty=None,

                    state=None,

                    district=None,

                    affected_area=None,

                    issued_at=(
                        pub_date
                        or None
                    ),

                    effective_at=None,

                    onset_at=None,

                    expires_at=None,

                    headline=(
                        title
                        or None
                    ),

                    description=(
                        description
                        or None
                    ),

                    instruction=None,

                    status="Actual",

                    message_type=None,

                    source_url=(
                        link
                        or "https://sachet.ndma.gov.in/"
                    ),

                    polygon_url=None,
                )


            alerts.append(
                alert
            )


        print(
            f"[SACHET] Received "
            f"{len(alerts)} detailed alerts."
        )

        return alerts


    except requests.RequestException as error:

        print(
            f"[SACHET] Network error: {error}"
        )

        return []


    except ET.ParseError as error:

        print(
            f"[SACHET] RSS XML parsing error: {error}"
        )

        return []


    except Exception as error:

        print(
            f"[SACHET] Unexpected error: {error}"
        )

        return []
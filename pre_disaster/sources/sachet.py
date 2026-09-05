import re
import xml.etree.ElementTree as ET
from typing import List, Optional

import feedparser
import requests

from models import DisasterAlert


SACHET_RSS_URL = (
    "https://sachet.ndma.gov.in/"
    "cap_public_website/rss/rss_india.xml"
)

SACHET_XML_URL = (
    "https://sachet.ndma.gov.in/"
    "cap_public_website/FetchXMLFile?identifier={identifier}"
)

CAP_NAMESPACE = {
    "cap": "urn:oasis:names:tc:emergency:cap:1.2"
}


def get_text(element, path: str) -> Optional[str]:
    """Safely get text from a CAP XML element."""
    node = element.find(path, CAP_NAMESPACE)

    if node is not None and node.text:
        return node.text.strip()

    return None


def get_preferred_info(alert_element):
    """
    CAP alerts can contain multiple language-specific <info> blocks.
    Prefer English when available.
    """

    info_nodes = alert_element.findall(
        "cap:info",
        CAP_NAMESPACE
    )

    if not info_nodes:
        return None

    for info in info_nodes:
        language = get_text(info, "cap:language")

        if language and language.lower().startswith("en"):
            return info

    return info_nodes[0]


def extract_state(area_desc: Optional[str]) -> Optional[str]:
    """Extract state from SACHET area description."""

    if not area_desc:
        return None

    match = re.search(
        r"(?:Districts?|Areas?)\s+of\s+(.+)",
        area_desc,
        flags=re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    return None


def extract_districts(headline: Optional[str]) -> Optional[str]:
    """
    Extract districts from common SACHET wording such as:

    '... over Dehradun, Haridwar, Pauri Garhwal,
     and Tehri Garhwal districts ...'
    """

    if not headline:
        return None

    match = re.search(
        r"\bover\s+(.+?)\s+districts?\b",
        headline,
        flags=re.IGNORECASE
    )

    if not match:
        return None

    district_text = match.group(1).strip()

    district_text = re.sub(
        r",?\s+and\s+",
        ", ",
        district_text,
        flags=re.IGNORECASE
    )

    district_text = district_text.strip(" ,.-")

    return district_text or None


def extract_polygon_url(info) -> Optional[str]:
    """
    SACHET may provide the polygon endpoint as a CAP
    parameter inside the <info> element.
    """

    if info is None:
        return None

    for parameter in info.findall(
        "cap:parameter",
        CAP_NAMESPACE
    ):
        name = get_text(parameter, "cap:valueName")
        value = get_text(parameter, "cap:value")

        if not name or not value:
            continue

        if "polygon" in name.lower():
            return value

    return None


def parse_cap_xml(xml_text: str) -> Optional[DisasterAlert]:
    """Convert one SACHET CAP XML document into DisasterAlert."""

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return None

    identifier = get_text(root, "cap:identifier")

    if not identifier:
        return None

    sender = get_text(root, "cap:sender")
    sent = get_text(root, "cap:sent")
    status = get_text(root, "cap:status")
    message_type = get_text(root, "cap:msgType")

    info = get_preferred_info(root)

    if info is None:
        return None

    category = get_text(info, "cap:category")
    event = get_text(info, "cap:event")
    urgency = get_text(info, "cap:urgency")
    severity = get_text(info, "cap:severity")
    certainty = get_text(info, "cap:certainty")

    effective = get_text(info, "cap:effective")
    onset = get_text(info, "cap:onset")
    expires = get_text(info, "cap:expires")

    headline = get_text(info, "cap:headline")
    instruction = get_text(info, "cap:instruction")

    area = info.find(
        "cap:area",
        CAP_NAMESPACE
    )

    area_desc = None

    if area is not None:
        area_desc = get_text(
            area,
            "cap:areaDesc"
        )

    state = extract_state(area_desc)
    district = extract_districts(headline)
    polygon_url = extract_polygon_url(info)

    return DisasterAlert(
        id=f"SACHET-{identifier}",
        source="NDMA SACHET",
        authority=sender or "NDMA",

        alert_type=event or "Unknown",

        category=category,
        severity=severity,
        urgency=urgency,
        certainty=certainty,

        state=state,
        district=district,
        affected_area=area_desc,

        issued_at=sent,
        effective_at=effective,
        onset_at=onset,
        expires_at=expires,

        headline=headline,
        instruction=instruction,

        status=status,
        message_type=message_type,

        source_url="https://sachet.ndma.gov.in/",
        polygon_url=polygon_url,
    )


def fetch_cap_xml(identifier: str) -> Optional[str]:
    """Fetch one official SACHET CAP XML document."""

    url = SACHET_XML_URL.format(
        identifier=identifier
    )

    response = requests.get(
        url,
        timeout=15
    )

    response.raise_for_status()

    return response.text


def fetch_sachet_alerts() -> List[DisasterAlert]:
    """
    Read the official SACHET India RSS feed and
    retrieve the corresponding CAP XML alerts.
    """

    feed = feedparser.parse(
        SACHET_RSS_URL
    )

    alerts = []

    for entry in feed.entries:

        identifier = (
            entry.get("identifier")
            or entry.get("id")
        )

        if not identifier:
            continue

        try:
            xml_text = fetch_cap_xml(
                identifier
            )

            alert = parse_cap_xml(
                xml_text
            )

            if alert:
                alerts.append(alert)

        except Exception as error:
            print(
                f"[SACHET] Failed to fetch "
                f"{identifier}: {error}"
            )

    print(
        f"[SACHET] Parsed {len(alerts)} alerts"
    )

    return alerts
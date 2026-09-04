import os


# How often the backend checks government sources
ALERT_CHECK_INTERVAL_SECONDS = int(
    os.getenv(
        "ALERT_CHECK_INTERVAL_SECONDS",
        "60"
    )
)


# Maximum number of alerts kept in memory
MAX_ALERTS = int(
    os.getenv(
        "MAX_ALERTS",
        "1000"
    )
)


# -------------------------------------------------
# Government Source URLs
# -------------------------------------------------

# NDMA SACHET CAP XML endpoint
SACHET_CAP_URL = os.getenv(
    "SACHET_CAP_URL",
    ""
)


# India Meteorological Department
IMD_API_URL = os.getenv(
    "IMD_API_URL",
    "https://api.imd.gov.in"
)


# Central Water Commission
CWC_API_URL = os.getenv(
    "CWC_API_URL",
    ""
)


# Indian National Centre for Ocean Information Services
INCOIS_API_URL = os.getenv(
    "INCOIS_API_URL",
    ""
)


# Forest Survey of India
FSI_API_URL = os.getenv(
    "FSI_API_URL",
    ""
)


# Defence Geoinformatics Research Establishment
DGRE_API_URL = os.getenv(
    "DGRE_API_URL",
    ""
)


# Fire Department / Fire & Emergency Services
FIRE_DEPARTMENT_URL = os.getenv(
    "FIRE_DEPARTMENT_URL",
    ""
)


# State / District Disaster Management sources
STATE_DISTRICT_API_URL = os.getenv(
    "STATE_DISTRICT_API_URL",
    ""
)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .scheduler import AlertScheduler


app = FastAPI(
    title="VayuNetra Disaster Alert API",
    description="Real-time government disaster alert aggregation service",
    version="1.0.0",
)


# -------------------------------------------------
# CORS
# -------------------------------------------------

# Allows the React frontend to communicate
# with this backend during development.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------
# Scheduler
# -------------------------------------------------

scheduler = AlertScheduler()


# -------------------------------------------------
# API ROUTES
# -------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "success",
        "service": "VayuNetra Disaster Alert API",
        "message": "Backend is running",
    }


@app.get("/api/alerts")
def get_alerts():
    """
    Return currently active disaster alerts.
    """

    alerts = scheduler.store.get_active()

    return {
        "status": "success",
        "count": len(alerts),
        "alerts": [
            alert.to_dict()
            for alert in alerts
        ],
    }


@app.get("/api/alerts/all")
def get_all_alerts():
    """
    Return all alerts currently stored.
    """

    alerts = scheduler.store.get_all()

    return {
        "status": "success",
        "count": len(alerts),
        "alerts": [
            alert.to_dict()
            for alert in alerts
        ],
    }


@app.get("/api/alerts/health")
def health():
    """
    Backend health-check endpoint.
    """

    return {
        "status": "ok",
        "service": "VayuNetra Alert Aggregator",
    }


@app.post("/api/alerts/check")
def check_alert_sources():
    """
    Manually trigger one check of all
    configured government sources.

    Useful during development and testing.
    """

    new_alerts = scheduler.check_sources()

    return {
        "status": "success",
        "new_count": len(new_alerts),
        "new_alerts": [
            alert.to_dict()
            for alert in new_alerts
        ],
    }
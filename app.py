from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sources.sachet import fetch_sachet_alerts
from deduplicator import AlertDeduplicator
from store import AlertStore


app = FastAPI(
    title="VayuNetra Pre-Disaster Alert API",
    description="Real-time government disaster alert aggregation service",
    version="1.0.0",
)


# Allow the React frontend to communicate with this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


store = AlertStore()
deduplicator = AlertDeduplicator()


@app.get("/")
def root():
    return {
        "status": "success",
        "service": "VayuNetra Pre-Disaster Alert API",
        "message": "Backend is running",
    }


@app.get("/api/alerts")
def get_active_alerts():
    alerts = store.get_active()

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
    alerts = store.get_all()

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
    return {
        "status": "ok",
        "service": "VayuNetra Pre-Disaster Alert Aggregator",
    }


@app.post("/api/alerts/check")
def check_alert_sources():
    """
    Manually fetch the latest alerts from
    official government sources.
    """

    try:
        alerts = fetch_sachet_alerts()

        new_alerts = [
            alert
            for alert in alerts
            if deduplicator.is_new(alert)
        ]

        store.add_many(new_alerts)

        return {
            "status": "success",
            "received_count": len(alerts),
            "new_count": len(new_alerts),
            "new_alerts": [
                alert.to_dict()
                for alert in new_alerts
            ],
        }

    except Exception as error:
        return {
            "status": "error",
            "message": str(error),
        }
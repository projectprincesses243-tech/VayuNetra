import { useEffect, useRef, useState } from "react";

//const API_URL = "http://localhost:8001/api/alerts";
const API_URL = "http://localhost:8000/api/state";

function PreDisaster() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [backendStatus, setBackendStatus] = useState("Connecting...");
  const [notification, setNotification] = useState(null);

  const knownAlertIds = useRef(new Set());
  const firstLoad = useRef(true);

  // Play one notification sound
  const playNotificationSound = () => {
    try {
      const AudioContext =
        window.AudioContext ||
        window.webkitAudioContext;

      if (!AudioContext) return;

      const audioContext = new AudioContext();

      const oscillator =
        audioContext.createOscillator();

      const gainNode =
        audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(
        audioContext.destination
      );

      oscillator.type = "sine";
      oscillator.frequency.value = 880;

      gainNode.gain.setValueAtTime(
        0.2,
        audioContext.currentTime
      );

      gainNode.gain.exponentialRampToValueAtTime(
        0.001,
        audioContext.currentTime + 0.5
      );

      oscillator.start();

      oscillator.stop(
        audioContext.currentTime + 0.5
      );
    } catch (error) {
      console.log(
        "Notification sound error:",
        error
      );
    }
  };

  // Get alerts from backend
  const fetchAlerts = async () => {
    try {
      const response = await fetch(API_URL);

      if (!response.ok) {
        throw new Error(
          `Backend error: ${response.status}`
        );
      }

    /*  const data = await response.json();

      const incomingAlerts =
        data.alerts || [];

      setAlerts(incomingAlerts);
*/
const data = await response.json();

let incomingAlerts = [];

if (data.scenario) {
    incomingAlerts = [
        {
            id: "scenario-1",
            alert_type: data.scenario.hazard,
            severity: data.scenario.severity,
            priority: data.scenario.priority,
            affected_area: data.scenario.affected_area,
            source: "VayuNetra Disaster Intelligence",
            authority: "IMD / ADRF",
            state: "",
            district: "",
            issued_at: new Date().toISOString(),
            description:
              "Pre-disaster scenario detected from government alert monitoring system.",
            status: "ACTIVE"
        }
    ];
}

setAlerts(incomingAlerts);
      setBackendStatus("Connected");

      setLoading(false);

      // Don't make sound for alerts already present
      // when the page first loads.
      if (!firstLoad.current) {
        const newAlerts =
          incomingAlerts.filter(
            (alert) =>
              !knownAlertIds.current.has(
                alert.id
              )
          );

        if (newAlerts.length > 0) {
          const newAlert = newAlerts[0];

          setNotification(newAlert);

          playNotificationSound();

          setTimeout(() => {
            setNotification(null);
          }, 7000);
        }
      }

      incomingAlerts.forEach((alert) => {
        knownAlertIds.current.add(
          alert.id
        );
      });

      firstLoad.current = false;
    } catch (error) {
      console.error(
        "Unable to connect to backend:",
        error
      );

      setBackendStatus(
        "Backend Offline"
      );

      setLoading(false);
    }
  };

  // Automatically check backend
  useEffect(() => {
    fetchAlerts();

    const interval = setInterval(() => {
      fetchAlerts();
    }, 30000);

    return () => {
      clearInterval(interval);
    };
  }, []);

  const severityClass = (severity) => {
    const value = String(
      severity || ""
    ).toLowerCase();

    if (value.includes("red")) {
      return "red";
    }

    if (value.includes("orange")) {
      return "orange";
    }

    if (value.includes("yellow")) {
      return "yellow";
    }

    return "normal";
  };

  const severityIcon = (severity) => {
    const value = String(
      severity || ""
    ).toLowerCase();

    if (value.includes("red")) {
      return "🔴";
    }

    if (value.includes("orange")) {
      return "🟠";
    }

    if (value.includes("yellow")) {
      return "🟡";
    }

    return "⚪";
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f1f5f9",
        fontFamily: "Arial, sans-serif",
        color: "#17202a"
      }}
    >

      {/* ============================= */}
      {/* NEW ALERT NOTIFICATION */}
      {/* ============================= */}

      {notification && (
        <div
          style={{
            position: "fixed",
            top: "20px",
            right: "20px",
            width: "350px",
            background: "#ffffff",
            borderLeft:
              "5px solid #dc2626",
            borderRadius: "10px",
            padding: "18px",
            boxShadow:
              "0 8px 30px rgba(0,0,0,0.25)",
            zIndex: 9999
          }}
        >
          <div
            style={{
              fontWeight: "bold",
              color: "#b91c1c",
              marginBottom: "8px"
            }}
          >
            🔔 NEW DISASTER ALERT
          </div>

          <div
            style={{
              fontSize: "18px",
              fontWeight: "bold",
              marginBottom: "6px"
            }}
          >
            {notification.alert_type}
          </div>

          <div>
            {notification.state || ""}
            {notification.district
              ? ` • ${notification.district}`
              : ""}
          </div>

          <div
            style={{
              marginTop: "8px",
              color: "#64748b",
              fontSize: "13px"
            }}
          >
            Source:{" "}
            {notification.source}
          </div>
        </div>
      )}

      {/* ============================= */}
      {/* HEADER */}
      {/* ============================= */}

      <header
        style={{
          background: "#111827",
          color: "white",
          padding: "28px 40px",
          display: "flex",
          justifyContent:
            "space-between",
          alignItems: "center"
        }}
      >
        <div>
          <h1
            style={{
              margin: 0,
              fontSize: "28px"
            }}
          >
            VayuNetra
          </h1>

          <h2
            style={{
              margin:
                "6px 0",
              fontSize: "22px"
            }}
          >
            Pre-Disaster Operations
          </h2>

          <p
            style={{
              margin: 0,
              color: "#cbd5e1"
            }}
          >
            Real-Time Government
            Disaster Alert Monitoring
          </p>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            fontWeight: "bold"
          }}
        >
          <span
            style={{
              width: "10px",
              height: "10px",
              borderRadius: "50%",
              background:
                backendStatus ===
                "Connected"
                  ? "#22c55e"
                  : "#ef4444"
            }}
          />

          {backendStatus}
        </div>
      </header>

      {/* ============================= */}
      {/* MONITORING STATUS */}
      {/* ============================= */}

      <div
        style={{
          background: "white",
          borderBottom:
            "1px solid #d1d5db",
          padding:
            "14px 40px",
          display: "flex",
          justifyContent:
            "space-between"
        }}
      >
        <strong>
          Government Alert Monitoring:
          {" "}
          <span
            style={{
              color:
                backendStatus ===
                "Connected"
                  ? "#16a34a"
                  : "#dc2626"
            }}
          >
            {backendStatus ===
            "Connected"
              ? "ACTIVE"
              : "INACTIVE"}
          </span>
        </strong>

        <span>
          Automatic update:
          every 30 seconds
        </span>
      </div>

      {/* ============================= */}
      {/* MAIN */}
      {/* ============================= */}

      <main
        style={{
          maxWidth: "1200px",
          margin: "0 auto",
          padding: "32px 24px"
        }}
      >

        <div
          style={{
            display: "flex",
            justifyContent:
              "space-between",
            alignItems: "center",
            marginBottom: "24px"
          }}
        >
          <div>
            <h2
              style={{
                margin: 0
              }}
            >
              Current Government Alerts
            </h2>

            <p
              style={{
                color: "#64748b"
              }}
            >
              Alerts collected from
              monitored official sources.
            </p>
          </div>

          <div
            style={{
              background: "#111827",
              color: "white",
              padding:
                "10px 16px",
              borderRadius: "8px",
              fontWeight: "bold"
            }}
          >
            {alerts.length} Active
          </div>
        </div>

        {/* ============================= */}
        {/* LOADING */}
        {/* ============================= */}

        {loading && (
          <div
            style={{
              background: "white",
              padding: "50px",
              textAlign: "center",
              borderRadius: "10px"
            }}
          >
            <h3>
              Connecting to VayuNetra
              Alert Service...
            </h3>

            <p>
              Waiting for backend
              government-alert data.
            </p>
          </div>
        )}

        {/* ============================= */}
        {/* NO ALERTS */}
        {/* ============================= */}

        {!loading &&
          alerts.length === 0 && (
            <div
              style={{
                background: "white",
                padding: "60px 30px",
                textAlign: "center",
                borderRadius: "10px"
              }}
            >
              <div
                style={{
                  fontSize: "40px"
                }}
              >
                ✓
              </div>

              <h3>
                No Active
                Pre-Disaster Alerts
              </h3>

              <p
                style={{
                  color: "#64748b"
                }}
              >
                No active alerts are
                currently available
                from the monitored
                government sources.
              </p>
            </div>
          )}

        {/* ============================= */}
        {/* ALERT LIST */}
        {/* ============================= */}

        <div
          style={{
            display: "flex",
            flexDirection:
              "column",
            gap: "18px"
          }}
        >
          {alerts.map((alert) => (

            <div
              key={alert.id}
              style={{
                background: "white",
                borderRadius: "12px",
                padding: "24px",
                border:
                  "1px solid #dbe0e6",
                boxShadow:
                  "0 3px 10px rgba(0,0,0,0.06)"
              }}
            >

              {/* Alert heading */}

              <div
                style={{
                  display: "flex",
                  justifyContent:
                    "space-between",
                  alignItems:
                    "flex-start"
                }}
              >
                <div>

                  <span
                    style={{
                      display:
                        "inline-block",
                      padding:
                        "6px 10px",
                      borderRadius: "6px",
                      fontWeight: "bold",
                      fontSize: "13px",
                      background:
                        severityClass(
                          alert.severity
                        ) === "red"
                          ? "#fee2e2"
                          : severityClass(
                              alert.severity
                            ) ===
                            "orange"
                          ? "#ffedd5"
                          : severityClass(
                              alert.severity
                            ) ===
                            "yellow"
                          ? "#fef9c3"
                          : "#e5e7eb",
                      color:
                        severityClass(
                          alert.severity
                        ) === "red"
                          ? "#b91c1c"
                          : severityClass(
                              alert.severity
                            ) ===
                            "orange"
                          ? "#c2410c"
                          : severityClass(
                              alert.severity
                            ) ===
                            "yellow"
                          ? "#a16207"
                          : "#374151"
                    }}
                  >
                    {severityIcon(
                      alert.severity
                    )}{" "}
                    {alert.severity ||
                      "Unknown"}
                  </span>

                  <h3>
                    {alert.alert_type}
                  </h3>

                </div>

                <span
                  style={{
                    background:
                      "#dcfce7",
                    color:
                      "#15803d",
                    padding:
                      "6px 10px",
                    borderRadius:
                      "6px",
                    fontSize:
                      "12px",
                    fontWeight:
                      "bold"
                  }}
                >
                  ACTIVE
                </span>

              </div>

              {/* Details */}

              <div
                style={{
                  marginTop:
                    "20px",
                  display: "grid",
                  gridTemplateColumns:
                    "repeat(3, 1fr)",
                  gap: "18px"
                }}
              >

                <div>
                  <small>
                    SOURCE
                  </small>

                  <strong>
                    {alert.source}
                  </strong>
                </div>

                <div>
                  <small>
                    AUTHORITY
                  </small>

                  <strong>
                    {alert.authority}
                  </strong>
                </div>

                <div>
                  <small>
                    STATE
                  </small>

                  <strong>
                    {alert.state ||
                      "—"}
                  </strong>
                </div>

                <div>
                  <small>
                    DISTRICT
                  </small>

                  <strong>
                    {alert.district ||
                      "—"}
                  </strong>
                </div>

                <div>
                  <small>
                    AFFECTED AREA
                  </small>

                  <strong>
                    {alert.affected_area ||
                      "—"}
                  </strong>
                </div>

                <div>
                  <small>
                    ISSUED
                  </small>

                  <strong>
                    {alert.issued_at ||
                      "—"}
                  </strong>
                </div>

              </div>

              {/* Description */}

              <div
                style={{
                  marginTop:
                    "22px",
                  paddingTop:
                    "18px",
                  borderTop:
                    "1px solid #e5e7eb"
                }}
              >
                <small>
                  DESCRIPTION
                </small>

                <p>
                  {alert.description ||
                    "No description available."}
                </p>
              </div>

              {/* Footer */}

              <div
                style={{
                  marginTop:
                    "18px",
                  paddingTop:
                    "15px",
                  borderTop:
                    "1px solid #e5e7eb",
                  display: "flex",
                  justifyContent:
                    "space-between",
                  fontSize:
                    "13px",
                  color:
                    "#64748b"
                }}
              >
                <span>
                  Status:{" "}
                  {alert.status}
                </span>

                {alert.source_url && (
                  <a
                    href={
                      alert.source_url
                    }
                    target="_blank"
                    rel="noreferrer"
                  >
                    Official Source ↗
                  </a>
                )}
              </div>

            </div>
          ))}
        </div>

      </main>
    </div>
  );
}

export default PreDisaster;
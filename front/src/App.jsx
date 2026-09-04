import { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:8001/api/alerts";

function App() {
  const [alerts, setAlerts] = useState([]);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchAlerts = async () => {
    try {
      const response = await fetch(API_URL);

      if (!response.ok) {
        throw new Error("Backend request failed");
      }

      const data = await response.json();

      setAlerts(data.alerts || []);
      setConnected(true);
    } catch (error) {
      console.error(error);
      setConnected(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();

    const interval = setInterval(fetchAlerts, 30000);

    return () => clearInterval(interval);
  }, []);

  const formatDate = (value) => {
    if (!value) return null;

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return date.toLocaleString();
  };

  const Field = ({ label, value }) => {
    if (!value) return null;

    return (
      <div style={styles.field}>
        <span style={styles.fieldLabel}>{label}</span>
        <span style={styles.fieldValue}>{value}</span>
      </div>
    );
  };

  return (
    <div style={styles.page}>

      {/* HEADER */}
      <header style={styles.header}>
        <div>
          <h1 style={styles.logo}>VayuNetra</h1>

          <h2 style={styles.title}>
            Pre-Disaster Operations
          </h2>

          <p style={styles.subtitle}>
            Real-Time Government Disaster Alert Monitoring
          </p>
        </div>

        <div style={styles.connection}>
          <span
            style={{
              ...styles.connectionDot,
              backgroundColor: connected
                ? "#16c784"
                : "#dc2626",
            }}
          />

          {connected ? "Connected" : "Disconnected"}
        </div>
      </header>

      {/* MONITORING BAR */}
      <div style={styles.monitorBar}>
        <div>
          <strong>Government Alert Monitoring:</strong>{" "}
          <span style={styles.activeText}>
            ACTIVE
          </span>
        </div>

        <div>
          Automatic update: every 30 seconds
        </div>
      </div>

      {/* MAIN CONTENT */}
      <main style={styles.main}>

        <div style={styles.sectionHeader}>
          <div>
            <h2 style={styles.sectionTitle}>
              Current Government Alerts
            </h2>

            <p style={styles.sectionSubtitle}>
              Alerts collected from monitored official sources.
            </p>
          </div>

          <div style={styles.countBox}>
            <strong>{alerts.length}</strong>
            <span>Active</span>
          </div>
        </div>

        {loading && (
          <div style={styles.message}>
            Loading government alerts...
          </div>
        )}

        {!loading && alerts.length === 0 && (
          <div style={styles.message}>
            No active government alerts available.
          </div>
        )}

        <div style={styles.alertList}>

          {alerts.map((alert) => (

            <article
              key={alert.id}
              style={styles.alertCard}
            >

              {/* CARD TOP */}
              <div style={styles.cardTop}>

                <div style={styles.severityBadge}>
                  <span style={styles.severityDot} />

                  {alert.severity || "Alert"}
                </div>

                <div style={styles.statusBadge}>
                  ACTIVE
                </div>

              </div>

              {/* ISSUE */}
              <div style={styles.issueSection}>

                <div style={styles.issueLabel}>
                  ISSUE
                </div>

                <h3 style={styles.issue}>
                  {alert.alert_type || "Government Alert"}
                </h3>

              </div>

              {/* INFORMATION */}
              <div style={styles.infoGrid}>

                <Field
                  label="SOURCE"
                  value={alert.source}
                />

                <Field
                  label="AUTHORITY"
                  value={alert.authority}
                />

                <Field
                  label="STATE"
                  value={alert.state}
                />

                <Field
                  label="DISTRICT"
                  value={alert.district}
                />

                <Field
                  label="AFFECTED AREA"
                  value={alert.affected_area}
                />

                <Field
                  label="ISSUED"
                  value={formatDate(alert.issued_at)}
                />

                <Field
                  label="EFFECTIVE"
                  value={formatDate(alert.effective_at)}
                />

                <Field
                  label="ONSET"
                  value={formatDate(alert.onset_at)}
                />

                <Field
                  label="EXPIRES"
                  value={formatDate(alert.expires_at)}
                />

                <Field
                  label="URGENCY"
                  value={alert.urgency}
                />

                <Field
                  label="CERTAINTY"
                  value={alert.certainty}
                />

                <Field
                  label="CATEGORY"
                  value={alert.category}
                />

                <Field
                  label="MESSAGE TYPE"
                  value={alert.message_type}
                />

              </div>

              {/* INSTRUCTION */}
              {alert.instruction && (
                <div style={styles.instruction}>
                  <div style={styles.issueLabel}>
                    OFFICIAL INSTRUCTION
                  </div>

                  <div style={styles.instructionText}>
                    {alert.instruction}
                  </div>
                </div>
              )}

              {/* HEADLINE */}
              {alert.headline && (
                <div style={styles.headline}>
                  {alert.headline}
                </div>
              )}

            </article>

          ))}

        </div>

      </main>
    </div>
  );
}


const styles = {

  page: {
    minHeight: "100vh",
    background: "#eef2f6",
    color: "#102033",
    fontFamily:
      "Arial, Helvetica, sans-serif",
  },

  header: {
    background: "#111827",
    color: "#ffffff",
    padding: "38px 60px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },

  logo: {
    margin: 0,
    fontSize: "38px",
    fontWeight: "700",
  },

  title: {
    margin: "8px 0 0",
    fontSize: "30px",
    fontWeight: "700",
  },

  subtitle: {
    margin: "10px 0 0",
    fontSize: "21px",
    color: "#d7e0ec",
  },

  connection: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    fontSize: "20px",
    fontWeight: "700",
  },

  connectionDot: {
    width: "14px",
    height: "14px",
    borderRadius: "50%",
    display: "inline-block",
  },

  monitorBar: {
    background: "#ffffff",
    borderBottom: "1px solid #cbd5e1",
    padding: "20px 60px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    fontSize: "19px",
  },

  activeText: {
    color: "#16a34a",
    fontWeight: "700",
  },

  main: {
    padding: "42px 40px",
    maxWidth: "1650px",
    margin: "0 auto",
  },

  sectionHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "35px",
  },

  sectionTitle: {
    margin: 0,
    fontSize: "31px",
  },

  sectionSubtitle: {
    margin: "12px 0 0",
    color: "#60758d",
    fontSize: "19px",
  },

  countBox: {
    background: "#111827",
    color: "#ffffff",
    borderRadius: "12px",
    padding: "16px 25px",
    display: "flex",
    alignItems: "center",
    gap: "8px",
    fontSize: "20px",
  },

  alertList: {
    display: "flex",
    flexDirection: "column",
    gap: "24px",
  },

  alertCard: {
    background: "#ffffff",
    border: "1px solid #dbe3eb",
    borderRadius: "16px",
    padding: "30px 32px",
    boxShadow:
      "0 3px 12px rgba(0,0,0,0.06)",
  },

  cardTop: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "24px",
  },

  severityBadge: {
    background: "#edf0f4",
    padding: "9px 16px",
    borderRadius: "9px",
    fontWeight: "700",
    fontSize: "17px",
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },

  severityDot: {
    width: "12px",
    height: "12px",
    borderRadius: "50%",
    background: "#8b5cf6",
    display: "inline-block",
  },

  statusBadge: {
    background: "#dcfce7",
    color: "#15803d",
    padding: "9px 15px",
    borderRadius: "8px",
    fontWeight: "700",
    fontSize: "14px",
  },

  issueSection: {
    marginBottom: "28px",
  },

  issueLabel: {
    color: "#52667c",
    fontSize: "13px",
    fontWeight: "700",
    letterSpacing: "0.8px",
    marginBottom: "7px",
  },

  issue: {
    margin: 0,
    fontSize: "24px",
    lineHeight: "1.35",
  },

  infoGrid: {
    display: "grid",
    gridTemplateColumns:
      "repeat(3, minmax(0, 1fr))",
    gap: "25px 40px",
  },

  field: {
    display: "flex",
    flexDirection: "column",
    gap: "7px",
  },

  fieldLabel: {
    color: "#52667c",
    fontSize: "13px",
    fontWeight: "500",
  },

  fieldValue: {
    fontSize: "17px",
    fontWeight: "600",
    lineHeight: "1.4",
    wordBreak: "break-word",
  },

  instruction: {
    borderTop: "1px solid #e2e8f0",
    marginTop: "28px",
    paddingTop: "20px",
  },

  instructionText: {
    fontSize: "16px",
    lineHeight: "1.5",
  },

  headline: {
    borderTop: "1px solid #e2e8f0",
    marginTop: "20px",
    paddingTop: "20px",
    color: "#52667c",
    fontSize: "15px",
    lineHeight: "1.5",
  },

  message: {
    background: "#ffffff",
    padding: "35px",
    borderRadius: "14px",
    textAlign: "center",
    fontSize: "18px",
    color: "#52667c",
  },
};


export default App;
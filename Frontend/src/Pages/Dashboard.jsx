function Dashboard() {
  return (
    <main className="dashboard">
      <section className="hero-section">
        <div>
          <p className="eyebrow">AUTONOMOUS DISASTER RESPONSE</p>

          <h2>
            VayuNetra <span>— Wings of Hope</span>
          </h2>

          <p className="hero-description">
            Intelligent drone swarm coordination for disaster
            search, survivor detection and rescue operations.
          </p>
        </div>

        <div className="mission-status">
          <span className="status-dot"></span>
          Awaiting Rescue Request
        </div>
      </section>

      <section className="dashboard-grid">

        <div className="dashboard-card">
          <div className="card-icon">🚨</div>

          <div>
            <p>RESCUE REQUESTS</p>
            <h3>0</h3>
            <span>Waiting for incoming request</span>
          </div>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">🚁</div>

          <div>
            <p>DRONE FLEET</p>
            <h3>—</h3>
            <span>Fleet status</span>
          </div>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">📡</div>

          <div>
            <p>ACTIVE MISSIONS</p>
            <h3>0</h3>
            <span>No operation currently active</span>
          </div>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">👁️</div>

          <div>
            <p>PERCEPTION</p>
            <h3>READY</h3>
            <span>YOLO + Thermal pipeline</span>
          </div>
        </div>

      </section>

      <section className="operation-grid">

        <div className="map-panel">

          <div className="panel-header">
            <div>
              <p>OPERATIONAL AREA</p>
              <h3>Live Mission Map</h3>
            </div>

            <span className="map-status">
              ● STANDBY
            </span>
          </div>

          <div className="map-placeholder">

            <div className="map-message">
              <div className="map-pin">⌖</div>

              <h3>Awaiting Mission</h3>

              <p>
                No rescue operation has been initiated.
                Incoming requests will appear here.
              </p>
            </div>

          </div>

        </div>

        <div className="actions-panel">

          <div className="panel-header">
            <div>
              <p>COMMAND CENTER</p>
              <h3>Live Actions</h3>
            </div>
          </div>

          <div className="action-item">
            <span className="action-indicator"></span>

            <div>
              <strong>System initialized</strong>
              <p>VayuNetra ready</p>
            </div>
          </div>

          <div className="action-item">
            <span className="action-indicator"></span>

            <div>
              <strong>Fleet monitoring active</strong>
              <p>Waiting for mission</p>
            </div>
          </div>

          <div className="action-item">
            <span className="action-indicator waiting"></span>

            <div>
              <strong>Waiting for request</strong>
              <p>Rescue communication channel active</p>
            </div>
          </div>

        </div>

      </section>
    </main>
  );
}

export default Dashboard;
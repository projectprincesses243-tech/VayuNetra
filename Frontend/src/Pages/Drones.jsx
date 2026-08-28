function Drones() {
  return (
    <main className="dashboard">

      {/* PAGE HEADER */}
      <section className="hero-section">
        <div>
          <p className="eyebrow">FLEET MANAGEMENT</p>

          <h2>
            Drone <span>Fleet</span>
          </h2>

          <p className="hero-description">
            Monitor the availability, health, location and
            operational status of the VayuNetra drone swarm.
          </p>
        </div>

        <div className="mission-status">
          <span className="status-dot"></span>
          Fleet Monitoring Active
        </div>
      </section>


      {/* FLEET OVERVIEW */}
      <section className="dashboard-grid">

        <div className="dashboard-card">
          <div className="card-icon">🚁</div>
          <div>
            <p>TOTAL FLEET</p>
            <h3>128</h3>
            <span>Registered drone units</span>
          </div>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">✓</div>
          <div>
            <p>AVAILABLE</p>
            <h3>94</h3>
            <span>Ready for deployment</span>
          </div>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">⚡</div>
          <div>
            <p>ACTIVE</p>
            <h3>21</h3>
            <span>Currently operating</span>
          </div>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">🔋</div>
          <div>
            <p>CHARGING</p>
            <h3>8</h3>
            <span>Currently charging</span>
          </div>
        </div>

      </section>


      {/* FLEET STATUS */}
      <section
        className="map-panel"
        style={{ marginTop: "18px" }}
      >

        <div className="panel-header">

          <div>
            <p>SWARM STATUS</p>
            <h3>Fleet Operations</h3>
          </div>

          <span className="map-status">
            128 UNITS
          </span>

        </div>


        <div style={{ padding: "25px" }}>

          <div className="action-item">
            <span className="action-indicator"></span>

            <div>
              <strong>94 drones available</strong>
              <p>Ready for immediate mission allocation</p>
            </div>
          </div>

          <div className="action-item">
            <span className="action-indicator"></span>

            <div>
              <strong>21 drones active</strong>
              <p>Currently assigned to operations</p>
            </div>
          </div>

          <div className="action-item">
            <span className="action-indicator waiting"></span>

            <div>
              <strong>8 drones charging</strong>
              <p>Returning to operational readiness</p>
            </div>
          </div>

          <div className="action-item">
            <span
              className="action-indicator"
              style={{ background: "#64748b" }}
            ></span>

            <div>
              <strong>5 drones unavailable</strong>
              <p>Offline or undergoing maintenance</p>
            </div>
          </div>

        </div>

      </section>


      {/* PHYSICAL DEMO */}
      <section
        className="map-panel"
        style={{ marginTop: "18px" }}
      >

        <div className="panel-header">

          <div>
            <p>PROTOTYPE HARDWARE</p>
            <h3>Physical Demonstration Fleet</h3>
          </div>

          <span className="map-status">
            4 DEMO UNITS
          </span>

        </div>


        <div
          style={{
            padding: "25px",
            display: "grid",
            gridTemplateColumns: "repeat(4, 1fr)",
            gap: "15px"
          }}
        >

          <div className="dashboard-card">
            <div className="card-icon">🚁</div>

            <div>
              <p>DRONE 01</p>
              <h3>READY</h3>
              <span>ESP32 Node</span>
            </div>
          </div>

          <div className="dashboard-card">
            <div className="card-icon">🚁</div>

            <div>
              <p>DRONE 02</p>
              <h3>READY</h3>
              <span>ESP32 Node</span>
            </div>
          </div>

          <div className="dashboard-card">
            <div className="card-icon">🚁</div>

            <div>
              <p>DRONE 03</p>
              <h3>READY</h3>
              <span>ESP32 Node</span>
            </div>
          </div>

          <div className="dashboard-card">
            <div className="card-icon">🚁</div>

            <div>
              <p>DRONE 04</p>
              <h3>READY</h3>
              <span>ESP32 Node</span>
            </div>
          </div>

        </div>

      </section>

    </main>
  );
}

export default Drones;
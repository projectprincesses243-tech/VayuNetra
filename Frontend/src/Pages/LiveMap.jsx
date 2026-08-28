function LiveMap() {
  return (
    <main className="dashboard">

      {/* PAGE HEADER */}
      <section className="hero-section">

        <div>
          <p className="eyebrow">OPERATIONAL INTELLIGENCE</p>

          <h2>
            Live <span>Mission Map</span>
          </h2>

          <p className="hero-description">
            Monitor disaster zones, drone positions, flight paths,
            VayuNetra operating range and active rescue operations.
          </p>
        </div>

        <div className="mission-status">
          <span className="status-dot"></span>
          Map Standby
        </div>

      </section>


      {/* MAP */}
      <section
        className="map-panel"
        style={{ marginTop: "18px" }}
      >

        <div className="panel-header">

          <div>
            <p>LIVE OPERATING AREA</p>
            <h3>VayuNetra Operational Map</h3>
          </div>

          <span className="map-status">
            ● NO ACTIVE MISSION
          </span>

        </div>


        <div className="map-placeholder">

          <div className="map-message">

            <div className="map-pin">
              ⌖
            </div>

            <h3>
              Awaiting Rescue Operation
            </h3>

            <p>
              Disaster zones, drone positions and
              mission paths will appear here when
              an operation begins.
            </p>

          </div>

        </div>

      </section>


      {/* MAP INFORMATION */}
      <section
        className="dashboard-grid"
        style={{ marginTop: "18px" }}
      >

        <div className="dashboard-card">

          <div className="card-icon">
            🚨
          </div>

          <div>
            <p>DISASTER ZONES</p>
            <h3>0</h3>
            <span>Active areas detected</span>
          </div>

        </div>


        <div className="dashboard-card">

          <div className="card-icon">
            🚁
          </div>

          <div>
            <p>DRONES ON MAP</p>
            <h3>0</h3>
            <span>Currently deployed</span>
          </div>

        </div>


        <div className="dashboard-card">

          <div className="card-icon">
            📍
          </div>

          <div>
            <p>OPERATING RANGE</p>
            <h3>—</h3>
            <span>VayuNetra coverage</span>
          </div>

        </div>


        <div className="dashboard-card">

          <div className="card-icon">
            🧭
          </div>

          <div>
            <p>FLIGHT PATHS</p>
            <h3>0</h3>
            <span>Active routes</span>
          </div>

        </div>

      </section>


      {/* MAP LEGEND */}
      <section
        className="map-panel"
        style={{ marginTop: "18px" }}
      >

        <div className="panel-header">

          <div>
            <p>MAP LEGEND</p>
            <h3>Operational Layers</h3>
          </div>

        </div>


        <div
          style={{
            padding: "25px",
            display: "grid",
            gridTemplateColumns: "repeat(4, 1fr)",
            gap: "15px"
          }}
        >

          <div className="action-item">
            <span className="action-indicator"></span>

            <div>
              <strong>Drone</strong>
              <p>Active drone position</p>
            </div>
          </div>


          <div className="action-item">
            <span className="action-indicator waiting"></span>

            <div>
              <strong>Disaster Zone</strong>
              <p>Detected operational area</p>
            </div>
          </div>


          <div className="action-item">

            <span
              className="action-indicator"
              style={{
                background: "#60a5fa"
              }}
            ></span>

            <div>
              <strong>Flight Path</strong>
              <p>Drone navigation route</p>
            </div>

          </div>


          <div className="action-item">

            <span
              className="action-indicator"
              style={{
                background: "#a78bfa"
              }}
            ></span>

            <div>
              <strong>Coverage Range</strong>
              <p>VayuNetra operating area</p>
            </div>

          </div>

        </div>

      </section>

    </main>
  );
}

export default LiveMap;
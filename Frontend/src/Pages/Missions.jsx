function Missions() {
  return (
    <main className="dashboard">

      {/* PAGE HEADER */}
      <section className="hero-section">

        <div>
          <p className="eyebrow">MISSION CONTROL</p>

          <h2>
            Rescue <span>Operations</span>
          </h2>

          <p className="hero-description">
            Receive, evaluate and coordinate disaster rescue
            missions using the VayuNetra drone swarm.
          </p>
        </div>

        <div className="mission-status">
          <span className="status-dot"></span>
          Awaiting Rescue Request
        </div>

      </section>


      {/* INCOMING REQUEST */}
      <section className="map-panel" style={{ marginTop: "18px" }}>

        <div className="panel-header">

          <div>
            <p>RESCUE COMMUNICATION</p>
            <h3>Incoming Request</h3>
          </div>

          <span className="map-status">
            ● LISTENING
          </span>

        </div>


        <div style={{ padding: "30px" }}>

          <div
            style={{
              padding: "25px",
              border: "1px dashed rgba(255,255,255,0.12)",
              borderRadius: "14px",
              textAlign: "center"
            }}
          >

            <div style={{ fontSize: "35px", marginBottom: "12px" }}>
              📡
            </div>

            <h3>No Rescue Request Received</h3>

            <p
              style={{
                color: "#697386",
                fontSize: "13px",
                marginTop: "8px"
              }}
            >
              VayuNetra is monitoring the rescue communication
              channel for a new emergency request.
            </p>

          </div>

        </div>

      </section>


      {/* MISSION CONFIGURATION */}
      <section className="operation-grid">

        {/* AUTOMATIC */}
        <div className="dashboard-card">

          <div className="card-icon">
            🤖
          </div>

          <div>

            <p>AUTONOMOUS MODE</p>

            <h3>Automatic Deployment</h3>

            <span>
              Let VayuNetra calculate the required
              number of drones and deployment strategy.
            </span>

          </div>

        </div>


        {/* MANUAL */}
        <div className="dashboard-card">

          <div className="card-icon">
            👤
          </div>

          <div>

            <p>ADMIN CONTROL</p>

            <h3>Manual Deployment</h3>

            <span>
              Allow an operator to specify the number
              of drones for the mission.
            </span>

          </div>

        </div>

      </section>


      {/* FUTURE MISSION PIPELINE */}
      <section
        className="map-panel"
        style={{ marginTop: "18px" }}
      >

        <div className="panel-header">

          <div>
            <p>MISSION PIPELINE</p>
            <h3>Operation Flow</h3>
          </div>

        </div>


        <div
          style={{
            padding: "30px",
            display: "grid",
            gridTemplateColumns: "repeat(5, 1fr)",
            gap: "12px"
          }}
        >

          <div className="dashboard-card">
            <div>
              <p>01</p>
              <h3>Request</h3>
              <span>Emergency received</span>
            </div>
          </div>

          <div className="dashboard-card">
            <div>
              <p>02</p>
              <h3>Analyze</h3>
              <span>Assess disaster</span>
            </div>
          </div>

          <div className="dashboard-card">
            <div>
              <p>03</p>
              <h3>Allocate</h3>
              <span>Select drones</span>
            </div>
          </div>

          <div className="dashboard-card">
            <div>
              <p>04</p>
              <h3>Plan</h3>
              <span>Calculate paths</span>
            </div>
          </div>

          <div className="dashboard-card">
            <div>
              <p>05</p>
              <h3>Deploy</h3>
              <span>Begin operation</span>
            </div>
          </div>

        </div>

      </section>

    </main>
  );
}

export default Missions;
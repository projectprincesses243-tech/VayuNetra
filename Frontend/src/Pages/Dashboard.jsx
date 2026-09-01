import { useLiveState } from "../hooks/useLiveState";

function Dashboard() {
  const state = useLiveState();

  // Prevent crash while the WebSocket is connecting
  if (!state) {
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
            Connecting to Swarm...
          </div>
        </section>
      </main>
    );
  }

  // =========================
  // LIVE DATA
  // =========================

  const drones = state.drones || [];
  const survivors = state.survivors || [];
  const metrics = state.metrics || {};
  const events = state.events || [];

  const totalDrones = drones.length;

  const activeDrones = drones.filter(
    (drone) => drone.alive && drone.state === "ACTIVE"
  ).length;

  const aliveDrones = drones.filter(
    (drone) => drone.alive
  ).length;

  const rescued = metrics.rescued ?? 0;
  const detected = metrics.detected ?? 0;
  const coverage = metrics.coverage ?? 0;

  const recentEvents = events.slice(-3).reverse();

  return (
    <main className="dashboard">

      {/* =========================
          HERO
      ========================== */}

      <section className="hero-section">

        <div>
          <p className="eyebrow">
            AUTONOMOUS DISASTER RESPONSE
          </p>

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

          {state.complete
            ? "Operation Complete"
            : "Live Swarm Simulation"}

        </div>

      </section>


      {/* =========================
          LIVE METRICS
      ========================== */}

      <section className="dashboard-grid">

        <div className="dashboard-card">

          <div className="card-icon">
            🚨
          </div>

          <div>

            <p>
              SURVIVORS
            </p>

            <h3>
              {survivors.length}
            </h3>

            <span>
              Detected in simulation
            </span>

          </div>

        </div>


        <div className="dashboard-card">

          <div className="card-icon">
            🚁
          </div>

          <div>

            <p>
              DRONE FLEET
            </p>

            <h3>
              {totalDrones}
            </h3>

            <span>
              {aliveDrones} currently operational
            </span>

          </div>

        </div>


        <div className="dashboard-card">

          <div className="card-icon">
            📡
          </div>

          <div>

            <p>
              ACTIVE DRONES
            </p>

            <h3>
              {activeDrones}
            </h3>

            <span>
              Participating in operation
            </span>

          </div>

        </div>


        <div className="dashboard-card">

          <div className="card-icon">
            👁️
          </div>

          <div>

            <p>
              PERCEPTION
            </p>

            <h3>
              {detected}
            </h3>

            <span>
              Detections reported
            </span>

          </div>

        </div>

      </section>


      {/* =========================
          OPERATIONAL AREA
      ========================== */}

      <section className="operation-grid">

        <div className="map-panel">

          <div className="panel-header">

            <div>

              <p>
                OPERATIONAL AREA
              </p>

              <h3>
                Live Mission Status
              </h3>

            </div>

            <span className="map-status">

              ● {state.complete
                ? "COMPLETE"
                : "LIVE"}

            </span>

          </div>


          <div className="map-placeholder">

            <div className="map-message">

              <div className="map-pin">
                ⌖
              </div>

              <h3>
                Swarm Operation Active
              </h3>

              <p>
                Coverage: {Number(coverage).toFixed(1)}%
              </p>

              <p>
                Rescued: {rescued}
              </p>

              <p>
                Simulation Tick: {state.tick}
              </p>

            </div>

          </div>

        </div>


        {/* =========================
            LIVE EVENTS
        ========================== */}

        <div className="actions-panel">

          <div className="panel-header">

            <div>

              <p>
                COMMAND CENTER
              </p>

              <h3>
                Live Events
              </h3>

            </div>

          </div>


          {recentEvents.length > 0 ? (

            recentEvents.map((event, index) => (

              <div
                className="action-item"
                key={index}
              >

                <span className="action-indicator"></span>

                <div>

                  <strong>
                    {typeof event === "string"
                      ? event
                      : event.type || "Simulation event"}
                  </strong>

                  <p>
                    {typeof event === "string"
                      ? ""
                      : event.message || ""}
                  </p>

                </div>

              </div>

            ))

          ) : (

            <div className="action-item">

              <span className="action-indicator waiting"></span>

              <div>

                <strong>
                  Waiting for events
                </strong>

                <p>
                  Swarm communication channel active
                </p>

              </div>

            </div>

          )}

        </div>

      </section>

    </main>
  );
}

export default Dashboard;
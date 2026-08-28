import { drones } from "../data/demoData";


function Drones() {

  // Demo fleet summary
  const totalFleet = 128;
  const available = 94;
  const active = 21;
  const charging = 8;
  const unavailable = 5;


  return (
    <main className="dashboard">

      {/* =========================
          PAGE HEADER
      ========================== */}

      <section className="hero-section">

        <div>

          <p className="eyebrow">
            FLEET MANAGEMENT
          </p>

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


      {/* =========================
          FLEET OVERVIEW
      ========================== */}

      <section className="dashboard-grid">

        <div className="dashboard-card">

          <div className="card-icon">
            🚁
          </div>

          <div>

            <p>
              TOTAL FLEET
            </p>

            <h3>
              {totalFleet}
            </h3>

            <span>
              Registered drone units
            </span>

          </div>

        </div>


        <div className="dashboard-card">

          <div className="card-icon">
            ✓
          </div>

          <div>

            <p>
              AVAILABLE
            </p>

            <h3>
              {available}
            </h3>

            <span>
              Ready for deployment
            </span>

          </div>

        </div>


        <div className="dashboard-card">

          <div className="card-icon">
            ⚡
          </div>

          <div>

            <p>
              ACTIVE
            </p>

            <h3>
              {active}
            </h3>

            <span>
              Currently operating
            </span>

          </div>

        </div>


        <div className="dashboard-card">

          <div className="card-icon">
            🔋
          </div>

          <div>

            <p>
              CHARGING
            </p>

            <h3>
              {charging}
            </h3>

            <span>
              Currently charging
            </span>

          </div>

        </div>

      </section>


      {/* =========================
          FLEET STATUS
      ========================== */}

      <section
        className="map-panel"
        style={{ marginTop: "18px" }}
      >

        <div className="panel-header">

          <div>

            <p>
              SWARM STATUS
            </p>

            <h3>
              Fleet Operations
            </h3>

          </div>


          <span className="map-status">
            {totalFleet} UNITS
          </span>

        </div>


        <div style={{ padding: "25px" }}>

          <div className="action-item">

            <span className="action-indicator"></span>

            <div>

              <strong>
                {available} drones available
              </strong>

              <p>
                Ready for immediate mission allocation
              </p>

            </div>

          </div>


          <div className="action-item">

            <span className="action-indicator"></span>

            <div>

              <strong>
                {active} drones active
              </strong>

              <p>
                Currently assigned to operations
              </p>

            </div>

          </div>


          <div className="action-item">

            <span className="action-indicator waiting"></span>

            <div>

              <strong>
                {charging} drones charging
              </strong>

              <p>
                Returning to operational readiness
              </p>

            </div>

          </div>


          <div className="action-item">

            <span
              className="action-indicator"
              style={{ background: "#64748b" }}
            ></span>

            <div>

              <strong>
                {unavailable} drones unavailable
              </strong>

              <p>
                Offline or undergoing maintenance
              </p>

            </div>

          </div>

        </div>

      </section>


      {/* =========================
          PHYSICAL DEMO FLEET
      ========================== */}

      <section
        className="map-panel"
        style={{ marginTop: "18px" }}
      >

        <div className="panel-header">

          <div>

            <p>
              PROTOTYPE HARDWARE
            </p>

            <h3>
              Physical Demonstration Fleet
            </h3>

          </div>


          <span className="map-status">
            {drones.length} DEMO UNITS
          </span>

        </div>


        <div
          style={{
            padding: "25px",
            display: "grid",
            gap: "10px"
          }}
        >

          {drones.map((drone) => (

            <div
              key={drone.id}
              className="dashboard-card"
              style={{
                display: "grid",
                gridTemplateColumns:
                  "110px 1fr 1fr 140px 120px",
                alignItems: "center",
                gap: "20px"
              }}
            >

              {/* DRONE ID */}

              <div>

                <p>
                  DRONE
                </p>

                <h3>
                  {drone.id}
                </h3>

              </div>


              {/* STATUS */}

              <div>

                <p>
                  STATUS
                </p>

                <strong>
                  {drone.status}
                </strong>

              </div>


              {/* MISSION */}

              <div>

                <p>
                  MISSION
                </p>

                <span>
                  {drone.mission}
                </span>

              </div>


              {/* BATTERY */}

              <div>

                <p>
                  BATTERY
                </p>

                <span>
                  🔋 {drone.battery}%
                </span>

              </div>


              {/* SURVIVORS */}

              <div>

                <p>
                  SURVIVORS
                </p>

                <h3>
                  {drone.survivorsDetected}
                </h3>

              </div>

            </div>

          ))}

        </div>

      </section>


      {/* =========================
          INTEGRATION INFORMATION
      ========================== */}

      <section
        className="map-panel"
        style={{ marginTop: "18px" }}
      >

        <div
          style={{
            padding: "18px",
            color: "#697386",
            fontSize: "10px"
          }}
        >

          <strong>
            Integration fields:
          </strong>

          {" "}
          Drone ID → Swarm System
          {" | "}
          Status → Simulation
          {" | "}
          Battery → Hardware
          {" | "}
          Mission → Mission Allocation
          {" | "}
          Survivor Count → Perception

        </div>

      </section>

    </main>
  );
}


export default Drones;
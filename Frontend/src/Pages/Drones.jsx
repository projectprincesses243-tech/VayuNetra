import { drones } from "../data/demoData";
import { getActiveOperation } from "../data/operationStorage";


function Drones() {

  // ==========================================
  // GET CURRENT ACTIVE OPERATION
  // ==========================================

  const activeOperation =
    getActiveOperation();


  // ==========================================
  // FLEET COUNTS
  // ==========================================

  const totalFleet = drones.length;

  const available =
    drones.filter(
      drone => drone.status === "AVAILABLE"
    ).length;

  const charging =
    drones.filter(
      drone => drone.status === "CHARGING"
    ).length;

  const unavailable =
    drones.filter(
      drone => drone.status === "UNAVAILABLE"
    ).length;


  // ==========================================
  // ACTIVE DRONES
  // ==========================================
  //
  // If an operation is currently running,
  // use the exact drones allocated to it.
  //
  // Otherwise use the demo ACTIVE drones.
  // ==========================================

  const operationDroneIds =
    activeOperation?.assignedDrones || [];


  const activeDrones =
    operationDroneIds.length > 0

      ? drones.filter(drone =>
          operationDroneIds.includes(drone.id)
        )

      : drones.filter(
          drone => drone.status === "ACTIVE"
        );


  const active =
    activeDrones.length;


  // ==========================================
  // DISPLAY FLEET
  // ==========================================

  const displayDrones =
    drones.map(drone => {

      const operationDrone =
        activeDrones.find(
          activeDrone =>
            activeDrone.id === drone.id
        );


      if (operationDrone) {

        return {

          ...drone,

          status: "ACTIVE",

          mission:
            activeOperation?.operation ||
            activeOperation?.name ||
            drone.mission ||
            "Active Operation"

        };

      }


      return drone;

    });


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


        {/* TOTAL */}

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


        {/* AVAILABLE */}

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


        {/* ACTIVE */}

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


        {/* CHARGING */}

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


          {/* AVAILABLE */}

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


          {/* ACTIVE */}

          <div className="action-item">

            <span className="action-indicator"></span>

            <div>

              <strong>
                {active} drones active
              </strong>

              <p>

                {activeOperation
                  ? `Assigned to ${activeOperation.operation || "active operation"}`
                  : "Currently assigned to operations"}

              </p>

            </div>

          </div>


          {/* CHARGING */}

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


          {/* UNAVAILABLE */}

          <div className="action-item">

            <span
              className="action-indicator"
              style={{
                background: "#64748b"
              }}
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
            {displayDrones.length} DEMO UNITS
          </span>

        </div>


        <div
          style={{
            padding: "25px",
            display: "grid",
            gap: "10px"
          }}
        >

          {displayDrones.map((drone) => (

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
                  {drone.mission || "Station"}
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
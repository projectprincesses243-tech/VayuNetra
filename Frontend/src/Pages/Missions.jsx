import { useState } from "react";
import { missions } from "../data/demoData";

function Missions() {

  /* =========================
     RESCUE REQUESTS
  ========================== */

  const rescueScenarios = missions.map((mission) => ({
    id: mission.id,
    disaster: mission.name
      .replace(" Rescue", "")
      .replace(" Search", "")
      .replace(" Assessment", ""),
    location: mission.area,
    survivors:
      mission.id === "MS-001"
        ? 12
        : mission.id === "MS-002"
        ? 6
        : 5,
    priority: mission.priority,
    dronesRequired:
      mission.id === "MS-001"
        ? 4
        : mission.id === "MS-002"
        ? 5
        : 4,
    description:
      mission.name === "Flood Rescue"
        ? "Flooding reported in a residential area. Multiple people may be stranded on rooftops."
        : mission.name === "Landslide Search"
        ? "Landslide has blocked access roads. Search operation required to locate trapped survivors."
        : "Structural assessment and survivor detection required in the affected area."
  }));


  /* =========================
     STATE
  ========================== */

  const [rescueRequest, setRescueRequest] =
    useState(null);

  const [missionStatus, setMissionStatus] =
    useState("pending");

  const [allocatedDrones, setAllocatedDrones] =
    useState([]);


  /* =========================
     DRONE ROLES
  ========================== */

  const droneRoles = [
    "Search",
    "Search",
    "Thermal Detection",
    "Communication Relay",
    "Search",
    "Thermal Detection",
    "Search",
    "Reserve"
  ];


  /* =========================
     SIMULATE REQUEST
  ========================== */

  const simulateRescueRequest = () => {

    const randomIndex =
      Math.floor(
        Math.random() *
        rescueScenarios.length
      );

    const selectedScenario =
      rescueScenarios[randomIndex];

    setRescueRequest({
      ...selectedScenario,
      time: new Date().toLocaleTimeString()
    });

    setMissionStatus("pending");

    setAllocatedDrones([]);
  };


  /* =========================
     ACCEPT MISSION
  ========================== */

  const acceptMission = () => {

    if (!rescueRequest) {
      return;
    }

    const required =
      Number(
        rescueRequest.dronesRequired
      ) || 4;

    const drones = [];

    for (let i = 0; i < required; i++) {

      drones.push({

        id:
          `DR-${String(i + 1).padStart(3, "0")}`,

        role:
          droneRoles[
            i % droneRoles.length
          ],

        status: "Allocated",

        battery:
          85 +
          Math.floor(
            Math.random() * 15
          ),

        survivors: 0,

        path: "Pending",

        position:
          `Sector ${
            String.fromCharCode(
              65 + (i % 6)
            )
          }`
      });
    }

    setAllocatedDrones(drones);

    setMissionStatus("accepted");
  };


  /* =========================
     REJECT REQUEST
  ========================== */

  const rejectRequest = () => {

    setRescueRequest(null);

    setMissionStatus("pending");

    setAllocatedDrones([]);
  };


  /* =========================
     START MISSION
  ========================== */

  const startMission = () => {

    setMissionStatus("active");

    setAllocatedDrones(
      previousDrones =>
        previousDrones.map(
          drone => ({

            ...drone,

            status:
              drone.role === "Search"
                ? "Searching"
                : drone.role ===
                  "Thermal Detection"
                ? "Scanning"
                : drone.role ===
                  "Communication Relay"
                ? "Relaying"
                : "Standby"

          })
        )
    );
  };


  /* =========================
     RENDER
  ========================== */

  return (

    <main className="dashboard">

      {/* =========================
          PAGE HEADER
      ========================== */}

      <section className="hero-section">

        <div>

          <p className="eyebrow">
            MISSION CONTROL
          </p>

          <h2>
            Rescue <span>Operations</span>
          </h2>

          <p className="hero-description">
            Receive, evaluate and coordinate
            disaster rescue missions using
            the VayuNetra drone swarm.
          </p>

        </div>


        <div className="mission-status">

          <span className="status-dot"></span>

          {missionStatus === "active"
            ? "Mission Active"
            : missionStatus === "accepted"
            ? "Mission Accepted"
            : rescueRequest
            ? "Rescue Request Received"
            : "Awaiting Rescue Request"}

        </div>

      </section>


      {/* =========================
          INCOMING REQUEST
      ========================== */}

      <section
        className="map-panel"
        style={{ marginTop: "18px" }}
      >

        <div className="panel-header">

          <div>

            <p>
              RESCUE COMMUNICATION
            </p>

            <h3>
              Incoming Request
            </h3>

          </div>


          <span className="map-status">

            ●{" "}

            {rescueRequest
              ? "REQUEST RECEIVED"
              : "LISTENING"}

          </span>

        </div>


        {/* NO REQUEST */}

        {!rescueRequest && (

          <div
            style={{
              padding: "30px"
            }}
          >

            <div
              style={{
                padding: "25px",
                border:
                  "1px dashed rgba(255,255,255,0.12)",
                borderRadius: "14px",
                textAlign: "center"
              }}
            >

              <div
                style={{
                  fontSize: "35px",
                  marginBottom: "12px"
                }}
              >
                📡
              </div>


              <h3>
                No Rescue Request Received
              </h3>


              <p
                style={{
                  color: "#697386",
                  fontSize: "13px",
                  marginTop: "8px"
                }}
              >
                VayuNetra is monitoring the
                rescue communication channel
                for a new emergency request.
              </p>


              <button
                type="button"
                onClick={
                  simulateRescueRequest
                }
                style={{
                  marginTop: "16px",
                  cursor: "pointer"
                }}
              >
                Simulate Rescue Request
              </button>

            </div>

          </div>

        )}


        {/* REQUEST RECEIVED */}

        {rescueRequest && (

          <div
            style={{
              padding: "20px"
            }}
          >

            {/* REQUEST DETAILS */}

            <div
              style={{
                display: "grid",
                gridTemplateColumns:
                  "repeat(3, 1fr)",
                gap: "12px"
              }}
            >

              <div className="dashboard-card">

                <div>

                  <p>
                    REQUEST ID
                  </p>

                  <h3>
                    {rescueRequest.id}
                  </h3>

                  <span>
                    Emergency request
                  </span>

                </div>

              </div>


              <div className="dashboard-card">

                <div>

                  <p>
                    DISASTER
                  </p>

                  <h3>
                    {rescueRequest.disaster}
                  </h3>

                  <span>
                    Incident type
                  </span>

                </div>

              </div>


              <div className="dashboard-card">

                <div>

                  <p>
                    LOCATION
                  </p>

                  <h3>
                    {rescueRequest.location}
                  </h3>

                  <span>
                    Emergency sector
                  </span>

                </div>

              </div>


              <div className="dashboard-card">

                <div>

                  <p>
                    SURVIVORS
                  </p>

                  <h3>
                    {rescueRequest.survivors}
                  </h3>

                  <span>
                    Estimated survivors
                  </span>

                </div>

              </div>


              <div className="dashboard-card">

                <div>

                  <p>
                    PRIORITY
                  </p>

                  <h3>
                    {rescueRequest.priority}
                  </h3>

                  <span>
                    Mission priority
                  </span>

                </div>

              </div>


              <div className="dashboard-card">

                <div>

                  <p>
                    DRONES REQUIRED
                  </p>

                  <h3>
                    {rescueRequest.dronesRequired}
                  </h3>

                  <span>
                    Initial estimate
                  </span>

                </div>

              </div>

            </div>


            {/* DESCRIPTION */}

            <div
              style={{
                marginTop: "14px",
                padding: "14px",
                borderRadius: "10px",
                background:
                  "rgba(255,255,255,0.025)",
                border:
                  "1px solid rgba(255,255,255,0.06)"
              }}
            >

              <p
                style={{
                  margin: "0 0 5px",
                  fontSize: "9px",
                  letterSpacing: "1px",
                  color: "#858da5"
                }}
              >
                INCIDENT DESCRIPTION
              </p>

              <span
                style={{
                  color: "#aeb3c7",
                  fontSize: "11px"
                }}
              >
                {rescueRequest.description}
              </span>

            </div>


            {/* ACTIONS */}

            <div
              style={{
                display: "flex",
                justifyContent:
                  "space-between",
                alignItems: "center",
                marginTop: "15px"
              }}
            >

              <div>

                <p
                  style={{
                    margin: 0,
                    fontSize: "9px",
                    letterSpacing: "1px",
                    color: "#858da5"
                  }}
                >
                  REQUEST TIME
                </p>

                <span
                  style={{
                    fontSize: "12px",
                    color: "#aeb3c7"
                  }}
                >
                  {rescueRequest.time}
                </span>

              </div>


              <div
                style={{
                  display: "flex",
                  gap: "10px"
                }}
              >

                <button
                  type="button"
                  onClick={rejectRequest}
                  style={{
                    cursor: "pointer"
                  }}
                >
                  Reject
                </button>


                {missionStatus === "pending" && (

                  <button
                    type="button"
                    onClick={acceptMission}
                    style={{
                      cursor: "pointer"
                    }}
                  >
                    Accept Mission
                  </button>

                )}

              </div>

            </div>

          </div>

        )}

      </section>


      {/* =========================
          DRONE ALLOCATION
      ========================== */}

      {missionStatus !== "pending" &&
        allocatedDrones.length > 0 && (

        <section
          className="map-panel"
          style={{
            marginTop: "18px"
          }}
        >

          <div className="panel-header">

            <div>

              <p>
                SWARM MANAGEMENT
              </p>

              <h3>
                Drone Allocation
              </h3>

            </div>


            <span className="map-status">

              ●{" "}
              {allocatedDrones.length}
              {" "}DRONES

            </span>

          </div>


          <div
            style={{
              padding: "20px"
            }}
          >

            {/* SUMMARY */}

            <div
              style={{
                display: "grid",
                gridTemplateColumns:
                  "repeat(4, 1fr)",
                gap: "10px",
                marginBottom: "15px"
              }}
            >

              <div className="dashboard-card">

                <div>

                  <p>
                    ALLOCATED
                  </p>

                  <h3>
                    {allocatedDrones.length}
                  </h3>

                  <span>
                    Mission drones
                  </span>

                </div>

              </div>


              <div className="dashboard-card">

                <div>

                  <p>
                    ACTIVE
                  </p>

                  <h3>
                    {missionStatus === "active"
                      ? allocatedDrones.length
                      : 0}
                  </h3>

                  <span>
                    Currently operating
                  </span>

                </div>

              </div>


              <div className="dashboard-card">

                <div>

                  <p>
                    SURVIVORS
                  </p>

                  <h3>
                    {allocatedDrones.reduce(
                      (total, drone) =>
                        total +
                        drone.survivors,
                      0
                    )}
                  </h3>

                  <span>
                    Detected
                  </span>

                </div>

              </div>


              <div className="dashboard-card">

                <div>

                  <p>
                    SWARM STATUS
                  </p>

                  <h3>
                    {missionStatus === "active"
                      ? "ACTIVE"
                      : "READY"}
                  </h3>

                  <span>
                    Operation state
                  </span>

                </div>

              </div>

            </div>


            {/* DRONE TABLE */}

            <div
              style={{
                width: "100%",
                overflowX: "auto",
                border:
                  "1px solid rgba(255,255,255,0.07)",
                borderRadius: "10px"
              }}
            >

              <table
                style={{
                  width: "100%",
                  borderCollapse:
                    "collapse",
                  minWidth: "850px",
                  fontSize: "11px"
                }}
              >

                <thead>

                  <tr
                    style={{
                      textAlign: "left",
                      borderBottom:
                        "1px solid rgba(255,255,255,0.08)"
                    }}
                  >

                    <th style={thStyle}>
                      DRONE
                    </th>

                    <th style={thStyle}>
                      ROLE
                    </th>

                    <th style={thStyle}>
                      STATUS
                    </th>

                    <th style={thStyle}>
                      BATTERY
                    </th>

                    <th style={thStyle}>
                      SURVIVORS
                    </th>

                    <th style={thStyle}>
                      PATH
                    </th>

                    <th style={thStyle}>
                      POSITION
                    </th>

                  </tr>

                </thead>


                <tbody>

                  {allocatedDrones.map(
                    drone => (

                    <tr
                      key={drone.id}
                      style={{
                        borderBottom:
                          "1px solid rgba(255,255,255,0.05)"
                      }}
                    >

                      <td style={tdStyle}>
                        <strong>
                          {drone.id}
                        </strong>
                      </td>

                      <td style={tdStyle}>
                        {drone.role}
                      </td>

                      <td style={tdStyle}>
                        {drone.status}
                      </td>

                      <td style={tdStyle}>
                        {drone.battery}%
                      </td>

                      <td style={tdStyle}>
                        {drone.survivors}
                      </td>

                      <td style={tdStyle}>
                        {drone.path}
                      </td>

                      <td style={tdStyle}>
                        {drone.position}
                      </td>

                    </tr>

                  ))}

                </tbody>

              </table>

            </div>


            {/* INTEGRATION NOTE */}

            <div
              style={{
                marginTop: "12px",
                padding: "12px",
                borderRadius: "8px",
                border:
                  "1px dashed rgba(255,255,255,0.08)",
                color: "#697386",
                fontSize: "10px"
              }}
            >

              <strong>
                Integration fields:
              </strong>

              {" "}
              Position → Localisation
              {" | "}
              Path → Path Planning
              {" | "}
              Status → Simulation
              {" | "}
              Survivors → Perception

            </div>


            {/* START MISSION */}

            {missionStatus === "accepted" && (

              <div
                style={{
                  textAlign: "right",
                  marginTop: "18px"
                }}
              >

                <button
                  type="button"
                  onClick={startMission}
                  style={{
                    cursor: "pointer"
                  }}
                >
                  Start Mission
                </button>

              </div>

            )}

          </div>

        </section>

      )}


      {/* =========================
          MISSION CONFIGURATION
      ========================== */}

      <section className="operation-grid">

        <div className="dashboard-card">

          <div className="card-icon">
            🤖
          </div>

          <div>

            <p>
              AUTONOMOUS MODE
            </p>

            <h3>
              Automatic Deployment
            </h3>

            <span>
              Let VayuNetra calculate the
              required number of drones and
              deployment strategy.
            </span>

          </div>

        </div>


        <div className="dashboard-card">

          <div className="card-icon">
            👤
          </div>

          <div>

            <p>
              ADMIN CONTROL
            </p>

            <h3>
              Manual Deployment
            </h3>

            <span>
              Allow an operator to specify
              the number of drones for the
              mission.
            </span>

          </div>

        </div>

      </section>


      {/* =========================
          MISSION PIPELINE
      ========================== */}

      <section
        className="map-panel"
        style={{
          marginTop: "18px"
        }}
      >

        <div className="panel-header">

          <div>

            <p>
              MISSION PIPELINE
            </p>

            <h3>
              Operation Flow
            </h3>

          </div>

        </div>


        <div className="mission-flow">

          <div className="mission-step">

            <div className="mission-step-number">
              01
            </div>

            <h3>
              Request
            </h3>

            <p>
              Emergency received
            </p>

          </div>


          <div className="mission-step">

            <div className="mission-step-number">
              02
            </div>

            <h3>
              Analyze
            </h3>

            <p>
              Assess disaster
            </p>

          </div>


          <div className="mission-step">

            <div className="mission-step-number">
              03
            </div>

            <h3>
              Allocate
            </h3>

            <p>
              Select drones
            </p>

          </div>


          <div className="mission-step">

            <div className="mission-step-number">
              04
            </div>

            <h3>
              Plan
            </h3>

            <p>
              Calculate paths
            </p>

          </div>


          <div className="mission-step">

            <div className="mission-step-number">
              05
            </div>

            <h3>
              Deploy
            </h3>

            <p>
              Begin operation
            </p>

          </div>

        </div>

      </section>

    </main>
  );
}


/* =========================
   TABLE STYLES
========================= */

const thStyle = {
  padding: "12px",
  color: "#858da5",
  fontSize: "9px",
  letterSpacing: "0.8px",
  fontWeight: "600",
  whiteSpace: "nowrap"
};

const tdStyle = {
  padding: "12px",
  color: "#aeb3c7",
  whiteSpace: "nowrap"
};


export default Missions;
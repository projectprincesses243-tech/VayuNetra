import { useEffect, useState } from "react";

import { missions, drones } from "../data/demoData";

import {
  getActiveOperation,
  saveActiveOperation,
  clearActiveOperation,
  addToHistory
} from "../data/operationStorage";


function Missions() {

  /* =========================
     RESCUE REQUESTS
  ========================== */

  const rescueScenarios = missions.map((mission) => ({

    id: mission.id,

    disaster:
      mission.name
        .replace(" Rescue", "")
        .replace(" Search", "")
        .replace(" Assessment", ""),

    location:
      mission.area,

    survivors:
      mission.id === "MS-001"
        ? 12
        : mission.id === "MS-002"
        ? 6
        : 5,

    priority:
      mission.priority,

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

  const [activeOperation, setActiveOperation] =
    useState(null);


  /* =========================
     STOP CONFIRMATION
  ========================== */

  const [showStopConfirm, setShowStopConfirm] =
    useState(false);

  const [showFinalStopConfirm, setShowFinalStopConfirm] =
    useState(false);


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
     LOAD ACTIVE OPERATION
  ========================== */

  useEffect(() => {

    const savedOperation =
      getActiveOperation();

    if (!savedOperation) {
      return;
    }


    setActiveOperation(
      savedOperation
    );

    setMissionStatus(
      "active"
    );


    /*
      Rebuild the allocated drone
      table using the SAME real
      drone IDs saved in the operation.
    */

    const restoredDrones =
      (savedOperation.assignedDrones || [])
        .map((droneId, index) => {

          const originalDrone =
            drones.find(
              drone =>
                drone.id === droneId
            );


          return {

            id:
              droneId,

            role:
              droneRoles[
                index %
                droneRoles.length
              ],

            status:
              "Searching",

            battery:
              originalDrone?.battery ??
              90,

            survivors:
              originalDrone?.survivorsDetected ??
              0,

            path:
              "Active",

            position:
              originalDrone
                ? `${originalDrone.latitude}, ${originalDrone.longitude}`
                : `Sector ${
                    String.fromCharCode(
                      65 + (index % 6)
                    )
                  }`

          };

        });


    setAllocatedDrones(
      restoredDrones
    );

  }, []);


  /* =========================
     SIMULATE REQUEST
  ========================== */

  const simulateRescueRequest = () => {

    /*
      Do not create another
      request while an operation
      is already active.
    */

    if (activeOperation) {
      return;
    }


    const randomIndex =
      Math.floor(
        Math.random() *
        rescueScenarios.length
      );


    const selectedScenario =
      rescueScenarios[randomIndex];


    setRescueRequest({

      ...selectedScenario,

      time:
        new Date().toLocaleTimeString()

    });


    setMissionStatus(
      "pending"
    );

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


    /*
      IMPORTANT FIX
      ---------------
      Only take drones whose
      current fleet status is
      AVAILABLE.

      This prevents us from
      accidentally allocating:

      ACTIVE
      CHARGING
      UNAVAILABLE

      drones.
    */

    const availableDrones =
      drones
        .filter(
          drone =>
            drone.status === "AVAILABLE"
        )
        .slice(
          0,
          required
        );


    /*
      Safety check.
    */

    if (
      availableDrones.length <
      required
    ) {

      alert(
        `Only ${availableDrones.length} drones are currently available.`
      );

      return;

    }


    /*
      Build the allocated drone
      records using the ACTUAL
      drone objects from demoData.
    */

    const allocated =
      availableDrones.map(
        (drone, index) => ({

          id:
            drone.id,

          role:
            droneRoles[
              index %
              droneRoles.length
            ],

          status:
            "Allocated",

          battery:
            drone.battery ?? 90,

          survivors:
            drone.survivorsDetected ?? 0,

          path:
            "Pending",

          position:
            `${drone.latitude}, ${drone.longitude}`

        })
      );


    setAllocatedDrones(
      allocated
    );


    setMissionStatus(
      "accepted"
    );

  };


  /* =========================
     REJECT REQUEST
  ========================== */

  const rejectRequest = () => {

    setRescueRequest(null);

    setMissionStatus(
      "pending"
    );

    setAllocatedDrones([]);

  };


  /* =========================
     START MISSION
  ========================== */

  const startMission = () => {

    if (
      !rescueRequest ||
      allocatedDrones.length === 0
    ) {
      return;
    }


    /*
      UNIQUE OPERATION ID
    */

    const operationId =
      `OP-${Date.now()}`;


    /*
      Create operation record.
    */

    const operation = {

      id:
        operationId,

      requestId:
        rescueRequest.id,

      operation:
        `${rescueRequest.disaster} Rescue`,

      disaster:
        rescueRequest.disaster,

      location:
        rescueRequest.location,

      survivors:
        rescueRequest.survivors,

      priority:
        rescueRequest.priority,

      dronesRequired:
        allocatedDrones.length,

      /*
        IMPORTANT:
        These are the ACTUAL
        drone IDs allocated above.
      */

      assignedDrones:
        allocatedDrones.map(
          drone => drone.id
        ),

      progress:
        0,

      status:
        "ACTIVE",

      startedAt:
        new Date().toISOString()

    };


    /*
      Save immediately.

      Refreshing the browser will
      therefore NOT remove the mission.
    */

    saveActiveOperation(
      operation
    );


    setActiveOperation(
      operation
    );


    setMissionStatus(
      "active"
    );


    /*
      Change allocated drone
      display status.
    */

    setAllocatedDrones(
      previousDrones =>

        previousDrones.map(
          drone => ({

            ...drone,

            status:
              drone.role === "Search"
                ? "Searching"
                : drone.role === "Thermal Detection"
                ? "Scanning"
                : drone.role === "Communication Relay"
                ? "Relaying"
                : "Standby"

          })
        )

    );

  };


  /* =========================
     MISSION PROGRESS
  ========================== */

  useEffect(() => {

    if (
      !activeOperation ||
      activeOperation.status !== "ACTIVE"
    ) {
      return;
    }


    /*
      Demo progress:

      +1% every 3 seconds.

      Later this can be replaced
      by simulation progress.
    */

    const timer =
      setInterval(() => {

        setActiveOperation(
          current => {

            if (!current) {
              return null;
            }


            const nextProgress =
              Math.min(
                Number(
                  current.progress || 0
                ) + 1,
                100
              );


            /* =========================
               COMPLETED
            ========================== */

            if (
              nextProgress >= 100
            ) {

              const completedOperation = {

                ...current,

                progress:
                  100,

                status:
                  "COMPLETED",

                completedAt:
                  new Date().toISOString()

              };


              /*
                Move completed operation
                into History.
              */

              addToHistory(
                completedOperation
              );


              /*
                Remove active operation.
              */

              clearActiveOperation();


              setMissionStatus(
                "pending"
              );


              setAllocatedDrones(
                []
              );


              setRescueRequest(
                null
              );


              return null;

            }


            /* =========================
               UPDATE PROGRESS
            ========================== */

            const updatedOperation = {

              ...current,

              progress:
                nextProgress

            };


            saveActiveOperation(
              updatedOperation
            );


            return updatedOperation;

          }
        );

      }, 3000);


    return () =>
      clearInterval(timer);

  }, [activeOperation?.id]);


  /* =========================
     STOP MISSION
  ========================== */

  const handleStopMission = () => {

    if (!activeOperation) {
      return;
    }

    setShowStopConfirm(
      true
    );

  };


  /* =========================
     FIRST CONFIRMATION
  ========================== */

  const continueStopMission = () => {

    setShowStopConfirm(
      false
    );

    setShowFinalStopConfirm(
      true
    );

  };


  /* =========================
     FINAL STOP
  ========================== */

  const confirmStopMission = () => {

    if (!activeOperation) {
      return;
    }


    const stoppedOperation = {

      ...activeOperation,

      status:
        "STOPPED",

      stoppedAt:
        new Date().toISOString()

    };


    /*
      Save stopped operation
      to History.
    */

    addToHistory(
      stoppedOperation
    );


    /*
      Remove from active storage.
    */

    clearActiveOperation();


    setActiveOperation(
      null
    );


    setMissionStatus(
      "pending"
    );


    setAllocatedDrones(
      []
    );


    setRescueRequest(
      null
    );


    setShowFinalStopConfirm(
      false
    );

  };


  /* =========================
     CANCEL STOP
  ========================== */

  const cancelStop = () => {

    setShowStopConfirm(
      false
    );

    setShowFinalStopConfirm(
      false
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
          ACTIVE OPERATION
      ========================== */}

      {activeOperation && (

        <section
          className="map-panel"
          style={{
            marginTop: "18px"
          }}
        >

          <div className="panel-header">

            <div>

              <p>
                ACTIVE OPERATION
              </p>

              <h3>
                {activeOperation.operation}
              </h3>

            </div>


            <span className="map-status">
              {activeOperation.id}
            </span>

          </div>


          <div
            style={{
              padding: "20px"
            }}
          >


            {/* =========================
                OPERATION DETAILS
            ========================== */}

            <div
              style={{
                display: "grid",
                gridTemplateColumns:
                  "repeat(4, 1fr)",
                gap: "10px"
              }}
            >


              <div className="dashboard-card">

                <div>

                  <p>
                    DISASTER
                  </p>

                  <h3>
                    {activeOperation.disaster}
                  </h3>

                </div>

              </div>


              <div className="dashboard-card">

                <div>

                  <p>
                    LOCATION
                  </p>

                  <h3>
                    {activeOperation.location}
                  </h3>

                </div>

              </div>


              <div className="dashboard-card">

                <div>

                  <p>
                    ACTIVE DRONES
                  </p>

                  <h3>
                    {
                      activeOperation
                        .assignedDrones
                        .length
                    }
                  </h3>

                </div>

              </div>


              <div className="dashboard-card">

                <div>

                  <p>
                    SURVIVORS
                  </p>

                  <h3>
                    {activeOperation.survivors}
                  </h3>

                </div>

              </div>

            </div>


            {/* =========================
                PROGRESS
            ========================== */}

            <div
              style={{
                marginTop: "20px"
              }}
            >

              <div
                style={{
                  display: "flex",
                  justifyContent:
                    "space-between",
                  alignItems: "center",
                  marginBottom: "8px"
                }}
              >

                <strong>
                  OPERATION PROGRESS
                </strong>

                <strong>
                  {activeOperation.progress}%
                </strong>

              </div>


              <div
                style={{
                  width: "100%",
                  height: "10px",
                  background:
                    "rgba(255,255,255,0.08)",
                  borderRadius: "10px",
                  overflow: "hidden"
                }}
              >

                <div
                  style={{
                    width:
                      `${activeOperation.progress}%`,
                    height: "100%",
                    background:
                      "#8b5cf6",
                    borderRadius: "10px",
                    transition:
                      "width 0.4s ease"
                  }}
                />

              </div>

            </div>


            {/* =========================
                DEPLOYED DRONES
            ========================== */}

            <div
              style={{
                marginTop: "20px"
              }}
            >

              <p>
                DEPLOYED UNITS
              </p>


              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "8px"
                }}
              >

                {(
                  activeOperation.assignedDrones ||
                  []
                ).map(
                  droneId => (

                    <span
                      key={droneId}
                      style={{
                        padding:
                          "7px 10px",
                        borderRadius:
                          "6px",
                        background:
                          "rgba(139,92,246,0.12)",
                        border:
                          "1px solid rgba(139,92,246,0.25)",
                        fontSize: "10px"
                      }}
                    >
                      🚁 {droneId}
                    </span>

                  )
                )}

              </div>

            </div>


            {/* =========================
                STOP BUTTON
            ========================== */}

            <div
              style={{
                display: "flex",
                justifyContent:
                  "flex-end",
                marginTop: "22px"
              }}
            >

              <button
                type="button"
                onClick={
                  handleStopMission
                }
                style={{
                  cursor: "pointer",
                  padding:
                    "10px 18px",
                  borderRadius: "7px",
                  border:
                    "1px solid rgba(255,80,80,0.5)",
                  background:
                    "rgba(255,80,80,0.10)",
                  color: "#ff7777",
                  fontWeight: "600"
                }}
              >
                ⏹ STOP MISSION
              </button>

            </div>

          </div>

        </section>

      )}


      {/* =========================
          INCOMING REQUEST
      ========================== */}

      {!activeOperation && (

        <section
          className="map-panel"
          style={{
            marginTop: "18px"
          }}
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


          {/* =========================
              NO REQUEST
          ========================== */}

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


          {/* =========================
              REQUEST RECEIVED
          ========================== */}

          {rescueRequest && (

            <div
              style={{
                padding: "20px"
              }}
            >

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns:
                    "repeat(4, 1fr)",
                  gap: "10px"
                }}
              >


                <div className="dashboard-card">

                  <div>

                    <p>
                      DISASTER
                    </p>

                    <h3>
                      {rescueRequest.disaster}
                    </h3>

                    <span>
                      Emergency type
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
                      Affected area
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
                    margin:
                      "0 0 5px",
                    fontSize: "9px",
                    letterSpacing:
                      "1px",
                    color:
                      "#858da5"
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
                  alignItems:
                    "center",
                  marginTop: "15px"
                }}
              >

                <div>

                  <p
                    style={{
                      margin: 0,
                      fontSize: "9px",
                      letterSpacing:
                        "1px",
                      color:
                        "#858da5"
                    }}
                  >
                    REQUEST TIME
                  </p>

                  <span
                    style={{
                      fontSize: "12px",
                      color:
                        "#aeb3c7"
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
                    onClick={
                      rejectRequest
                    }
                    style={{
                      cursor:
                        "pointer"
                    }}
                  >
                    Reject
                  </button>


                  {missionStatus ===
                    "pending" && (

                    <button
                      type="button"
                      onClick={
                        acceptMission
                      }
                      style={{
                        cursor:
                          "pointer"
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

      )}


      {/* =========================
          DRONE ALLOCATION
      ========================== */}

      {!activeOperation &&
        missionStatus !== "pending" &&
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
                gap: "10px"
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
                    Available fleet units
                  </span>

                </div>

              </div>


              <div className="dashboard-card">

                <div>

                  <p>
                    SEARCH
                  </p>

                  <h3>
                    {
                      allocatedDrones.filter(
                        drone =>
                          drone.role ===
                          "Search"
                      ).length
                    }
                  </h3>

                  <span>
                    Search units
                  </span>

                </div>

              </div>


              <div className="dashboard-card">

                <div>

                  <p>
                    THERMAL
                  </p>

                  <h3>
                    {
                      allocatedDrones.filter(
                        drone =>
                          drone.role ===
                          "Thermal Detection"
                      ).length
                    }
                  </h3>

                  <span>
                    Thermal units
                  </span>

                </div>

              </div>


              <div className="dashboard-card">

                <div>

                  <p>
                    RELAY
                  </p>

                  <h3>
                    {
                      allocatedDrones.filter(
                        drone =>
                          drone.role ===
                          "Communication Relay"
                      ).length
                    }
                  </h3>

                  <span>
                    Communication units
                  </span>

                </div>

              </div>

            </div>


            {/* DRONE TABLE */}

            <div
              style={{
                width: "100%",
                overflowX: "auto",
                marginTop: "18px",
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
                        🔋 {drone.battery}%
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


            {/* START */}

            {missionStatus ===
              "accepted" && (

              <div
                style={{
                  display: "flex",
                  justifyContent:
                    "flex-end",
                  marginTop: "20px"
                }}
              >

                <button
                  type="button"
                  onClick={
                    startMission
                  }
                  style={{
                    cursor:
                      "pointer",
                    padding:
                      "11px 20px",
                    borderRadius:
                      "7px",
                    fontWeight:
                      "600"
                  }}
                >
                  🚁 START MISSION
                </button>

              </div>

            )}

          </div>

        </section>

      )}


      {/* =========================
          MISSION FLOW
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
              OPERATIONAL WORKFLOW
            </p>

            <h3>
              Mission Flow
            </h3>

          </div>

        </div>


        <div
          className="mission-flow"
        >

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
              Select available drones
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


      {/* =========================
          FIRST STOP CONFIRMATION
      ========================== */}

      {showStopConfirm && (

        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 9999,
            background:
              "rgba(0,0,0,0.75)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px"
          }}
        >

          <div
            style={{
              width: "100%",
              maxWidth: "430px",
              background: "#15131f",
              border:
                "1px solid rgba(255,255,255,0.1)",
              borderRadius: "12px",
              padding: "25px"
            }}
          >

            <div
              style={{
                fontSize: "28px",
                marginBottom: "10px"
              }}
            >
              ⚠️
            </div>


            <h3>
              Stop Operation?
            </h3>


            <p
              style={{
                color: "#9aa1b5",
                lineHeight: "1.6",
                fontSize: "12px"
              }}
            >
              You are attempting to stop
              an active rescue operation.
              This may interrupt drone
              deployment and survivor
              search activities.
            </p>


            <div
              style={{
                display: "flex",
                justifyContent:
                  "flex-end",
                gap: "10px",
                marginTop: "20px"
              }}
            >

              <button
                type="button"
                onClick={
                  cancelStop
                }
              >
                CANCEL
              </button>


              <button
                type="button"
                onClick={
                  continueStopMission
                }
              >
                CONTINUE
              </button>

            </div>

          </div>

        </div>

      )}


      {/* =========================
          SECOND STOP CONFIRMATION
      ========================== */}

      {showFinalStopConfirm && (

        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 10000,
            background:
              "rgba(0,0,0,0.80)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px"
          }}
        >

          <div
            style={{
              width: "100%",
              maxWidth: "430px",
              background: "#15131f",
              border:
                "1px solid rgba(255,80,80,0.4)",
              borderRadius: "12px",
              padding: "25px"
            }}
          >

            <div
              style={{
                fontSize: "28px",
                marginBottom: "10px"
              }}
            >
              🛑
            </div>


            <h3>
              Confirm Operation Stop
            </h3>


            <p
              style={{
                color: "#9aa1b5",
                lineHeight: "1.6",
                fontSize: "12px"
              }}
            >
              This will terminate the active
              operation and move its complete
              record to Mission History.
            </p>


            <div
              style={{
                marginTop: "20px",
                padding: "12px",
                borderRadius: "8px",
                background:
                  "rgba(255,255,255,0.03)"
              }}
            >

              <p
                style={{
                  margin: 0,
                  fontSize: "9px",
                  color: "#858da5"
                }}
              >
                OPERATION ID
              </p>

              <strong
                style={{
                  fontSize: "12px"
                }}
              >
                {activeOperation?.id}
              </strong>

            </div>


            <div
              style={{
                display: "flex",
                justifyContent:
                  "flex-end",
                gap: "10px",
                marginTop: "20px"
              }}
            >

              <button
                type="button"
                onClick={
                  cancelStop
                }
              >
                GO BACK
              </button>


              <button
                type="button"
                onClick={
                  confirmStopMission
                }
                style={{
                  cursor: "pointer",
                  padding:
                    "10px 15px",
                  borderRadius: "6px",
                  background:
                    "#7f1d1d",
                  color: "white",
                  border:
                    "1px solid #ef4444",
                  fontWeight: "600"
                }}
              >
                STOP OPERATION
              </button>

            </div>

          </div>

        </div>

      )}

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
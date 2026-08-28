import { useEffect, useState, useRef } from "react";

import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  Circle,
  useMap
} from "react-leaflet";

import L from "leaflet";

import "leaflet/dist/leaflet.css";

import {
  drones,
  survivors,
  disaster
} from "../data/demoData";

import {
  getActiveOperation
} from "../data/operationStorage";


// ==========================================
// LEAFLET ICON FIX
// ==========================================

delete L.Icon.Default.prototype._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",

  iconUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",

  shadowUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png"
});


// ==========================================
// DRONE ICON
// ==========================================

const droneIcon = L.divIcon({
  className: "drone-marker",

  html: `
    <div style="
      width:34px;
      height:34px;
      border-radius:50%;
      background:#171027;
      border:2px solid #8b5cf6;
      display:flex;
      align-items:center;
      justify-content:center;
      color:white;
      font-size:17px;
      box-shadow:0 0 15px rgba(139,92,246,0.7);
    ">
      🚁
    </div>
  `,

  iconSize: [34, 34],
  iconAnchor: [17, 17]
});


// ==========================================
// DISASTER ICON
// ==========================================

const disasterIcon = L.divIcon({
  className: "disaster-marker",

  html: `
    <div style="
      width:38px;
      height:38px;
      border-radius:50%;
      background:#351313;
      border:2px solid #ff5c5c;
      display:flex;
      align-items:center;
      justify-content:center;
      color:white;
      font-size:18px;
      box-shadow:0 0 18px rgba(255,80,80,0.6);
    ">
      ⚠
    </div>
  `,

  iconSize: [38, 38],
  iconAnchor: [19, 19]
});


// ==========================================
// SURVIVOR ICON
// ==========================================

const survivorIcon = L.divIcon({
  className: "survivor-marker",

  html: `
    <div style="
      width:30px;
      height:30px;
      border-radius:50%;
      background:#102d20;
      border:2px solid #35e88a;
      display:flex;
      align-items:center;
      justify-content:center;
      color:white;
      font-size:15px;
      box-shadow:0 0 15px rgba(53,232,138,0.6);
    ">
      👤
    </div>
  `,

  iconSize: [30, 30],
  iconAnchor: [15, 15]
});


// ==========================================
// MAP RESIZE HANDLER
// ==========================================

function MapResizeHandler({ fullscreen }) {

  const map = useMap();

  useEffect(() => {

    const resizeMap = () => {
      map.invalidateSize();
    };

    resizeMap();

    const timer1 = setTimeout(
      resizeMap,
      100
    );

    const timer2 = setTimeout(
      resizeMap,
      400
    );

    window.addEventListener(
      "resize",
      resizeMap
    );

    return () => {

      clearTimeout(timer1);
      clearTimeout(timer2);

      window.removeEventListener(
        "resize",
        resizeMap
      );

    };

  }, [fullscreen, map]);

  return null;
}


// ==========================================
// MAP FOCUS
// ==========================================

function MapFocus({ selectedDrone }) {

  const map = useMap();

  useEffect(() => {

    if (!selectedDrone) {
      return;
    }

    map.flyTo(
      [
        selectedDrone.latitude,
        selectedDrone.longitude
      ],
      16,
      {
        duration: 1
      }
    );

  }, [selectedDrone, map]);

  return null;
}


// ==========================================
// LIVE MAP
// ==========================================

function LiveMap() {

  const [activeOperation, setActiveOperation] =
    useState(null);

  const [selectedDrone, setSelectedDrone] =
    useState(null);

  const [fullscreen, setFullscreen] =
    useState(false);

  const mapFullscreenRef =
    useRef(null);


  // ========================================
  // LOAD ACTIVE OPERATION
  // ========================================

  useEffect(() => {

    const loadOperation = () => {

      const operation =
        getActiveOperation();

      setActiveOperation(operation);

    };

    loadOperation();

    const interval =
      setInterval(
        loadOperation,
        1000
      );

    return () => {
      clearInterval(interval);
    };

  }, []);


  // ========================================
  // FULLSCREEN CHANGE
  // ========================================

  useEffect(() => {

    const handleFullscreenChange = () => {

      const isFullscreen =
        document.fullscreenElement ===
        mapFullscreenRef.current;

      setFullscreen(isFullscreen);

    };

    document.addEventListener(
      "fullscreenchange",
      handleFullscreenChange
    );

    return () => {

      document.removeEventListener(
        "fullscreenchange",
        handleFullscreenChange
      );

    };

  }, []);


  // ========================================
  // FULLSCREEN
  // ========================================

  const toggleFullscreen = async () => {

    try {

      if (
        document.fullscreenElement ===
        mapFullscreenRef.current
      ) {

        await document.exitFullscreen();

      } else {

        await mapFullscreenRef.current?.requestFullscreen();

      }

    } catch (error) {

      console.error(
        "Fullscreen error:",
        error
      );

    }

  };


  // ========================================
  // GET ALLOCATED DRONE IDS
  // ========================================

  const assignedDroneIds =
    Array.isArray(
      activeOperation?.assignedDrones
    )
      ? activeOperation.assignedDrones
      : [];


  // ========================================
  // ONLY DRONES IN CURRENT OPERATION
  // ========================================

  const activeMissionDrones =
    drones.filter(
      (drone) =>
        assignedDroneIds.includes(
          drone.id
        )
    );


  // ========================================
  // CLEAR INVALID SELECTION
  // ========================================

  useEffect(() => {

    if (!selectedDrone) {
      return;
    }

    const exists =
      activeMissionDrones.some(
        (drone) =>
          drone.id === selectedDrone.id
      );

    if (!exists) {
      setSelectedDrone(null);
    }

  }, [
    activeOperation,
    selectedDrone,
    activeMissionDrones
  ]);


  // ========================================
  // OPERATION NAME
  // ========================================

  const operationName =
    activeOperation?.operation ||
    activeOperation?.name ||
    "No Active Operation";


  // ========================================
  // PAGE
  // ========================================

  return (

    <main className="dashboard">

      {/* ==================================
          HEADER
      ================================== */}

      {!fullscreen && (

        <section className="hero-section">

          <div>

            <p className="eyebrow">
              SWARM NAVIGATION
            </p>

            <h2>
              Live <span>Map</span>
            </h2>

            <p className="hero-description">
              Real-time operational view of the
              VayuNetra drone swarm.
            </p>

          </div>

          <div className="mission-status">

            <span className="status-dot"></span>

            LOCALISATION ONLINE

          </div>

        </section>

      )}


      {/* ==================================
          MAP PANEL
      ================================== */}

      <section
        className={
          fullscreen
            ? "map-panel live-map-panel fullscreen-panel"
            : "map-panel live-map-panel"
        }

        style={{
          marginTop: fullscreen
            ? 0
            : "18px",

          height: fullscreen
            ? "100vh"
            : "calc(100vh - 250px)",

          minHeight: fullscreen
            ? "100vh"
            : "560px"
        }}
      >


        {/* =================================
            NORMAL HEADER
        ================================= */}

        {!fullscreen && (

          <div className="panel-header">

            <div>

              <p>
                GEOSPATIAL MONITORING
              </p>

              <h3>
                Mission Control Map
              </h3>

            </div>

            <span className="map-status">

              {activeMissionDrones.length}
              {" "}
              ACTIVE DRONES

            </span>

          </div>

        )}


        {/* =================================
            MAP + SIDEBAR
        ================================= */}

        <div
          style={{
            display: "grid",

            gridTemplateColumns:
              fullscreen
                ? "1fr"
                : "minmax(0, 3fr) minmax(280px, 1fr)",

            width: "100%",

            height: fullscreen
              ? "100%"
              : "calc(100% - 0px)",

            minHeight: 0
          }}
        >


          {/* =================================
              MAP AREA
          ================================= */}

          <div
            ref={mapFullscreenRef}

            style={{
              position: "relative",

              width: "100%",

              height: fullscreen
                ? "100vh"
                : "100%",

              minHeight: fullscreen
                ? "100vh"
                : "500px",

              overflow: "hidden",

              background: "#0d0b16"
            }}
          >


            {/* =================================
                FULLSCREEN BUTTON
            ================================= */}

            <button
              type="button"

              onClick={toggleFullscreen}

              style={{
                position: "absolute",

                zIndex: 2000,

                top: "12px",

                right: "12px",

                padding: "9px 14px",

                border: "none",

                borderRadius: "7px",

                background: "#7c3aed",

                color: "white",

                fontSize: "10px",

                fontWeight: 700,

                cursor: "pointer",

                boxShadow:
                  "0 5px 18px rgba(0,0,0,0.35)"
              }}
            >

              {fullscreen
                ? "⛶ EXIT FULLSCREEN"
                : "⛶ FULLSCREEN"}

            </button>


            {/* =================================
                OPERATION BADGE
            ================================= */}

            <div
              style={{
                position: "absolute",

                zIndex: 1000,

                top: "12px",

                left: "12px",

                padding: "10px 13px",

                borderRadius: "7px",

                background:
                  "rgba(13,11,22,0.92)",

                border:
                  "1px solid rgba(255,255,255,0.1)",

                color: "white",

                minWidth: "180px",

                backdropFilter: "blur(8px)"
              }}
            >

              <div
                style={{
                  fontSize: "8px",
                  letterSpacing: "1px",
                  color: "#858da5",
                  marginBottom: "3px"
                }}
              >
                CURRENT OPERATION
              </div>

              <strong
                style={{
                  display: "block",
                  fontSize: "12px"
                }}
              >
                {operationName}
              </strong>

              <small
                style={{
                  color: "#697386",
                  fontSize: "9px"
                }}
              >
                {activeMissionDrones.length}
                {" "}
                drones deployed
              </small>

            </div>


            {/* =================================
                MAP
            ================================= */}

            <MapContainer
              center={[
                disaster.latitude,
                disaster.longitude
              ]}

              zoom={14}

              scrollWheelZoom={true}

              style={{
                width: "100%",
                height: "100%",
                minHeight: "100%"
              }}
            >

              <TileLayer
                attribution="&copy; OpenStreetMap contributors"

                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />


              <MapResizeHandler
                fullscreen={fullscreen}
              />


              <MapFocus
                selectedDrone={
                  selectedDrone
                }
              />


              {/* =================================
                  DISASTER
              ================================= */}

              <Marker
                position={[
                  disaster.latitude,
                  disaster.longitude
                ]}

                icon={disasterIcon}
              >

                <Popup>

                  <strong>
                    ACTIVE DISASTER
                  </strong>

                  <br />

                  Type:
                  {" "}
                  {disaster.type}

                  <br />

                  Severity:
                  {" "}
                  {disaster.severity}

                </Popup>

              </Marker>


              {/* =================================
                  MISSION AREA
              ================================= */}

              <Circle
                center={[
                  disaster.latitude,
                  disaster.longitude
                ]}

                radius={1200}

                pathOptions={{
                  color: "#8b5cf6",
                  fillColor: "#8b5cf6",
                  fillOpacity: 0.08
                }}
              />


              {/* =================================
                  SURVIVORS
              ================================= */}

              {survivors.map(
                (survivor) => (

                  <Marker
                    key={
                      survivor.id
                    }

                    position={[
                      survivor.latitude,
                      survivor.longitude
                    ]}

                    icon={survivorIcon}
                  >

                    <Popup>

                      <strong>
                        {survivor.id}
                      </strong>

                      <br />

                      Survivor detected

                      <br />

                      Confidence:
                      {" "}
                      {survivor.confidence}%

                    </Popup>

                  </Marker>

                )
              )}


              {/* =================================
                  IMPORTANT

                  ONLY ALLOCATED DRONES

                  NOT ALL 128 DRONES
              ================================= */}

              {activeMissionDrones.map(
                (drone) => (

                  <Marker
                    key={
                      drone.id
                    }

                    position={[
                      drone.latitude,
                      drone.longitude
                    ]}

                    icon={droneIcon}

                    eventHandlers={{
                      click: () =>
                        setSelectedDrone(
                          drone
                        )
                    }}
                  >

                    <Popup>

                      <strong>
                        {drone.id}
                      </strong>

                      <br />

                      Status:
                      {" "}
                      ACTIVE

                      <br />

                      Battery:
                      {" "}
                      {drone.battery}%

                      <br />

                      Mission:
                      {" "}
                      {operationName}

                      <br />

                      Survivors:
                      {" "}
                      {drone.survivorsDetected}

                    </Popup>

                  </Marker>

                )
              )}


              {/* =================================
                  ROUTES

                  ONLY ALLOCATED DRONES
              ================================= */}

              {activeMissionDrones.map(
                (drone) => (

                  <Polyline
                    key={
                      `route-${drone.id}`
                    }

                    positions={[
                      [
                        drone.latitude,
                        drone.longitude
                      ],

                      [
                        disaster.latitude,
                        disaster.longitude
                      ]
                    ]}

                    pathOptions={{
                      color: "#8b5cf6",
                      weight: 3,
                      opacity: 0.6
                    }}
                  />

                )
              )}

            </MapContainer>


            {/* =================================
                LEGEND
            ================================= */}

            <div
              style={{
                position: "absolute",

                zIndex: 1000,

                bottom: "12px",

                left: "12px",

                display: "flex",

                gap: "14px",

                padding: "7px 10px",

                borderRadius: "6px",

                background:
                  "rgba(13,11,22,0.9)",

                color: "white",

                fontSize: "9px"
              }}
            >

              <span>
                🚁 Drone
              </span>

              <span>
                ⚠ Disaster
              </span>

              <span>
                👤 Survivor
              </span>

              <span>
                ━ Route
              </span>

              <span>
                ◯ Mission Area
              </span>

            </div>

          </div>


          {/* =================================
              DRONE SIDEBAR

              HIDDEN IN FULLSCREEN
          ================================= */}

          {!fullscreen && (

            <aside
              style={{
                minWidth: 0,

                height: "100%",

                overflowY: "auto",

                background: "#11101b",

                borderLeft:
                  "1px solid rgba(255,255,255,0.08)"
              }}
            >

              {/* SIDEBAR HEADER */}

              <div
                style={{
                  padding: "18px",

                  borderBottom:
                    "1px solid rgba(255,255,255,0.08)"
                }}
              >

                <p
                  style={{
                    margin: 0,

                    fontSize: "9px",

                    letterSpacing: "1px",

                    color: "#858da5"
                  }}
                >
                  SWARM STATUS
                </p>

                <h3
                  style={{
                    margin:
                      "5px 0"
                  }}
                >
                  Drone Fleet
                </h3>

                <span
                  style={{
                    fontSize: "9px",

                    color: "#697386"
                  }}
                >
                  {activeMissionDrones.length}
                  {" "}
                  active mission units
                </span>

              </div>


              {/* =================================
                  NO ACTIVE OPERATION
              ================================= */}

              {activeMissionDrones.length === 0 ? (

                <div
                  style={{
                    padding: "40px 18px",

                    textAlign: "center",

                    color: "#697386"
                  }}
                >

                  <div
                    style={{
                      fontSize: "30px",
                      marginBottom: "10px"
                    }}
                  >
                    🛰️
                  </div>

                  <strong
                    style={{
                      display: "block",
                      color: "white",
                      fontSize: "11px"
                    }}
                  >
                    No Active Operation
                  </strong>

                  <p
                    style={{
                      fontSize: "9px",
                      lineHeight: 1.5
                    }}
                  >
                    Start a mission to display
                    its allocated drones here.
                  </p>

                </div>

              ) : (

                /* =================================
                   ACTIVE DRONES
                ================================= */

                <div>

                  {activeMissionDrones.map(
                    (drone) => {

                      const isSelected =
                        selectedDrone?.id ===
                        drone.id;

                      return (

                        <div
                          key={
                            drone.id
                          }

                          onClick={() =>
                            setSelectedDrone(
                              drone
                            )
                          }

                          style={{
                            padding: "15px",

                            borderBottom:
                              "1px solid rgba(255,255,255,0.06)",

                            borderLeft:
                              isSelected
                                ? "3px solid #8b5cf6"
                                : "3px solid transparent",

                            background:
                              isSelected
                                ? "rgba(139,92,246,0.10)"
                                : "transparent",

                            cursor: "pointer"
                          }}
                        >

                          {/* TITLE */}

                          <div
                            style={{
                              display: "flex",

                              justifyContent:
                                "space-between",

                              alignItems:
                                "center"
                            }}
                          >

                            <strong
                              style={{
                                fontSize: "12px"
                              }}
                            >
                              🚁 {drone.id}
                            </strong>

                            <span
                              style={{
                                fontSize: "8px",
                                color: "#35e88a"
                              }}
                            >
                              ● ACTIVE
                            </span>

                          </div>


                          {/* DETAILS */}

                          <div
                            style={{
                              marginTop: "12px",

                              display: "grid",

                              gap: "7px"
                            }}
                          >

                            <div
                              style={{
                                display: "flex",
                                justifyContent:
                                  "space-between",
                                fontSize: "9px"
                              }}
                            >

                              <span
                                style={{
                                  color: "#858da5"
                                }}
                              >
                                Status
                              </span>

                              <strong>
                                ACTIVE
                              </strong>

                            </div>


                            <div
                              style={{
                                display: "flex",
                                justifyContent:
                                  "space-between",
                                fontSize: "9px"
                              }}
                            >

                              <span
                                style={{
                                  color: "#858da5"
                                }}
                              >
                                Battery
                              </span>

                              <span>
                                🔋 {drone.battery}%
                              </span>

                            </div>


                            <div
                              style={{
                                display: "flex",
                                justifyContent:
                                  "space-between",
                                fontSize: "9px"
                              }}
                            >

                              <span
                                style={{
                                  color: "#858da5"
                                }}
                              >
                                Survivors
                              </span>

                              <strong>
                                👤{" "}
                                {
                                  drone.survivorsDetected
                                }
                              </strong>

                            </div>


                            <div
                              style={{
                                display: "flex",
                                justifyContent:
                                  "space-between",
                                gap: "10px",
                                fontSize: "9px"
                              }}
                            >

                              <span
                                style={{
                                  color: "#858da5"
                                }}
                              >
                                Mission
                              </span>

                              <span>
                                {operationName}
                              </span>

                            </div>

                          </div>


                          {/* FOCUS BUTTON */}

                          <button
                            type="button"

                            onClick={(event) => {

                              event.stopPropagation();

                              setSelectedDrone(
                                drone
                              );

                            }}

                            style={{
                              width: "100%",

                              marginTop: "12px",

                              padding: "7px",

                              border: "none",

                              borderRadius: "5px",

                              background: "#7c3aed",

                              color: "white",

                              fontSize: "9px",

                              cursor: "pointer"
                            }}
                          >
                            Focus Drone
                          </button>

                        </div>

                      );

                    }
                  )}

                </div>

              )}

            </aside>

          )}

        </div>


        {/* =================================
            NORMAL MODE FOOTER
        ================================= */}

        {!fullscreen && (

          <div
            style={{
              minHeight: "34px",

              padding:
                "8px 14px",

              display: "flex",

              justifyContent:
                "space-between",

              alignItems: "center",

              gap: "15px",

              borderTop:
                "1px solid rgba(255,255,255,0.08)",

              fontSize: "9px",

              color: "#858da5"
            }}
          >

            <div
              style={{
                display: "flex",
                gap: "15px"
              }}
            >

              <span>
                🚁 Active Drone
              </span>

              <span>
                ⚠ Disaster
              </span>

              <span>
                👤 Survivor
              </span>

              <span>
                ━ Route
              </span>

              <span>
                ◯ Mission Area
              </span>

            </div>

            <span>

              {selectedDrone
                ? `Tracking ${selectedDrone.id}`
                : "Select a drone to track"}

            </span>

          </div>

        )}

      </section>


      {/* ==================================
          INTEGRATION INFO
      ================================== */}

      {!fullscreen && (

        <section
          className="map-panel"
          style={{
            marginTop: "18px"
          }}
        >

          <div
            style={{
              padding: "15px",

              color: "#697386",

              fontSize: "10px"
            }}
          >

            <strong>
              Integration fields:
            </strong>

            {" "}
            Drone position → Localisation

            {" | "}

            Survivor position → Perception

            {" | "}

            Route → Simulation / Path Planning

            {" | "}

            Drone status → Swarm System

          </div>

        </section>

      )}

    </main>
  );
}


export default LiveMap;
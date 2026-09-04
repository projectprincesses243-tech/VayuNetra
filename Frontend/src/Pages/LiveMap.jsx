import React, { useEffect, useState, useRef } from "react";
import { useLiveState } from "../hooks/useLiveState";

import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  Circle,
} from "react-leaflet";

import L from "leaflet";
import "leaflet/dist/leaflet.css";


// =====================================================
// LEAFLET DEFAULT ICON FIX
// =====================================================

delete L.Icon.Default.prototype._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",

  iconUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",

  shadowUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});


// =====================================================
// DRONE ICON
// =====================================================

const droneIcon = L.divIcon({
  className: "drone-marker",

  html: `
    <div style="
      width:30px;
      height:30px;
      border-radius:50%;
      background:#15101f;
      border:2px solid #8b5cf6;
      display:flex;
      align-items:center;
      justify-content:center;
      color:white;
      font-size:15px;
      box-shadow:0 0 14px rgba(139,92,246,0.8);
    ">
      🚁
    </div>
  `,

  iconSize: [30, 30],
  iconAnchor: [15, 15],
});


// =====================================================
// TRUE POSITION
// BLACK HOLLOW RING
// =====================================================

const truePositionIcon = L.divIcon({
  className: "true-position",

  html: `
    <div style="
      width:18px;
      height:18px;
      border-radius:50%;
      border:3px solid #000000;
      background:rgba(255,255,255,0.25);
      box-sizing:border-box;
      box-shadow:0 0 5px rgba(255,255,255,0.9);
    "></div>
  `,

  iconSize: [18, 18],
  iconAnchor: [9, 9],
});


// =====================================================
// BELIEF POSITION
// PURPLE SOLID DOT
// =====================================================

const beliefPositionIcon = L.divIcon({
  className: "belief-position",

  html: `
    <div style="
      width:14px;
      height:14px;
      border-radius:50%;
      background:#8b5cf6;
      border:2px solid white;
      box-sizing:border-box;
      box-shadow:0 0 12px rgba(139,92,246,1);
    "></div>
  `,

  iconSize: [14, 14],
  iconAnchor: [7, 7],
});


// =====================================================
// DISASTER ICON
// =====================================================

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
      box-shadow:0 0 18px rgba(255,80,80,0.7);
    ">
      ⚠
    </div>
  `,

  iconSize: [38, 38],
  iconAnchor: [19, 19],
});


// =====================================================
// SURVIVOR ICON
// =====================================================

const survivorIcon = L.divIcon({
  className: "survivor-marker",

  html: `
    <div style="
      width:28px;
      height:28px;
      border-radius:50%;
      background:#102d20;
      border:2px solid #35e88a;
      display:flex;
      align-items:center;
      justify-content:center;
      color:white;
      font-size:14px;
      box-shadow:0 0 13px rgba(53,232,138,0.7);
    ">
      👤
    </div>
  `,

  iconSize: [28, 28],
  iconAnchor: [14, 14],
});


// =====================================================
// WORLD → LAT/LNG
// =====================================================

function worldToLatLng(position) {

  if (
    !Array.isArray(position) ||
    position.length < 2
  ) {
    return null;
  }

  const x = Number(position[0]);
  const y = Number(position[1]);

  if (
    !Number.isFinite(x) ||
    !Number.isFinite(y)
  ) {
    return null;
  }

  /*
   * Backend world:
   *
   * 500 x 500
   * center = 250,250
   *
   * Map center is kept around the
   * disaster location.
   */

  const centerLat = 15.4589;
  const centerLng = 75.0078;

  const northMeters = 250 - y;
  const eastMeters = x - 250;

  const lat =
    centerLat +
    northMeters / 111320;

  const lng =
    centerLng +
    eastMeters /
      (
        111320 *
        Math.cos(
          centerLat *
          Math.PI /
          180
        )
      );

  return [lat, lng];
}


// =====================================================
// MAP RESIZE
// =====================================================

function MapResizeHandler() {

  useEffect(() => {

    const resize = () => {

      window.dispatchEvent(
        new Event("resize")
      );

    };

    const timer1 =
      setTimeout(resize, 100);

    const timer2 =
      setTimeout(resize, 500);

    return () => {

      clearTimeout(timer1);
      clearTimeout(timer2);

    };

  }, []);

  return null;
}


// =====================================================
// LIVE MAP
// =====================================================

export default function LiveMap() {

  // ===================================================
  // LIVE STATE
  // ===================================================

  const state = useLiveState();


  // ===================================================
  // UI STATE
  // ===================================================

  const [
    selectedDrone,
    setSelectedDrone
  ] = useState(null);

  const [
    fullscreen,
    setFullscreen
  ] = useState(false);

  const [
    actionStatus,
    setActionStatus
  ] = useState("");

  const mapContainerRef =
    useRef(null);


  // ===================================================
  // ALL DRONES FROM BACKEND
  // ===================================================

  const allDrones =
    Array.isArray(state?.drones)
      ? state.drones
      : [];


  const activeOperation =
    JSON.parse(
      localStorage.getItem(
        "vayunetra_active_operation"
      ) || "null"
    );


  const missionRunning =
    Boolean(
      activeOperation &&
      activeOperation.status === "ACTIVE"
    );


  const deployment =
    state?.deployment || {};


  const recon =
    deployment?.recon || {};


  const mainSwarm =
    deployment?.main_swarm || {};


  const activeDroneIds = [
    ...(recon.assessment_drone_ids || []),
    ...(mainSwarm.assigned_drone_ids || [])
  ].map((id) => {

    const match =
      String(id).match(/\d+/);

    return match
      ? Number(match[0])
      : Number(id);

  });


  // ===================================================
  // ONLY ACTIVE MISSION DRONES ARE SHOWN
  // ===================================================

  const drones =
    missionRunning

      ? allDrones.filter(
          (drone) => {

            const droneId =
              Number(
                String(drone.id).match(/\d+/)?.[0]
                ?? drone.id
              );


            return (
              activeDroneIds.includes(droneId) &&
              drone.alive !== false
            );

          }
        )

      : [];


  // ===================================================
  // SURVIVORS
  // ===================================================

  const survivors =
    Array.isArray(state?.survivors)
      ? state.survivors
      : [];


  // ===================================================
  // SEARCHED CELLS
  // ===================================================

  const searchedCells =
    Array.isArray(
      state?.world?.searched_cells
    )
      ? state.world.searched_cells
      : [];


  // ===================================================
  // FULLSCREEN LISTENER
  // ===================================================

  useEffect(() => {

    const handleFullscreen =
      () => {

        setFullscreen(
          document.fullscreenElement ===
          mapContainerRef.current
        );

      };

    document.addEventListener(
      "fullscreenchange",
      handleFullscreen
    );

    return () => {

      document.removeEventListener(
        "fullscreenchange",
        handleFullscreen
      );

    };

  }, []);


  // ===================================================
  // FULLSCREEN
  // ===================================================

  const toggleFullscreen =
    async () => {

      try {

        if (
          document.fullscreenElement ===
          mapContainerRef.current
        ) {

          await document.exitFullscreen();

        } else {

          await mapContainerRef.current?.requestFullscreen();

        }

      } catch (error) {

        console.error(
          "Fullscreen error:",
          error
        );

      }

    };


  // ===================================================
  // BACKEND ACTION
  // ===================================================

  const runBackendAction =
    async (
      url,
      successMessage
    ) => {

      try {

        setActionStatus(
          "Working..."
        );

        const response =
          await fetch(
            url,
            {
              method: "POST",
            }
          );

        if (!response.ok) {

          throw new Error(
            `HTTP ${response.status}`
          );

        }

        setActionStatus(
          successMessage
        );

        setTimeout(() => {

          setActionStatus("");

        }, 2500);

      } catch (error) {

        console.error(
          "Backend action failed:",
          error
        );

        setActionStatus(
          "Backend action failed"
        );

        setTimeout(() => {

          setActionStatus("");

        }, 2500);

      }

    };


  // ===================================================
  // DENY GPS
  // ===================================================

  const denyGPS = () => {

    runBackendAction(
      "http://127.0.0.1:8000/api/ranging/false",
      "GPS / ranging disabled"
    );

  };


  // ===================================================
  // KILL DRONE
  // ===================================================

  const killDrone = () => {

    runBackendAction(
      "http://127.0.0.1:8000/api/kill",
      "Drone killed"
    );

  };


  // ===================================================
  // RESET
  // ===================================================

  const resetSimulation = () => {

    runBackendAction(
      "http://127.0.0.1:8000/api/reset",
      "Simulation reset"
    );

  };


  // ===================================================
  // WAIT FOR LIVE STATE
  // ===================================================

  if (!state) {

    return (

      <main
        className="dashboard"
        style={{
          padding: "20px",
        }}
      >

        <section
          className="hero-section"
        >

          <div>

            <p className="eyebrow">
              SWARM NAVIGATION
            </p>

            <h2>
              Live <span>Map</span>
            </h2>

            <p className="hero-description">
              Connecting to the VayuNetra live simulation...
            </p>

          </div>

          <div className="mission-status">

            <span className="status-dot"></span>

            CONNECTING TO SWARM

          </div>

        </section>

      </main>

    );

  }


  // ===================================================
  // MAP CENTER
  // ===================================================

  const mapCenter = [
    15.4589,
    75.0078,
  ];


  // ===================================================
  // RENDER
  // ===================================================

  return (

    <main className="dashboard">


      {/* =================================================
          HEADER
      ================================================= */}

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
              Real-time operational view of the VayuNetra drone swarm.
            </p>

          </div>

          <div className="mission-status">

            <span className="status-dot"></span>

            LOCALISATION ONLINE

          </div>

        </section>

      )}


      {/* =================================================
          MAP PANEL
      ================================================= */}

      <section
        className="map-panel live-map-panel"

        style={{
          marginTop:
            fullscreen
              ? 0
              : "18px",

          height:
            fullscreen
              ? "100vh"
              : "calc(100vh - 250px)",

          minHeight:
            fullscreen
              ? "100vh"
              : "560px",
        }}
      >


        {/* =================================================
            PANEL HEADER
        ================================================= */}

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

              {drones.length}
              {" "}
              LIVE DRONES

            </span>

          </div>

        )}


        {/* =================================================
            MAP + SIDEBAR
        ================================================= */}

        <div
          style={{
            display:
              "grid",

            gridTemplateColumns:
              fullscreen
                ? "1fr"
                : "minmax(0, 3fr) minmax(300px, 1fr)",

            width:
              "100%",

            height:
              "100%",

            minHeight:
              0,
          }}
        >


          {/* =================================================
              MAP
          ================================================= */}

          <div
            ref={mapContainerRef}

            style={{
              position:
                "relative",

              width:
                "100%",

              height:
                fullscreen
                  ? "100vh"
                  : "100%",

              minHeight:
                fullscreen
                  ? "100vh"
                  : "500px",

              overflow:
                "hidden",

              background:
                "#0d0b16",
            }}
          >


            {/* =================================================
                DEMO BUTTONS
            ================================================= */}

            <div
              style={{
                position:
                  "absolute",

                zIndex:
                  2000,

                top:
                  "12px",

                left:
                  "50%",

                transform:
                  "translateX(-50%)",

                display:
                  "flex",

                gap:
                  "7px",

                alignItems:
                  "center",

                whiteSpace:
                  "nowrap",
              }}
            >

              <button
                type="button"
                onClick={denyGPS}

                style={{
                  padding:
                    "9px 12px",

                  border:
                    "none",

                  borderRadius:
                    "6px",

                  background:
                    "#dc2626",

                  color:
                    "white",

                  fontSize:
                    "9px",

                  fontWeight:
                    700,

                  cursor:
                    "pointer",

                  boxShadow:
                    "0 3px 10px rgba(0,0,0,0.3)",
                }}
              >

                🚫 DENY GPS

              </button>


              <button
                type="button"
                onClick={killDrone}

                style={{
                  padding:
                    "9px 12px",

                  border:
                    "none",

                  borderRadius:
                    "6px",

                  background:
                    "#b45309",

                  color:
                    "white",

                  fontSize:
                    "9px",

                  fontWeight:
                    700,

                  cursor:
                    "pointer",

                  boxShadow:
                    "0 3px 10px rgba(0,0,0,0.3)",
                }}
              >

                ⚠ KILL DRONE

              </button>


              <button
                type="button"
                onClick={resetSimulation}

                style={{
                  padding:
                    "9px 12px",

                  border:
                    "none",

                  borderRadius:
                    "6px",

                  background:
                    "#2563eb",

                  color:
                    "white",

                  fontSize:
                    "9px",

                  fontWeight:
                    700,

                  cursor:
                    "pointer",

                  boxShadow:
                    "0 3px 10px rgba(0,0,0,0.3)",
                }}
              >

                ↻ RESET

              </button>


              {actionStatus && (

                <span
                  style={{
                    padding:
                      "8px 10px",

                    borderRadius:
                      "6px",

                    background:
                      "rgba(13,11,22,0.96)",

                    color:
                      "white",

                    fontSize:
                      "9px",

                    border:
                      "1px solid rgba(255,255,255,0.12)",
                  }}
                >

                  {actionStatus}

                </span>

              )}

            </div>


            {/* =================================================
                FULLSCREEN
            ================================================= */}

            <button
              type="button"
              onClick={toggleFullscreen}

              style={{
                position:
                  "absolute",

                zIndex:
                  2000,

                top:
                  "12px",

                right:
                  "12px",

                padding:
                  "9px 14px",

                border:
                  "none",

                borderRadius:
                  "7px",

                background:
                  "#7c3aed",

                color:
                  "white",

                fontSize:
                  "10px",

                fontWeight:
                  700,

                cursor:
                  "pointer",

                boxShadow:
                  "0 5px 18px rgba(0,0,0,0.35)",
              }}
            >

              {fullscreen
                ? "⛶ EXIT FULLSCREEN"
                : "⛶ FULLSCREEN"}

            </button>


            {/* =================================================
                LIVE STATUS
            ================================================= */}

            <div
              style={{
                position:
                  "absolute",

                zIndex:
                  1000,

                top:
                  "12px",

                left:
                  "12px",

                padding:
                  "10px 13px",

                borderRadius:
                  "7px",

                background:
                  "rgba(13,11,22,0.92)",

                border:
                  "1px solid rgba(255,255,255,0.1)",

                color:
                  "white",

                minWidth:
                  "150px",

                backdropFilter:
                  "blur(8px)",
              }}
            >

              <div
                style={{
                  fontSize:
                    "8px",

                  letterSpacing:
                    "1px",

                  color:
                    "#858da5",

                  marginBottom:
                    "4px",
                }}
              >

                LIVE SWARM

              </div>

              <strong>

                {drones.length}
                {" "}
                active drones

              </strong>

              <div
                style={{
                  marginTop:
                    "4px",

                  fontSize:
                    "9px",

                  color:
                    "#35e88a",
                }}
              >

                ● Tick {state.tick}

              </div>

            </div>


            {/* =================================================
                LEGEND
            ================================================= */}

            <div
              style={{
                position:
                  "absolute",

                zIndex:
                  1000,

                bottom:
                  "12px",

                left:
                  "12px",

                padding:
                  "10px 12px",

                borderRadius:
                  "7px",

                background:
                  "rgba(15,15,18,0.94)",

                color:
                  "white",

                fontSize:
                  "9px",

                display:
                  "grid",

                gap:
                  "7px",

                boxShadow:
                  "0 2px 10px rgba(0,0,0,0.3)",
              }}
            >

              <div>

                <span
                  style={{
                    display:
                      "inline-block",

                    width:
                      "14px",

                    height:
                      "14px",

                    borderRadius:
                      "50%",

                    border:
                      "3px solid #000000",

                    background:
                      "white",

                    marginRight:
                      "7px",

                    verticalAlign:
                      "middle",
                  }}
                />

                True Position

              </div>


              <div>

                <span
                  style={{
                    display:
                      "inline-block",

                    width:
                      "14px",

                    height:
                      "14px",

                    borderRadius:
                      "50%",

                    background:
                      "#8b5cf6",

                    border:
                      "2px solid white",

                    marginRight:
                      "7px",

                    verticalAlign:
                      "middle",
                  }}
                />

                Belief Position

              </div>


              <div>

                <span
                  style={{
                    display:
                      "inline-block",

                    width:
                      "28px",

                    borderTop:
                      "3px dashed #000000",

                    marginRight:
                      "7px",

                    verticalAlign:
                      "middle",
                  }}
                />

                Position Error

              </div>


              <div>

                <span
                  style={{
                    display:
                      "inline-block",

                    width:
                      "14px",

                    height:
                      "14px",

                    borderRadius:
                      "50%",

                    border:
                      "1px solid #8b5cf6",

                    marginRight:
                      "7px",

                    verticalAlign:
                      "middle",
                  }}
                />

                Uncertainty

              </div>

            </div>


            {/* =================================================
                LEAFLET MAP
            ================================================= */}

            <MapContainer

              center={
                mapCenter
              }

              zoom={
                17
              }

              minZoom={
                2
              }

              maxZoom={
                22
              }

              scrollWheelZoom={
                true
              }

              doubleClickZoom={
                true
              }

              touchZoom={
                true
              }

              zoomControl={
                true
              }

              style={{
                width:
                  "100%",

                height:
                  "100%",

                minHeight:
                  "100%",
              }}
            >

              <TileLayer

                attribution="
                  &copy; OpenStreetMap contributors
                "

                url="
                  https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png
                "

                maxZoom={
                  22
                }

              />


              <MapResizeHandler />


              {/* =================================================
                  DISASTER
              ================================================= */}

              <Marker

                position={
                  mapCenter
                }

                icon={
                  disasterIcon
                }

              >

                <Popup>

                  <strong>
                    ACTIVE DISASTER
                  </strong>

                  <br />

                  Type:
                  {" "}
                  Flood

                  <br />

                  Severity:
                  {" "}
                  HIGH

                </Popup>

              </Marker>


              {/* =================================================
                  MISSION AREA
              ================================================= */}

              <Circle

                center={
                  mapCenter
                }

                radius={
                  300
                }

                pathOptions={{
                  color:
                    "#8b5cf6",

                  fillColor:
                    "#8b5cf6",

                  fillOpacity:
                    0.05,

                  weight:
                    1,
                }}

              />


              {/* =================================================
                  SEARCHED CELLS
              ================================================= */}

              {searchedCells.map(
                (cell, index) => {

                  const position =
                    worldToLatLng(
                      cell
                    );

                  if (!position) {
                    return null;
                  }

                  return (

                    <Circle

                      key={
                        `searched-${index}`
                      }

                      center={
                        position
                      }

                      radius={
                        25
                      }

                      pathOptions={{
                        color:
                          "#35e88a",

                        fillColor:
                          "#35e88a",

                        fillOpacity:
                          0.10,

                        weight:
                          1,
                      }}

                    />

                  );

                }
              )}


              {/* =================================================
                  SURVIVORS
              ================================================= */}

              {survivors.map(
                (survivor) => {

                  const position =
                    worldToLatLng(
                      survivor.pos
                    );

                  if (!position) {
                    return null;
                  }

                  return (

                    <Marker

                      key={
                        `survivor-${survivor.id}`
                      }

                      position={
                        position
                      }

                      icon={
                        survivorIcon
                      }

                    >

                      <Popup>

                        <strong>
                          Survivor{" "}
                          {survivor.id}
                        </strong>

                        <br />

                        {survivor.found
                          ? "Detected"
                          : "Searching"}

                        <br />

                        {survivor.rescued
                          ? "Rescued"
                          : "Not rescued"}

                      </Popup>

                    </Marker>

                  );

                }
              )}


              {/* =================================================
                  LIVE DRONES
              ================================================= */}

              {drones.map(
                (drone) => {

                  const truePosition =
                    worldToLatLng(
                      drone.true_pos
                    );

                  const beliefPosition =
                    worldToLatLng(
                      drone.belief_pos
                    );

                  if (
                    !truePosition ||
                    !beliefPosition
                  ) {
                    return null;
                  }

                  const uncertainty =
                    Number(
                      drone.uncertainty
                    ) || 0;

                  return (

                    <React.Fragment
                      key={
                        `drone-${drone.id}`
                      }
                    >


                      {/* ==========================================
                          UNCERTAINTY CIRCLE
                      ========================================== */}

                      <Circle

                        center={
                          beliefPosition
                        }

                        radius={
                          uncertainty
                        }

                        pathOptions={{
                          color:
                            "#8b5cf6",

                          fillColor:
                            "#8b5cf6",

                          fillOpacity:
                            0.08,

                          weight:
                            1,

                          opacity:
                            0.6,
                        }}

                      />


                      {/* ==========================================
                          TRUE → BELIEF
                          BLACK DASHED ERROR LINE
                      ========================================== */}

                      <Polyline

                        positions={[
                          truePosition,
                          beliefPosition
                        ]}

                        pathOptions={{
                          color:
                            "#000000",

                          weight:
                            4,

                          dashArray:
                            "8 8",

                          opacity:
                            1,

                          lineCap:
                            "butt",

                          lineJoin:
                            "round",
                        }}

                      />


                      {/* ==========================================
                          TRUE POSITION
                      ========================================== */}

                      <Marker

                        position={
                          truePosition
                        }

                        icon={
                          truePositionIcon
                        }

                      >

                        <Popup>

                          <strong>
                            Drone{" "}
                            {drone.id}
                          </strong>

                          <br />

                          TRUE POSITION

                          <br />

                          X:
                          {" "}
                          {Number(
                            drone.true_pos?.[0] ?? 0
                          ).toFixed(1)}

                          <br />

                          Y:
                          {" "}
                          {Number(
                            drone.true_pos?.[1] ?? 0
                          ).toFixed(1)}

                        </Popup>

                      </Marker>


                      {/* ==========================================
                          BELIEF POSITION
                      ========================================== */}

                      <Marker

                        position={
                          beliefPosition
                        }

                        icon={
                          beliefPositionIcon
                        }

                        eventHandlers={{
                          click:
                            () =>
                              setSelectedDrone(
                                drone.id
                              ),
                        }}

                      >

                        <Popup>

                          <strong>
                            Drone{" "}
                            {drone.id}
                          </strong>

                          <br />

                          BELIEF POSITION

                          <br />

                          Error:
                          {" "}
                          {Number(
                            drone.error ?? 0
                          ).toFixed(2)}
                          {" "}
                          m

                          <br />

                          Uncertainty:
                          {" "}
                          {uncertainty.toFixed(2)}
                          {" "}
                          m

                        </Popup>

                      </Marker>


                      {/* ==========================================
                          DRONE LABEL
                      ========================================== */}

                      <Marker

                        position={
                          beliefPosition
                        }

                        icon={
                          L.divIcon({

                            className:
                              "drone-label",

                            html: `
                              <div style="
                                transform:translate(11px,-29px);
                                white-space:nowrap;
                                color:white;
                                font-size:9px;
                                font-weight:700;
                                text-shadow:
                                  0 1px 3px #000,
                                  0 0 4px #000;
                              ">
                                D${drone.id}
                              </div>
                            `,

                            iconSize:
                              [40, 20],

                            iconAnchor:
                              [0, 0],

                          })
                        }

                      />

                    </React.Fragment>

                  );

                }
              )}

            </MapContainer>

          </div>


          {/* =================================================
              SIDEBAR
          ================================================= */}

          {!fullscreen && (

            <aside
              style={{
                minWidth:
                  0,

                height:
                  "100%",

                overflowY:
                  "auto",

                background:
                  "#11101b",

                borderLeft:
                  "1px solid rgba(255,255,255,0.08)",
              }}
            >


              {/* ================================================
                  HEADER
              ================================================= */}

              <div
                style={{
                  padding:
                    "18px",

                  borderBottom:
                    "1px solid rgba(255,255,255,0.08)",
                }}
              >

                <p
                  style={{
                    margin:
                      0,

                    fontSize:
                      "9px",

                    letterSpacing:
                      "1px",

                    color:
                      "#858da5",
                  }}
                >

                  LIVE SWARM

                </p>

                <h3
                  style={{
                    margin:
                      "5px 0",
                  }}
                >

                  Drone Fleet

                </h3>

                <span
                  style={{
                    fontSize:
                      "9px",

                    color:
                      "#697386",
                  }}
                >

                  {drones.length}
                  {" "}
                  active drones

                </span>

              </div>


              {/* ================================================
                  DRONE CARDS
              ================================================= */}

              {drones.map(
                (drone) => {

                  const error =
                    Number(
                      drone.error
                    ) || 0;

                  const uncertainty =
                    Number(
                      drone.uncertainty
                    ) || 0;

                  const isSelected =
                    selectedDrone ===
                    drone.id;


                  return (

                    <div

                      key={
                        `card-${drone.id}`
                      }

                      onClick={() =>
                        setSelectedDrone(
                          drone.id
                        )
                      }

                      style={{
                        padding:
                          "15px",

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

                        cursor:
                          "pointer",
                      }}
                    >


                      {/* HEADER */}

                      <div
                        style={{
                          display:
                            "flex",

                          justifyContent:
                            "space-between",

                          alignItems:
                            "center",
                        }}
                      >

                        <strong>
                          🚁 Drone{" "}
                          {drone.id}
                        </strong>

                        <span
                          style={{
                            fontSize:
                              "8px",

                            color:
                              "#35e88a",
                          }}
                        >

                          ● LIVE

                        </span>

                      </div>


                      {/* ERROR */}

                      <div
                        style={{
                          marginTop:
                            "13px",

                          padding:
                            "10px",

                          borderRadius:
                            "6px",

                          background:
                            "rgba(139,92,246,0.08)",
                        }}
                      >

                        <div
                          style={{
                            fontSize:
                              "8px",

                            color:
                              "#858da5",

                            letterSpacing:
                              "1px",
                          }}
                        >

                          LOCALISATION ERROR

                        </div>

                        <strong
                          style={{
                            display:
                              "block",

                            marginTop:
                              "3px",

                            fontSize:
                              "20px",
                          }}
                        >

                          {error.toFixed(2)}
                          {" "}
                          m

                        </strong>

                      </div>


                      {/* DETAILS */}

                      <div
                        style={{
                          marginTop:
                            "12px",

                          display:
                            "grid",

                          gap:
                            "7px",
                        }}
                      >

                        <div
                          style={{
                            display:
                              "flex",

                            justifyContent:
                              "space-between",

                            fontSize:
                              "9px",
                          }}
                        >

                          <span
                            style={{
                              color:
                                "#858da5",
                            }}
                          >
                            State
                          </span>

                          <strong>
                            {drone.state}
                          </strong>

                        </div>


                        <div
                          style={{
                            display:
                              "flex",

                            justifyContent:
                              "space-between",

                            fontSize:
                              "9px",
                          }}
                        >

                          <span
                            style={{
                              color:
                                "#858da5",
                            }}
                          >
                            Battery
                          </span>

                          <span>

                            🔋{" "}

                            {Number(
                              drone.battery ?? 0
                            ).toFixed(1)}

                            %

                          </span>

                        </div>


                        <div
                          style={{
                            display:
                              "flex",

                            justifyContent:
                              "space-between",

                            fontSize:
                              "9px",
                          }}
                        >

                          <span
                            style={{
                              color:
                                "#858da5",
                            }}
                          >
                            Uncertainty
                          </span>

                          <span>

                            {uncertainty.toFixed(2)}
                            {" "}
                            m

                          </span>

                        </div>


                        <div
                          style={{
                            display:
                              "flex",

                            justifyContent:
                              "space-between",

                            fontSize:
                              "9px",
                          }}
                        >

                          <span
                            style={{
                              color:
                                "#858da5",
                            }}
                          >
                            Search Target
                          </span>

                          <span>

                            {drone.search_target
                              ? `[${drone.search_target[0]}, ${drone.search_target[1]}]`
                              : "None"}

                          </span>

                        </div>

                      </div>


                      {/* POSITION */}

                      <div
                        style={{
                          marginTop:
                            "12px",

                          paddingTop:
                            "10px",

                          borderTop:
                            "1px solid rgba(255,255,255,0.06)",
                        }}
                      >

                        <div
                          style={{
                            fontSize:
                              "8px",

                            color:
                              "#858da5",

                            marginBottom:
                              "5px",
                          }}
                        >

                          POSITION ESTIMATE

                        </div>


                        <div
                          style={{
                            fontSize:
                              "9px",
                          }}
                        >

                          <span
                            style={{
                              color:
                                "#858da5",
                            }}
                          >
                            True:
                          </span>

                          {" "}

                          [
                          {Number(
                            drone.true_pos?.[0] ?? 0
                          ).toFixed(1)}
                          ,

                          {" "}

                          {Number(
                            drone.true_pos?.[1] ?? 0
                          ).toFixed(1)}
                          ]

                        </div>


                        <div
                          style={{
                            marginTop:
                              "4px",

                            fontSize:
                              "9px",
                          }}
                        >

                          <span
                            style={{
                              color:
                                "#858da5",
                            }}
                          >
                            Belief:
                          </span>

                          {" "}

                          [
                          {Number(
                            drone.belief_pos?.[0] ?? 0
                          ).toFixed(1)}
                          ,

                          {" "}

                          {Number(
                            drone.belief_pos?.[1] ?? 0
                          ).toFixed(1)}
                          ]

                        </div>

                      </div>

                    </div>

                  );

                }
              )}


              {/* ================================================
                  NO DRONES
              ================================================= */}

              {drones.length === 0 && (

                <div
                  style={{
                    padding:
                      "30px 20px",

                    textAlign:
                      "center",

                    color:
                      "#858da5",

                    fontSize:
                      "10px",
                  }}
                >

                  No active drones.

                </div>

              )}

            </aside>

          )}

        </div>


        {/* =================================================
            FOOTER
        ================================================= */}

        {!fullscreen && (

          <div
            style={{
              minHeight:
                "38px",

              padding:
                "8px 14px",

              display:
                "flex",

              justifyContent:
                "space-between",

              alignItems:
                "center",

              borderTop:
                "1px solid rgba(255,255,255,0.08)",

              fontSize:
                "9px",

              color:
                "#858da5",
            }}
          >

            <span>
              ○ True position
            </span>

            <span>
              ● Belief position
            </span>

            <span>
              - - - Position error
            </span>

            <span>
              ◯ Uncertainty
            </span>

            <span>
              Tick {state.tick}
            </span>

          </div>

        )}

      </section>

    </main>

  );
}
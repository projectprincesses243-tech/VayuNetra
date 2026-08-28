import { useState, useRef } from "react";

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
// MAP FOCUS COMPONENT
// ==========================================

function MapFocus({ selectedDrone }) {

  const map = useMap();

  if (selectedDrone) {

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

  }

  return null;
}


// ==========================================
// LIVE MAP
// ==========================================

function LiveMap() {

  const [selectedDrone, setSelectedDrone] =
    useState(null);

  const [fullscreen, setFullscreen] =
    useState(false);

  const mapSectionRef =
    useRef(null);


  // ========================================
  // FULLSCREEN
  // ========================================

  const toggleFullscreen = async () => {

    try {

      if (!fullscreen) {

        await mapSectionRef.current?.requestFullscreen();

        setFullscreen(true);

      } else {

        await document.exitFullscreen();

        setFullscreen(false);

      }

    } catch (error) {

      console.log(
        "Fullscreen not available",
        error
      );

    }

  };


  return (

    <main className="dashboard">

      {/* ==================================
          HEADER
      ================================== */}

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


      {/* ==================================
          MAP + DRONE CONTROL
      ================================== */}

      <section
        ref={mapSectionRef}
        className="map-panel"
        style={{
          marginTop: "18px",
          overflow: "hidden",
          background: "#0d0b16"
        }}
      >

        {/* =================================
            TOP BAR
        ================================= */}

        <div
          style={{
            padding: "14px 18px",
            display: "flex",
            justifyContent:
              "space-between",
            alignItems: "center",
            borderBottom:
              "1px solid rgba(255,255,255,0.08)"
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
              GEOSPATIAL MONITORING
            </p>

            <h3
              style={{
                margin: "4px 0 0"
              }}
            >
              Mission Control Map
            </h3>

          </div>


          <button
            type="button"
            onClick={toggleFullscreen}
            style={{
              cursor: "pointer",
              padding: "9px 14px"
            }}
          >

            {fullscreen
              ? "⛶ EXIT FULLSCREEN"
              : "⛶ FULLSCREEN"}

          </button>

        </div>


        {/* =================================
            MAIN MAP AREA
        ================================= */}

        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "minmax(0, 3fr) minmax(280px, 1fr)",
            minHeight: "600px"
          }}
        >

          {/* ===============================
              MAP
          ================================ */}

          <div
            style={{
              minWidth: 0,
              height: "600px"
            }}
          >

            <MapContainer

              center={[
                disaster.latitude,
                disaster.longitude
              ]}

              zoom={14}

              scrollWheelZoom={true}

              style={{
                width: "100%",
                height: "100%"
              }}

            >

              <TileLayer

                attribution="&copy; OpenStreetMap contributors"

                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"

              />


              {/* SELECTED DRONE FOCUS */}

              <MapFocus
                selectedDrone={
                  selectedDrone
                }
              />


              {/* =========================
                  DISASTER
              ========================== */}

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


              {/* =========================
                  MISSION AREA
              ========================== */}

              <Circle

                center={[
                  disaster.latitude,
                  disaster.longitude
                ]}

                radius={1200}

                pathOptions={{
                  color: "#8b5cf6",
                  fillOpacity: 0.08
                }}

              />


              {/* =========================
                  SURVIVORS
              ========================== */}

              {survivors.map(
                (survivor) => (

                  <Marker

                    key={survivor.id}

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


              {/* =========================
                  DRONES
              ========================== */}

              {drones.map(
                (drone) => (

                  <Marker

                    key={drone.id}

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
                      {drone.status}

                      <br />

                      Battery:
                      {" "}
                      {drone.battery}%

                      <br />

                      Mission:
                      {" "}
                      {drone.mission}

                      <br />

                      Survivors:
                      {" "}
                      {drone.survivorsDetected}

                    </Popup>

                  </Marker>

                )
              )}


              {/* =========================
                  DRONE ROUTES
              ========================== */}

              {drones.map(
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

          </div>


          {/* ===============================
              RIGHT DRONE PANEL
          ================================ */}

          <aside
            style={{
              borderLeft:
                "1px solid rgba(255,255,255,0.08)",
              background: "#11101b",
              overflowY: "auto",
              height: "600px"
            }}
          >

            {/* PANEL HEADER */}

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
                  margin: "5px 0"
                }}
              >
                Drone Fleet
              </h3>

              <span
                style={{
                  fontSize: "10px",
                  color: "#697386"
                }}
              >
                {drones.length} active demo units

              </span>

            </div>


            {/* DRONE LIST */}

            <div>

              {drones.map(
                (drone) => {

                  const isSelected =
                    selectedDrone?.id ===
                    drone.id;

                  return (

                    <div
                      key={drone.id}
                      onClick={() =>
                        setSelectedDrone(
                          drone
                        )
                      }
                      style={{
                        padding: "16px",
                        borderBottom:
                          "1px solid rgba(255,255,255,0.06)",
                        cursor: "pointer",
                        background:
                          isSelected
                            ? "rgba(139,92,246,0.10)"
                            : "transparent",
                        borderLeft:
                          isSelected
                            ? "3px solid #8b5cf6"
                            : "3px solid transparent"
                      }}
                    >

                      {/* DRONE NAME */}

                      <div
                        style={{
                          display: "flex",
                          justifyContent:
                            "space-between",
                          alignItems: "center"
                        }}
                      >

                        <strong>
                          🚁 {drone.id}
                        </strong>

                        <span
                          style={{
                            fontSize: "9px"
                          }}
                        >
                          ● LIVE
                        </span>

                      </div>


                      {/* STATUS */}

                      <div
                        style={{
                          marginTop: "10px",
                          display: "grid",
                          gap: "6px"
                        }}
                      >

                        <div
                          style={{
                            display: "flex",
                            justifyContent:
                              "space-between"
                          }}
                        >

                          <span>
                            Status
                          </span>

                          <strong>
                            {drone.status}
                          </strong>

                        </div>


                        <div
                          style={{
                            display: "flex",
                            justifyContent:
                              "space-between"
                          }}
                        >

                          <span>
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
                              "space-between"
                          }}
                        >

                          <span>
                            Survivors
                          </span>

                          <strong>
                            👤{" "}
                            {drone.survivorsDetected}
                          </strong>

                        </div>


                        <div
                          style={{
                            display: "flex",
                            justifyContent:
                              "space-between"
                          }}
                        >

                          <span>
                            Mission
                          </span>

                          <span>
                            {drone.mission}
                          </span>

                        </div>

                      </div>


                      {/* VIEW BUTTON */}

                      <button
                        type="button"
                        onClick={(event) => {

                          event.stopPropagation();

                          setSelectedDrone(
                            drone
                          );

                        }}
                        style={{
                          marginTop: "12px",
                          width: "100%",
                          cursor: "pointer",
                          padding: "7px"
                        }}
                      >
                        Focus Drone
                      </button>

                    </div>

                  );

                }
              )}

            </div>

          </aside>

        </div>


        {/* =================================
            BOTTOM STATUS BAR
        ================================= */}

        <div
          style={{
            padding: "11px 18px",
            display: "flex",
            justifyContent:
              "space-between",
            alignItems: "center",
            gap: "15px",
            flexWrap: "wrap",
            borderTop:
              "1px solid rgba(255,255,255,0.08)"
          }}
        >

          {/* LEGEND */}

          <div
            style={{
              display: "flex",
              gap: "18px",
              flexWrap: "wrap",
              fontSize: "10px"
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


          {/* SELECTED DRONE */}

          <span
            style={{
              fontSize: "10px",
              color: "#858da5"
            }}
          >

            {selectedDrone
              ? `Tracking ${selectedDrone.id}`
              : "Select a drone to track"}

          </span>

        </div>

      </section>


      {/* ==================================
          INTEGRATION NOTE
      ================================== */}

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

    </main>
  );
}


export default LiveMap;
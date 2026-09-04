import { useEffect, useMemo, useState } from "react";
import { drones as demoDrones } from "../data/demoData";
import { getActiveOperation } from "../data/operationStorage";

const BACKEND_HTTP = "http://127.0.0.1:8000";
const BACKEND_WS = "ws://127.0.0.1:8000/ws";

function formatDroneId(id) {
  if (typeof id === "number") return `DR-${String(id + 1).padStart(3, "0")}`;
  const value = String(id ?? "");
  if (/^DR-\d+$/i.test(value)) return value.toUpperCase();
  if (/^\d+$/.test(value)) return `DR-${String(Number(value) + 1).padStart(3, "0")}`;
  return value || "DR-???";
}

function numericBackendId(id) {
  if (typeof id === "number") return id;
  const value = String(id ?? "");
  const match = value.match(/^DR-(\d+)$/i);
  if (match) return Math.max(0, Number(match[1]) - 1);
  if (/^\d+$/.test(value)) return Number(value);
  return null;
}

function normalizeStatus(status) {
  const value = String(status || "").toUpperCase();

  if (
    value.includes("DISABLED") ||
    value.includes("UNAVAILABLE") ||
    value.includes("OFFLINE")
  ) return "UNAVAILABLE";

  if (value.includes("CHARG")) return "CHARGING";

  if (
    value.includes("DEPLOY") ||
    value.includes("ASSESS") ||
    value.includes("ACTIVE") ||
    value.includes("OPERAT") ||
    value.includes("TRAVEL") ||
    value.includes("ARRIVE")
  ) return "ACTIVE";

  return "AVAILABLE";
}

function getBackendDroneMap(
  state,
  activeOperation
) {

  if (!activeOperation) {
    return new Map();
  }
  const map = new Map();
  const fleet = state?.fleet || {};
  const deployment = state?.deployment || {};
  const recon = deployment?.recon || {};

  const addIds = (ids, status, mission, zone) => {
    (Array.isArray(ids) ? ids : []).forEach((id) => {
      map.set(numericBackendId(id), {
        status,
        mission,
        zone,
      });
    });
  };

  addIds(
    recon.assessment_drone_ids || fleet.assessment_drone_ids,
    "ACTIVE",
    deployment.mission_name || deployment.mission_id || "Initial Assessment",
    "ASSESSMENT"
  );

  const mainSwarm = deployment.main_swarm || {};

  addIds(
    mainSwarm.assigned_drone_ids || fleet.main_swarm_drone_ids,
    "ACTIVE",
    deployment.mission_name || deployment.mission_id || "Main Swarm",
    null
  );

  const disabledIds =
    fleet.disabled_drone_ids ||
    fleet.unavailable_drone_ids ||
    deployment.disabled_drone_ids ||
    [];

  addIds(disabledIds, "UNAVAILABLE", "Unavailable", null);

  return map;
}

function mergeDrones(
  state,
  activeOperation
) {
  const backendMap =
    getBackendDroneMap(
      state,
      activeOperation
    );

  const base = Array.from({ length: 128 }, (_, index) => {
    const demo = demoDrones.find(
      (drone) => numericBackendId(drone.id) === index
    );

    return {
      ...(demo || {}),
      id: formatDroneId(index),
      backendId: index,
      battery: demo?.battery ?? 100,
      survivorsDetected: demo?.survivorsDetected ?? 0,
      mission: demo?.mission || "Station",
      zone: demo?.zone || "—",
      status: normalizeStatus(demo?.status || "AVAILABLE"),
    };
  });

  if (!state) return base;

  const backendFleet = state.fleet || {};
  const backendMapValues = backendMap;

  return base.map((drone) => {
    const backend = backendMapValues.get(drone.backendId);

    if (!backend) return drone;

    return {
      ...drone,
      status: backend.status,
      mission: backend.mission || drone.mission,
      zone: backend.zone || drone.zone,
    };
  });
}

function Drones() {
  const [backendState, setBackendState] = useState(null);
  const [connection, setConnection] = useState("CONNECTING");

  const [activeOperation, setActiveOperation] =
    useState(() => getActiveOperation());

  useEffect(() => {

    const syncOperation = () => {
      setActiveOperation(
        getActiveOperation()
      );
    };

    const timer = setInterval(
      syncOperation,
      1000
    );

    return () => {
      clearInterval(timer);
    };

  }, []);

  useEffect(() => {
    let socket;
    let cancelled = false;
    let reconnectTimer;

    const loadState = async () => {
      try {
        const response = await fetch(`${BACKEND_HTTP}/api/state`);
        if (!response.ok) throw new Error("Backend state unavailable");
        const state = await response.json();

        if (!cancelled) {
          setBackendState(state);
          setConnection("CONNECTED");
        }
      } catch {
        if (!cancelled) setConnection("DEMO");
      }
    };

    const connect = () => {
      if (cancelled) return;

      try {
        socket = new WebSocket(BACKEND_WS);

        socket.onopen = () => {
          if (!cancelled) setConnection("CONNECTED");
        };

        socket.onmessage = (event) => {
          try {
            const state = JSON.parse(event.data);
            if (!cancelled) {
              setBackendState(state);
              setConnection("CONNECTED");
            }
          } catch {
            // Ignore malformed websocket messages.
          }
        };

        socket.onerror = () => {
          if (!cancelled) setConnection("DEMO");
        };

        socket.onclose = () => {
          if (cancelled) return;
          setConnection("RECONNECTING");
          reconnectTimer = setTimeout(connect, 2000);
        };
      } catch {
        if (!cancelled) setConnection("DEMO");
      }
    };

    loadState();
    connect();

    return () => {
      cancelled = true;
      clearTimeout(reconnectTimer);
      if (socket) socket.close();
    };
  }, []);

  const displayDrones = useMemo(
    () =>
      mergeDrones(
        backendState,
        activeOperation
      ),
    [
      backendState,
      activeOperation
    ]
  );

  const counts = useMemo(() => {
    return displayDrones.reduce(
      (result, drone) => {
        result.total += 1;
        if (drone.status === "ACTIVE") result.active += 1;
        else if (drone.status === "CHARGING") result.charging += 1;
        else if (drone.status === "UNAVAILABLE") result.unavailable += 1;
        else result.available += 1;
        return result;
      },
      {
        total: 0,
        active: 0,
        available: 0,
        charging: 0,
        unavailable: 0,
      }
    );
  }, [displayDrones]);

  const deployment = backendState?.deployment || {};
  const recon = deployment?.recon || {};
  const mainSwarm = deployment?.main_swarm || {};

  const assessmentIds = new Set(
    activeOperation
      ? (recon.assessment_drone_ids || [])
          .map(numericBackendId)
      : []
  );

  const mainSwarmIds = new Set(
    activeOperation
      ? (
          mainSwarm.assigned_drone_ids ||
          backendState?.fleet?.main_swarm_drone_ids ||
          []
        ).map(numericBackendId)
      : []
  );

  const currentMission =
    deployment.mission_name ||
    deployment.mission_id ||
    activeOperation?.operation ||
    activeOperation?.name ||
    "No active mission";

  return (
    <main className="dashboard">
      <section className="hero-section">
        <div>
          <p className="eyebrow">FLEET MANAGEMENT</p>
          <h2>
            Drone <span>Fleet</span>
          </h2>
          <p className="hero-description">
            Monitor the availability, health, mission assignment and
            operational status of the VayuNetra drone swarm.
          </p>
        </div>

        <div className="mission-status">
          <span className="status-dot"></span>
          {connection === "CONNECTED"
            ? "Live Fleet Monitoring"
            : connection === "RECONNECTING"
              ? "Reconnecting to Backend"
              : "Demo Fleet Data"}
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="dashboard-card">
          <div className="card-icon">🚁</div>
          <div>
            <p>TOTAL FLEET</p>
            <h3>{counts.total}</h3>
            <span>Maximum fleet capacity</span>
          </div>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">✓</div>
          <div>
            <p>AVAILABLE</p>
            <h3>{counts.available}</h3>
            <span>Ready for deployment</span>
          </div>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">⚡</div>
          <div>
            <p>ACTIVE</p>
            <h3>{counts.active}</h3>
            <span>Assessment and swarm drones</span>
          </div>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">🔋</div>
          <div>
            <p>CHARGING</p>
            <h3>{counts.charging}</h3>
            <span>Returning to readiness</span>
          </div>
        </div>
      </section>

      <section className="map-panel" style={{ marginTop: "18px" }}>
        <div className="panel-header">
          <div>
            <p>LIVE FLEET STATUS</p>
            <h3>Current Deployment</h3>
          </div>

          <span className="map-status">{counts.total} UNITS</span>
        </div>

        <div style={{ padding: "25px" }}>
          <div className="action-item">
            <span className="action-indicator"></span>
            <div>
              <strong>{counts.active} drones active</strong>
              <p>
                {deployment.status || "Fleet is ready for mission activity"}
              </p>
            </div>
          </div>

          <div className="action-item">
            <span className="action-indicator"></span>
            <div>
              <strong>
                {assessmentIds.size} assessment drones
              </strong>
              <p>
                {assessmentIds.size > 0
                  ? "DR-001 to DR-004 are reserved for initial assessment."
                  : "No assessment team is currently deployed."}
              </p>
            </div>
          </div>

          <div className="action-item">
            <span className="action-indicator"></span>
            <div>
              <strong>{mainSwarmIds.size} main-swarm drones</strong>
              <p>
                {mainSwarmIds.size > 0
                  ? `Assigned to dynamic priority zones for ${currentMission}.`
                  : "Main swarm has not been allocated yet."}
              </p>
            </div>
          </div>

          <div className="action-item">
            <span className="action-indicator waiting"></span>
            <div>
              <strong>{counts.available} reserve drones</strong>
              <p>
                Available capacity remains outside the current mission
                allocation.
              </p>
            </div>
          </div>

          {counts.unavailable > 0 && (
            <div className="action-item">
              <span
                className="action-indicator"
                style={{ background: "#64748b" }}
              ></span>
              <div>
                <strong>{counts.unavailable} drones unavailable</strong>
                <p>Offline, disabled or undergoing maintenance.</p>
              </div>
            </div>
          )}
        </div>
      </section>

      <section className="map-panel" style={{ marginTop: "18px" }}>
        <div className="panel-header">
          <div>
            <p>128-DRONE FLEET</p>
            <h3>Drone Units</h3>
          </div>

          <span className="map-status">
            {connection === "CONNECTED" ? "LIVE" : "LOCAL"}
          </span>
        </div>

        <div
          style={{
            padding: "25px",
            display: "grid",
            gap: "10px",
          }}
        >
          {displayDrones.map((drone) => {
            const isAssessment = assessmentIds.has(drone.backendId);
            const isMainSwarm = mainSwarmIds.has(drone.backendId);

            let displayStatus = drone.status;
            let mission = drone.mission || "Station";
            let zone = drone.zone || "—";

            if (isAssessment) {
              displayStatus = "ACTIVE";
              mission = currentMission || "Initial Assessment";
              zone = "ASSESSMENT";
            } else if (isMainSwarm) {
              displayStatus = "ACTIVE";
              mission = currentMission || "Main Swarm";
              zone = drone.zone || "DYNAMIC ZONE";
            }

            return (
              <div
                key={drone.backendId}
                className="dashboard-card"
                style={{
                  display: "grid",
                  gridTemplateColumns:
                    "110px 120px minmax(180px, 1fr) 130px 110px 140px",
                  alignItems: "center",
                  gap: "18px",
                }}
              >
                <div>
                  <p>DRONE</p>
                  <h3>{drone.id}</h3>
                </div>

                <div>
                  <p>STATUS</p>
                  <strong>{displayStatus}</strong>
                </div>

                <div>
                  <p>MISSION</p>
                  <span>{mission}</span>
                </div>

                <div>
                  <p>ZONE</p>
                  <span>{zone}</span>
                </div>

                <div>
                  <p>BATTERY</p>
                  <span>🔋 {drone.battery ?? "—"}%</span>
                </div>

                <div>
                  <p>DETECTION</p>
                  <span>
                    {drone.survivorsDetected ?? 0} survivors
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <section className="map-panel" style={{ marginTop: "18px" }}>
        <div
          style={{
            padding: "18px",
            color: "#697386",
            fontSize: "10px",
          }}
        >
          <strong>Fleet accounting:</strong>{" "}
          128 = maximum fleet capacity · 4 assessment drones are reserved
          during initial assessment · main-swarm allocation is dynamic ·
          remaining drones stay available as reserve.
        </div>
      </section>
    </main>
  );
}

export default Drones;

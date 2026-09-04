import { useEffect, useState } from "react";

import { missions, drones } from "../data/demoData";

import {
  getActiveOperation,
  saveActiveOperation,
  clearActiveOperation,
  addToHistory
} from "../data/operationStorage";


/* ============================================================
   BACKEND
============================================================ */

const API_BASE = "http://127.0.0.1:8000";


/* ============================================================
   GEOCODING
   OpenStreetMap Nominatim
============================================================ */

const GEOCODING_API =
  "https://nominatim.openstreetmap.org";


/* ============================================================
   FIXED ADMIN BASE
============================================================ */

const ADMIN_BASE = {
  name: "New Horizon College of Engineering",
  city: "Bengaluru",
  state: "Karnataka",
  country: "India"
};


/* ============================================================
   DRONE ROLES
============================================================ */

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


/* ============================================================
   LOCATION SEARCH
============================================================ */

async function searchLocation(locationText) {

  const query = locationText.trim();

  if (!query) {
    return [];
  }

  const nominatimUrl =
    `${GEOCODING_API}/search?format=jsonv2&limit=8&countrycodes=in&addressdetails=1&dedupe=1&accept-language=en&q=${encodeURIComponent(
      query
    )}`;

  const normaliseResults = (results, source) =>
    (Array.isArray(results) ? results : [])
      .filter(
        result =>
          result &&
          result.lat != null &&
          result.lon != null &&
          result.display_name
      )
      .map(result => ({
        name: result.display_name,
        latitude: Number(result.lat),
        longitude: Number(result.lon),
        type: result.type || null,
        source
      }))
      .filter(
        result =>
          Number.isFinite(result.latitude) &&
          Number.isFinite(result.longitude)
      );

  try {

    const response =
      await fetch(
        nominatimUrl,
        {
          headers: {
            Accept:
              "application/json"
          }
        }
      );

    if (response.ok) {

      const results =
        await response.json();

      const normalised =
        normaliseResults(
          results,
          "OpenStreetMap"
        );

      if (normalised.length) {
        return normalised;
      }
    }

  } catch (error) {

    console.warn(
      "Nominatim search failed:",
      error
    );

  }

  /*
    Nominatim can be strict with misspelled village/locality
    names. Photon is used only as a fallback to improve
    partial/spelling-tolerant place discovery.
  */

  try {

    const photonResponse =
      await fetch(
        `https://photon.komoot.io/api/?limit=10&q=${encodeURIComponent(
          query
        )}`,
        {
          headers: {
            Accept:
              "application/json"
          }
        }
      );

    if (photonResponse.ok) {

      const photonData =
        await photonResponse.json();

      const photonResults =
        (photonData?.features || [])
          .filter(feature => {

            const country =
              String(
                feature?.properties?.country || ""
              ).toLowerCase();

            return (
              !country ||
              country.includes("india")
            );

          })
          .map(feature => {

            const coordinates =
              feature?.geometry?.coordinates || [];

            const properties =
              feature?.properties || {};

            const parts =
              [
                properties.name,
                properties.city,
                properties.state,
                properties.country
              ].filter(Boolean);

            return {
              name:
                parts.join(", "),
              latitude:
                Number(coordinates[1]),
              longitude:
                Number(coordinates[0]),
              type:
                properties.type || null,
              source:
                "Photon / OpenStreetMap"
            };

          })
          .filter(
            result =>
              result.name &&
              Number.isFinite(
                result.latitude
              ) &&
              Number.isFinite(
                result.longitude
              )
          );

      return photonResults;

    }

  } catch (error) {

    console.warn(
      "Photon fallback failed:",
      error
    );

  }

  return [];

}


/* ============================================================
   REVERSE LOCATION
============================================================ */

async function reverseLocation(
  latitude,
  longitude
) {

  const response = await fetch(
    `${GEOCODING_API}/reverse?format=jsonv2&lat=${encodeURIComponent(
      latitude
    )}&lon=${encodeURIComponent(
      longitude
    )}&zoom=18&addressdetails=1`,
    {
      headers: {
        Accept: "application/json"
      }
    }
  );


  if (!response.ok) {
    throw new Error(
      "Reverse geocoding failed."
    );
  }


  const result =
    await response.json();


  if (
    !result ||
    !result.display_name
  ) {
    return null;
  }


  return {

    name:
      result.display_name,

    latitude:
      Number(result.lat),

    longitude:
      Number(result.lon),

    type:
      result.type || null,

    source:
      "OpenStreetMap"

  };

}


/* ============================================================
   COMPONENT
============================================================ */

function Missions() {


  /* ==========================================================
     EXISTING RESCUE SCENARIOS
  ========================================================== */

  const rescueScenarios =
    missions.map((mission) => ({

      id:
        mission.id,

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
        mission.name ===
        "Flood Rescue"
          ? "Flooding reported in a residential area. Multiple people may be stranded on rooftops."
          : mission.name ===
            "Landslide Search"
          ? "Landslide has blocked access roads. Search operation required to locate trapped survivors."
          : "Structural assessment and survivor detection required in the affected area."

    }));


  /* ==========================================================
     EXISTING MISSION STATE
  ========================================================== */

  const [rescueRequest, setRescueRequest] =
    useState(null);

  const [missionStatus, setMissionStatus] =
    useState("pending");

  const [allocatedDrones, setAllocatedDrones] =
    useState([]);

  const [activeOperation, setActiveOperation] =
    useState(() => {

        return getActiveOperation();

    });


  /* ==========================================================
     NEW MISSION
  ========================================================== */

  const [showNewMission, setShowNewMission] =
    useState(false);

  const [newMissionName, setNewMissionName] =
    useState("");

  const [incidentLocation, setIncidentLocation] =
    useState("");

  const [incidentLatitude, setIncidentLatitude] =
    useState("");

  const [incidentLongitude, setIncidentLongitude] =
    useState("");

  const [missionMode, setMissionMode] =
    useState("SIMULATION");


  /* ==========================================================
     LOCATION STATE
  ========================================================== */

  const [resolvedLocation, setResolvedLocation] =
    useState(null);

  const [locationSearching, setLocationSearching] =
    useState(false);

  const [locationSearchError, setLocationSearchError] =
    useState("");

  const [coordinatesTouched, setCoordinatesTouched] =
    useState(false);

  const [locationSuggestions, setLocationSuggestions] =
    useState([]);

  const [showLocationSuggestions, setShowLocationSuggestions] =
    useState(false);

  const [locationSearchRequest, setLocationSearchRequest] =
    useState(0);


  /* ==========================================================
     BACKEND LIVE STATE
  ========================================================== */

  const [backendMission, setBackendMission] =
    useState(null);

  const [deployment, setDeployment] =
    useState(null);


  /* ==========================================================
     GENERAL ERRORS
  ========================================================== */

  const [missionError, setMissionError] =
    useState("");

  const [isConfiguring, setIsConfiguring] =
    useState(false);


  /* ==========================================================
     STOP CONFIRMATION
  ========================================================== */

  const [showStopConfirm, setShowStopConfirm] =
    useState(false);

  const [showFinalStopConfirm, setShowFinalStopConfirm] =
    useState(false);


  /* ==========================================================
     RESTORE ACTIVE OPERATION
  ========================================================== */

  // ==========================================================
// MAX OPERATION TIMER
// Keeps mission alive for 4 hours.
// Only stops automatically after timeout.
// ==========================================================


// ==========================================
// RESTORE STORED ACTIVE MISSION
// ==========================================

useEffect(() => {

    const stored =
        getActiveOperation();


    if(!stored){
        return;
    }


    console.log(
        "Restored mission:",
        stored
    );


    setActiveOperation(
        stored
    );


    setMissionStatus(
        stored.status || "active"
    );


    if(
        stored.allocatedDrones
    ){

        setAllocatedDrones(
            stored.allocatedDrones
        );

    }


    if(
        stored.deployment
    ){

        setDeployment(
            stored.deployment
        );

    }


},[]);


  /* ==========================================================
     LIVE WEBSOCKET
  ========================================================== */

  useEffect(() => {

    let socket = null;

    let reconnectTimer = null;

    let stopped = false;


    const connect = () => {

      if (stopped) {
        return;
      }


      socket =
        new WebSocket(
          "ws://127.0.0.1:8000/ws"
        );


      socket.onmessage =
        (event) => {

          try {

            const state =
              JSON.parse(
                event.data
              );


            if (
              state.mission
            ) {

              setBackendMission(
                state.mission
              );

              // Backend controls the mission lifecycle.
              const backendStatus =
                state.mission.status;

              if (
                backendStatus === "MAIN_SWARM_DEPLOYED" ||
                backendStatus === "SWARM_DEPLOYED"
              ) {

                setMissionStatus(
                  "active"
                );

              } else if (
                backendStatus === "STOPPED" ||
                backendStatus === "COMPLETED"
              ) {

                setMissionStatus(
                  "pending"
                );

              }

            }


            if (
              state.deployment
            ) {

              setDeployment(
                state.deployment
              );

              /*
                Backend is the source of truth for swarm allocation.
                This keeps the Missions page synchronized with the
                dynamically allocated main swarm and its zone mapping.
              */
              const backendMainSwarm =
                state.deployment.main_swarm || {};

              const backendDroneIds =
                backendMainSwarm.assigned_drone_ids || [];

              if (backendDroneIds.length > 0) {

                const zoneMap =
                  backendMainSwarm.drone_zone_map ||
                  {};

                const zoneByDrone =
                  Object.keys(zoneMap).length > 0
                    ? zoneMap
                    : Object.fromEntries(
                        (backendMainSwarm.zone_allocations || [])
                          .flatMap(zone =>
                            (zone.allocated_drone_ids || []).map(id => [
                              String(id),
                              zone.id
                            ])
                          )
                      );

                const liveAllocated =
                  backendDroneIds.map((droneId, index) => {

                    const originalDrone =
                      drones.find(
                        drone =>
                          Number(drone.id) ===
                          Number(droneId)
                      );

                    const zoneId =
                      zoneByDrone[String(droneId)] ||
                      "-";

                    return {
                      id:
                        `DR-${String(Number(droneId) + 1).padStart(3, "0")}`,

                      backendId:
                        Number(droneId),

                      role:
                        droneRoles[
                          index % droneRoles.length
                        ],

                      status:
                        backendMainSwarm.status === "DEPLOYED"
                          ? "Deployed"
                          : "Deploying",

                      battery:
                        originalDrone?.battery ??
                        90,

                      survivors:
                        originalDrone?.survivorsDetected ??
                        0,

                      zoneId,

                      path:
                        state.deployment.direct_feasible
                          ? "Admin Base → Incident"
                          : "Forward Base → Incident",

                      position:
                        originalDrone
                          ? `${originalDrone.latitude}, ${originalDrone.longitude}`
                          : "Live backend telemetry"

                    };

                  });

                setAllocatedDrones(
                  liveAllocated
                );

                setActiveOperation(
                  current => {

                    if (!current) {
                      return current;
                    }

                    const updated = {
                      ...current,

                      status:
                        backendMainSwarm.status === "DEPLOYED"
                          ? "ACTIVE"
                          : current.status,

                      dronesRequired:
                        backendDroneIds.length,

                      assignedDrones:
                        liveAllocated.map(
                          drone => drone.id
                        ),

                      backendDroneIds,

                      deploymentMode:
                        backendMainSwarm.deployment_method ||
                        (state.deployment.direct_feasible
                          ? "AUTOMATIC"
                          : "FORWARD_BASE"),

                      launchPoint:
                        backendMainSwarm.launch_point ||
                        current.launchPoint,

                      progress:
                        Number(
                          backendMainSwarm.zone_arrival_progress_percent || 0
                        )

                    };

                    saveActiveOperation(
                      updated
                    );

                    return updated;

                  }
                );

              }

            }

          } catch (error) {

            console.error(
              "Failed to parse VayuNetra state:",
              error
            );

          }

        };


      socket.onclose = () => {

        if (stopped) {
          return;
        }


        reconnectTimer =
          setTimeout(
            connect,
            1500
          );

      };


      socket.onerror = () => {

        try {

          socket.close();

        } catch {

          // Ignore cleanup error.

        }

      };

    };


    connect();


    return () => {

      stopped = true;


      if (reconnectTimer) {

        clearTimeout(
          reconnectTimer
        );

      }


      try {

        socket?.close();

      } catch {

        // Ignore cleanup error.

      }

    };

  }, []);


  /* ==========================================================
     GOOGLE-STYLE LOCATION AUTOCOMPLETE
  ========================================================== */

  useEffect(() => {

    const query =
      incidentLocation.trim();

    if (
      query.length < 2 ||
      coordinatesTouched
    ) {

      setLocationSuggestions([]);
      setShowLocationSuggestions(false);

      return;

    }

    let cancelled = false;

    const timer =
      setTimeout(
        async () => {

          try {

            const results =
              await searchLocation(query);

            if (cancelled) {
              return;
            }

            setLocationSuggestions(
              results.slice(0, 8)
            );

            setShowLocationSuggestions(
              results.length > 0
            );

          } catch (error) {

            if (!cancelled) {

              console.warn(
                "Location autocomplete failed:",
                error
              );

              setLocationSuggestions([]);
              setShowLocationSuggestions(false);

            }

          }

        },
        450
      );

    return () => {

      cancelled = true;

      clearTimeout(timer);

    };

  }, [
    incidentLocation,
    coordinatesTouched,
    locationSearchRequest
  ]);


  /* ==========================================================
     REVERSE GEOCODE WHEN COORDINATES ARE ENTERED
  ========================================================== */

  useEffect(() => {

    const latitude =
      Number(
        incidentLatitude
      );

    const longitude =
      Number(
        incidentLongitude
      );


    if (
      !coordinatesTouched ||
      !incidentLatitude ||
      !incidentLongitude
    ) {

      return;

    }


    if (
      Number.isNaN(latitude) ||
      Number.isNaN(longitude) ||
      latitude < -90 ||
      latitude > 90 ||
      longitude < -180 ||
      longitude > 180
    ) {

      setResolvedLocation(
        null
      );

      setLocationSearchError(
        "Enter valid latitude and longitude values."
      );

      return;

    }


    const timer =
      setTimeout(
        async () => {

          setLocationSearching(
            true
          );

          setLocationSearchError(
            ""
          );


          try {

            const result =
              await reverseLocation(
                latitude,
                longitude
              );


            if (!result) {

              setResolvedLocation(
                null
              );

              setLocationSearchError(
                "Location could not be identified from these coordinates."
              );

              return;

            }


            setResolvedLocation(
              result
            );


            setIncidentLocation(
              result.name
            );


          } catch (error) {

            console.error(
              "Reverse geocoding error:",
              error
            );


            setLocationSearchError(
              "Unable to identify this location right now."
            );

          } finally {

            setLocationSearching(
              false
            );

          }

        },
        700
      );


    return () =>
      clearTimeout(
        timer
      );

  }, [
    incidentLatitude,
    incidentLongitude,
    coordinatesTouched
  ]);


  /* ==========================================================
     OPEN NEW MISSION
  ========================================================== */

  const openNewMission = () => {

    if (activeOperation) {
      return;
    }


    setShowNewMission(
      true
    );

    setMissionError(
      ""
    );

    setLocationSearchError(
      ""
    );

  };


  /* ==========================================================
     CLOSE NEW MISSION
  ========================================================== */

  const closeNewMission = () => {

    setShowNewMission(
      false
    );

    setMissionError(
      ""
    );

  };


  /* ==========================================================
     CREATE NEW MISSION
  ========================================================== */

  const createNewMission =
    async () => {

      setMissionError(
        ""
      );


      let coordinates =
        null;

      let finalLocationName =
        incidentLocation.trim();


      /* ------------------------------------------------------
         CASE 1
         Coordinates supplied
      ------------------------------------------------------ */

      if (
        incidentLatitude &&
        incidentLongitude
      ) {

        const latitude =
          Number(
            incidentLatitude
          );

        const longitude =
          Number(
            incidentLongitude
          );


        if (
          Number.isNaN(latitude) ||
          Number.isNaN(longitude) ||
          latitude < -90 ||
          latitude > 90 ||
          longitude < -180 ||
          longitude > 180
        ) {

          setMissionError(
            "Please enter valid latitude and longitude values."
          );

          return;

        }


        coordinates = {

          latitude,

          longitude

        };


        /*
          If reverse geocoding has already
          resolved the coordinates, use that.
        */

        if (
          resolvedLocation
        ) {

          finalLocationName =
            resolvedLocation.name;

        } else {

          try {

            setIsConfiguring(
              true
            );


            const resolved =
              await reverseLocation(
                latitude,
                longitude
              );


            if (resolved) {

              setResolvedLocation(
                resolved
              );


              finalLocationName =
                resolved.name;

            }

          } catch (error) {

            console.warn(
              "Could not reverse geocode coordinates:",
              error
            );

          } finally {

            setIsConfiguring(
              false
            );

          }

        }

      }


      /* ------------------------------------------------------
         CASE 2
         Location name supplied
      ------------------------------------------------------ */

      else if (
        incidentLocation.trim()
      ) {

        try {

          setIsConfiguring(
            true
          );


          const results =
            await searchLocation(
              incidentLocation.trim()
            );

          const result =
            results[0];

          if (!result) {

            setMissionError(
              "Location not found. Try a nearby locality, village, landmark, district or state, or provide latitude and longitude."
            );

            return;

          }

          coordinates = {

            latitude:
              result.latitude,

            longitude:
              result.longitude

          };

          finalLocationName =
            result.name;

          setResolvedLocation(
            result
          );

          setLocationSuggestions([]);

          setShowLocationSuggestions(
            false
          );

          setIncidentLatitude(
            String(
              result.latitude
            )
          );

          setIncidentLongitude(
            String(
              result.longitude
            ));


        } catch (error) {

          console.error(
            "Location search failed:",
            error
          );


          setMissionError(
            "Unable to resolve the incident location."
          );


          return;

        } finally {

          setIsConfiguring(
            false
          );

        }

      }


      /* ------------------------------------------------------
         NO LOCATION
      ------------------------------------------------------ */

      else {

        setMissionError(
          "Enter an incident location or provide latitude and longitude."
        );

        return;

      }


      if (!coordinates) {

        setMissionError(
          "The incident location could not be resolved."
        );

        return;

      }


      setIsConfiguring(
        true
      );


      try {

        const response =
          await fetch(
            `${API_BASE}/api/mission/configure`,
            {
              method:
                "POST",

              headers: {
                "Content-Type":
                  "application/json"
              },

              body:
                JSON.stringify({

                  name:
                    newMissionName.trim()
                    ||
                    "VayuNetra Operation",

                  latitude:
                    coordinates.latitude,

                  longitude:
                    coordinates.longitude,

                  location_name:
                    finalLocationName,

                  mode:
                    missionMode

                })

            }
          );


        if (!response.ok) {

          throw new Error(
            `Backend returned ${response.status}`
          );

        }


        const result =
          await response.json();


        if (
          result.configured ===
          false
        ) {

          throw new Error(
            result.reason ||
            "Mission configuration failed."
          );

        }


        /*
          Store backend mission data.
        */

        setBackendMission({

          id:
            result.mission_id,

          name:
            newMissionName.trim()
            ||
            "VayuNetra Operation",

          mode:
            missionMode,

          status:
            "PLANNING",

          incident_location:
            finalLocationName,

          latitude:
            coordinates.latitude,

          longitude:
            coordinates.longitude,

          admin_base:
            ADMIN_BASE

        });


        if (
          result.deployment
        ) {

          setDeployment(
            result.deployment
          );

        }


        /*
          Create frontend active operation.
        */

        const operation = {

          id:
            result.mission_id
            ||
            `OP-${Date.now()}`,

          requestId:
            null,

          operation:
            newMissionName.trim()
            ||
            "VayuNetra Operation",

          disaster:
            "Unknown / Under Assessment",

          location:
            finalLocationName,

          latitude:
            coordinates.latitude,

          longitude:
            coordinates.longitude,

          mode:
            missionMode,

          survivors:
            0,

          priority:
            "PENDING",

          dronesRequired:
            0,

          assignedDrones:
            [],

          progress:
            0,

          status:
            "PLANNING",

          startedAt:
            new Date().toISOString()

        };


        saveActiveOperation(
          operation
        );


        setActiveOperation(
          operation
        );


        setMissionStatus(
          "planning"
        );


        setRescueRequest(
          null
        );


        setAllocatedDrones(
          []
        );


        setShowNewMission(
          false
        );


      } catch (error) {

        console.error(
          "Mission configuration failed:",
          error
        );


        setMissionError(
          "Could not connect to the VayuNetra backend. Make sure the server is running."
        );

      } finally {

        setIsConfiguring(
          false
        );

      }

    };


  /* ==========================================================
     START MOBILE ZONE
  ========================================================== */

  const startMobileZone =
    async () => {

      try {

        const response =
          await fetch(
            `${API_BASE}/api/mission/mobile-zone/start`,
            {
              method:
                "POST"
            }
          );

        const result =
          await response.json();

        if (!response.ok || !result.started) {

          throw new Error(
            result.reason ||
            "Mobile Zone could not be started."
          );

        }

        setMissionStatus(
          "mobile-zone"
        );

      } catch (error) {

        console.error(
          "Mobile Zone start failed:",
          error
        );

        alert(
          error.message ||
          "Unable to start the Mobile Zone."
        );

      }

    };


  /* ==========================================================
     START RECON
  ========================================================== */

  const startRecon =
    async () => {

      try {

        const response =
          await fetch(
            `${API_BASE}/api/mission/recon/start`,
            {
              method:
                "POST"
            }
          );


        const result =
          await response.json();


        if (!response.ok) {

          throw new Error(
            result.detail ||
            "Reconnaissance failed."
          );

        }


        setMissionStatus(
          "recon"
        );

      } catch (error) {

        console.error(
          "Recon start failed:",
          error
        );


        alert(
          "Unable to start reconnaissance. Check that the backend is running."
        );

      }

    };


  /* ==========================================================
     COMPLETE RECON
  ========================================================== */

  const completeRecon =
    async (
      candidateViable
    ) => {

      try {

        const response =
          await fetch(
            `${API_BASE}/api/mission/recon/complete`,
            {
              method:
                "POST",

              headers: {
                "Content-Type":
                  "application/json"
              },

              body:
                JSON.stringify({

                  candidate_viable:
                    candidateViable,

                  hazards:
                    [],

                  communication_quality:
                    "GOOD",

                  accessibility:
                    "ASSESSMENT_PENDING"

                })

            }
          );


        const result =
          await response.json();


        if (!response.ok) {

          throw new Error(
            result.detail ||
            "Recon completion failed."
          );

        }


        if (
          candidateViable
        ) {

          setMissionStatus(
            "forward-base"
          );

        } else {

          setMissionStatus(
            "reposition"
          );

        }

      } catch (error) {

        console.error(
          "Recon completion failed:",
          error
        );


        alert(
          "Unable to submit reconnaissance assessment."
        );

      }

    };


  /* ==========================================================
     DEPLOY MAIN SWARM
  ========================================================== */

  const deployMainSwarm =
    async () => {

      try {

        const response =
          await fetch(
            `${API_BASE}/api/mission/deploy`,
            {
              method:
                "POST"
            }
          );


        const result =
          await response.json();


        if (!response.ok) {

          throw new Error(
            result.detail ||
            "Deployment failed."
          );

        }


        if (
          !result.deployed
        ) {

          alert(
            result.reason ||
            "Main swarm cannot be deployed yet."
          );

          return;

        }


        /*
          Backend is the source of truth for dynamic allocation.
          Never rebuild the swarm from the static demoData list.
        */

        const backendDroneIds =
          deployment?.main_swarm?.assigned_drone_ids ||
          result.assigned_drone_ids ||
          [];

        const zoneMap =
          deployment?.main_swarm?.drone_zone_map ||
          {};

        const allocated =
          backendDroneIds.map(
            (
              droneId,
              index
            ) => {

              const originalDrone =
                drones.find(
                  drone =>
                    Number(drone.id) ===
                    Number(droneId)
                );

              return {

                id:
                  `DR-${String(Number(droneId) + 1).padStart(3, "0")}`,

                backendId:
                  Number(droneId),

                role:
                  droneRoles[
                    index %
                    droneRoles.length
                  ],

                status:
                  "Deployed",

                battery:
                  originalDrone?.battery ??
                  90,

                survivors:
                  originalDrone?.survivorsDetected ??
                  0,

                zoneId:
                  zoneMap[String(droneId)] ||
                  "-",

                path:
                  result.mode ===
                  "FORWARD_BASE"
                    ? "Forward Base → Incident"
                    : "Admin Base → Incident",

                position:
                  originalDrone
                    ? `${originalDrone.latitude}, ${originalDrone.longitude}`
                    : "Live backend telemetry"

              };

            }
          );


        setAllocatedDrones(
          allocated
        );


        setActiveOperation(
          current => {

            if (!current) {
              return current;
            }


            const updated = {

              ...current,

              status:
                "ACTIVE",

              dronesRequired:
                allocated.length,

              assignedDrones:
                allocated.map(
                  drone =>
                    drone.id
                ),

              deploymentMode:
                result.mode,

              launchPoint:
                result.launch_point,

              progress:
                0

            };


            saveActiveOperation(
              updated
            );


            return updated;

          }
        );


        setMissionStatus(
          "active"
        );


      } catch (error) {

        console.error(
          "Main swarm deployment failed:",
          error
        );


        alert(
          "Unable to deploy the main swarm."
        );

      }

    };


  /* ==========================================================
     EXISTING RESCUE REQUEST
  ========================================================== */

  const simulateRescueRequest =
    () => {

      if (activeOperation) {
        return;
      }


      const randomIndex =
        Math.floor(
          Math.random() *
          rescueScenarios.length
        );


      const selectedScenario =
        rescueScenarios[
          randomIndex
        ];


      setRescueRequest({

        ...selectedScenario,

        time:
          new Date().toLocaleTimeString()

      });


      setMissionStatus(
        "pending"
      );


      setAllocatedDrones(
        []
      );

    };


  /* ==========================================================
     ACCEPT RESCUE MISSION
  ========================================================== */

  const acceptMission =
    () => {

      if (!rescueRequest) {
        return;
      }


      const required =
        Number(
          rescueRequest.dronesRequired
        ) || 4;


      const availableDrones =
        drones
          .filter(
            drone =>
              drone.status ===
              "AVAILABLE"
          )
          .slice(
            0,
            required
          );


      if (
        availableDrones.length <
        required
      ) {

        alert(
          `Only ${availableDrones.length} drones are currently available.`
        );

        return;

      }


      const allocated =
        availableDrones.map(
          (
            drone,
            index
          ) => ({

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
              drone.battery ??
              90,

            survivors:
              drone.survivorsDetected ??
              0,

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


  /* ==========================================================
     REJECT RESCUE REQUEST
  ========================================================== */

  const rejectRequest =
    () => {

      setRescueRequest(
        null
      );


      setMissionStatus(
        "pending"
      );


      setAllocatedDrones(
        []
      );

    };


  /* ==========================================================
     START EXISTING MISSION
  ========================================================== */

  const startMission =
    () => {

      if (
        !rescueRequest ||
        allocatedDrones.length ===
          0
      ) {

        return;

      }


      const operationId =
        `OP-${Date.now()}`;


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

        assignedDrones:
          allocatedDrones.map(
            drone =>
              drone.id
          ),

        progress:
          0,

        status:
          "ACTIVE",

        startedAt:
          new Date().toISOString()

      };


      saveActiveOperation(
        operation
      );


      setActiveOperation(
        operation
      );


      setMissionStatus(
        "active"
      );


      setAllocatedDrones(
        previousDrones =>

          previousDrones.map(
            drone => ({

              ...drone,

              status:
                drone.role ===
                "Search"
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


  /* ==========================================================
     EXISTING PROGRESS
  ========================================================== */

  useEffect(() => {

    if (
      !activeOperation ||
      activeOperation.status !==
        "ACTIVE" ||
      backendMission
    ) {

      return;

    }


    const timer =
      setInterval(
        () => {

          setActiveOperation(
            current => {

              if (!current) {
                return null;
              }
const nextProgress =
  Math.min(
    Number(current.progress || 0) + 0.01,
    99
  );


const updatedOperation = {

    ...current,

    progress:
        nextProgress,

    status:
        "ACTIVE"

};


saveActiveOperation(
    updatedOperation
);


return updatedOperation;
            }

             

              
          );

        },
        3000
      );


    return () =>
      clearInterval(
        timer
      );

  }, [
    activeOperation?.id
  ]);


  /* ==========================================================
     STOP MISSION
  ========================================================== */
const handleStopMission =
  async () => {

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


    // Save in history
    addToHistory(
      stoppedOperation
    );


    // Remove active mission permanently
    localStorage.removeItem(
      "vayunetra_active_operation"
    );


    // Clear React state
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


    setBackendMission(
      current =>
        current
          ? {
              ...current,
              status:
                "STOPPED"
            }
          : current
    );


    setDeployment(
      current =>
        current
          ? {
              ...current,
              status:
                "STOPPED"
            }
          : current
    );

};
  


  const continueStopMission =
    () => {

      setShowStopConfirm(
        false
      );


      setShowFinalStopConfirm(
        true
      );

    };


  const confirmStopMission =
    async () => {

      if (!activeOperation) {
        return;
      }

      try {

        const response =
          await fetch(
            `${API_BASE}/api/mission/stop`,
            {
              method:
                "POST",
              headers: {
                "Content-Type":
                  "application/json"
              },
              body:
                JSON.stringify({
                  reason:
                    "operator_stop"
                })
            }
          );

        if (!response.ok) {

          const errorBody =
            await response.text();

          throw new Error(
            errorBody ||
            `Stop request failed with ${response.status}`
          );

        }

      } catch (error) {

        console.error(
          "Backend mission stop failed:",
          error
        );

        alert(
          "The backend could not stop the mission. Please make sure the VayuNetra server is running."
        );

        return;

      }


      const stoppedOperation =
        {

          ...activeOperation,

          status:
            "STOPPED",

          stoppedAt:
            new Date().toISOString()

        };


      addToHistory(
        stoppedOperation
      );


      clearActiveOperation();
localStorage.removeItem(
  "vayunetra_active_operation"
);

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


      setBackendMission(
        current =>
          current
            ? {
                ...current,
                status:
                  "STOPPED"
              }
            : current
      );


      setDeployment(
        current =>
          current
            ? {
                ...current,
                status:
                  "STOPPED"
              }
            : current
      );


      setShowFinalStopConfirm(
        false
      );

    };


  const cancelStop =
    () => {

      setShowStopConfirm(
        false
      );


      setShowFinalStopConfirm(
        false
      );

    };


  /* ==========================================================
     DEPLOYMENT STATE
  ========================================================== */

  const deploymentStatus =
    deployment?.status ||
    "WAITING_FOR_LOCATION";


  const directFeasible =
    deployment?.direct_feasible;

// ==========================================
// PERSIST ACTIVE MISSION STATE
// ==========================================

useEffect(() => {

    if (activeOperation) {

        saveActiveOperation(
            activeOperation
        );

    }

}, [
    activeOperation
]);
  /* ==========================================================
     RENDER
  ========================================================== */

  return (

    <main className="dashboard">


      {/* ======================================================
          HEADER
      ====================================================== */}

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


        <div
          style={{
            display:
              "flex",
            alignItems:
              "center",
            gap:
              "10px"
          }}
        >

          <button
            type="button"
            onClick={
              openNewMission
            }
            disabled={
              Boolean(
                activeOperation
              )
            }
            style={{
              cursor:
                activeOperation
                  ? "not-allowed"
                  : "pointer",
              padding:
                "10px 16px",
              borderRadius:
                "7px",
              fontWeight:
                "700"
            }}
          >
            NEW MISSION
          </button>


          <div className="mission-status">

            <span className="status-dot"></span>

            {missionStatus ===
            "active"

              ? "Mission Active"

              : missionStatus ===
                "planning"

              ? "Mission Planning"

              : missionStatus ===
                "recon"

              ? "Recon In Progress"

              : missionStatus ===
                "forward-base"

              ? "Forward Base Selected"

              : missionStatus ===
                "reposition"

              ? "Reposition Required"

              : missionStatus ===
                "accepted"

              ? "Mission Accepted"

              : rescueRequest

              ? "Rescue Request Received"

              : "Awaiting Rescue Request"}

          </div>

        </div>

      </section>


      {/* ======================================================
          ALWAYS-VISIBLE ACTIVE MISSION STOP CONTROL
      ====================================================== */}

      {activeOperation &&
        activeOperation.status !==
          "STOPPED" && (

        <div
          style={{
            position:
              "sticky",
            top:
              "10px",
            zIndex:
              900,
            display:
              "flex",
            justifyContent:
              "flex-end",
            marginTop:
              "12px"
          }}
        >

          <button
            type="button"
            onClick={
              handleStopMission
            }
            style={{
              cursor:
                "pointer",
              padding:
                "11px 18px",
              borderRadius:
                "7px",
              border:
                "1px solid rgba(255,80,80,0.60)",
              background:
                "rgba(127,29,29,0.95)",
              color:
                "#ffffff",
              fontWeight:
                "800",
              letterSpacing:
                "0.5px",
              boxShadow:
                "0 6px 18px rgba(0,0,0,0.30)"
            }}
          >
            STOP MISSION
          </button>

        </div>

      )}


      {/* ======================================================
          NEW MISSION
      ====================================================== */}

      {showNewMission && (

        <section
          className="map-panel"
          style={{
            marginTop:
              "18px"
          }}
        >

          <div className="panel-header">

            <div>

              <p>
                MISSION CREATION
              </p>

              <h3>
                New Mission
              </h3>

            </div>


            <span className="map-status">
              PLANNING
            </span>

          </div>


          <div
            style={{
              padding:
                "22px"
            }}
          >

            {/* ------------------------------------------------
                MISSION NAME
            ------------------------------------------------ */}

            <div>

              <label
                style={labelStyle}
              >
                MISSION NAME
              </label>


              <input
                type="text"
                value={
                  newMissionName
                }
                onChange={
                  event =>
                    setNewMissionName(
                      event.target.value
                    )
                }
                placeholder="Operation Phoenix"
                style={
                  inputStyle
                }
              />

            </div>


            {/* ------------------------------------------------
                LOCATION NAME
            ------------------------------------------------ */}

            <div
              style={{
                marginTop:
                  "18px"
              }}
            >

              <label
                style={labelStyle}
              >
                INCIDENT LOCATION
              </label>


              <div
                style={{
                  position:
                    "relative"
                }}
              >

                <input
                  type="text"
                  value={
                    incidentLocation
                  }
                  onFocus={() => {

                    if (
                      locationSuggestions.length
                    ) {

                      setShowLocationSuggestions(
                        true
                      );

                    }

                  }}
                  onChange={
                    event => {

                      const value =
                        event.target.value;

                      setIncidentLocation(
                        value
                      );

                      setResolvedLocation(
                        null
                      );

                      setLocationSearchError(
                        ""
                      );

                      setCoordinatesTouched(
                        false
                      );

                      setMissionError(
                        ""
                      );

                      setLocationSearchRequest(
                        previous =>
                          previous + 1
                      );

                    }
                  }
                  onKeyDown={
                    event => {

                      if (
                        event.key ===
                        "Escape"
                      ) {

                        setShowLocationSuggestions(
                          false
                        );

                      }

                    }
                  }
                  placeholder="Start typing a village, town, city or landmark..."
                  style={
                    inputStyle
                  }
                />


                {showLocationSuggestions &&
                  locationSuggestions.length >
                    0 && (

                  <div
                    style={{
                      position:
                        "absolute",
                      left:
                        0,
                      right:
                        0,
                      top:
                        "calc(100% + 4px)",
                      zIndex:
                        1000,
                      maxHeight:
                        "280px",
                      overflowY:
                        "auto",
                      border:
                        "1px solid rgba(255,255,255,0.12)",
                      borderRadius:
                        "8px",
                      background:
                        "#15131f",
                      boxShadow:
                        "0 12px 30px rgba(0,0,0,0.45)"
                    }}
                  >

                    {locationSuggestions.map(
                      (
                        suggestion,
                        index
                      ) => (

                        <button
                          key={`${suggestion.latitude}-${suggestion.longitude}-${index}`}
                          type="button"
                          onMouseDown={
                            event => {
                              event.preventDefault();
                            }
                          }
                          onClick={() => {

                            setIncidentLocation(
                              suggestion.name
                            );

                            setIncidentLatitude(
                              String(
                                suggestion.latitude
                              )
                            );

                            setIncidentLongitude(
                              String(
                                suggestion.longitude
                              )
                            );

                            setResolvedLocation(
                              suggestion
                            );

                            setLocationSuggestions(
                              []
                            );

                            setShowLocationSuggestions(
                              false
                            );

                            setCoordinatesTouched(
                              false
                            );

                            setLocationSearchError(
                              ""
                            );

                            setMissionError(
                              ""
                            );

                          }}
                          style={{
                            display:
                              "block",
                            width:
                              "100%",
                            padding:
                              "11px 13px",
                            border:
                              "none",
                            borderBottom:
                              "1px solid rgba(255,255,255,0.05)",
                            background:
                              "transparent",
                            color:
                              "#e6e8f0",
                            textAlign:
                              "left",
                            cursor:
                              "pointer"
                          }}
                        >

                          <span
                            style={{
                              display:
                                "block",
                              fontSize:
                                "11px",
                              fontWeight:
                                "600"
                            }}
                          >
                            📍{" "}
                            {suggestion.name}
                          </span>


                          <span
                            style={{
                              display:
                                "block",
                              marginTop:
                                "4px",
                              color:
                                "#697386",
                              fontSize:
                                "9px"
                            }}
                          >
                            {suggestion.type
                              ? `${suggestion.type} • `
                              : ""}
                            {suggestion.latitude.toFixed(
                              5
                            )}
                            {" , "}
                            {suggestion.longitude.toFixed(
                              5
                            )}
                          </span>

                        </button>

                      )
                    )}

                  </div>

                )}

              </div>


              <button
                type="button"
                onClick={
                  async () => {

                    if (
                      !incidentLocation.trim()
                    ) {

                      setLocationSearchError(
                        "Enter a location to search."
                      );

                      return;

                    }

                    setLocationSearching(
                      true
                    );

                    setLocationSearchError(
                      ""
                    );

                    try {

                      const results =
                        await searchLocation(
                          incidentLocation.trim()
                        );

                      const result =
                        results[0];

                      if (!result) {

                        setResolvedLocation(
                          null
                        );

                        setLocationSearchError(
                          "Location not found. Try a nearby locality, village, landmark, district or state."
                        );

                        return;

                      }

                      setResolvedLocation(
                        result
                      );

                      setIncidentLocation(
                        result.name
                      );

                      setIncidentLatitude(
                        String(
                          result.latitude
                        )
                      );

                      setIncidentLongitude(
                        String(
                          result.longitude
                        )
                      );

                      setLocationSuggestions(
                        []
                      );

                      setShowLocationSuggestions(
                        false
                      );

                      setCoordinatesTouched(
                        false
                      );

                    } catch (
                      error
                    ) {

                      console.error(
                        "Location search error:",
                        error
                      );

                      setLocationSearchError(
                        "Unable to search for this location right now."
                      );

                    } finally {

                      setLocationSearching(
                        false
                      );

                    }

                  }
                }
                style={{
                  marginTop:
                    "8px",
                  cursor:
                    "pointer"
                }}
              >
                {locationSearching
                  ? "SEARCHING..."
                  : "🔍 SEARCH LOCATION"}
              </button>


              {resolvedLocation && (

                <div
                  style={{
                    marginTop:
                      "10px",
                    padding:
                      "12px",
                    borderRadius:
                      "8px",
                    background:
                      "rgba(34,197,94,0.06)",
                    border:
                      "1px solid rgba(34,197,94,0.20)"
                  }}
                >

                  <strong
                    style={{
                      display:
                        "block",
                      fontSize:
                        "11px"
                    }}
                  >
                    ✓ LOCATION FOUND
                  </strong>


                  <span
                    style={{
                      display:
                        "block",
                      marginTop:
                        "5px",
                      color:
                        "#aeb3c7",
                      fontSize:
                        "10px",
                      lineHeight:
                        "1.5"
                    }}
                  >
                    {
                      resolvedLocation.name
                    }
                  </span>


                  <span
                    style={{
                      display:
                        "block",
                      marginTop:
                        "5px",
                      color:
                        "#697386",
                      fontSize:
                        "9px"
                    }}
                  >
                    Coordinates:{" "}
                    {resolvedLocation.latitude.toFixed(
                      6
                    )}
                    {" , "}
                    {resolvedLocation.longitude.toFixed(
                      6
                    )}
                  </span>

                </div>

              )}


              {locationSearchError && (

                <span
                  style={{
                    display:
                      "block",
                    marginTop:
                      "7px",
                    color:
                      "#ff8b8b",
                    fontSize:
                      "10px"
                  }}
                >
                  ⚠{" "}
                  {locationSearchError}
                </span>

              )}

            </div>


            {/* ------------------------------------------------
                OPTIONAL COORDINATES
            ------------------------------------------------ */}

            <div
              style={{
                marginTop:
                  "18px"
              }}
            >

              <label
                style={labelStyle}
              >
                OPTIONAL COORDINATES
              </label>


              <div
                style={{
                  display:
                    "grid",
                  gridTemplateColumns:
                    "1fr 1fr",
                  gap:
                    "12px"
                }}
              >

                <input
                  type="number"
                  step="any"
                  value={
                    incidentLatitude
                  }
                  onChange={
                    event => {

                      setIncidentLatitude(
                        event.target.value
                      );

                      setCoordinatesTouched(
                        true
                      );

                    }
                  }
                  placeholder="Latitude e.g. 12.962100"
                  style={
                    inputStyle
                  }
                />


                <input
                  type="number"
                  step="any"
                  value={
                    incidentLongitude
                  }
                  onChange={
                    event => {

                      setIncidentLongitude(
                        event.target.value
                      );

                      setCoordinatesTouched(
                        true
                      );

                    }
                  }
                  placeholder="Longitude e.g. 76.637500"
                  style={
                    inputStyle
                  }
                />

              </div>


              <span
                style={{
                  display:
                    "block",
                  marginTop:
                    "7px",
                  color:
                    "#697386",
                  fontSize:
                    "9px"
                }}
              >
                Optional. Enter both coordinates
                and VayuNetra will automatically
                identify the corresponding location.
                Selecting a search result automatically
                updates the incident coordinates.
              </span>

            </div>


            {/* ------------------------------------------------
                OPERATION MODE
            ------------------------------------------------ */}

            <div
              style={{
                marginTop:
                  "18px"
              }}
            >

              <label
                style={labelStyle}
              >
                OPERATION MODE
              </label>


              <div
                style={{
                  display:
                    "flex",
                  gap:
                    "10px",
                  marginTop:
                    "8px"
                }}
              >

                <button
                  type="button"
                  onClick={() =>
                    setMissionMode(
                      "SIMULATION"
                    )
                  }
                  style={{
                    ...modeButtonStyle,
                    opacity:
                      missionMode ===
                      "SIMULATION"
                        ? 1
                        : 0.5
                  }}
                >
                  🧪 SIMULATION
                </button>


                <button
                  type="button"
                  onClick={() =>
                    setMissionMode(
                      "REAL"
                    )
                  }
                  style={{
                    ...modeButtonStyle,
                    opacity:
                      missionMode ===
                      "REAL"
                        ? 1
                        : 0.5
                  }}
                >
                  🌐 REAL
                </button>

              </div>

            </div>


            {/* ------------------------------------------------
                ADMIN BASE
            ------------------------------------------------ */}

            <div
              style={{
                marginTop:
                  "18px",
                padding:
                  "14px",
                borderRadius:
                  "10px",
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
                  fontSize:
                    "9px",
                  letterSpacing:
                    "1px",
                  color:
                    "#858da5"
                }}
              >
                ADMIN BASE
              </p>


              <strong>
                {ADMIN_BASE.name}
              </strong>


              <span
                style={{
                  display:
                    "block",
                  marginTop:
                    "4px",
                  color:
                    "#697386",
                  fontSize:
                    "10px"
                }}
              >
                {ADMIN_BASE.city},{" "}
                {ADMIN_BASE.state},{" "}
                {ADMIN_BASE.country}
              </span>

            </div>


            {/* ------------------------------------------------
                ERROR
            ------------------------------------------------ */}

            {missionError && (

              <div
                style={{
                  marginTop:
                    "15px",
                  padding:
                    "12px",
                  borderRadius:
                    "8px",
                  border:
                    "1px solid rgba(255,80,80,0.3)",
                  background:
                    "rgba(255,80,80,0.08)",
                  color:
                    "#ff8b8b",
                  fontSize:
                    "11px"
                }}
              >
                ⚠ {missionError}
              </div>

            )}


            {/* ------------------------------------------------
                ACTIONS
            ------------------------------------------------ */}

            <div
              style={{
                display:
                  "flex",
                justifyContent:
                  "flex-end",
                gap:
                  "10px",
                marginTop:
                  "20px"
              }}
            >

              <button
                type="button"
                onClick={
                  closeNewMission
                }
                style={{
                  cursor:
                    "pointer"
                }}
              >
                CANCEL
              </button>


              <button
                type="button"
                onClick={
                  createNewMission
                }
                disabled={
                  isConfiguring
                }
                style={{
                  cursor:
                    isConfiguring
                      ? "wait"
                      : "pointer",
                  fontWeight:
                    "700"
                }}
              >
                {isConfiguring
                  ? "CREATING..."
                  : "CREATE MISSION"}
              </button>

            </div>

          </div>

        </section>

      )}


      {/* ======================================================
          DEPLOYMENT / MOBILE ZONE CONTROL
      ====================================================== */}

      {activeOperation &&
        activeOperation.status !==
          "STOPPED" && (
        <section
          className="map-panel"
          style={{
            marginTop: "18px"
          }}
        >

          <div className="panel-header">

            <div>
              <p>DEPLOYMENT ASSESSMENT</p>
              <h3>
                {directFeasible
                  ? "Direct Deployment"
                  : "Mobile Zone Deployment"}
              </h3>
            </div>

            <span className="map-status">
              {activeOperation.mode || "SIMULATION"}
            </span>

          </div>

          <div style={{ padding: "20px" }}>

            {/* =================================================
                DEPLOYMENT DECISION
            ================================================= */}

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(4, 1fr)",
                gap: "10px"
              }}
            >

              <div className="dashboard-card">
                <p>INCIDENT</p>
                <h3>
                  {activeOperation.location}
                </h3>
              </div>

              <div className="dashboard-card">
                <p>DISTANCE FROM ADMIN BASE</p>
                <h3>
                  {deployment?.distance_km ?? "-"} km
                </h3>
              </div>

              <div className="dashboard-card">
                <p>DIRECT FLIGHT</p>
                <h3>
                  {directFeasible
                    ? "FEASIBLE"
                    : "NOT FEASIBLE"}
                </h3>
              </div>

              <div className="dashboard-card">
                <p>DEPLOYMENT DECISION</p>
                <h3>
                  {directFeasible
                    ? "DIRECT FLEET"
                    : "MOBILE ZONE"}
                </h3>
              </div>

            </div>

            {/* =================================================
                DIRECT DEPLOYMENT TAB / ACTION
            ================================================= */}

            {directFeasible && (
              <div
                style={{
                  marginTop: "18px",
                  padding: "20px",
                  border: "1px solid rgba(139,92,246,0.35)",
                  borderRadius: "12px"
                }}
              >

                <p
                  style={{
                    fontSize: "10px",
                    letterSpacing: "1px",
                    color: "#a78bfa"
                  }}
                >
                  DIRECT DEPLOYMENT
                </p>

                <h3 style={{ marginTop: "6px" }}>
                  Main swarm can launch directly from Admin Base.
                </h3>

                <p
                  style={{
                    color: "#697386",
                    fontSize: "11px",
                    marginTop: "7px"
                  }}
                >
                  The calculated one-way flight time is within the
                  usable drone endurance envelope.
                </p>

                {deployment?.main_swarm?.status !== "DEPLOYED" && (
                  <button
                    type="button"
                    onClick={deployMainSwarm}
                    style={{
                      marginTop: "16px",
                      cursor: "pointer",
                      fontWeight: "700"
                    }}
                  >
                    DEPLOY MAIN SWARM DIRECTLY
                  </button>
                )}

                {deployment?.main_swarm?.status === "DEPLOYED" && (
                  <div
                    style={{
                      marginTop: "16px",
                      padding: "12px",
                      borderRadius: "8px",
                      border: "1px solid rgba(34,197,94,0.22)",
                      background: "rgba(34,197,94,0.05)",
                      fontSize: "10px"
                    }}
                  >
                    MAIN SWARM AUTOMATICALLY DEPLOYED
                  </div>
                )}

              </div>
            )}

            {/* =================================================
                MOBILE ZONE DEPLOYMENT TAB / ACTION
            ================================================= */}

            {!directFeasible && (
              <div
                style={{
                  marginTop: "18px",
                  padding: "20px",
                  border: "1px solid rgba(139,92,246,0.35)",
                  borderRadius: "12px"
                }}
              >

                <p
                  style={{
                    fontSize: "10px",
                    letterSpacing: "1px",
                    color: "#a78bfa"
                  }}
                >
                  MOBILE ZONE
                </p>

                <h3 style={{ marginTop: "6px" }}>
                  Mobile Zone → Incident
                </h3>

                <p
                  style={{
                    color: "#697386",
                    fontSize: "11px",
                    marginTop: "7px"
                  }}
                >
                  The Mobile Zone carries the swarm closer to the
                  incident until the initial assessment range is reached.
                </p>

                {/* MOBILE ZONE TELEMETRY */}

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(4, 1fr)",
                    gap: "10px",
                    marginTop: "16px"
                  }}
                >

                  <div className="dashboard-card">
                    <p>STATUS</p>
                    <h3>
                      {deployment?.mobile_zone?.status ||
                        "STANDBY"}
                    </h3>
                  </div>

                  <div className="dashboard-card">
                    <p>SPEED</p>
                    <h3>
                      {deployment?.mobile_zone?.speed_kmph ??
                        45} km/h
                    </h3>
                  </div>

                  <div className="dashboard-card">
                    <p>DISTANCE TO INCIDENT</p>
                    <h3>
                      {deployment?.mobile_zone?.distance_to_incident_km != null
                        ? `${deployment.mobile_zone.distance_to_incident_km} km`
                        : "-"}
                    </h3>
                  </div>

                  <div className="dashboard-card">
                    <p>DIRECT FLEET RANGE</p>
                    <h3>
                      {deployment?.initial_drone_operational_range_km ?? deployment?.maximum_operational_range_km ?? "—"} km
                    </h3>
                  </div>

                </div>

                {/* HORIZONTAL TRAVEL PROGRESS */}

                <div style={{ marginTop: "18px" }}>

                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      marginBottom: "7px"
                    }}
                  >
                    <strong>
                      MOBILE ZONE TRAVEL
                    </strong>

                    <strong>
                      {Number(
                        deployment?.mobile_zone?.progress_percent || 0
                      ).toFixed(1)}
                      %
                    </strong>
                  </div>

                  <div
                    style={{
                      height: "12px",
                      borderRadius: "999px",
                      background: "rgba(255,255,255,0.08)",
                      overflow: "hidden"
                    }}
                  >
                    <div
                      style={{
                        width: `${Math.min(
                          100,
                          Math.max(
                            0,
                            Number(
                              deployment?.mobile_zone?.progress_percent || 0
                            )
                          )
                        )}%`,
                        height: "100%",
                        borderRadius: "999px",
                        background:
                          "linear-gradient(90deg,#8b5cf6,#38bdf8)",
                        transition: "width 300ms linear"
                      }}
                    />
                  </div>

                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      marginTop: "7px",
                      color: "#697386",
                      fontSize: "9px"
                    }}
                  >
                    <span>ADMIN BASE</span>
                    <span>
                      {deployment?.mobile_zone?.status ===
                      "AT_ASSESSMENT_RANGE"
                        ? "INSIDE INITIAL ASSESSMENT RANGE"
                        : "MOVING TO ASSESSMENT RANGE"}
                    </span>
                    <span>INCIDENT</span>
                  </div>

                </div>

                {/* MOBILE ZONE START BUTTON */}

                {(deployment?.mobile_zone?.status === "STANDBY" ||
                  deploymentStatus === "MOBILE_ZONE_REQUIRED") && (
                  <button
                    type="button"
                    onClick={startMobileZone}
                    style={{
                      marginTop: "18px",
                      cursor: "pointer",
                      fontWeight: "700"
                    }}
                  >
                    🚚 START MOBILE BASE
                  </button>
                )}

                {/* INITIAL ASSESSMENT DEPLOYMENT */}

                {deployment?.mobile_zone?.status ===
                  "AT_ASSESSMENT_RANGE" && (
                  <div
                    style={{
                      marginTop: "18px",
                      padding: "16px",
                      borderRadius: "10px",
                      border: "1px solid rgba(56,189,248,0.35)"
                    }}
                  >

                    <strong>
                      🔎 INITIAL ASSESSMENT RANGE REACHED
                    </strong>

                    <p
                      style={{
                        marginTop: "7px",
                        color: "#697386",
                        fontSize: "11px"
                      }}
                    >
                      Mobile Zone is within direct-fleet operating
                      range. Deploy the initial assessment drones now.
                    </p>

                    <button
                      type="button"
                      onClick={startRecon}
                      style={{
                        marginTop: "13px",
                        cursor: "pointer",
                        fontWeight: "700"
                      }}
                    >
                      🔎 DEPLOY INITIAL ASSESSMENT DRONES
                    </button>

                  </div>
                )}

              </div>
            )}

            {/* =================================================
                INITIAL ASSESSMENT RESULT
            ================================================= */}

            {deployment?.recon?.launched && (
              <div
                style={{
                  marginTop: "18px",
                  padding: "20px",
                  borderRadius: "12px",
                  border: "1px solid rgba(56,189,248,0.25)"
                }}
              >

                <div className="panel-header">
                  <div>
                    <p>INITIAL ASSESSMENT</p>
                    <h3>
                      Re-evaluation & Priority Zoning
                    </h3>
                  </div>

                  <span className="map-status">
                    {deployment.recon.status}
                  </span>
                </div>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(4, 1fr)",
                    gap: "10px",
                    marginTop: "15px"
                  }}
                >

                  <div className="dashboard-card">
                    <p>DISASTER FOOTPRINT</p>
                    <h3>
                      {deployment.recon.disaster_region?.radius_km ?? "-"} km
                    </h3>
                  </div>

                  <div className="dashboard-card">
                    <p>ESTIMATED AREA</p>
                    <h3>
                      {deployment.recon.disaster_region?.estimated_area_km2 ?? "-"} km²
                    </h3>
                  </div>

                  <div className="dashboard-card">
                    <p>INITIAL DRONES</p>
                    <h3>
                      {(deployment.recon.drones_deployed || []).length}
                    </h3>
                  </div>

                  <div className="dashboard-card">
                    <p>SURVIVORS DETECTED</p>
                    <h3>
                      {deployment.recon.survivors_detected ?? 0}
                    </h3>
                  </div>

                </div>

                {/* REAL-MODE SUPPORTING IMAGERY STATUS */}

                {activeOperation.mode === "REAL" && (
                  <div
                    style={{
                      marginTop: "16px",
                      padding: "15px",
                      borderRadius: "10px",
                      border: "1px solid rgba(56,189,248,0.25)",
                      background: "rgba(56,189,248,0.04)"
                    }}
                  >

                    <p
                      style={{
                        fontSize: "9px",
                        letterSpacing: "1px",
                        color: "#38bdf8"
                      }}
                    >
                      REAL-MODE EXTERNAL SUPPORTING IMAGERY
                    </p>

                    <strong>
                      {deployment.recon.imagery_source ||
                        "MOSDAC / Bhuvan"}
                    </strong>

                    <p
                      style={{
                        marginTop: "7px",
                        color: "#697386",
                        fontSize: "10px",
                        lineHeight: "1.5"
                      }}
                    >
                      Status:{" "}
                      {deployment.recon.imagery_status ||
                        "AWAITING_EXTERNAL_SOURCE"}
                      <br />
                      {deployment.recon.supporting_information_note ||
                        "Real-world disaster evidence is not fabricated. Obtain supporting imagery before making a disaster assessment."}
                    </p>

                    <a
                      href={
                        deployment.recon.imagery_source_url ||
                        "https://www.mosdac.gov.in/mosdac-live"
                      }
                      target="_blank"
                      rel="noreferrer"
                      style={{
                        display: "inline-block",
                        marginTop: "10px",
                        color: "#a78bfa",
                        fontSize: "10px"
                      }}
                    >
                      OPEN OFFICIAL SATELLITE SOURCE ↗
                    </a>

                  </div>
                )}

                {/* INITIAL DRONE IDs */}

                <div
                  style={{
                    marginTop: "15px",
                    display: "flex",
                    gap: "8px",
                    flexWrap: "wrap"
                  }}
                >

                  {(deployment.recon.drones_deployed || []).map(
                    (id) => (
                      <span
                        key={id}
                        style={{
                          padding: "7px 10px",
                          borderRadius: "8px",
                          background: "rgba(56,189,248,0.10)",
                          border: "1px solid rgba(56,189,248,0.20)",
                          fontSize: "10px"
                        }}
                      >
                        🔎 DR-{String(Number(id) + 1).padStart(3, "0")}
                      </span>
                    )
                  )}

                </div>

                {/* PRIORITY TABLE */}

                <div style={{ overflowX: "auto", marginTop: "18px" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse" }}>
                    <thead>
                      <tr>
                        <th style={{ textAlign: "left", padding: "10px" }}>ZONE</th>
                        <th style={{ textAlign: "left", padding: "10px" }}>AREA</th>
                        <th style={{ textAlign: "left", padding: "10px" }}>PRIORITY</th>
                        <th style={{ textAlign: "left", padding: "10px" }}>RISK</th>
                        <th style={{ textAlign: "left", padding: "10px" }}>ALLOCATED</th>
                        <th style={{ textAlign: "left", padding: "10px" }}>ACTIVE</th>
                      </tr>
                    </thead>

                    <tbody>
                      {(deployment.recon.priority_zones || []).map(
                        (zone, index) => (
                          <tr key={zone.id || index}>
                            <td style={{ padding: "10px" }}>
                              {zone.id || `Zone ${index + 1}`}
                            </td>
                            <td style={{ padding: "10px" }}>
                              {zone.area_km2 ?? "-"} km²
                            </td>
                            <td style={{ padding: "10px" }}>
                              {zone.priority || "-"}
                            </td>
                            <td style={{ padding: "10px" }}>
                              {zone.risk || "-"}
                            </td>
                            <td style={{ padding: "10px" }}>
                              {(zone.allocated_drone_ids || []).map(
                                (id) =>
                                  `DR-${String(Number(id) + 1).padStart(3, "0")}`
                              ).join(", ") || "-"}
                            </td>
                            <td style={{ padding: "10px" }}>
                              {zone.active_drone_count ??
                                (zone.allocated_drone_ids || []).length}
                            </td>
                          </tr>
                        )
                      )}
                    </tbody>
                  </table>
                </div>

                {/* FORWARD BASE */}

                <div
                  style={{
                    marginTop: "18px",
                    padding: "16px",
                    borderRadius: "10px",
                    background: "rgba(139,92,246,0.06)"
                  }}
                >

                  <p
                    style={{
                      fontSize: "9px",
                      color: "#858da5",
                      letterSpacing: "1px"
                    }}
                  >
                    PROPOSED FORWARD BASE SITE
                  </p>

                  <strong>
                    {deployment.forward_base?.position
                      ? `${deployment.forward_base.position.latitude}, ${deployment.forward_base.position.longitude}`
                      : "Awaiting safety assessment"}
                  </strong>

                  <p
                    style={{
                      marginTop: "7px",
                      color: "#697386",
                      fontSize: "10px"
                    }}
                  >
                    Safety score:{" "}
                    {deployment.forward_base?.safety_score ?? "-"}
                    {" · "}
                    Source:{" "}
                    {deployment.forward_base?.source || "-"}
                  </p>

                  {deployment.forward_base?.status === "SELECTED" &&
                    !deployment.direct_feasible && (
                    <div
                      style={{
                        marginTop: "12px",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        gap: "12px"
                      }}
                    >

                      <span
                        style={{
                          color: "#aeb3c7",
                          fontSize: "10px"
                        }}
                      >
                        Mobile Zone continues to this selected safe site.
                        The main swarm deploys automatically when the
                        Forward Base is reached. Manual deployment remains
                        available as an operator override.
                      </span>

                      <button
                        type="button"
                        onClick={deployMainSwarm}
                        style={{
                          cursor: "pointer",
                          fontWeight: "700",
                          whiteSpace: "nowrap"
                        }}
                      >
                        DEPLOY SWARM NOW
                      </button>

                    </div>
                  )}

                  {deployment.direct_feasible &&
                    deployment.main_swarm?.status === "DEPLOYED" && (
                    <div
                      style={{
                        marginTop: "12px",
                        padding: "12px",
                        borderRadius: "8px",
                        border: "1px solid rgba(34,197,94,0.22)",
                        background: "rgba(34,197,94,0.05)",
                        color: "#aeb3c7",
                        fontSize: "10px"
                      }}
                    >
                      Main swarm automatically deployed from the Admin
                      Base. Forward Base candidates were assessed but are
                      not part of this direct deployment path.
                    </div>
                  )}

                </div>

              </div>
            )}

          </div>

        </section>
      )}

      {/* ======================================================
          ACTIVE OPERATION
      ====================================================== */}

      {activeOperation &&
        activeOperation.status !==
          "STOPPED" && (


        <section
          className="map-panel"
          style={{
            marginTop:
              "18px"
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
              padding:
                "20px"
            }}
          >

            <div
              style={{
                display:
                  "grid",
                gridTemplateColumns:
                  "repeat(4, 1fr)",
                gap:
                  "10px"
              }}
            >

              <div className="dashboard-card">

                <div>

                  <p>
                    MODE
                  </p>


                  <h3>
                    {activeOperation.mode ||
                      "SIMULATION"}
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
                      (
                        activeOperation
                          .assignedDrones ||
                        []
                      ).length
                    }
                  </h3>

                </div>

              </div>


              <div className="dashboard-card">

                <div>

                  <p>
                    DEPLOYMENT
                  </p>


                  <h3>
                    {activeOperation.deploymentMode ||
                      "DIRECT"}
                  </h3>

                </div>

              </div>

            </div>


            {/* Progress */}

            <div
              style={{
                marginTop:
                  "20px"
              }}
            >

              <div
                style={{
                  display:
                    "flex",
                  justifyContent:
                    "space-between",
                  marginBottom:
                    "8px"
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
                  width:
                    "100%",
                  height:
                    "10px",
                  background:
                    "rgba(255,255,255,0.08)",
                  borderRadius:
                    "10px",
                  overflow:
                    "hidden"
                }}
              >

                <div
                  style={{
                    width:
                      `${activeOperation.progress}%`,
                    height:
                      "100%",
                    background:
                      "#8b5cf6",
                    borderRadius:
                      "10px",
                    transition:
                      "width 0.4s ease"
                  }}
                />

              </div>

            </div>


            {/* Deployed units */}

            <div
              style={{
                marginTop:
                  "20px"
              }}
            >

              <p>
                DEPLOYED UNITS
              </p>


              <div
                style={{
                  display:
                    "flex",
                  flexWrap:
                    "wrap",
                  gap:
                    "8px"
                }}
              >

                {(
                  activeOperation
                    .assignedDrones ||
                  []
                ).map(
                  droneId => (

                    <span
                      key={
                        droneId
                      }
                      style={{
                        padding:
                          "7px 10px",
                        borderRadius:
                          "6px",
                        background:
                          "rgba(139,92,246,0.12)",
                        border:
                          "1px solid rgba(139,92,246,0.25)",
                        fontSize:
                          "10px"
                      }}
                    >
                      🚁 {droneId}
                    </span>

                  )
                )}

              </div>

            </div>


            {/* Stop */}

            <div
              style={{
                display:
                  "flex",
                justifyContent:
                  "flex-end",
                marginTop:
                  "22px"
              }}
            >

              <button
                type="button"
                onClick={
                  handleStopMission
                }
                style={{
                  cursor:
                    "pointer",
                  padding:
                    "10px 18px",
                  borderRadius:
                    "7px",
                  border:
                    "1px solid rgba(255,80,80,0.5)",
                  background:
                    "rgba(255,80,80,0.10)",
                  color:
                    "#ff7777",
                  fontWeight:
                    "600"
                }}
              >
                STOP MISSION
              </button>

            </div>

          </div>

        </section>

      )}


      {/* ======================================================
          EXISTING RESCUE REQUEST
      ====================================================== */}

      {!activeOperation && (

        <section
          className="map-panel"
          style={{
            marginTop:
              "18px"
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


          {!rescueRequest && (

            <div
              style={{
                padding:
                  "30px"
              }}
            >

              <div
                style={{
                  padding:
                    "25px",
                  border:
                    "1px dashed rgba(255,255,255,0.12)",
                  borderRadius:
                    "14px",
                  textAlign:
                    "center"
                }}
              >

                <div
                  style={{
                    fontSize:
                      "35px",
                    marginBottom:
                      "12px"
                  }}
                >
                  📡
                </div>


                <h3>
                  No Rescue Request Received
                </h3>


                <p
                  style={{
                    color:
                      "#697386",
                    fontSize:
                      "13px",
                    marginTop:
                      "8px"
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
                    marginTop:
                      "16px",
                    cursor:
                      "pointer"
                  }}
                >
                  Simulate Rescue Request
                </button>

              </div>

            </div>

          )}


          {rescueRequest && (

            <div
              style={{
                padding:
                  "20px"
              }}
            >

              <div
                style={{
                  display:
                    "grid",
                  gridTemplateColumns:
                    "repeat(4, 1fr)",
                  gap:
                    "10px"
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

                  </div>

                </div>

              </div>


              <div
                style={{
                  marginTop:
                    "14px",
                  padding:
                    "14px",
                  borderRadius:
                    "10px",
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
                    fontSize:
                      "9px",
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
                    color:
                      "#aeb3c7",
                    fontSize:
                      "11px"
                  }}
                >
                  {rescueRequest.description}
                </span>

              </div>


              <div
                style={{
                  display:
                    "flex",
                  justifyContent:
                    "space-between",
                  alignItems:
                    "center",
                  marginTop:
                    "15px"
                }}
              >

                <div>

                  <p
                    style={{
                      margin:
                        0,
                      fontSize:
                        "9px",
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
                      fontSize:
                        "12px",
                      color:
                        "#aeb3c7"
                    }}
                  >
                    {rescueRequest.time}
                  </span>

                </div>


                <div
                  style={{
                    display:
                      "flex",
                    gap:
                      "10px"
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


      {/* ======================================================
          DRONE ALLOCATION
      ====================================================== */}

      {!activeOperation &&
        missionStatus !==
          "pending" &&
        allocatedDrones.length >
          0 && (

        <section
          className="map-panel"
          style={{
            marginTop:
              "18px"
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
              padding:
                "20px"
            }}
          >

            <div
              style={{
                width:
                  "100%",
                overflowX:
                  "auto",
                marginTop:
                  "18px",
                border:
                  "1px solid rgba(255,255,255,0.07)",
                borderRadius:
                  "10px"
              }}
            >

              <table
                style={{
                  width:
                    "100%",
                  borderCollapse:
                    "collapse",
                  minWidth:
                    "850px",
                  fontSize:
                    "11px"
                }}
              >

                <thead>

                  <tr
                    style={{
                      textAlign:
                        "left",
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
                      key={
                        drone.id
                      }
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


            {missionStatus ===
              "accepted" && (

              <div
                style={{
                  display:
                    "flex",
                  justifyContent:
                    "flex-end",
                  marginTop:
                    "20px"
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


      {/* ======================================================
          MISSION FLOW
      ====================================================== */}

      <section
        className="map-panel"
        style={{
          marginTop:
            "18px"
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


        <div className="mission-flow">

          <div className="mission-step">

            <div className="mission-step-number">
              01
            </div>


            <h3>
              Mission
            </h3>


            <p>
              Define incident
            </p>

          </div>


          <div className="mission-step">

            <div className="mission-step-number">
              02
            </div>


            <h3>
              Assess
            </h3>


            <p>
              Check deployment
            </p>

          </div>


          <div className="mission-step">

            <div className="mission-step-number">
              03
            </div>


            <h3>
              Recon
            </h3>


            <p>
              Establish operational picture
            </p>

          </div>


          <div className="mission-step">

            <div className="mission-step-number">
              04
            </div>


            <h3>
              Stage
            </h3>


            <p>
              Select Forward Base
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
              Launch swarm
            </p>

          </div>

        </div>

      </section>


      {/* ======================================================
          STOP CONFIRMATION
      ====================================================== */}

      {showStopConfirm && (

        <div
          style={{
            position:
              "fixed",
            inset:
              0,
            zIndex:
              9999,
            background:
              "rgba(0,0,0,0.75)",
            display:
              "flex",
            alignItems:
              "center",
            justifyContent:
              "center",
            padding:
              "20px"
          }}
        >

          <div
            style={{
              width:
                "100%",
              maxWidth:
                "430px",
              background:
                "#15131f",
              border:
                "1px solid rgba(255,255,255,0.1)",
              borderRadius:
                "12px",
              padding:
                "25px"
            }}
          >

            <h3>
              Confirm Operation Stop
            </h3>


            <p
              style={{
                color:
                  "#9aa1b5",
                lineHeight:
                  "1.6",
                fontSize:
                  "12px"
              }}
            >
              This will terminate the active
              operation and move its complete
              record to Mission History.
            </p>


            <div
              style={{
                marginTop:
                  "20px",
                padding:
                  "12px",
                borderRadius:
                  "8px",
                background:
                  "rgba(255,255,255,0.03)"
              }}
            >

              <p
                style={{
                  margin:
                    0,
                  fontSize:
                    "9px",
                  color:
                    "#858da5"
                }}
              >
                OPERATION ID
              </p>


              <strong
                style={{
                  fontSize:
                    "12px"
                }}
              >
                {activeOperation?.id}
              </strong>

            </div>


            <div
              style={{
                display:
                  "flex",
                justifyContent:
                  "flex-end",
                gap:
                  "10px",
                marginTop:
                  "20px"
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
                  cursor:
                    "pointer",
                  padding:
                    "10px 15px",
                  borderRadius:
                    "6px",
                  background:
                    "#7f1d1d",
                  color:
                    "white",
                  border:
                    "1px solid #ef4444",
                  fontWeight:
                    "600"
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


/* ============================================================
   STYLES
============================================================ */

const labelStyle = {

  display:
    "block",

  fontSize:
    "9px",

  letterSpacing:
    "1px",

  color:
    "#858da5",

  marginBottom:
    "7px"

};


const inputStyle = {

  width:
    "100%",

  boxSizing:
    "border-box",

  padding:
    "11px 12px",

  borderRadius:
    "7px",

  border:
    "1px solid rgba(255,255,255,0.10)",

  background:
    "rgba(255,255,255,0.035)",

  color:
    "#e6e8f0",

  outline:
    "none",

  fontSize:
    "12px"

};


const modeButtonStyle = {

  cursor:
    "pointer",

  padding:
    "10px 14px",

  borderRadius:
    "7px",

  border:
    "1px solid rgba(255,255,255,0.12)",

  background:
    "rgba(255,255,255,0.04)",

  color:
    "#e6e8f0",

  fontWeight:
    "600"

};


const thStyle = {

  padding:
    "12px",

  color:
    "#858da5",

  fontSize:
    "9px",

  letterSpacing:
    "0.8px",

  fontWeight:
    "600",

  whiteSpace:
    "nowrap"

};


const tdStyle = {

  padding:
    "12px",

  color:
    "#aeb3c7",

  whiteSpace:
    "nowrap"

};


export default Missions;








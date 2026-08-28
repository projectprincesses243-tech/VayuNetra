// ==========================================
// VayuNetra Frontend Demo Data
// ==========================================
//
// MOCK DATA ONLY
//
// This file contains the common demo data
// used by the frontend.
//
// Later, the integration person can replace
// these values with real data coming from:
//
// - Perception
// - Localisation
// - Simulation
// - Path Planning
// - Hardware / ESP32
//
// ==========================================


// ==========================================
// DRONE FLEET
// ==========================================
//
// 128 registered drones
//
// Initial fleet:
//
// 100 AVAILABLE
// 12 ACTIVE
// 8 CHARGING
// 8 UNAVAILABLE
//
// Drone IDs:
// DR-001 ... DR-128
//
// ==========================================

const droneStatuses = [
  ...Array(100).fill("AVAILABLE"),
  ...Array(12).fill("ACTIVE"),
  ...Array(8).fill("CHARGING"),
  ...Array(8).fill("UNAVAILABLE")
];


export const drones = droneStatuses.map((status, index) => {

  const droneNumber = index + 1;

  return {

    // --------------------------------------
    // UNIQUE DRONE ID
    // --------------------------------------

    id:
      `DR-${String(droneNumber).padStart(3, "0")}`,

    // --------------------------------------
    // DEMO LOCATION
    // --------------------------------------

    latitude:
      15.3173 +
      (index % 10) * 0.001,

    longitude:
      75.7139 +
      Math.floor(index / 10) * 0.001,

    // --------------------------------------
    // FLEET STATUS
    // --------------------------------------

    status,

    // --------------------------------------
    // BATTERY
    // --------------------------------------

    battery:
      status === "CHARGING"
        ? 40 + (index % 35)
        : status === "UNAVAILABLE"
        ? 20 + (index % 40)
        : 75 + (index % 26),

    // --------------------------------------
    // CURRENT MISSION
    // --------------------------------------

    mission:
      status === "ACTIVE"
        ? "Existing Operation"
        : null,

    // --------------------------------------
    // SURVIVORS DETECTED
    // --------------------------------------

    survivorsDetected:
      status === "ACTIVE"
        ? index % 3
        : 0

  };

});


// ==========================================
// SURVIVOR DATA
// ==========================================

export const survivors = [

  {
    id: "SV-001",

    latitude: 15.3078,

    longitude: 75.7045,

    confidence: 94
  },

  {
    id: "SV-002",

    latitude: 15.3085,

    longitude: 75.7055,

    confidence: 91
  },

  {
    id: "SV-003",

    latitude: 15.3068,

    longitude: 75.7028,

    confidence: 89
  }

];


// ==========================================
// ACTIVE DISASTER
// ==========================================

export const disaster = {

  type: "Flood",

  latitude: 15.3123,

  longitude: 75.7089,

  severity: "HIGH"

};


// ==========================================
// PERCEPTION RESULTS
// ==========================================

export const detections = [

  {
    droneId: "DR-003",

    object: "Survivor",

    confidence: 94,

    sensor: "Thermal",

    disasterType: "Flood"
  },

  {
    droneId: "DR-003",

    object: "Survivor",

    confidence: 91,

    sensor: "RGB",

    disasterType: "Flood"
  },

  {
    droneId: "DR-001",

    object: "Debris",

    confidence: 88,

    sensor: "RGB",

    disasterType: "Landslide"
  },

  {
    droneId: "DR-004",

    object: "Structural Damage",

    confidence: 89,

    sensor: "RGB",

    disasterType: "Building Collapse"
  },

  {
    droneId: "DR-003",

    object: "Structural Damage",

    confidence: 86,

    sensor: "RGB",

    disasterType: "Earthquake"
  }

];


// ==========================================
// MISSIONS
// ==========================================
//
// These are the demo rescue scenarios.
//
// IMPORTANT:
// assignedDrone is initially null.
//
// Missions.jsx will allocate the actual
// drone IDs from the drone fleet.
//
// ==========================================

export const missions = [

  {
    id: "MS-001",

    name: "Flood Rescue",

    area: "Sector A",

    priority: "HIGH",

    status: "PENDING",

    assignedDrone: null
  },

  {
    id: "MS-002",

    name: "Landslide Search",

    area: "Sector B",

    priority: "MEDIUM",

    status: "PENDING",

    assignedDrone: null
  },

  {
    id: "MS-003",

    name: "Building Assessment",

    area: "Sector C",

    priority: "HIGH",

    status: "PENDING",

    assignedDrone: null
  }

];
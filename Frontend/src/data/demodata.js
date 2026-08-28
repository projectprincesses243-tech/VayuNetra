// ==========================================
// VayuNetra Frontend Demo Data
// ==========================================
//
// MOCK data only.
//
// This is the single source of truth for the
// frontend demo.
//
// Later, the integration person can replace
// these values with real data from:
//
// - Perception
// - Localisation
// - Simulation
// - Path Planning
// - Drone hardware
//
// ==========================================


// ==========================================
// FLEET CONFIGURATION
// ==========================================

export const fleet = {

  total: 128,

  charging: 8,

  unavailable: 20

};


// ==========================================
// DRONE DATA
// ==========================================
//
// Only drones with deployed: true are shown
// as operating on the Live Map.
//
// Currently 6 drones are deployed.
// ==========================================

export const drones = [

  {
    id: "DR-001",
    latitude: 15.3173,
    longitude: 75.7139,

    status: "SEARCHING",

    battery: 87,

    mission: "Landslide Search",

    survivorsDetected: 1,

    deployed: true
  },

  {
    id: "DR-002",
    latitude: 15.3273,
    longitude: 75.7239,

    status: "SEARCHING",

    battery: 74,

    mission: "Flood Search",

    survivorsDetected: 0,

    deployed: true
  },

  {
    id: "DR-003",
    latitude: 15.3073,
    longitude: 75.7039,

    status: "SURVIVOR FOUND",

    battery: 61,

    mission: "Flood Rescue",

    survivorsDetected: 3,

    deployed: true
  },

  {
    id: "DR-004",
    latitude: 15.3373,
    longitude: 75.6939,

    status: "RETURNING",

    battery: 48,

    mission: "Building Fire",

    survivorsDetected: 0,

    deployed: true
  },

  {
    id: "DR-005",
    latitude: 15.3223,
    longitude: 75.6989,

    status: "SEARCHING",

    battery: 92,

    mission: "Flood Rescue",

    survivorsDetected: 1,

    deployed: true
  },

  {
    id: "DR-006",
    latitude: 15.3023,
    longitude: 75.7189,

    status: "SCANNING",

    battery: 79,

    mission: "Flood Rescue",

    survivorsDetected: 0,

    deployed: true
  }

];


// ==========================================
// DERIVED FLEET VALUES
// ==========================================
//
// These values should NOT be manually typed
// into individual pages.
// ==========================================

export const deployedDrones =
  drones.filter(
    drone => drone.deployed === true
  );


export const activeDrones =
  deployedDrones.length;


export const availableDrones =
  fleet.total -
  activeDrones -
  fleet.charging -
  fleet.unavailable;


// ==========================================
// SURVIVOR DATA
// ==========================================

export const survivors = [

  {
    id: "SV-001",

    latitude: 15.3078,

    longitude: 75.7045,

    confidence: 94,

    detectedBy: "DR-003"

  },

  {
    id: "SV-002",

    latitude: 15.3085,

    longitude: 75.7055,

    confidence: 91,

    detectedBy: "DR-003"

  },

  {
    id: "SV-003",

    latitude: 15.3068,

    longitude: 75.7028,

    confidence: 89,

    detectedBy: "DR-003"

  },

  {
    id: "SV-004",

    latitude: 15.3190,

    longitude: 75.7115,

    confidence: 92,

    detectedBy: "DR-005"

  },

  {
    id: "SV-005",

    latitude: 15.3210,

    longitude: 75.7130,

    confidence: 87,

    detectedBy: "DR-001"

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
  },

  {
    droneId: "DR-005",

    object: "Survivor",

    confidence: 92,

    sensor: "Thermal",

    disasterType: "Flood"
  },

  {
    droneId: "DR-001",

    object: "Survivor",

    confidence: 87,

    sensor: "RGB",

    disasterType: "Flood"
  }

];


// ==========================================
// MISSIONS
// ==========================================

export const missions = [

  {
    id: "MS-001",

    name: "Flood Rescue",

    area: "Sector A",

    priority: "HIGH",

    status: "ACTIVE",

    assignedDrones: [
      "DR-002",
      "DR-003",
      "DR-005",
      "DR-006"
    ],

    progress: 72
  },

  {
    id: "MS-002",

    name: "Landslide Search",

    area: "Sector B",

    priority: "MEDIUM",

    status: "ACTIVE",

    assignedDrones: [
      "DR-001"
    ],

    progress: 58
  },

  {
    id: "MS-003",

    name: "Building Assessment",

    area: "Sector C",

    priority: "HIGH",

    status: "ACTIVE",

    assignedDrones: [
      "DR-004"
    ],

    progress: 41
  }

];


// ==========================================
// ACTIVE OPERATION
// ==========================================
//
// This represents the operation currently
// being demonstrated.
// ==========================================

export const activeOperation = {

  id: "OP-001",

  mission: "Flood Rescue",

  status: "ACTIVE",

  progress: 72,

  deployedDroneCount: activeDrones,

  survivorsDetected:
    survivors.length

};
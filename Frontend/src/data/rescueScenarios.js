const rescueScenarios = [
  {
    id: "RES-001",
    location: "Sector B-4",
    disaster: "Collapsed Building",
    priority: "HIGH",
    survivors: 8,
    dronesRequired: 4,
    description:
      "Possible survivors detected inside a collapsed structure.",
  },

  {
    id: "RES-002",
    location: "Sector C-2",
    disaster: "Flood",
    priority: "CRITICAL",
    survivors: 15,
    dronesRequired: 6,
    description:
      "Multiple people reported stranded in a flooded residential area.",
  },

  {
    id: "RES-003",
    location: "Sector A-7",
    disaster: "Forest Fire",
    priority: "HIGH",
    survivors: 5,
    dronesRequired: 5,
    description:
      "Search operation required in a forest region affected by fire.",
  },

  {
    id: "RES-004",
    location: "Sector D-1",
    disaster: "Earthquake",
    priority: "CRITICAL",
    survivors: 21,
    dronesRequired: 8,
    description:
      "Large affected zone requiring coordinated aerial search.",
  },

  {
    id: "RES-005",
    location: "Sector E-3",
    disaster: "Landslide",
    priority: "CRITICAL",
    survivors: 12,
    dronesRequired: 6,
    description:
      "Landslide has blocked roads and may have trapped people in the affected area.",
  },

  {
    id: "RES-006",
    location: "Sector F-5",
    disaster: "Building Fire",
    priority: "CRITICAL",
    survivors: 10,
    dronesRequired: 5,
    description:
      "Active building fire requiring aerial survivor detection and monitoring.",
  },
];

export default rescueScenarios;
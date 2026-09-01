from core.bus import BUS
from core.contracts import make_drone, make_task

# Two different modules "listening" for the same event
def mission_layer(payload):
    print(f"   mission: creating task for survivor at {payload['location']}")

def dashboard_layer(payload):
    print(f"   dashboard: showing alert, confidence {payload['confidence']}")

BUS.subscribe("SURVIVOR_DETECTED", mission_layer)
BUS.subscribe("SURVIVOR_DETECTED", dashboard_layer)

drone = make_drone(1, 100, 200)
print("drone:", drone)
print()

print("publishing SURVIVOR_DETECTED...")
BUS.publish("SURVIVOR_DETECTED", {
    "drone_id": 1,
    "location": [340, 120],
    "confidence": 0.87,
})

print()
print("events logged:", len(BUS.log))
print("detections:", BUS.count("SURVIVOR_DETECTED"))
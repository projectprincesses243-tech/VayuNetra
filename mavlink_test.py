from pymavlink import mavutil

print("Connecting to STM32 on /dev/ttyUSB0...")

connection = mavutil.mavlink_connection(
    "/dev/ttyUSB0",
    baud=115200
)

print("Waiting for MAVLink heartbeat...")

connection.wait_heartbeat()

print(
    f"Heartbeat received! "
    f"System ID: {connection.target_system}, "
    f"Component ID: {connection.target_component}"
)

print("\nReceiving MAVLink telemetry...\n")

while True:
    msg = connection.recv_match(blocking=True)

    if msg:
        print(msg)

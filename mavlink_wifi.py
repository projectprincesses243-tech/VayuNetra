from pymavlink import mavutil
import socket

PI_SERIAL = "/dev/ttyUSB0"
BAUD = 115200

LAPTOP_IP = "10.221.96.73"
LAPTOP_PORT = 14550

print("Connecting to STM32...")
connection = mavutil.mavlink_connection(
    PI_SERIAL,
    baud=BAUD
)

udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print("Waiting for STM32 heartbeat...")
connection.wait_heartbeat()

print(
    f"Heartbeat received: "
    f"System {connection.target_system}, "
    f"Component {connection.target_component}"
)

print(f"Forwarding MAVLink to {LAPTOP_IP}:{LAPTOP_PORT}")
print("Press Ctrl+C to stop.\n")

while True:
    msg = connection.recv_match(blocking=True)

    if msg:
        packet = msg.get_msgbuf()

        if packet:
            udp.sendto(packet, (LAPTOP_IP, LAPTOP_PORT))

        print(
            f"Forwarded: {msg.get_type()} "
            f"({len(packet)} bytes)"
        )

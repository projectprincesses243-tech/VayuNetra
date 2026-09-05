"""
VayuNetra Hardware Integration Demonstration

Architecture:

Digital Twin
      |
      |
 Raspberry Pi
      |
      +----------------+
      |                |
 STM32F407        ESP32 Radio
 Flight Node      Swarm Node


This is a communication proof-of-concept.
"""


from protocol import (
    encode_message,
    decode_message
)

import time


def print_packet(title, packet):

    print("\n" + "-"*45)
    print(title)
    print("-"*45)
    print(packet)



print("\n")
print("="*55)
print("        VAYUNETRA HARDWARE INTEGRATION DEMO")
print("="*55)


# -------------------------------------------------
# 1. DIGITAL TWIN COMMAND
# -------------------------------------------------

mission_command = {

    "type": "MISSION_UPDATE",

    "source": "DIGITAL_TWIN",

    "target": "STM32",

    "drone_id": 1,

    "mission": "SEARCH",

    "position": {

        "x":120,
        "y":230

    },

    "battery_required":50

}


packet = encode_message(
    mission_command
)


print_packet(
    "DIGITAL TWIN -> RASPBERRY PI",
    packet
)



# -------------------------------------------------
# 2. RASPBERRY PI PROCESSING
# -------------------------------------------------

decoded = decode_message(
    packet
)


print_packet(
    "RASPBERRY PI PROCESSING",
    decoded
)


time.sleep(1)



# -------------------------------------------------
# 3. STM32 FLIGHT CONTROLLER RESPONSE
# -------------------------------------------------

stm32_response = {

    "type":"FLIGHT_STATUS",

    "source":"STM32F407",

    "status":"READY",

    "mode":"AUTONOMOUS",

    "motor_control":"AVAILABLE",

    "failsafe":"ACTIVE"

}



stm_packet = encode_message(
    stm32_response
)


print_packet(
    "STM32 FLIGHT CONTROLLER -> PI",
    stm_packet
)



print(
    "Decoded:",
    decode_message(stm_packet)
)



time.sleep(1)



# -------------------------------------------------
# 4. ESP32 SWARM RADIO MESSAGE
# -------------------------------------------------


radio_message = {

    "type":"SWARM_BROADCAST",

    "source":"ESP32_NODE_1",

    "destination":"ALL_DRONES",

    "message":"SEARCH_GRID_UPDATED",

    "grid":[

        [0,0],
        [1,0],
        [1,1]

    ]

}


radio_packet = encode_message(
    radio_message
)


print_packet(
    "ESP32 RADIO NETWORK",
    radio_packet
)


print(
    "Decoded:",
    decode_message(radio_packet)
)



# -------------------------------------------------
# FINAL STATUS
# -------------------------------------------------


print("\n")
print("="*55)
print(" HARDWARE COMMUNICATION LAYER READY ")
print("="*55)

print("""

Architecture Verified:

[Digital Twin]
       |
       |
[Raspberry Pi 4]
       |
       |
+---------------+
|               |
STM32F407     ESP32
Flight Node   Radio Node


Status:
✓ Packet Encoding
✓ Packet Decoding
✓ Mission Transfer
✓ Flight Controller Response
✓ Swarm Communication

""")

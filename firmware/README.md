# VayuNetra Firmware

Embedded firmware used in the VayuNetra disaster response system.

## ESP32 Firmware

### ESP32_Node1
Wireless ESP-NOW communication node.

### ESP32_Node2
ESP-NOW relay/gateway node.

### ESP32_Node3
ESP-NOW receiver node.


## STM32 Firmware

### STM32_MAVLink

STM32F407G-DISC1 firmware.

Used for:
- MAVLink telemetry generation
- Mission Planner communication
- ArduPilot integration

Communication:

STM32F407G-DISC1
        |
        |
USB-TTL
        |
        |
Raspberry Pi
        |
        |
Telemetry Dashboard
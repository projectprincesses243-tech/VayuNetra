# VayuNetra Firmware

This folder contains embedded firmware used in the VayuNetra autonomous disaster response system.

## ESP32 Firmware

### Node1
ESP32 communication node responsible for wireless mesh communication.

### Node2
ESP32 relay/gateway node used for forwarding communication.

### Node3
ESP32 receiver node for telemetry exchange.

Communication:
- ESP-NOW protocol
- Wireless node-to-node communication


## STM32 Firmware

### stmsketch

STM32F407G-DISC1 firmware used for MAVLink telemetry generation.

Hardware:
- STM32F407G DISC1
- USB-TTL serial communication

Software:
- Arduino IDE
- MAVLink protocol
- ArduPilot Mission Planner integration


## Hardware Flow

STM32
↓
USB-TTL
↓
Raspberry Pi
↓
MAVLink Telemetry Processing
↓
VayuNetra Dashboard
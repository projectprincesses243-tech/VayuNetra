"""
VayuNetra Aerospace Mission Console

Raspberry Pi Mission Computer Dashboard

Architecture:

Digital Twin
      |
      |
Raspberry Pi 4
      |
      +----------------+
      |                |
 STM32F407          ESP32
 Flight Node        Swarm Radio

"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.text import Text

import time
import random


console = Console()


tick = 0
battery = 98.0
coverage = 60.0


def create_dashboard():

    global tick
    global battery
    global coverage


    tick += 1

    battery -= 0.02

    coverage += 0.05

    if coverage > 100:
        coverage = 100


    layout = Layout()


    layout.split(
        Layout(name="header", size=5),
        Layout(name="main"),
        Layout(name="footer", size=3)
    )


    # -----------------------------
    # HEADER
    # -----------------------------

    layout["header"].update(

        Panel(

            Text(
                "✈ VAYUNETRA AUTONOMOUS SWARM COMMAND CENTER ✈",
                justify="center",
                style="bold cyan"
            ),

            title="MISSION CONTROL"

        )
    )



    # -----------------------------
    # DRONE TABLE
    # -----------------------------

    drones = Table(
        title="DRONE FLEET STATUS"
    )


    drones.add_column("NODE")
    drones.add_column("STATE")
    drones.add_column("BATTERY")
    drones.add_column("LOCALIZATION")


    for i in range(4):

        drones.add_row(

            f"DRONE-{i}",

            "SEARCHING",

            f"{battery-i*4:.1f}%",

            f"{random.uniform(2,5):.2f} m"

        )



    # -----------------------------
    # HARDWARE TABLE
    # -----------------------------

    hardware = Table(
        title="HARDWARE COMMUNICATION BUS"
    )


    hardware.add_column("DEVICE")
    hardware.add_column("STATUS")
    hardware.add_column("ROLE")


    hardware.add_row(
        "Raspberry Pi 4",
        "ONLINE",
        "DIGITAL TWIN HOST"
    )


    hardware.add_row(
        "STM32F407",
        "CONNECTED",
        "FLIGHT CONTROLLER"
    )


    hardware.add_row(
        "ESP32 RADIO",
        "ACTIVE",
        "SWARM NETWORK"
    )



    # -----------------------------
    # MISSION TABLE
    # -----------------------------

    mission = Table(
        title="MISSION TELEMETRY"
    )


    mission.add_column("PARAMETER")
    mission.add_column("VALUE")


    mission.add_row(
        "Mission Tick",
        str(tick)
    )


    mission.add_row(
        "Search Coverage",
        f"{coverage:.1f}%"
    )


    mission.add_row(
        "Mission Mode",
        "AUTONOMOUS SEARCH"
    )


    mission.add_row(
        "Threat Status",
        "NORMAL"
    )


    mission.add_row(
        "Localization Error",
        f"{random.uniform(2,5):.2f} m"
    )



    # -----------------------------
    # MAIN AREA
    # -----------------------------


    main_layout = Layout()


    main_layout.split_row(

        Layout(name="left"),
        Layout(name="right")

    )


    main_layout["left"].update(
        drones
    )


    right_layout = Layout()


    right_layout.split_column(

        Layout(hardware),
        Layout(mission)

    )


    main_layout["right"].update(
        right_layout
    )


    layout["main"].update(
        main_layout
    )



    # -----------------------------
    # FOOTER
    # -----------------------------


    layout["footer"].update(

        Panel(

            "SYSTEM STATUS: NOMINAL | STM32 LINK OK | ESP32 RADIO OK | DIGITAL TWIN ACTIVE",

            style="green"

        )
    )


    return layout



console.clear()


with Live(
    create_dashboard(),
    refresh_per_second=2
) as live:


    while True:

        time.sleep(0.5)

        live.update(
            create_dashboard()
        )

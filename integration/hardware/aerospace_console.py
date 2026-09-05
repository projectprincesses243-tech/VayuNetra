from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text

import time
import random


console = Console()



mission_tick = 0
battery = 98
coverage = 62
localization_error = 4.2



def create_dashboard():


    global mission_tick
    global battery
    global coverage
    global localization_error


    mission_tick += 1

    battery -= 0.01

    coverage = min(
        100,
        coverage + 0.05
    )

    localization_error = round(
        random.uniform(2,5),
        2
    )


    layout = Layout()


    layout.split_column(

        Layout(
            name="header",
            size=5
        ),

        Layout(
            name="body"
        ),

        Layout(
            name="footer",
            size=3
        )

    )


    # HEADER

    header = Panel(
        Text(
            "VAYUNETRA AUTONOMOUS SWARM COMMAND SYSTEM",
            justify="center",
            style="bold cyan"
        ),
        title="MISSION CONTROL"
    )


    layout["header"].update(header)



    # LEFT TABLE

    drone_table = Table(
        title="DRONE FLEET STATUS"
    )

    drone_table.add_column(
        "ID"
    )

    drone_table.add_column(
        "STATE"
    )

    drone_table.add_column(
        "BATTERY"
    )

    drone_table.add_column(
        "LOCALIZATION"
    )


    for i in range(4):

        drone_table.add_row(

            f"D{i}",

            "SEARCHING",

            f"{battery-i*5:.1f}%",

            f"{localization_error+i:.2f} m"

        )




    # HARDWARE TABLE


    hardware = Table(
        title="HARDWARE BUS"
    )


    hardware.add_column("NODE")
    hardware.add_column("STATUS")
    hardware.add_column("ROLE")


    hardware.add_row(
        "Raspberry Pi 4",
        "ONLINE",
        "DIGITAL TWIN"
    )

    hardware.add_row(
        "STM32F407",
        "CONNECTED",
        "FLIGHT CONTROLLER"
    )

    hardware.add_row(
        "ESP32 RADIO",
        "LINK ACTIVE",
        "SWARM NETWORK"
    )



    # MISSION TABLE


    mission = Table(
        title="MISSION PARAMETERS"
    )


    mission.add_column("PARAMETER")
    mission.add_column("VALUE")


    mission.add_row(
        "Mission Tick",
        str(mission_tick)
    )

    mission.add_row(
        "Search Coverage",
        f"{coverage:.1f}%"
    )

    mission.add_row(
        "Mode",
        "AUTONOMOUS SEARCH"
    )

    mission.add_row(
        "Threat Level",
        "NORMAL"
    )


    body = Layout()

    body.split_row(

        Layout(drone_table),
        Layout()

    )


    body["1"].split_column(

        Layout(hardware),
        Layout(mission)

    )


    layout["body"].update(body)



    layout["footer"].update(

        Panel(
            "STATUS: ALL SYSTEMS NOMINAL | RADIO LINK OK | STM32 READY",
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

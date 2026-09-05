"""
VayuNetra Aerospace Mission Console

Digital Twin + Hardware Mission Display

Raspberry Pi 4
STM32F407 Flight Controller
ESP32 Swarm Radio

"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text

import random
import time


console = Console()


mission_tick = 0
coverage = 60.0


drone_states = [
    "SEARCHING",
    "ENROUTE",
    "RESCUING",
    "RETURNING"
]


def mission_table():

    global mission_tick
    global coverage


    mission_tick += random.randint(1,4)

    coverage = min(
        coverage + random.uniform(0.1,0.8),
        100
    )


    table = Table(
        title="MISSION STATUS"
    )


    table.add_column(
        "PARAMETER",
        style="cyan"
    )

    table.add_column(
        "VALUE",
        style="green"
    )


    data = [

        ("Mission Tick", mission_tick),

        ("Coverage",
         f"{coverage:.1f}%"),

        ("Survivors Detected",
         "4 / 5"),

        ("Survivors Rescued",
         "3 / 5"),

        ("Mission Mode",
         "AUTONOMOUS SEARCH"),

        ("Threat Level",
         "NORMAL")

    ]


    for k,v in data:

        table.add_row(
            k,
            str(v)
        )


    return table





def hardware_panel():


    text = """

RASPBERRY PI 4

STATUS :
ONLINE

ROLE :
DIGITAL TWIN HOST



STM32F407

STATUS :
CONNECTED

ROLE :
FLIGHT CONTROLLER



ESP32 RADIO

STATUS :
ACTIVE

ROLE :
SWARM NETWORK


"""


    return Panel(
        text,
        title="HARDWARE BUS"
    )





def drone_table():


    table = Table(
        title="DRONE FLEET TELEMETRY"
    )


    table.add_column(
        "ID"
    )

    table.add_column(
        "STATE"
    )

    table.add_column(
        "BATTERY"
    )

    table.add_column(
        "TASK"
    )

    table.add_column(
        "LOCAL ERROR"
    )


    for i in range(4):

        battery = random.randint(
            75,
            100
        )


        error = random.uniform(
            1,
            5
        )


        table.add_row(

            f"D-{i}",

            random.choice(
                drone_states
            ),

            f"{battery}%",

            f"SURVIVOR-{random.randint(0,5)}",

            f"{error:.2f} m"

        )


    return table





def localization_table():


    table = Table(
        title="LOCALIZATION ENGINE"
    )


    table.add_column(
        "PARAMETER"
    )


    table.add_column(
        "VALUE"
    )


    table.add_row(
        "Method",
        "INTER DRONE RANGING"
    )


    table.add_row(
        "Mean Error",
        f"{random.uniform(2,5):.2f} m"
    )


    table.add_row(
        "Uncertainty",
        f"{random.uniform(5,15):.2f}"
    )


    table.add_row(
        "Status",
        "ACTIVE"
    )


    return table





def search_grid():


    symbols = [

        "D     #       #",

        "        #      ",

        "   S          D",

        "######        ",

        "        D     "

    ]


    return Panel(

        "\n".join(symbols),

        title="SEARCH GRID"

    )





def create_dashboard():


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



    layout["header"].update(

        Panel(

            Text(

                "✈ VAYUNETRA AUTONOMOUS MISSION CONTROL ✈",

                justify="center",

                style="bold cyan"

            )

        )

    )



    body = Layout()


    body.split_column(

        Layout(
            name="top",
            size=15
        ),

        Layout(
            name="middle",
            size=12
        ),

        Layout(
            name="bottom"
        )

    )



    top = Layout()


    top.split_row(

        Layout(
            mission_table()
        ),

        Layout(
            hardware_panel()
        )

    )


    body["top"].update(
        top
    )


    body["middle"].update(
        drone_table()
    )



    bottom = Layout()


    bottom.split_row(

        Layout(
            search_grid()
        ),

        Layout(
            localization_table()
        )

    )


    body["bottom"].update(
        bottom
    )


    layout["body"].update(
        body
    )



    layout["footer"].update(

        Panel(

            "SYSTEM NOMINAL | DIGITAL TWIN ACTIVE | STM32 ONLINE | ESP32 RADIO READY",

            style="green"

        )

    )


    return layout





with Live(
    refresh_per_second=1,
    screen=True
) as live:


    while True:

        live.update(
            create_dashboard()
        )

        time.sleep(1)

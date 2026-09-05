import math
import time
import socket

from pymavlink import mavutil

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.align import Align


# ============================================================
# CONFIGURATION
# ============================================================

SERIAL_PORT = "/dev/ttyUSB0"
BAUD = 115200

MISSION_PLANNER_IP = "10.221.96.73"
MISSION_PLANNER_PORT = 14550


# ============================================================
# CONNECTION
# ============================================================

console = Console()

connection = mavutil.mavlink_connection(
    SERIAL_PORT,
    baud=BAUD
)

udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


# ============================================================
# TELEMETRY STATE
# ============================================================

telemetry = {
    "lat": 0.0,
    "lon": 0.0,

    "alt": 0.0,
    "relative_alt": 0.0,

    "vx": 0.0,
    "vy": 0.0,
    "vz": 0.0,

    "groundspeed": 0.0,

    "heading": 0.0,

    "roll": 0.0,
    "pitch": 0.0,
    "yaw": 0.0,

    "voltage": 0.0,
    "current": 0.0,
    "battery": 0,

    "heartbeat": False,
    "attitude": False,
    "position": False,
    "system": False,

    "last_message": "WAITING",
    "messages_received": 0,
    "messages_forwarded": 0,

    "last_update": time.time(),
}


# ============================================================
# WAIT FOR HEARTBEAT
# ============================================================

console.print(
    Panel(
        Align.center(
            Text(
                "VAYUNETRA\n\n"
                "INITIALIZING MAVLINK TELEMETRY...",
                style="bold cyan"
            )
        ),
        border_style="cyan"
    )
)

connection.wait_heartbeat()

telemetry["heartbeat"] = True

console.print(
    f"Connected: System {connection.target_system}, "
    f"Component {connection.target_component}"
)

time.sleep(1)


# ============================================================
# MESSAGE PROCESSING
# ============================================================

def process_message(msg):

    msg_type = msg.get_type()

    telemetry["messages_received"] += 1
    telemetry["last_message"] = msg_type
    telemetry["last_update"] = time.time()

    # --------------------------------------------------------
    # HEARTBEAT
    # --------------------------------------------------------

    if msg_type == "HEARTBEAT":

        telemetry["heartbeat"] = True

    # --------------------------------------------------------
    # ATTITUDE
    # --------------------------------------------------------

    elif msg_type == "ATTITUDE":

        telemetry["roll"] = math.degrees(msg.roll)
        telemetry["pitch"] = math.degrees(msg.pitch)
        telemetry["yaw"] = math.degrees(msg.yaw)

        if telemetry["yaw"] < 0:
            telemetry["yaw"] += 360

        telemetry["attitude"] = True

    # --------------------------------------------------------
    # POSITION
    # --------------------------------------------------------

    elif msg_type == "GLOBAL_POSITION_INT":

        telemetry["lat"] = msg.lat / 1e7
        telemetry["lon"] = msg.lon / 1e7

        telemetry["alt"] = msg.alt / 1000.0
        telemetry["relative_alt"] = msg.relative_alt / 1000.0

        telemetry["vx"] = msg.vx / 100.0
        telemetry["vy"] = msg.vy / 100.0
        telemetry["vz"] = msg.vz / 100.0

        telemetry["groundspeed"] = math.sqrt(
            telemetry["vx"] ** 2 +
            telemetry["vy"] ** 2
        )

        telemetry["heading"] = msg.hdg / 100.0

        telemetry["position"] = True

    # --------------------------------------------------------
    # SYSTEM STATUS
    # --------------------------------------------------------

    elif msg_type == "SYS_STATUS":

        telemetry["voltage"] = msg.voltage_battery / 1000.0
        telemetry["current"] = msg.current_battery / 100.0
        telemetry["battery"] = msg.battery_remaining

        telemetry["system"] = True


# ============================================================
# STATUS HELPERS
# ============================================================

def status(value):
    if value:
        return "[bold green]ONLINE[/]"
    return "[bold red]OFFLINE[/]"


def check(value):
    if value:
        return "[bold green]✓[/]"
    return "[dim]—[/]"


def battery_style(value):

    if value > 50:
        return "bold green"

    if value > 20:
        return "bold yellow"

    return "bold red"


# ============================================================
# HEADER
# ============================================================

def header():

    title = Text()

    title.append(
        "VAYUNETRA",
        style="bold white"
    )

    title.append(
        "  //  AUTONOMOUS MISSION CONTROL",
        style="bold cyan"
    )

    subtitle = Text(
        "\nRASPBERRY PI 4  •  LIVE HARDWARE TELEMETRY",
        style="dim"
    )

    combined = Text.assemble(
        title,
        subtitle
    )

    return Panel(
        Align.center(combined),
        border_style="bright_blue"
    )


# ============================================================
# MISSION / SYSTEM STATUS
# ============================================================

def mission_panel():

    table = Table.grid(
        padding=(0, 2)
    )

    table.add_column(
        justify="right",
        style="bold grey70"
    )

    table.add_column()

    table.add_row(
        "MISSION",
        "[bold green]ACTIVE[/]"
    )

    table.add_row(
        "LINK",
        "[bold green]MAVLINK[/]"
    )

    table.add_row(
        "SYSTEM ID",
        f"[cyan]{connection.target_system}[/]"
    )

    table.add_row(
        "COMPONENT",
        f"[cyan]{connection.target_component}[/]"
    )

    table.add_row(
        "MESSAGES",
        f"[bold cyan]{telemetry['messages_received']}[/]"
    )

    table.add_row(
        "FORWARDED",
        f"[bold green]{telemetry['messages_forwarded']}[/]"
    )

    return Panel(
        table,
        title="[bold]MISSION STATUS[/]",
        border_style="cyan"
    )


# ============================================================
# HARDWARE BUS
# ============================================================

def hardware_panel():

    text = Text()

    text.append(
        "RASPBERRY PI 4\n",
        style="bold white"
    )

    text.append("  STATUS   ")
    text.append("ONLINE\n", style="bold green")

    text.append(
        "  ROLE     TELEMETRY GATEWAY\n\n"
    )

    text.append(
        "STM32F407\n",
        style="bold white"
    )

    text.append("  STATUS   ")
    text.append("CONNECTED\n", style="bold green")

    text.append(
        "  ROLE     CONTROL LAYER\n\n"
    )

    text.append(
        "ESP32 SWARM MESH\n",
        style="bold white"
    )

    text.append("  STATUS   ")
    text.append("READY FOR INTEGRATION\n", style="bold yellow")

    text.append(
        "  ROLE     INTER-DRONE COMMS\n"
    )

    return Panel(
        text,
        title="[bold]HARDWARE BUS[/]",
        border_style="magenta"
    )


# ============================================================
# DRONE TELEMETRY
# ============================================================

def drone_panel():

    table = Table(
        border_style="grey50",
        header_style="bold white on grey23",
        expand=True
    )

    table.add_column(
        "UNIT",
        justify="center"
    )

    table.add_column(
        "STATE",
        justify="center"
    )

    table.add_column(
        "BATTERY",
        justify="right"
    )

    table.add_column(
        "ALTITUDE",
        justify="right"
    )

    table.add_column(
        "SPEED",
        justify="right"
    )

    table.add_column(
        "HEADING",
        justify="right"
    )

    battery = telemetry["battery"]

    if telemetry["heartbeat"]:
        state = "[bold cyan]TELEMETRY[/]"
        unit = "[bold green]● D1[/]"
    else:
        state = "[bold red]OFFLINE[/]"
        unit = "[red]X D1[/]"

    table.add_row(
        unit,
        state,
        f"[{battery_style(battery)}]{battery}%[/]",
        f"{telemetry['relative_alt']:.1f} m",
        f"{telemetry['groundspeed']:.2f} m/s",
        f"{telemetry['heading']:.1f}°",
    )

    # Future swarm nodes

    table.add_row(
        "[dim]● D2[/]",
        "[dim]PENDING[/]",
        "[dim]--[/]",
        "[dim]--[/]",
        "[dim]--[/]",
        "[dim]--[/]",
    )

    table.add_row(
        "[dim]● D3[/]",
        "[dim]PENDING[/]",
        "[dim]--[/]",
        "[dim]--[/]",
        "[dim]--[/]",
        "[dim]--[/]",
    )

    return Panel(
        table,
        title="[bold]DRONE FLEET TELEMETRY[/]",
        border_style="green"
    )


# ============================================================
# POSITION PANEL
# ============================================================

def position_panel():

    table = Table.grid(
        padding=(0, 2)
    )

    table.add_column(
        style="bold grey70"
    )

    table.add_column(
        justify="right"
    )

    table.add_row(
        "LATITUDE",
        f"[cyan]{telemetry['lat']:.7f}°[/]"
    )

    table.add_row(
        "LONGITUDE",
        f"[cyan]{telemetry['lon']:.7f}°[/]"
    )

    table.add_row(
        "ALTITUDE",
        f"[yellow]{telemetry['alt']:.2f} m[/]"
    )

    table.add_row(
        "RELATIVE ALT",
        f"[yellow]{telemetry['relative_alt']:.2f} m[/]"
    )

    table.add_row(
        "HEADING",
        f"[green]{telemetry['heading']:.2f}°[/]"
    )

    return Panel(
        table,
        title="[bold]NAVIGATION / POSITION[/]",
        border_style="yellow"
    )


# ============================================================
# ATTITUDE PANEL
# ============================================================

def attitude_panel():

    table = Table.grid(
        padding=(0, 2)
    )

    table.add_column(
        style="bold grey70"
    )

    table.add_column(
        justify="right"
    )

    table.add_row(
        "ROLL",
        f"[magenta]{telemetry['roll']:.2f}°[/]"
    )

    table.add_row(
        "PITCH",
        f"[magenta]{telemetry['pitch']:.2f}°[/]"
    )

    table.add_row(
        "YAW",
        f"[magenta]{telemetry['yaw']:.2f}°[/]"
    )

    return Panel(
        table,
        title="[bold]ATTITUDE[/]",
        border_style="blue"
    )


# ============================================================
# BATTERY PANEL
# ============================================================

def battery_panel():

    battery = max(
        0,
        min(100, telemetry["battery"])
    )

    filled = int(
        20 * battery / 100
    )

    empty = 20 - filled

    bar = (
        f"[{battery_style(battery)}]"
        + "█" * filled
        + "[/]"
        + "[grey30]"
        + "░" * empty
        + "[/]"
    )

    table = Table.grid(
        padding=(0, 2)
    )

    table.add_column(
        style="bold grey70"
    )

    table.add_column()

    table.add_row(
        "LEVEL",
        f"{bar}  {battery}%"
    )

    table.add_row(
        "VOLTAGE",
        f"[green]{telemetry['voltage']:.2f} V[/]"
    )

    table.add_row(
        "CURRENT",
        f"[yellow]{telemetry['current']:.2f} A[/]"
    )

    return Panel(
        table,
        title="[bold]POWER SYSTEM[/]",
        border_style="green"
    )


# ============================================================
# MOTION PANEL
# ============================================================

def motion_panel():

    table = Table.grid(
        padding=(0, 2)
    )

    table.add_column(
        style="bold grey70"
    )

    table.add_column(
        justify="right"
    )

    table.add_row(
        "GROUND SPEED",
        f"[cyan]{telemetry['groundspeed']:.2f} m/s[/]"
    )

    table.add_row(
        "VX / NORTH",
        f"{telemetry['vx']:.2f} m/s"
    )

    table.add_row(
        "VY / EAST",
        f"{telemetry['vy']:.2f} m/s"
    )

    table.add_row(
        "VZ / DOWN",
        f"{telemetry['vz']:.2f} m/s"
    )

    return Panel(
        table,
        title="[bold]MOTION VECTOR[/]",
        border_style="cyan"
    )


# ============================================================
# TELEMETRY HEALTH
# ============================================================

def telemetry_panel():

    table = Table.grid(
        padding=(0, 2)
    )

    table.add_column(
        style="bold grey70"
    )

    table.add_column()

    table.add_row(
        "HEARTBEAT",
        check(telemetry["heartbeat"])
    )

    table.add_row(
        "ATTITUDE",
        check(telemetry["attitude"])
    )

    table.add_row(
        "POSITION",
        check(telemetry["position"])
    )

    table.add_row(
        "SYSTEM STATUS",
        check(telemetry["system"])
    )

    table.add_row(
        "LAST MESSAGE",
        f"[cyan]{telemetry['last_message']}[/]"
    )

    table.add_row(
        "MISSION PLANNER",
        "[bold green]UDP 14550[/]"
    )

    return Panel(
        table,
        title="[bold]TELEMETRY HEALTH[/]",
        border_style="blue"
    )


# ============================================================
# FOOTER
# ============================================================

def footer():

    return Panel(
        Align.center(
            Text(
                " VAYUNETRA  |  LIVE HARDWARE TELEMETRY  |  "
                "MISSION ACTIVE ",
                style="bold white on dark_green"
            )
        ),
        border_style="green"
    )


# ============================================================
# COMPLETE LAYOUT
# ============================================================

def build_layout():

    layout = Layout()

    layout.split_column(
        Layout(
            header(),
            name="header",
            size=4
        ),

        Layout(
            name="body"
        ),

        Layout(
            footer(),
            name="footer",
            size=3
        )
    )

    layout["body"].split_column(

        Layout(
            name="top",
            size=11
        ),

        Layout(
            name="middle",
            size=13
        ),

        Layout(
            name="bottom"
        )
    )

    # --------------------------------------------------------
    # TOP
    # --------------------------------------------------------

    layout["top"].split_row(

        Layout(
            mission_panel(),
            ratio=1
        ),

        Layout(
            hardware_panel(),
            ratio=1
        )
    )

    # --------------------------------------------------------
    # MIDDLE
    # --------------------------------------------------------

    layout["middle"].split_row(

        Layout(
            drone_panel(),
            ratio=2
        ),

        Layout(
            position_panel(),
            ratio=1
        )
    )

    # --------------------------------------------------------
    # BOTTOM
    # --------------------------------------------------------

    layout["bottom"].split_row(

        Layout(
            attitude_panel(),
            ratio=1
        ),

        Layout(
            motion_panel(),
            ratio=1
        ),

        Layout(
            battery_panel(),
            ratio=1
        ),

        Layout(
            telemetry_panel(),
            ratio=1
        )
    )

    return layout


# ============================================================
# MAIN LOOP
# ============================================================

try:

    with Live(
        build_layout(),
        console=console,
        refresh_per_second=5,
        screen=True
    ) as live:

        while True:

            msg = connection.recv_match(
                blocking=True,
                timeout=0.2
            )

            if msg:

                # ------------------------------------------------
                # Forward original MAVLink packet
                # ------------------------------------------------

                packet = msg.get_msgbuf()

                if packet:

                    udp.sendto(
                        packet,
                        (
                            MISSION_PLANNER_IP,
                            MISSION_PLANNER_PORT
                        )
                    )

                    telemetry["messages_forwarded"] += 1

                # ------------------------------------------------
                # Update dashboard
                # ------------------------------------------------

                process_message(msg)

            # Refresh screen

            live.update(
                build_layout()
            )


except KeyboardInterrupt:

    pass


finally:

    udp.close()
    connection.close()

    console.print(
        "\n[bold yellow]VayuNetra dashboard stopped.[/]"
    )

PYEOF

import pygame
import config

from world.environment import Environment
from swarm.drone import Drone
from swarm.swarm import Swarm
from simulation.telemetry import Telemetry


# =========================================================
# INITIALIZE
# =========================================================

pygame.init()

clock = pygame.time.Clock()

environment = Environment()

swarm = Swarm()

telemetry = Telemetry()


# =========================================================
# CREATE DRONES
# =========================================================

drone1 = Drone(
    drone_id=1,
    position=(100, 250)
)

drone1.velocity = [
    0.0,
    0.0
]


drone2 = Drone(
    drone_id=2,
    position=(100, 350)
)

drone2.velocity = [
    0.0,
    0.0
]


drone3 = Drone(
    drone_id=3,
    position=(100, 450)
)

drone3.velocity = [
    0.0,
    0.0
]


drone4 = Drone(
    drone_id=4,
    position=(850, 100)
)

drone4.velocity = [
    -20.0,
    0.0
]


drone5 = Drone(
    drone_id=5,
    position=(850, 600)
)

drone5.velocity = [
    -20.0,
    0.0
]


# =========================================================
# ADD DRONES
# =========================================================

swarm.add_drone(drone1)
swarm.add_drone(drone2)
swarm.add_drone(drone3)
swarm.add_drone(drone4)
swarm.add_drone(drone5)


print(
    "Number of drones in swarm:",
    len(swarm.drones)
)


# =========================================================
# ASSIGN MISSIONS
# =========================================================

swarm.mission_manager.assign_zone(
    drone1,
    environment.zones[0]
)

swarm.mission_manager.assign_zone(
    drone2,
    environment.zones[1]
)

swarm.mission_manager.assign_zone(
    drone3,
    environment.zones[2]
)


# =========================================================
# INITIALIZE A*
# =========================================================

swarm.initialize_path_planner(
    environment
)


# =========================================================
# PLAN PATHS
# =========================================================

print()
print("A* OBSTACLE STRESS TEST")
print("--------------------------------")

swarm.plan_all_paths()


# =========================================================
# DISPLAY
# =========================================================

screen = pygame.display.set_mode(
    (
        environment.width,
        environment.height
    )
)

pygame.display.set_caption(
    "VAYUNETRA - A* Path Planning Test"
)


# =========================================================
# SIMULATION
# =========================================================

running = True

while (
    running
    and
    telemetry.time <
    config.SIMULATION_DURATION
):

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False


    dt = (
        clock.tick(60)
        /
        1000.0
    )


    telemetry.update_time(
        dt
    )


    swarm.update(
        environment,
        dt
    )


    telemetry.record_swarm(
        swarm,
        environment
    )


    screen.fill(
        (
            20,
            20,
            25
        )
    )


    environment.draw(
        screen
    )


    swarm.draw(
        screen
    )


    pygame.display.flip()


# =========================================================
# RESULTS
# =========================================================

telemetry.save_csv()


print()
print("Mission summary:")

print(
    swarm.mission_manager.summary()
)


print()
print("Simulation summary:")

print(
    telemetry.summary()
)


pygame.quit()
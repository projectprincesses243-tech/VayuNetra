import heapq
import math


class AStarPlanner:

    def __init__(
        self,
        environment,
        grid_size=20,
        drone_radius=10
    ):
        self.environment = environment

        self.grid_size = grid_size

        self.drone_radius = drone_radius

        self.width = environment.width

        self.height = environment.height

        self.columns = math.ceil(
            self.width / self.grid_size
        )

        self.rows = math.ceil(
            self.height / self.grid_size
        )

        self.grid = self._build_grid()

    # =====================================================
    # GRID CREATION
    # =====================================================

    def _build_grid(self):

        grid = []

        for row in range(self.rows):

            row_data = []

            for column in range(self.columns):

                position = self.grid_to_world(
                    column,
                    row
                )

                blocked = self.environment.is_obstacle(
                    position,
                    self.drone_radius
                )

                row_data.append(
                    blocked
                )

            grid.append(
                row_data
            )

        return grid

    # =====================================================
    # COORDINATE CONVERSION
    # =====================================================

    def world_to_grid(
        self,
        position
    ):

        x = int(
            position[0] /
            self.grid_size
        )

        y = int(
            position[1] /
            self.grid_size
        )

        x = max(
            0,
            min(
                x,
                self.columns - 1
            )
        )

        y = max(
            0,
            min(
                y,
                self.rows - 1
            )
        )

        return (
            x,
            y
        )

    def grid_to_world(
        self,
        column,
        row
    ):

        x = (
            column *
            self.grid_size
            +
            self.grid_size / 2
        )

        y = (
            row *
            self.grid_size
            +
            self.grid_size / 2
        )

        return [
            x,
            y
        ]

    # =====================================================
    # VALIDITY
    # =====================================================

    def is_valid_node(
        self,
        node
    ):

        column, row = node

        if column < 0:
            return False

        if column >= self.columns:
            return False

        if row < 0:
            return False

        if row >= self.rows:
            return False

        return not self.grid[row][column]

    # =====================================================
    # NEIGHBOURS
    # =====================================================

    def get_neighbors(
        self,
        node
    ):

        column, row = node

        directions = [

            # Cardinal movement
            (1, 0),
            (-1, 0),
            (0, 1),
            (0, -1),

            # Diagonal movement
            (1, 1),
            (1, -1),
            (-1, 1),
            (-1, -1)
        ]

        neighbors = []

        for dx, dy in directions:

            neighbor = (
                column + dx,
                row + dy
            )

            if self.is_valid_node(
                neighbor
            ):

                neighbors.append(
                    neighbor
                )

        return neighbors

    # =====================================================
    # DISTANCE / HEURISTIC
    # =====================================================

    def distance(
        self,
        node_a,
        node_b
    ):

        dx = (
            node_a[0] -
            node_b[0]
        )

        dy = (
            node_a[1] -
            node_b[1]
        )

        return math.sqrt(
            dx ** 2 +
            dy ** 2
        )

    def heuristic(
        self,
        node,
        goal
    ):

        return self.distance(
            node,
            goal
        )

    # =====================================================
    # A* SEARCH
    # =====================================================

    def find_path(
        self,
        start_position,
        goal_position
    ):

        start = self.world_to_grid(
            start_position
        )

        goal = self.world_to_grid(
            goal_position
        )

        # -------------------------------------------------
        # Start or goal may fall inside an obstacle
        # -------------------------------------------------

        if not self.is_valid_node(start):

            start = self.find_nearest_free_node(
                start
            )

        if not self.is_valid_node(goal):

            goal = self.find_nearest_free_node(
                goal
            )

        if start is None:

            return []

        if goal is None:

            return []

        # -------------------------------------------------
        # Open set
        # -------------------------------------------------

        open_set = []

        heapq.heappush(
            open_set,
            (
                0,
                start
            )
        )

        # -------------------------------------------------
        # Cost from start
        # -------------------------------------------------

        g_score = {
            start: 0
        }

        # -------------------------------------------------
        # Parent relationships
        # -------------------------------------------------

        came_from = {}

        # -------------------------------------------------
        # A* search
        # -------------------------------------------------

        while open_set:

            _, current = heapq.heappop(
                open_set
            )

            if current == goal:

                path = self._reconstruct_path(
                    came_from,
                    current
                )

                return [
                    self.grid_to_world(
                        column,
                        row
                    )
                    for column, row in path
                ]

            for neighbor in self.get_neighbors(
                current
            ):

                movement_cost = self.distance(
                    current,
                    neighbor
                )

                tentative_g_score = (
                    g_score[current]
                    +
                    movement_cost
                )

                if (
                    neighbor not in g_score
                    or
                    tentative_g_score <
                    g_score[neighbor]
                ):

                    came_from[neighbor] = current

                    g_score[neighbor] = (
                        tentative_g_score
                    )

                    f_score = (
                        tentative_g_score
                        +
                        self.heuristic(
                            neighbor,
                            goal
                        )
                    )

                    heapq.heappush(
                        open_set,
                        (
                            f_score,
                            neighbor
                        )
                    )

        # -------------------------------------------------
        # No path found
        # -------------------------------------------------

        return []

    # =====================================================
    # RECONSTRUCT PATH
    # =====================================================

    def _reconstruct_path(
        self,
        came_from,
        current
    ):

        path = [
            current
        ]

        while current in came_from:

            current = came_from[
                current
            ]

            path.append(
                current
            )

        path.reverse()

        return path

    # =====================================================
    # FIND NEAREST FREE NODE
    # =====================================================

    def find_nearest_free_node(
        self,
        blocked_node
    ):

        column, row = blocked_node

        candidates = []

        max_radius = max(
            self.columns,
            self.rows
        )

        for radius in range(
            1,
            max_radius
        ):

            for dx in range(
                -radius,
                radius + 1
            ):

                for dy in range(
                    -radius,
                    radius + 1
                ):

                    if (
                        abs(dx) != radius
                        and
                        abs(dy) != radius
                    ):
                        continue

                    candidate = (
                        column + dx,
                        row + dy
                    )

                    if self.is_valid_node(
                        candidate
                    ):

                        distance = self.distance(
                            blocked_node,
                            candidate
                        )

                        candidates.append(
                            (
                                distance,
                                candidate
                            )
                        )

            if candidates:

                candidates.sort(
                    key=lambda item: item[0]
                )

                return candidates[0][1]

        return None

    # =====================================================
    # PATH LENGTH
    # =====================================================

    def path_length(
        self,
        path
    ):

        if len(path) < 2:

            return 0.0

        total = 0.0

        for i in range(
            1,
            len(path)
        ):

            dx = (
                path[i][0] -
                path[i - 1][0]
            )

            dy = (
                path[i][1] -
                path[i - 1][1]
            )

            total += math.sqrt(
                dx ** 2 +
                dy ** 2
            )

        return total

    # =====================================================
    # PATH SMOOTHING
    # =====================================================

    def smooth_path(
        self,
        path
    ):

        if len(path) <= 2:

            return path

        smoothed = [
            path[0]
        ]

        current_index = 0

        while current_index < len(path) - 1:

            furthest_index = (
                current_index + 1
            )

            for candidate_index in range(
                current_index + 2,
                len(path)
            ):

                if self.line_is_clear(
                    path[current_index],
                    path[candidate_index]
                ):

                    furthest_index = (
                        candidate_index
                    )

                else:

                    break

            smoothed.append(
                path[furthest_index]
            )

            current_index = (
                furthest_index
            )

        return smoothed

    # =====================================================
    # LINE OF SIGHT
    # =====================================================

    def line_is_clear(
        self,
        start,
        end
    ):

        dx = end[0] - start[0]

        dy = end[1] - start[1]

        distance = math.sqrt(
            dx ** 2 +
            dy ** 2
        )

        if distance == 0:

            return True

        steps = max(
            1,
            int(
                distance /
                (self.grid_size / 2)
            )
        )

        for i in range(
            steps + 1
        ):

            ratio = (
                i /
                steps
            )

            position = [

                start[0] +
                dx * ratio,

                start[1] +
                dy * ratio
            ]

            if self.environment.is_obstacle(
                position,
                self.drone_radius
            ):

                return False

        return True

    # =====================================================
    # COMPLETE PLANNING PIPELINE
    # =====================================================

    def plan(
        self,
        start_position,
        goal_position
    ):

        raw_path = self.find_path(
            start_position,
            goal_position
        )

        if not raw_path:

            return []

        smooth_path = self.smooth_path(
            raw_path
        )

        return smooth_path
"""Board model and checks for the watchtower and ring clues.

Coordinates are (row, column), with (0, 0) at the upper-left lattice point.
The board has 11 x 12 lattice points and therefore 10 x 11 cells.
"""

POINT_ROWS, POINT_COLS = 11, 12
CELL_ROWS, CELL_COLS = POINT_ROWS - 1, POINT_COLS - 1

# Each entry is (required number of distinct adjacent regions, row, column).
# A lattice point touches up to four cells diagonally around that point.
WATCHTOWERS = [
    (1, 1, 3),
    (3, 1, 6),
    (1, 2, 8),
    (1, 3, 2),
    (1, 3, 5),
    (3, 4, 8),
    (1, 4, 10),
    (1, 5, 4),
    (1, 5, 7),
    (3, 6, 1),
    (3, 6, 3),
    (3, 7, 6),
    (1, 7, 9),
    (1, 8, 3),
    (3, 9, 5),
    (3, 9, 8),
]


def make_cell_grid(value=None):
    """Create a 10 x 11 grid of cell region IDs; None means unassigned."""
    return [[value for _ in range(CELL_COLS)] for _ in range(CELL_ROWS)]


def p(grid):
    """Print a cell grid with row and column indices."""
    _validate_cell_grid(grid)
    print("     " + " ".join(f"{col:2}" for col in range(CELL_COLS)))
    for row, values in enumerate(grid):
        print(f"{row:3}: " + " ".join(f"{value!s:>2}" for value in values))


def _validate_cell_grid(grid):
    if len(grid) != CELL_ROWS or any(len(row) != CELL_COLS for row in grid):
        raise ValueError(f"cell grid must have shape {CELL_ROWS} x {CELL_COLS}")


def _validate_edge_grids(horizontal_edges, vertical_edges):
    # horizontal_edges[r][c] joins lattice points (r,c) and (r,c+1).
    # vertical_edges[r][c] joins lattice points (r,c) and (r+1,c).
    if (len(horizontal_edges) != POINT_ROWS
            or any(len(row) != POINT_COLS - 1 for row in horizontal_edges)):
        raise ValueError(f"horizontal_edges must have shape {POINT_ROWS} x {POINT_COLS - 1}")
    if (len(vertical_edges) != POINT_ROWS - 1
            or any(len(row) != POINT_COLS for row in vertical_edges)):
        raise ValueError(f"vertical_edges must have shape {POINT_ROWS - 1} x {POINT_COLS}")


def _edge_neighbors(horizontal_edges, vertical_edges, point):
    """Return lattice points connected to point by a drawn segment."""
    row, col = point
    neighbors = []
    if col > 0 and horizontal_edges[row][col - 1]:
        neighbors.append((row, col - 1))
    if col < POINT_COLS - 1 and horizontal_edges[row][col]:
        neighbors.append((row, col + 1))
    if row > 0 and vertical_edges[row - 1][col]:
        neighbors.append((row - 1, col))
    if row < POINT_ROWS - 1 and vertical_edges[row][col]:
        neighbors.append((row + 1, col))
    return neighbors


def check_single_path(horizontal_edges, vertical_edges,
                      start=(0, 0), end=(POINT_ROWS - 1, POINT_COLS - 1)):
    """Check that drawn segments form one simple path from start to end.

    Unused lattice points have degree zero, the two endpoints degree one, and
    every other used point degree two. This rejects branches and cycles.
    """
    _validate_edge_grids(horizontal_edges, vertical_edges)
    for point in (start, end):
        row, col = point
        if not (0 <= row < POINT_ROWS and 0 <= col < POINT_COLS):
            raise ValueError(f"endpoint {point} is outside the lattice")
    if start == end:
        raise ValueError("start and end must be different lattice points")

    used_points = set()
    for row in range(POINT_ROWS):
        for col in range(POINT_COLS):
            point = (row, col)
            degree = len(_edge_neighbors(horizontal_edges, vertical_edges, point))
            if degree:
                used_points.add(point)
            expected = 1 if point in (start, end) else (2 if degree else 0)
            if degree != expected:
                return False
    if start not in used_points or end not in used_points:
        return False

    reached = {start}
    stack = [start]
    while stack:
        point = stack.pop()
        for neighbor in _edge_neighbors(horizontal_edges, vertical_edges, point):
            if neighbor not in reached:
                reached.add(neighbor)
                stack.append(neighbor)
    return reached == used_points and end in reached


def find_cell_regions(horizontal_edges, vertical_edges):
    """Label cells by connected region, treating drawn segments as walls.

    Returns a 10 x 11 matrix of integer region IDs, numbered from zero.
    This can be used directly by check_watchtowers.
    """
    _validate_edge_grids(horizontal_edges, vertical_edges)
    regions = [[None] * CELL_COLS for _ in range(CELL_ROWS)]
    region_id = 0
    for start_row in range(CELL_ROWS):
        for start_col in range(CELL_COLS):
            if regions[start_row][start_col] is not None:
                continue
            regions[start_row][start_col] = region_id
            stack = [(start_row, start_col)]
            while stack:
                row, col = stack.pop()
                # Neighboring cells are separated by the lattice edge they share.
                candidates = []
                if row > 0 and not horizontal_edges[row][col]:
                    candidates.append((row - 1, col))
                if row < CELL_ROWS - 1 and not horizontal_edges[row + 1][col]:
                    candidates.append((row + 1, col))
                if col > 0 and not vertical_edges[row][col]:
                    candidates.append((row, col - 1))
                if col < CELL_COLS - 1 and not vertical_edges[row][col + 1]:
                    candidates.append((row, col + 1))
                for next_row, next_col in candidates:
                    if regions[next_row][next_col] is None:
                        regions[next_row][next_col] = region_id
                        stack.append((next_row, next_col))
            region_id += 1
    return regions


def check_watchtowers(cell_regions, clues=WATCHTOWERS):
    """Check each tower's count of distinct regions touching its lattice point.

    Cell (r, c) is bounded by lattice points (r,c), (r,c+1),
    (r+1,c), and (r+1,c+1). Thus the four candidate cells around point
    (r,c) have top-left coordinates (r-1,c-1), (r-1,c), (r,c-1), (r,c).
    Cells beyond the board edge are ignored.
    """
    _validate_cell_grid(cell_regions)
    for required, row, col in clues:
        if not (0 <= row < POINT_ROWS and 0 <= col < POINT_COLS):
            raise ValueError(f"watchtower coordinate {(row, col)} is outside the lattice")
        touching_regions = {
            cell_regions[r][c]
            for r, c in ((row - 1, col - 1), (row - 1, col),
                         (row, col - 1), (row, col))
            if 0 <= r < CELL_ROWS and 0 <= c < CELL_COLS
            and cell_regions[r][c] is not None
        }
        # A None cell means the region assignment is incomplete, so this
        # check cannot safely accept the tower yet.
        touching_cells = sum(
            1 for r, c in ((row - 1, col - 1), (row - 1, col),
                           (row, col - 1), (row, col))
            if 0 <= r < CELL_ROWS and 0 <= c < CELL_COLS
        )
        if len(touching_regions) != touching_cells or len(touching_regions) != required:
            return False
    return True


def check_rings(horizontal_edges, vertical_edges):
    """Return False if any lattice point has exactly three incident lines.

    Horizontal edge array shape: 11 x 11. Vertical edge array shape: 10 x 12.
    Entries are truthy when the corresponding segment is drawn.
    """
    _validate_edge_grids(horizontal_edges, vertical_edges)
    for row in range(POINT_ROWS):
        for col in range(POINT_COLS):
            incident = 0
            if col > 0:
                incident += bool(horizontal_edges[row][col - 1])
            if col < POINT_COLS - 1:
                incident += bool(horizontal_edges[row][col])
            if row > 0:
                incident += bool(vertical_edges[row - 1][col])
            if row < POINT_ROWS - 1:
                incident += bool(vertical_edges[row][col])
            if incident == 3:
                return False
    return True


def check_local_rules(cell_regions, horizontal_edges, vertical_edges):
    """Check watchtowers and ring clues on a complete candidate board."""
    return (check_watchtowers(cell_regions)
            and check_rings(horizontal_edges, vertical_edges))


def check_candidate(horizontal_edges, vertical_edges,
                    start=(0, 0), end=(POINT_ROWS - 1, POINT_COLS - 1)):
    """Check path shape, ring clues, and watchtowers for a complete route."""
    if not check_single_path(horizontal_edges, vertical_edges, start, end):
        return False
    if not check_rings(horizontal_edges, vertical_edges):
        return False
    cell_regions = find_cell_regions(horizontal_edges, vertical_edges)
    return check_watchtowers(cell_regions)


if __name__ == "__main__":
    regions = make_cell_grid()
    horizontal = [[False] * (POINT_COLS - 1) for _ in range(POINT_ROWS)]
    vertical = [[False] * POINT_COLS for _ in range(POINT_ROWS - 1)]
    print(f"lattice: {POINT_ROWS} x {POINT_COLS}; cells: {CELL_ROWS} x {CELL_COLS}")
    print("Assign cell region IDs and line segments before checking the clues.")

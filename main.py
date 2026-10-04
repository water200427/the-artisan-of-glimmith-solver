"""Coloring model for the Glimmith board.

The grid stores cell colors (not line segments): 1 and 2 are the two colors,
and 0 is reserved for an unassigned cell while building a candidate.
Coordinates are (row, column), with (0, 0) at the upper-left cell.
"""

ROWS, COLS = 11, 12
COLORS = (1, 2)
COLOR_2_WAYPOINTS = ((1, 1), (1, 10), (9, 1), (9, 10))

# Each entry is (required number of unlike-color boundary edges, row, column).
FENCES = (
    (1, 1, 3), (3, 1, 6), (1, 2, 8), (1, 3, 2),
    (1, 3, 5), (3, 4, 8), (1, 4, 10), (1, 5, 4),
    (1, 5, 7), (3, 6, 1), (3, 6, 3), (3, 7, 6),
    (1, 7, 9), (1, 8, 3), (3, 9, 5), (3, 9, 8),
)


def make_grid(value=0):
    """Create an 11 x 12 coloring grid."""
    return [[value for _ in range(COLS)] for _ in range(ROWS)]


def make_initial_grid():
    """Set the known outer ring to color 1 and the four waypoints to color 2."""
    grid = make_grid()
    for row in range(ROWS):
        for col in range(COLS):
            if row in (0, ROWS - 1) or col in (0, COLS - 1):
                grid[row][col] = 1
    for row, col in COLOR_2_WAYPOINTS:
        grid[row][col] = 2
    return grid


def print_grid(grid):
    _validate_grid(grid)
    print("     " + " ".join(f"{col:2}" for col in range(COLS)))
    for row, values in enumerate(grid):
        print(f"{row:3}: " + " ".join(f"{value:2}" for value in values))


def _validate_grid(grid):
    if len(grid) != ROWS or any(len(row) != COLS for row in grid):
        raise ValueError(f"grid must have shape {ROWS} x {COLS}")


def _neighbors(row, col):
    for next_cell in ((row - 1, col), (row, col + 1),
                      (row + 1, col), (row, col - 1)):
        next_row, next_col = next_cell
        if 0 <= next_row < ROWS and 0 <= next_col < COLS:
            yield next_cell


def color_components(grid, color):
    """Return all 4-neighbor connected components for one color."""
    _validate_grid(grid)
    if color not in COLORS:
        raise ValueError(f"color must be one of {COLORS}")
    unseen = {
        (row, col)
        for row in range(ROWS)
        for col in range(COLS)
        if grid[row][col] == color
    }
    components = []
    while unseen:
        start = unseen.pop()
        component = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for neighbor in _neighbors(row, col):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def check_watchtowers(grid):
    """Every 2 x 2 cell block must contain both colors.

    This is the full-board form of the screenshot's watchtower rule: no
    lattice point may touch four cells belonging to one and the same region.
    """
    _validate_grid(grid)
    for row in range(ROWS - 1):
        for col in range(COLS - 1):
            color = grid[row][col]
            if (grid[row][col + 1] == color
                    and grid[row + 1][col] == color
                    and grid[row + 1][col + 1] == color):
                return False
    return True


def check_fences(grid, clues=FENCES):
    """Check the exact number of color boundaries around each fence cell.

    For a clue (style, row, col), count orthogonally adjacent cells whose
    color differs from the clue cell. Each such unlike-color side is one edge.
    Neighbors beyond the board are not counted.
    """
    _validate_grid(grid)
    for style, row, col in clues:
        if not (0 <= row < ROWS and 0 <= col < COLS):
            raise ValueError(f"fence coordinate {(row, col)} is outside the grid")
        center_color = grid[row][col]
        boundary_edges = sum(
            grid[next_row][next_col] != center_color
            for next_row, next_col in _neighbors(row, col)
        )
        if boundary_edges != style:
            return False
    return True


def check_rose_windows(grid, symbols, required_symbols=None):
    """Require every region to contain exactly one of each rose-window motif.

    `symbols` is an iterable of (motif, row, column), using cell coordinates.
    Each motif should occur twice on the board, once in each color region.
    """
    _validate_grid(grid)
    components = {
        color: color_components(grid, color)
        for color in COLORS
    }
    if any(len(components[color]) != 1 for color in COLORS):
        return False
    motif_cells = {}
    for motif, row, col in symbols:
        if not (0 <= row < ROWS and 0 <= col < COLS):
            raise ValueError(f"rose-window coordinate {(row, col)} is outside the grid")
        if grid[row][col] not in COLORS:
            return False
        motif_cells.setdefault(motif, []).append((row, col))
    required = set(required_symbols) if required_symbols is not None else set(motif_cells)
    for motif in required:
        locations = motif_cells.get(motif, [])
        if len(locations) != 2:
            return False
        if {grid[row][col] for row, col in locations} != set(COLORS):
            return False
    return True


def check_coloring(grid, rose_symbols=(), required_symbols=None):
    """Check the known coloring rules and optional rose-window clues.

    Requires only colors 1 and 2, color 1 around the entire board boundary,
    the four specified color-2 waypoints, and exactly one connected component
    of each color. Connectivity makes the 2-region contain a path through all
    four waypoints.
    """
    _validate_grid(grid)
    if any(value not in COLORS for row in grid for value in row):
        return False
    for row in range(ROWS):
        for col in range(COLS):
            if (row in (0, ROWS - 1) or col in (0, COLS - 1)) and grid[row][col] != 1:
                return False
    if any(grid[row][col] != 2 for row, col in COLOR_2_WAYPOINTS):
        return False
    if not check_watchtowers(grid):
        return False
    if not check_fences(grid):
        return False
    if any(len(color_components(grid, color)) != 1 for color in COLORS):
        return False
    if rose_symbols or required_symbols:
        return check_rose_windows(grid, rose_symbols, required_symbols)
    return True


if __name__ == "__main__":
    print_grid(make_initial_grid())

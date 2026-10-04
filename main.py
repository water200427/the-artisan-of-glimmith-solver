"""Board model and checks for the watchtower and ring clues.

Coordinates are (row, column), with (0, 0) at the upper-left lattice point.
The screenshot has 10 x 11 lattice points and therefore 9 x 10 cells.
"""

POINT_ROWS, POINT_COLS = 10, 11
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
    """Create a 9 x 10 grid of cell region IDs; None means unassigned."""
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

    Returns a 9 x 10 matrix of integer region IDs, numbered from zero.
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


def _cells_by_region(cell_regions):
    _validate_cell_grid(cell_regions)
    grouped = {}
    for row, values in enumerate(cell_regions):
        for col, region_id in enumerate(values):
            grouped.setdefault(region_id, set()).add((row, col))
    return grouped


def check_rose_windows(cell_regions, symbols, required_symbols=None):
    """Require each region to contain exactly one of every rose-window type.

    `symbols` is an iterable of (symbol_name, row, column) entries using cell
    coordinates. `required_symbols` may list symbol types required even when
    the supplied board currently contains none of that type.
    """
    regions = _cells_by_region(cell_regions)
    symbol_cells = {}
    for symbol, row, col in symbols:
        if not (0 <= row < CELL_ROWS and 0 <= col < CELL_COLS):
            raise ValueError(f"rose-window coordinate {(row, col)} is outside the cell grid")
        symbol_cells.setdefault((row, col), []).append(symbol)
    required = set(required_symbols) if required_symbols is not None else {
        symbol for symbol, _, _ in symbols
    }
    if not required:
        return True
    cell_to_region = {
        cell: region_id
        for region_id, cells in regions.items()
        for cell in cells
    }
    counts = {region_id: {symbol: 0 for symbol in required} for region_id in regions}
    for (row, col), cell_symbols in symbol_cells.items():
        region_id = cell_to_region[(row, col)]
        for symbol in cell_symbols:
            if symbol in required:
                counts[region_id][symbol] += 1
    return all(count == 1 for per_region in counts.values() for count in per_region.values())


def _rotated_shape(shape, turns):
    """Rotate relative (row, column) cells clockwise around the origin."""
    cells = set(shape)
    for _ in range(turns % 4):
        cells = {(col, -row) for row, col in cells}
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return frozenset((row - min_row, col - min_col) for row, col in cells)


def _normalized_shape(cells):
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return frozenset((row - min_row, col - min_col) for row, col in cells)


def check_fence_shapes(cell_regions, clues):
    """Check region shapes against rotatable fence clues.

    Each clue is `(row, column, shape)`, where row/column locate the clue cell
    and `shape` is a collection of relative (row, column) cell offsets. The
    region containing the clue must match that shape, allowing rotation.
    """
    regions = _cells_by_region(cell_regions)
    cell_to_region = {
        cell: region_id
        for region_id, cells in regions.items()
        for cell in cells
    }
    for row, col, shape in clues:
        if not (0 <= row < CELL_ROWS and 0 <= col < CELL_COLS):
            raise ValueError(f"fence clue coordinate {(row, col)} is outside the cell grid")
        shape = tuple(shape)
        if not shape or (0, 0) not in shape:
            raise ValueError("fence shape must be non-empty and include its clue cell at offset (0, 0)")
        region = regions[cell_to_region[(row, col)]]
        actual = _normalized_shape(region)
        matches = False
        for turns in range(4):
            oriented = _rotated_shape(shape, turns)
            # The clue cell can occupy any cell in the translated shape.
            for clue_offset_row, clue_offset_col in oriented:
                origin_row = row - clue_offset_row
                origin_col = col - clue_offset_col
                translated = frozenset(
                    (origin_row + r, origin_col + c) for r, c in oriented
                )
                if translated == region:
                    matches = True
                    break
            if matches:
                break
        if not matches:
            return False
    return True


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

    Horizontal edge array shape: 10 x 10. Vertical edge array shape: 9 x 11.
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
                    start=(0, 0), end=(POINT_ROWS - 1, POINT_COLS - 1),
                    rose_symbols=(), required_symbols=None, fence_shapes=()):
    """Check all supplied clues for a complete route.

    Rose symbols use `(name, row, column)` cell coordinates. Fence shapes use
    `(row, column, relative_cells)` with the clue cell at relative `(0, 0)`.
    """
    if not check_single_path(horizontal_edges, vertical_edges, start, end):
        return False
    if not check_rings(horizontal_edges, vertical_edges):
        return False
    cell_regions = find_cell_regions(horizontal_edges, vertical_edges)
    return (check_watchtowers(cell_regions)
            and check_rose_windows(cell_regions, rose_symbols, required_symbols)
            and check_fence_shapes(cell_regions, fence_shapes))


class SearchLimitExceeded(RuntimeError):
    """Raised when path search reaches its configured node limit."""


def path_to_edges(path):
    """Convert a sequence of lattice points into horizontal/vertical edge grids."""
    horizontal = [[False] * (POINT_COLS - 1) for _ in range(POINT_ROWS)]
    vertical = [[False] * POINT_COLS for _ in range(POINT_ROWS - 1)]
    if len(path) < 2 or len(set(path)) != len(path):
        raise ValueError("path must contain at least two distinct lattice points")
    for (row1, col1), (row2, col2) in zip(path, path[1:]):
        if not (0 <= row1 < POINT_ROWS and 0 <= col1 < POINT_COLS
                and 0 <= row2 < POINT_ROWS and 0 <= col2 < POINT_COLS):
            raise ValueError("path contains a point outside the lattice")
        if row1 == row2 and abs(col1 - col2) == 1:
            horizontal[row1][min(col1, col2)] = True
        elif col1 == col2 and abs(row1 - row2) == 1:
            vertical[min(row1, row2)][col1] = True
        else:
            raise ValueError(f"consecutive path points {(row1, col1)} and {(row2, col2)} are not adjacent")
    return horizontal, vertical


def _lattice_neighbors(point):
    row, col = point
    for next_point in ((row - 1, col), (row, col + 1),
                       (row + 1, col), (row, col - 1)):
        next_row, next_col = next_point
        if 0 <= next_row < POINT_ROWS and 0 <= next_col < POINT_COLS:
            yield next_point


def _can_reach_end(current, end, visited):
    """Check reachability through unused points plus the current point."""
    reached = {current}
    stack = [current]
    while stack:
        point = stack.pop()
        for neighbor in _lattice_neighbors(point):
            if neighbor == end or (neighbor not in visited and neighbor not in reached):
                if neighbor == end:
                    return True
                reached.add(neighbor)
                stack.append(neighbor)
    return current == end


def solve_path(start=(0, 0), end=(POINT_ROWS - 1, POINT_COLS - 1),
               rose_symbols=(), required_symbols=None, fence_shapes=(),
               max_nodes=1_000_000):
    """Find the first route satisfying the supplied clues.

    Returns a list of (row, column) lattice points, or None if the search
    exhausts all routes. Raises SearchLimitExceeded if `max_nodes` is reached.
    Pass the complete rose-window and fence clue data for a meaningful solve;
    omitting them intentionally leaves those clue families unconstrained.
    """
    for point in (start, end):
        row, col = point
        if not (0 <= row < POINT_ROWS and 0 <= col < POINT_COLS):
            raise ValueError(f"endpoint {point} is outside the lattice")
    if start == end:
        raise ValueError("start and end must be different lattice points")
    if max_nodes <= 0:
        raise ValueError("max_nodes must be positive")

    path = [start]
    visited = {start}
    explored = 0

    def search(current):
        nonlocal explored
        explored += 1
        if explored > max_nodes:
            raise SearchLimitExceeded(
                f"search exceeded {max_nodes:,} nodes without completing"
            )
        if current == end:
            horizontal, vertical = path_to_edges(path)
            if check_candidate(horizontal, vertical, start, end,
                               rose_symbols, required_symbols, fence_shapes):
                return path.copy()
            return None

        candidates = sorted(
            (point for point in _lattice_neighbors(current) if point not in visited),
            key=lambda point: abs(point[0] - end[0]) + abs(point[1] - end[1]),
        )
        for point in candidates:
            visited.add(point)
            path.append(point)
            if _can_reach_end(point, end, visited):
                result = search(point)
                if result is not None:
                    return result
            path.pop()
            visited.remove(point)
        return None

    return search(start)


if __name__ == "__main__":
    regions = make_cell_grid()
    horizontal = [[False] * (POINT_COLS - 1) for _ in range(POINT_ROWS)]
    vertical = [[False] * POINT_COLS for _ in range(POINT_ROWS - 1)]
    print(f"lattice: {POINT_ROWS} x {POINT_COLS}; cells: {CELL_ROWS} x {CELL_COLS}")
    print("Assign cell region IDs and line segments before checking the clues.")

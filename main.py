"""Coloring model for the Glimmith board.

The grid stores cell colors (not line segments): 1 and 2 are the two colors,
and 0 is reserved for an unassigned cell while building a candidate.
Coordinates are (row, column), with (0, 0) at the upper-left cell.
"""

from itertools import product

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


def display_grid(grid, save_path="solution.png", show=True):
    """Draw the coloring with yellow for 1 and purple for 2.

    Saves a PNG to `save_path`; when `show` is True, also opens a Matplotlib
    window. Cell values and zero-based row/column labels are shown for checking.
    Requires Matplotlib.
    """
    _validate_grid(grid)
    if any(value not in COLORS for row in grid for value in row):
        raise ValueError("display_grid requires a complete grid containing only 1 and 2")

    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch

    palette = {1: "#F4D03F", 2: "#8E44AD"}
    image = [[value - 1 for value in row] for row in grid]
    fig, ax = plt.subplots(figsize=(12, 9))
    ax.imshow(image, cmap=ListedColormap((palette[1], palette[2])),
              vmin=0, vmax=1, interpolation="nearest")
    ax.set_xticks(range(COLS), labels=range(COLS))
    ax.set_yticks(range(ROWS), labels=range(ROWS))
    ax.set_xticks([col - 0.5 for col in range(COLS + 1)], minor=True)
    ax.set_yticks([row - 0.5 for row in range(ROWS + 1)], minor=True)
    ax.grid(which="minor", color="#333333", linewidth=1.2)
    ax.tick_params(which="minor", bottom=False, left=False)
    ax.tick_params(top=True, labeltop=True, bottom=False, labelbottom=False)
    ax.set_xlabel("Column (0-indexed)")
    ax.set_ylabel("Row (0-indexed)")
    ax.set_title("Glimmith coloring solution")
    for row in range(ROWS):
        for col in range(COLS):
            text_color = "#222222" if grid[row][col] == 1 else "#FFFFFF"
            ax.text(col, row, str(grid[row][col]), ha="center", va="center",
                    color=text_color, fontsize=9, fontweight="bold")
    ax.legend(handles=[
        Patch(facecolor=palette[1], edgecolor="#333333", label="1"),
        Patch(facecolor=palette[2], edgecolor="#333333", label="2"),
    ], loc="upper left", bbox_to_anchor=(1.01, 1.0))
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=180, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close(fig)


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
            top_left = grid[row][col]
            top_right = grid[row][col + 1]
            bottom_left = grid[row + 1][col]
            bottom_right = grid[row + 1][col + 1]
            monochrome = top_left == top_right == bottom_left == bottom_right
            checkerboard = (top_left == bottom_right
                            and top_right == bottom_left
                            and top_left != top_right)
            if monochrome or checkerboard:
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


class SearchLimitExceeded(RuntimeError):
    """Raised when the coloring search reaches its configured node limit."""


def _has_mixed_2x2(upper, lower):
    return all(
        not (
            upper[col] == upper[col + 1] == lower[col] == lower[col + 1]
            or (upper[col] == lower[col + 1]
                and upper[col + 1] == lower[col]
                and upper[col] != upper[col + 1])
        )
        for col in range(COLS - 1)
    )


def _check_fences_in_row(rows, row, clues):
    partial_grid = list(rows)
    # A clue row is checked only once its row above and below are both known.
    for style, clue_row, col in clues:
        if clue_row != row:
            continue
        center = partial_grid[row][col]
        boundary_count = 0
        for next_row, next_col in ((row - 1, col), (row + 1, col),
                                   (row, col - 1), (row, col + 1)):
            if 0 <= next_row < len(partial_grid) and 0 <= next_col < COLS:
                boundary_count += partial_grid[next_row][next_col] != center
        if boundary_count != style:
            return False
    return True


def _connectivity_still_possible(rows):
    """Prune partial row assignments that can no longer connect either color."""
    assigned_rows = len(rows)
    possible = {1: set(), 2: set()}
    assigned_cells = {1: set(), 2: set()}
    for row in range(ROWS):
        for col in range(COLS):
            cell = (row, col)
            if row < assigned_rows:
                value = rows[row][col]
                if value in COLORS:
                    possible[value].add(cell)
                    assigned_cells[value].add(cell)
            elif row in (0, ROWS - 1) or col in (0, COLS - 1):
                possible[1].add(cell)
            elif cell in COLOR_2_WAYPOINTS:
                possible[2].add(cell)
            else:
                possible[1].add(cell)
                possible[2].add(cell)

    def reachable(starts, allowed):
        reached = set(starts) & allowed
        stack = list(reached)
        while stack:
            row, col = stack.pop()
            for neighbor in _neighbors(row, col):
                if neighbor in allowed and neighbor not in reached:
                    reached.add(neighbor)
                    stack.append(neighbor)
        return reached

    # All color-1 cells must remain connectable to the already connected border.
    border = {
        (row, col)
        for row in range(ROWS)
        for col in range(COLS)
        if row in (0, ROWS - 1) or col in (0, COLS - 1)
    }
    if not assigned_cells[1].issubset(reachable(border, possible[1])):
        return False

    # The four required color-2 points and every assigned 2 must remain joined.
    reached_2 = reachable((COLOR_2_WAYPOINTS[0],), possible[2])
    if not set(COLOR_2_WAYPOINTS).issubset(reached_2):
        return False
    if not assigned_cells[2].issubset(reached_2):
        return False
    return True


def _search_colorings(rose_symbols, required_symbols, max_nodes, solution_limit):
    """Enumerate colorings, stopping at solution_limit when it is not None."""
    if max_nodes <= 0:
        raise ValueError("max_nodes must be positive")
    if solution_limit is not None and solution_limit <= 0:
        raise ValueError("solution_limit must be positive or None")

    symbols = tuple(rose_symbols)
    motif_cells = {}
    for motif, row, col in symbols:
        if not (0 <= row < ROWS and 0 <= col < COLS):
            raise ValueError(f"rose-window coordinate {(row, col)} is outside the grid")
        motif_cells.setdefault(motif, []).append((row, col))
    required = set(required_symbols) if required_symbols is not None else set(motif_cells)
    if any(len(motif_cells.get(motif, ())) != 2 for motif in required):
        raise ValueError("each required rose-window motif must occur exactly twice")

    rows = [[1] * COLS]
    explored = 0
    candidate_cache = {}
    solutions = []
    stopped_at_limit = False

    def row_candidates(row):
        if row in candidate_cache:
            return candidate_cache[row]
        ranked = []
        for middle in product(COLORS, repeat=COLS - 2):
            candidate = (1, *middle, 1)
            if any(r == row and candidate[col] != 2
                   for r, col in COLOR_2_WAYPOINTS):
                continue
            fence_rank = 0
            feasible = True
            for style, clue_row, col in FENCES:
                if clue_row != row:
                    continue
                center = candidate[col]
                horizontal_edges = int(candidate[col - 1] != center)
                horizontal_edges += int(candidate[col + 1] != center)
                known_vertical_edges = 0
                unknown_vertical_edges = 2
                if row == 1:
                    known_vertical_edges += int(center != 1)
                    unknown_vertical_edges -= 1
                if row == ROWS - 2:
                    known_vertical_edges += int(center != 1)
                    unknown_vertical_edges -= 1
                needed = style - horizontal_edges - known_vertical_edges
                if not 0 <= needed <= unknown_vertical_edges:
                    feasible = False
                    break
                fence_rank += needed
            if feasible:
                transitions = sum(candidate[col] != candidate[col + 1]
                                  for col in range(COLS - 1))
                ranked.append(((fence_rank, transitions, -candidate.count(2)), candidate))
        ranked.sort(key=lambda item: item[0])
        candidate_cache[row] = [candidate for _, candidate in ranked]
        return candidate_cache[row]

    def rose_pairs_still_possible(through_row):
        for motif in required:
            locations = motif_cells[motif]
            if all(row <= through_row for row, _ in locations):
                first, second = locations
                if rows[first[0]][first[1]] == rows[second[0]][second[1]]:
                    return False
        return True

    def search(row):
        nonlocal explored, stopped_at_limit
        if row == ROWS:
            grid = [list(values) for values in rows]
            if check_coloring(grid, symbols, required):
                solutions.append(grid)
                if solution_limit is not None and len(solutions) >= solution_limit:
                    stopped_at_limit = True
                    return True
            return False

        candidates = ((1,) * COLS,) if row == ROWS - 1 else row_candidates(row)
        for candidate in candidates:
            explored += 1
            if explored > max_nodes:
                raise SearchLimitExceeded(
                    f"search exceeded {max_nodes:,} row candidates without completing"
                )
            if not _has_mixed_2x2(rows[-1], candidate):
                continue
            rows.append(candidate)
            if (_check_fences_in_row(rows, row - 1, FENCES)
                    and rose_pairs_still_possible(row)
                    and _connectivity_still_possible(rows)):
                if search(row + 1):
                    rows.pop()
                    return True
            rows.pop()
        return False

    search(1)
    return solutions, not stopped_at_limit


def solve_coloring(rose_symbols=(), required_symbols=None, max_nodes=10_000_000):
    """Find one coloring satisfying the encoded rules, or return None."""
    solutions, _ = _search_colorings(
        rose_symbols, required_symbols, max_nodes, solution_limit=1
    )
    return solutions[0] if solutions else None


def count_colorings(rose_symbols=(), required_symbols=None,
                    max_nodes=10_000_000, stop_after=2):
    """Count solutions, returning (count, exhaustive).

    `stop_after=2` is enough to prove a puzzle is not unique. A result of one
    is a uniqueness proof only when exhaustive is True; use stop_after=None
    to exhaust the full search space.
    """
    solutions, exhaustive = _search_colorings(
        rose_symbols, required_symbols, max_nodes, solution_limit=stop_after
    )
    return len(solutions), exhaustive


if __name__ == "__main__":
    try:
        solution = solve_coloring()
    except SearchLimitExceeded as error:
        print(error)
    else:
        if solution is None:
            print("No coloring satisfies the encoded clues.")
        else:
            print_grid(solution)
            display_grid(solution, save_path="solution.png", show=True)

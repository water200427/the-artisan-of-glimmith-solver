m, n = 11, 12
grid = [[0]*n for _ in range(m)]
#          0   1   ...   y   ... n-1=11
# 0        0   0         0       0
# 1        0
# ...
# x        0
# ...
# m-1=10   0                     0

contrains = []
fences = [[1, 1, 3],
          [3, 1, 6],
          [1, 2, 8],
          [1, 3, 2],
          [1, 3, 5],
          [3, 4, 8],
          [1, 4, 10],
          [1, 5, 4],
          [1, 5, 7],
          [3, 6, 1],
          [3, 6, 3],
          [3, 7, 6],
          [1, 7, 9],
          [1, 8, 3],
          [3, 9, 5],
          [3, 9, 8]
          ]


def p(grid=grid):
    m, n = len(grid), len(grid[0])
    print(" "*5, end="")
    for j in range(n):
        print(f"{j:<3}", end="")
    print()
    for i, row in enumerate(grid):
        print(f"{i:<3} {row}")


def check(grid) -> bool:
    m, n = len(grid), len(grid[0])

    # check watchtower
    for i in range(m-1):
        for j in range(n-1):
            square = get_square(grid, i, j)
            if all(e == grid[i][j] for e in square):
                return False

    # check fence
    for s, x, y in fences:
        curr = grid[x][y]
        neighbors = get_neighbors(grid, x, y)
        if s != neighbors.count(curr):
            return False

    return True


def get_square(grid: list[list[int]], x: int, y: int, edge: int = 2) -> list[int]:
    return [v for row in grid[x:x+edge] for v in row[y:y+edge]]


def get_neighbors(grid: list[list[int]], x: int, y: int) -> list[int]:
    directions = [[1, 1], [1, -1], [-1, 1], [-1, -1]]
    return [grid[x+dx][y+dy] for dx, dy in directions]


def flat(grid: list[list[int]]) -> list[int]:
    return sum(grid, [])

# for s, x, y in fences:
#     grid[x][y] = s


for i in range(m):
    for j in range(n):
        ...

# p()
print(grid)

# Glimmith 塗色解答器

這個程式把盤面視為 `11 × 12` 的格子，每格填入 `1` 或 `2`，並搜尋符合目前線索的著色方式。程式以繁體中文專案說明為主；程式內的座標一律是 **0-indexed `(row, column)`**，左上角是 `(0, 0)`。

## 執行

需要 Python 3 和 Matplotlib。若尚未安裝 Matplotlib：

```powershell
python -m pip install matplotlib
```

在專案資料夾執行：

```powershell
python main.py
```

程式會搜尋第一個解、在終端機列出數字盤面、將圖存成專案資料夾中的 `solution.png`，並開啟彩色圖形視窗。黃色代表 `1`，紫色代表 `2`；列與欄標籤都是從 0 開始。

若只想產生 PNG、不開視窗：

```python
from main import display_grid, solve_coloring

solution = solve_coloring()
if solution is not None:
    display_grid(solution, save_path="solution.png", show=False)
```

## 目前使用的規則

- 棋盤尺寸為 11 列、12 欄；外圈固定為 `1`。
- `(1, 1)`、`(1, 10)`、`(9, 1)`、`(9, 10)` 固定為 `2`。
- 全盤每個 `2 × 2` 小方塊不能四格同色（望塔條件）。
- 每種顏色都必須形成一個四方向連通區域。
- 每個圍欄線索 `(style, row, column)` 要求該格上下左右異色鄰格的數量恰好等於 `style`。超出棋盤的方向不計。
- 玫瑰窗可用圖案座標額外檢查；請參閱下方輸入格式。若未提供圖案座標，程式仍會套用兩色各自連通的條件，但無法逐一核對每種玫瑰圖案是否在兩區各出現一次。

目前已輸入的圍欄線索在 `main.py` 的 `FENCES`：

```python
FENCES = (
    (1, 1, 3),  # style=1，row=1，column=3
    (3, 1, 6),  # style=3，row=1，column=6
    # 其餘線索……
)
```

例如 `(3, 1, 6)` 表示在 `(1, 6)` 的格子，四個正交鄰格中必須恰有 3 格與中心格不同色。若中心格是 `1`，這就等同於四鄰格中恰有 3 格為 `2`。

## 可以調整的輸入

### 1. 圍欄線索

在 `main.py` 編輯 `FENCES`。每筆格式為：

```python
(style, row, column)
```

例如，要新增一個位於第 4 列、第 7 欄，要求恰有 1 條異色邊的線索：

```python
FENCES = FENCES + ((1, 4, 7),)
```

座標是格子座標，不是格點座標。有效範圍為 `row=0..10`、`column=0..11`。

### 2. 固定為 2 的指定格

在 `main.py` 編輯 `COLOR_2_WAYPOINTS`，格式是 `(row, column)`：

```python
COLOR_2_WAYPOINTS = ((1, 1), (1, 10), (9, 1), (9, 10))
```

### 3. 玫瑰窗圖案位置

將每個圖案命名，並輸入它所在的兩個格子。格式為 `(圖案名稱, row, column)`：

```python
ROSE_SYMBOLS = (
    ("太陽", 2, 3),
    ("太陽", 8, 4),
    ("月亮", 3, 7),
    ("月亮", 7, 8),
)
REQUIRED_SYMBOLS = {"太陽", "月亮"}
```

把主程式呼叫改成：

```python
solution = solve_coloring(
    rose_symbols=ROSE_SYMBOLS,
    required_symbols=REQUIRED_SYMBOLS,
)
```

每種必要圖案必須輸入兩次；解答器會要求兩個位置分屬 `1`、`2` 兩區。圖案名稱可用字串或其他可雜湊值，但相同圖案必須使用完全相同的名稱。

### 4. 棋盤尺寸與顏色

- `ROWS`、`COLS` 設定格子列數和欄數。若更改尺寸，請一併確認指定格、圍欄及玫瑰窗座標仍在範圍內；目前固定座標與外圈規則是依這張截圖設定的。
- `COLORS = (1, 2)` 設定兩種顏色的數值。程式目前的圍欄及著色規則假設顏色就是 `1`、`2`。
- `display_grid` 函數中的 `palette` 設定圖色：目前 `1` 是黃色 `#F4D03F`，`2` 是紫色 `#8E44AD`。

## 搜尋與唯一解確認

`solve_coloring(...)` 回傳第一個符合條件的 `11 × 12` 二維清單；無解時回傳 `None`。預設最多搜尋 10,000,000 個列候選。可調整上限：

```python
solution = solve_coloring(max_nodes=20_000_000)
```

超過上限會丟出 `SearchLimitExceeded`，這代表搜尋尚未完成，不能據此判定無解。

`count_colorings(...)` 用來確認唯一性，回傳 `(找到的解數, 是否已窮舉完成)`：

```python
count, exhaustive = count_colorings(stop_after=2)
```

- `(2, False)` 表示至少有兩解，已足以證明不唯一。
- `(1, True)` 表示完整搜尋後只有一解，因此在目前輸入的規則下唯一。
- `stop_after=None` 會嘗試找出所有解；若解很多，搜尋可能花很久或超過節點上限。

目前已用已輸入的外圈、指定格、望塔和圍欄條件搜尋，結果為 **1 個解且已窮舉完成**。這個唯一性結論只涵蓋程式目前輸入的條件；若尚未填入玫瑰窗圖案座標，就尚未逐圖案驗證玫瑰窗規則。

## 常用函數

```python
from main import (
    check_coloring,
    check_fences,
    check_rose_windows,
    check_watchtowers,
    count_colorings,
    display_grid,
    print_grid,
    solve_coloring,
)
```

- `check_coloring(grid, rose_symbols=..., required_symbols=...)`：檢查完整盤面。
- `check_watchtowers(grid)`：檢查所有 `2 × 2` 區塊。
- `check_fences(grid, clues=...)`：檢查指定圍欄線索。
- `check_rose_windows(grid, symbols, required_symbols=...)`：檢查玫瑰窗圖案。
- `print_grid(grid)`：在終端機列出數字盤面。
- `display_grid(grid, save_path="solution.png", show=True)`：顯示並儲存彩色盤面。

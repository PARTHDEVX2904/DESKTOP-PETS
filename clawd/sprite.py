"""Single source of truth for the Claw'd pixel-art sprite.

The character is a 12-wide x 8-tall grid. Each cell is one of three states:
    0 = transparent / empty
    1 = body  -> #F05B45
    2 = eye   -> #110C0A

Keeping the sprite as grid data (rather than an image asset) means future
animation frames (V2+) slot in as additional grids without touching any window
logic. The painter always reads from a "current frame" grid, which for V1 is the
single static SPRITE below.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

# --- Config -----------------------------------------------------------------

SCALE = 8  # pixels per grid cell -> window content is 12*SCALE x 8*SCALE

# --- Sprite data (verbatim from spec section 2; do NOT approximate) ----------

# rows top->bottom, each row left->right (12 wide, 8 tall)
SPRITE = [
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 2, 1, 1, 1, 1, 2, 1, 0, 0],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0],
    [0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0],
]

COLORS = {
    1: "#F05B45",  # body
    2: "#110C0A",  # eyes
}

GRID_COLS = len(SPRITE[0])  # 12
GRID_ROWS = len(SPRITE)     # 8


# --- Rendering helpers -------------------------------------------------------

def paint_grid(painter: QPainter, grid: list[list[int]], scale: int) -> None:
    """Draw ``grid`` onto ``painter``: one non-zero cell -> a scale x scale rect.

    Zero cells are skipped so they stay fully transparent. Antialiasing is left
    off by the caller so the pixel rects keep crisp edges when scaled.
    """
    for row_index, row in enumerate(grid):
        for col_index, cell in enumerate(row):
            if cell == 0:
                continue
            color = QColor(COLORS[cell])
            painter.fillRect(
                QRect(col_index * scale, row_index * scale, scale, scale),
                color,
            )


def render_pixmap(grid: list[list[int]] = SPRITE, scale: int = SCALE) -> QPixmap:
    """Render ``grid`` to a transparent QPixmap (reused for the tray icon)."""
    pixmap = QPixmap(GRID_COLS * scale, GRID_ROWS * scale)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    paint_grid(painter, grid, scale)
    painter.end()
    return pixmap


def cell_is_solid(x: int, y: int, scale: int = SCALE,
                  grid: list[list[int]] = SPRITE) -> bool:
    """Return True if the pixel at widget-local (x, y) lands on a non-empty cell."""
    col = x // scale
    row = y // scale
    if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
        return grid[row][col] != 0
    return False


class SpriteWidget(QWidget):
    """A QWidget that paints the current sprite frame, one filled square per cell."""

    def __init__(self, scale: int = SCALE, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.scale = scale
        self.frame = SPRITE  # "current frame" grid (single static frame in V1)
        self.setFixedSize(self.sizeHint())

    def sizeHint(self) -> QSize:  # noqa: N802 (Qt naming)
        return QSize(GRID_COLS * self.scale, GRID_ROWS * self.scale)

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        painter = QPainter(self)
        # Crisp edges: no antialiasing on the pixel rects.
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        paint_grid(painter, self.frame, self.scale)
        painter.end()

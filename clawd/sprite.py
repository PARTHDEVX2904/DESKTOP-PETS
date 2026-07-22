"""Single source of truth for the Claw'd pixel-art sprite.

The character is a 12-wide x 8-tall grid. Each cell is one of four states:
    0 = transparent / empty
    1 = body        -> #F05B45
    2 = eye (open)  -> #110C0A, filled square
    3 = eye (blink) -> #110C0A, thin horizontal line (closed eye)

Keeping the sprite as grid data (rather than an image asset) means future
animation frames (V2+) slot in as additional grids without touching any window
logic. The painter always reads from a "current frame" grid, which for V1 is the
single static SPRITE below.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QRect, QSize, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

# --- Config -----------------------------------------------------------------

SCALE = 8  # pixels per grid cell -> window content is 12*SCALE x 8*SCALE
BLINK_DURATION_MS = 150  # how long the eyes stay closed on click

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

# Same as SPRITE, but the eye row has its eye cells (2) swapped for closed-eye
# lines (3), so a click can briefly swap to this frame for a blink.
BLINK_SPRITE = [
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 3, 1, 1, 1, 1, 3, 1, 0, 0],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0],
    [0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0],
]

# Walk cycle: same as SPRITE, but the bottom leg row alternates which pair of
# legs is planted vs lifted (cleared to 0), for a 2-frame walking gait.
WALK1_SPRITE = [
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 2, 1, 1, 1, 1, 2, 1, 0, 0],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0],  # outer legs planted, inner legs lifted
]

WALK2_SPRITE = [
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 2, 1, 1, 1, 1, 2, 1, 0, 0],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0],  # inner legs planted, outer legs lifted
]

COLORS = {
    1: "#F05B45",  # body
    2: "#110C0A",  # eyes (open)
    3: "#110C0A",  # eyes (blink line)
}

GRID_COLS = len(SPRITE[0])  # 12
GRID_ROWS = len(SPRITE)     # 8


# --- Accessories --------------------------------------------------------------
# Accessories are higher-resolution overlays with their own grid/coordinate
# system, positioned over the base sprite via fractional base-cell offsets so
# they scale together with it as SCALE changes. This keeps window/drag/tray
# logic untouched — an accessory is just "an extra thing paintEvent draws".
# Sunglasses are the first one; more (hats, etc.) could follow the same shape.

# Sunglasses overlay (44 wide x 10 tall), drawn over the eyes when enabled.
#   0 = transparent (base sprite shows through, incl. the nose-bridge gap)
#   1 = frame -> #0A0B1F
#   2 = highlight -> #F5F5F5
SUNGLASSES = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 2, 2, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 2, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 2, 2, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 2, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [1, 1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
]

SUNGLASSES_COLORS = {1: "#0A0B1F", 2: "#F5F5F5"}
SUNGLASSES_ROWS = len(SUNGLASSES)     # 10
SUNGLASSES_COLS = len(SUNGLASSES[0])  # 44

# Placement, in fractional base-sprite cells (tunable by eye). Centers the
# lenses on SPRITE's eyes and lets the orange nose-bridge show through the gap.
GLASSES_LEFT_CELLS = 1.6
GLASSES_TOP_CELLS = 0.5
GLASSES_WIDTH_CELLS = 8.8


def paint_sunglasses(painter: QPainter, scale: int) -> None:
    """Draw SUNGLASSES over the sprite, in its own finer coordinate system.

    Positioned via fractional base-cell offsets so it scales together with the
    sprite as SCALE changes. Cell boundaries are rounded to whole pixels so
    adjacent cells tile with no seams even when the per-cell size isn't an
    integer.
    """
    ox = GLASSES_LEFT_CELLS * scale
    oy = GLASSES_TOP_CELLS * scale
    cw = (GLASSES_WIDTH_CELLS * scale) / SUNGLASSES_COLS
    ch = cw
    for r, row in enumerate(SUNGLASSES):
        for c, v in enumerate(row):
            if v == 0:
                continue
            x0 = round(ox + c * cw)
            x1 = round(ox + (c + 1) * cw)
            y0 = round(oy + r * ch)
            y1 = round(oy + (r + 1) * ch)
            painter.fillRect(QRect(x0, y0, x1 - x0, y1 - y0), QColor(SUNGLASSES_COLORS[v]))


# --- Rendering helpers -------------------------------------------------------

def paint_grid(painter: QPainter, grid: list[list[int]], scale: int) -> None:
    """Draw ``grid`` onto ``painter``: one non-zero cell -> a scale x scale rect.

    Zero cells are skipped so they stay fully transparent. A ``3`` cell (blinking
    eye) is drawn as a body-colored square with a thin eye-colored line across
    its middle, instead of a full square. Antialiasing is left off by the caller
    so the pixel rects keep crisp edges when scaled.
    """
    for row_index, row in enumerate(grid):
        for col_index, cell in enumerate(row):
            if cell == 0:
                continue
            x, y = col_index * scale, row_index * scale
            if cell == 3:
                painter.fillRect(QRect(x, y, scale, scale), QColor(COLORS[1]))
                line_height = max(1, scale // 4)
                line_y = y + (scale - line_height) // 2
                painter.fillRect(QRect(x, line_y, scale, line_height), QColor(COLORS[3]))
                continue
            painter.fillRect(QRect(x, y, scale, scale), QColor(COLORS[cell]))


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

    glasses_changed = Signal(bool)

    def __init__(self, scale: int = SCALE, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.scale = scale
        self.frame = SPRITE  # "current frame" grid (what's actually painted)
        self._base_frame = SPRITE  # frame to restore to once a blink ends
        self.glasses_on = False
        self.setFixedSize(self.sizeHint())

        self._blink_timer = QTimer(self)
        self._blink_timer.setSingleShot(True)
        self._blink_timer.timeout.connect(self._end_blink)

    def sizeHint(self) -> QSize:  # noqa: N802 (Qt naming)
        return QSize(GRID_COLS * self.scale, GRID_ROWS * self.scale)

    def set_base_frame(self, grid: list[list[int]]) -> None:
        """Set the resting/walking frame (idle or walk-cycle), independent of blink.

        If a blink is currently mid-flight, the change is deferred: it takes
        effect once the blink ends instead of interrupting it.
        """
        self._base_frame = grid
        if not self._blink_timer.isActive():
            self.frame = grid
            self.update()

    def blink(self) -> None:
        """Briefly swap to the eyes-closed frame, then back to the base frame."""
        self.frame = BLINK_SPRITE
        self.update()
        self._blink_timer.start(BLINK_DURATION_MS)

    def _end_blink(self) -> None:
        self.frame = self._base_frame
        self.update()

    def set_glasses(self, on: bool) -> None:
        if on == self.glasses_on:
            return
        self.glasses_on = on
        self.glasses_changed.emit(on)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        painter = QPainter(self)
        # Crisp edges: no antialiasing on the pixel rects.
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        paint_grid(painter, self.frame, self.scale)
        if self.glasses_on:
            paint_sunglasses(painter, self.scale)
        painter.end()

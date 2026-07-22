"""The frameless, translucent, always-on-top, draggable pet window."""

from __future__ import annotations

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QMenu, QWidget

from .sprite import SpriteWidget, cell_is_solid

# --- Config ---------------------------------------------------------------

ALWAYS_ON_TOP = True
SIDE_MARGIN = 12     # px gap from the right screen edge
TASKBAR_GAP = 0  # px gap left above the taskbar so the pet clearly floats above it


class PetWindow(QWidget):
    """A tiny always-on-top window that shows Claw'd and can be dragged around."""

    def __init__(self) -> None:
        super().__init__()

        # Window type flags: frameless, tool (no taskbar / alt-tab entry), and
        # optionally always-on-top.
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        if ALWAYS_ON_TOP:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

        # Only the sprite pixels should be visible; everything else transparent.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # The sprite is the sole content; the window is sized exactly to it.
        self._sprite = SpriteWidget(parent=self)
        self.setFixedSize(self._sprite.size())
        self._scale = self._sprite.scale

        self._drag_offset: QPoint | None = None

        # Always open in the bottom-right corner, just above the taskbar.
        self.reset_position()

    # --- Placement ----------------------------------------------------------

    def reset_position(self) -> None:
        """Move the pet to the bottom-right corner, just above the taskbar."""
        screen = QGuiApplication.primaryScreen()
        area = screen.availableGeometry()  # working area — excludes the taskbar
        x = area.right() - self.width() - SIDE_MARGIN
        y = area.bottom() - self.height() - TASKBAR_GAP
        self.move(QPoint(x, y))

    # --- Dragging -----------------------------------------------------------

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            # Only react when the click lands on a solid sprite cell.
            if cell_is_solid(pos.x(), pos.y(), self._scale):
                self._sprite.blink()
                self._drag_offset = (
                    event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                )
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        if self._drag_offset is not None and (event.buttons() & Qt.MouseButton.LeftButton):
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        if self._drag_offset is not None and event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    # --- Context menu (nice-to-have; mirrors the tray menu) ------------------

    def contextMenuEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        pos = event.pos()
        if not cell_is_solid(pos.x(), pos.y(), self._scale):
            return
        menu = QMenu(self)
        menu.addAction("Reset position", self.reset_position)
        menu.addAction("Quit", QGuiApplication.quit)
        menu.exec(event.globalPos())

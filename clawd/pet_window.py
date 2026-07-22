"""The frameless, translucent, always-on-top, draggable pet window."""

from __future__ import annotations

import math
import random

from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication, QMenu, QWidget

from .music import MusicWatcher
from .settings import load_glasses_state, save_glasses_state
from .sprite import (
    BLINK_SPRITE,
    GRID_COLS,
    GRID_ROWS,
    MARGIN_CELLS,
    SPRITE,
    WALK1_SPRITE,
    WALK2_SPRITE,
    SpriteWidget,
    cell_is_solid,
)

# --- Config ---------------------------------------------------------------

ALWAYS_ON_TOP = True
SIDE_MARGIN = 12     # px gap from the right screen edge
TASKBAR_GAP = 0  # px gap left above the taskbar so the pet clearly floats above it

TICK_MS = 33                  # animation tick interval (~30fps)
BOB_AMPLITUDE = 3             # px of vertical travel while idle
BOB_PERIOD_MS = 1200          # duration of one full idle-bob cycle
WALK_SPEED = 50                # px/sec while walking
WALK_FRAME_INTERVAL_MS = 180  # leg-swap interval while walking
WALK_MIN_INTERVAL_S = 8       # min seconds between autonomous walks
WALK_MAX_INTERVAL_S = 20      # max seconds between autonomous walks
WALK_MIN_DISTANCE = 60        # px, so a walk isn't a tiny shuffle

TUCK_IN_DURATION_MS = 500     # how long Claw'd's eyes-closed goodbye shows before quitting


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

        # The sprite is the sole content; the window is sized exactly to it
        # (which includes a transparent margin around the sprite itself, for
        # accessories like the headphones that extend beyond the 12x8 body).
        self._sprite = SpriteWidget(parent=self)
        self.setFixedSize(self._sprite.size())
        self._scale = self._sprite.scale
        self._margin_px = MARGIN_CELLS * self._scale
        self._sprite_w = GRID_COLS * self._scale
        self._sprite_h = GRID_ROWS * self._scale

        self._drag_offset: QPoint | None = None

        # Animation state: self._anchor is the logical resting/walking position
        # (without the idle-bob offset applied).
        self._anchor = QPoint(0, 0)
        self._bob_phase = 0.0
        self._walking = False
        self._walk_target_x = 0
        self._walk_frame_toggle = False
        self._walk_frame_elapsed = 0

        self._walk_timer = QTimer(self)
        self._walk_timer.setSingleShot(True)
        self._walk_timer.timeout.connect(self._start_walk)

        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._on_tick)

        # Restore whether the sunglasses accessory was on last session.
        self._sprite.set_glasses(load_glasses_state())

        # Headphones are fully automatic (music-driven) and never persisted —
        # recomputed fresh each run by polling off the GUI thread.
        self._music_watcher = MusicWatcher(self)
        self._music_watcher.playing_changed.connect(self._sprite.set_headphones)

        # Always open in the bottom-right corner, just above the taskbar.
        self.reset_position()
        self._tick_timer.start(TICK_MS)

    # --- Placement ----------------------------------------------------------

    def reset_position(self) -> None:
        """Move the pet (sprite, not the padded window) to the bottom-right
        corner, just above the taskbar."""
        screen = QGuiApplication.primaryScreen()
        area = screen.availableGeometry()  # working area — excludes the taskbar
        sprite_right = area.right() - SIDE_MARGIN
        sprite_bottom = area.bottom() - TASKBAR_GAP
        x = sprite_right - self._sprite_w - self._margin_px
        y = sprite_bottom - self._sprite_h - self._margin_px
        self._anchor = QPoint(x, y)
        self._walking = False
        self._sprite.set_base_frame(SPRITE)
        self.move(self._anchor)
        self._schedule_next_walk()

    # --- Idle bob / autonomous walk ------------------------------------------

    def _schedule_next_walk(self) -> None:
        delay_s = random.uniform(WALK_MIN_INTERVAL_S, WALK_MAX_INTERVAL_S)
        self._walk_timer.start(int(delay_s * 1000))

    def _start_walk(self) -> None:
        if self._drag_offset is not None:
            # Being dragged right now; try again after the usual random delay.
            self._schedule_next_walk()
            return

        screen = QGuiApplication.primaryScreen()
        area = screen.availableGeometry()
        min_x = area.left() + SIDE_MARGIN
        max_x = area.right() - self.width() - SIDE_MARGIN
        if max_x <= min_x:
            self._schedule_next_walk()
            return

        candidate = self._anchor.x()
        for _ in range(5):
            candidate = random.randint(min_x, max_x)
            if abs(candidate - self._anchor.x()) >= WALK_MIN_DISTANCE:
                break

        self._walk_target_x = candidate
        self._walking = True
        self._walk_frame_toggle = False
        self._walk_frame_elapsed = 0
        self._sprite.set_base_frame(WALK1_SPRITE)

    def _on_tick(self) -> None:
        if self._drag_offset is not None:
            return  # dragging already drives position via mouse events
        if self._walking:
            self._step_walk()
        else:
            self._step_idle_bob()

    def _step_walk(self) -> None:
        step = max(1, round(WALK_SPEED * TICK_MS / 1000))
        dx = self._walk_target_x - self._anchor.x()
        if abs(dx) <= step:
            self._anchor.setX(self._walk_target_x)
            self._walking = False
            self._sprite.set_base_frame(SPRITE)
            self.move(self._anchor)
            self._schedule_next_walk()
            return

        self._anchor.setX(self._anchor.x() + (step if dx > 0 else -step))
        self.move(self._anchor)

        self._walk_frame_elapsed += TICK_MS
        if self._walk_frame_elapsed >= WALK_FRAME_INTERVAL_MS:
            self._walk_frame_elapsed = 0
            self._walk_frame_toggle = not self._walk_frame_toggle
            self._sprite.set_base_frame(WALK2_SPRITE if self._walk_frame_toggle else WALK1_SPRITE)

    def _step_idle_bob(self) -> None:
        self._bob_phase = (self._bob_phase + TICK_MS / BOB_PERIOD_MS) % 1.0
        offset = round(BOB_AMPLITUDE * math.sin(self._bob_phase * 2 * math.pi))
        self.move(self._anchor.x(), self._anchor.y() + offset)

    # --- Dragging -----------------------------------------------------------

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        pos = event.position().toPoint()
        # Window coords -> sprite-local coords (undo the accessory margin)
        # before hit-testing against the base grid.
        sprite_x = pos.x() - self._margin_px
        sprite_y = pos.y() - self._margin_px
        # Only react when the click lands on a solid sprite cell.
        if not cell_is_solid(sprite_x, sprite_y, self._scale):
            super().mousePressEvent(event)
            return

        if event.button() == Qt.MouseButton.LeftButton:
            self._walking = False
            self._sprite.set_base_frame(SPRITE)
            self._sprite.blink()
            self._drag_offset = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()
            return

        super().mousePressEvent(event)

    def contextMenuEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                padding: 2px;
                font-size: 11px;
            }
            QMenu::item {
                padding: 3px 12px 3px 18px;
            }
            QMenu::separator {
                height: 1px;
                margin: 2px 4px;
            }
        """)

        savage_action = menu.addAction("Savage mode")
        savage_action.setCheckable(True)
        savage_action.setChecked(self._sprite.glasses_on)
        savage_action.toggled.connect(self._on_savage_toggled)

        menu.addSeparator()
        menu.addAction("Reset position", self.reset_position)
        menu.addAction("Tuck pet in", self._tuck_in_and_quit)

        menu.exec(event.globalPos())

    def _on_savage_toggled(self, on: bool) -> None:
        self._sprite.set_glasses(on)
        save_glasses_state(on)

    def _tuck_in_and_quit(self) -> None:
        """Freeze Claw'd with his eyes closed for a moment, then quit."""
        self._tick_timer.stop()
        self._walk_timer.stop()
        self._sprite._blink_timer.stop()
        self._sprite.frame = BLINK_SPRITE
        self._sprite.update()
        QTimer.singleShot(TUCK_IN_DURATION_MS, QApplication.quit)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        if self._drag_offset is not None and (event.buttons() & Qt.MouseButton.LeftButton):
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        if self._drag_offset is not None and event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = None
            self._anchor = self.pos()
            self._schedule_next_walk()
            event.accept()
            return
        super().mouseReleaseEvent(event)

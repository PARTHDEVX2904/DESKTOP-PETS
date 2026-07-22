"""Persist and restore the pet window's on-screen position.

Uses QSettings, which on Windows writes to the registry automatically, so no
external file handling is needed. First run (no saved position) returns None so
the caller can place the pet bottom-right with a margin.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QSettings

APP_NAME = "Clawd"
ORG_NAME = "Clawd"

_POS_X = "window/x"
_POS_Y = "window/y"


def _settings() -> QSettings:
    return QSettings(ORG_NAME, APP_NAME)


def load_position() -> QPoint | None:
    """Return the saved window position, or None if there is no saved position."""
    s = _settings()
    x = s.value(_POS_X, None)
    y = s.value(_POS_Y, None)
    if x is None or y is None:
        return None
    try:
        return QPoint(int(x), int(y))
    except (TypeError, ValueError):
        return None


def save_position(pos: QPoint) -> None:
    """Persist the window position (x, y)."""
    s = _settings()
    s.setValue(_POS_X, int(pos.x()))
    s.setValue(_POS_Y, int(pos.y()))
    s.sync()

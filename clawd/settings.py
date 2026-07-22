"""Persist and restore small bits of pet state (position, accessories).

Uses QSettings, which on Windows writes to the registry automatically, so no
external file handling is needed.

Note: window position is intentionally NOT restored on launch — the pet always
opens bottom-right above the taskbar (see pet_window.reset_position). The
load_position/save_position helpers are kept for potential future use but are
not currently called.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QSettings

APP_NAME = "Clawd"
ORG_NAME = "Clawd"

_POS_X = "window/x"
_POS_Y = "window/y"
_GLASSES_ON = "accessories/glasses_on"


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


def load_glasses_state() -> bool:
    """Return whether the sunglasses accessory was on last time, default False."""
    value = _settings().value(_GLASSES_ON, False)
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("true", "1")


def save_glasses_state(on: bool) -> None:
    """Persist whether the sunglasses accessory is on."""
    s = _settings()
    s.setValue(_GLASSES_ON, bool(on))
    s.sync()

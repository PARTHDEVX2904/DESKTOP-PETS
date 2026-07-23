"""Background detection of keystroke activity (Windows GetAsyncKeyState).

Only detects THAT a key was pressed, never which key. No keystroke content is
read, buffered, logged, or written anywhere — just a boolean "activity" pulse.
"""

from __future__ import annotations

import ctypes

from PySide6.QtCore import QThread, Signal

POLL_MS = 50

WATCHED_VKS = (
    [0x08, 0x09, 0x0D, 0x20]                            # backspace, tab, enter, space
    + list(range(0x30, 0x3A))                           # 0-9
    + list(range(0x41, 0x5B))                           # A-Z
    + list(range(0xBA, 0xC1)) + list(range(0xDB, 0xE0))  # punctuation
)


def _any_key_pressed() -> bool:
    user32 = ctypes.windll.user32
    for vk in WATCHED_VKS:
        if user32.GetAsyncKeyState(vk) & 0x0001:
            return True
    return False


class TypingWatcher(QThread):
    """Polls every POLL_MS; emits key_pressed() when any watched key was hit."""

    key_pressed = Signal()

    def run(self) -> None:
        while not self.isInterruptionRequested():
            try:
                if _any_key_pressed():
                    self.key_pressed.emit()
            except Exception:
                # Not Windows, no user32, or any other environment quirk ->
                # typing detection just never fires; the app runs normally.
                pass
            self.msleep(POLL_MS)

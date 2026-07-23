"""Entry point: build the QApplication, show Claw'd + tray, run the event loop.

Run with:  python -m clawd
"""

from __future__ import annotations

import ctypes
import sys

from PySide6.QtWidgets import QApplication

from .pet_window import PetWindow
from .settings import APP_NAME, ORG_NAME
from .tray import build_tray

_MUTEX_NAME = "Global\\ClawdDesktopPetSingleInstance"


def _already_running() -> bool:
    """True if another Claw'd instance already holds the single-instance mutex.

    Windows releases the mutex automatically when the owning process exits
    (including a crash), so there's no stale-lock state to clean up.
    """
    ctypes.windll.kernel32.CreateMutexW(None, False, _MUTEX_NAME)
    return ctypes.windll.kernel32.GetLastError() == 183  # ERROR_ALREADY_EXISTS


def main() -> int:
    if _already_running():
        return 0

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    # The pet lives in the tray; don't quit when the (only) window is hidden.
    app.setQuitOnLastWindowClosed(False)

    pet = PetWindow()
    pet.show()

    # Keep a reference so the tray icon isn't garbage-collected.
    tray = build_tray(pet)  # noqa: F841

    # Start the background watchers now that the window is showing.
    pet._music_watcher.start()
    pet._typing_watcher.start()

    def _stop_watchers() -> None:
        pet._music_watcher.requestInterruption()
        pet._music_watcher.wait()
        pet._typing_watcher.requestInterruption()
        pet._typing_watcher.wait()
        pet._typing_anim_timer.stop()
        pet._typing_linger_timer.stop()

    app.aboutToQuit.connect(_stop_watchers)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

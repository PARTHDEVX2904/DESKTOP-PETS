"""Entry point: build the QApplication, show Claw'd + tray, run the event loop.

Run with:  python -m clawd
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .pet_window import PetWindow
from .settings import APP_NAME, ORG_NAME
from .tray import build_tray


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    # The pet lives in the tray; don't quit when the (only) window is hidden.
    app.setQuitOnLastWindowClosed(False)

    pet = PetWindow()
    pet.show()

    # Keep a reference so the tray icon isn't garbage-collected.
    tray = build_tray(pet)  # noqa: F841

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

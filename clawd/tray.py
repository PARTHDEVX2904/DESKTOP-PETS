"""System-tray icon and menu (Reset position, Quit).

The tray icon is rendered from the sprite grid itself, so no external icon asset
is needed.
"""

from __future__ import annotations

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .pet_window import PetWindow
from .sprite import render_pixmap


def build_tray(pet: PetWindow) -> QSystemTrayIcon:
    """Create the tray icon + menu wired to the given pet window."""
    icon = QIcon(render_pixmap())
    tray = QSystemTrayIcon(icon, parent=pet)
    tray.setToolTip("Claw'd")

    menu = QMenu()
    menu.addAction("Reset position", pet.reset_position)
    menu.addSeparator()
    menu.addAction("Quit", QApplication.quit)
    tray.setContextMenu(menu)

    tray.show()
    return tray

"""Background detection of whether a song is actively playing (winsdk / SMTC).

Polls off the GUI thread and reports changes via a Qt signal. If winsdk isn't
installed (or this isn't Windows), detection just always reports "not playing"
— the app runs normally, it simply never shows headphones.
"""

from __future__ import annotations

import asyncio

from PySide6.QtCore import QThread, Signal

POLL_MS = 2000


async def _is_playing() -> bool:
    from winsdk.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager as MediaManager,
        GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
    )

    manager = await MediaManager.request_async()
    session = manager.get_current_session()
    if session is None:
        return False
    info = session.get_playback_info()
    return info is not None and info.playback_status == PlaybackStatus.PLAYING


class MusicWatcher(QThread):
    """Polls playback state every POLL_MS; emits playing_changed(bool) on change."""

    playing_changed = Signal(bool)

    def run(self) -> None:
        last: bool | None = None
        while not self.isInterruptionRequested():
            try:
                playing = asyncio.run(_is_playing())
            except Exception:
                # winsdk missing, no session, COM error, etc. -> not playing.
                playing = False
            if playing != last:
                self.playing_changed.emit(playing)
                last = playing
            self.msleep(POLL_MS)

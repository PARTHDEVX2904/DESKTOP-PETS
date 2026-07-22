# Claude Code prompt — music-reactive headphones for Claw'd (Windows / winsdk)

Paste everything below into Claude Code, in the existing Claw'd project (V1 + sunglasses).

---

## Task
Add **headphones** to Claw'd that appear automatically **whenever a song is actually playing**
on Windows, and disappear when playback pauses/stops. Detect playback with the **`winsdk`**
package (Windows System Media Transport Controls / "Now Playing" API). The headphones must
render correctly **at the same time as the sunglasses** — both overlays can be on together.

This extends the existing app. Keep ALL current behavior (frameless, translucent, always-on-top,
drag, tray Quit/Reset, remembered position, right-click sunglasses toggle + persisted glasses state).

---

## STEP 1 — Give the window headroom (required, do this first)
The headphone band arcs **above** the head and the cups sit **beside** it, so they fall outside
the current sprite-sized window and would be clipped. Add a transparent margin around the sprite:

```python
MARGIN_CELLS = 2   # transparent padding (in base cells) on every side, room for accessories
```
- Window size becomes `(12 + 2*MARGIN_CELLS)*SCALE` wide x `(8 + 2*MARGIN_CELLS)*SCALE` tall.
- Define the sprite's on-window origin once and draw EVERY layer relative to it:
  ```python
  sprite_ox = MARGIN_CELLS * SCALE
  sprite_oy = MARGIN_CELLS * SCALE
  ```
- Draw base sprite, sunglasses, and headphones all offset by `(sprite_ox, sprite_oy)`.
  **The sunglasses placement constants stay the same** — they're relative to the sprite origin,
  which is now `(sprite_ox, sprite_oy)` instead of `(0,0)`. Just add the offset when drawing.
- Because the window grew, re-check drag + first-run/reset placement still position Claw'd sensibly
  (account for the margin when snapping to a screen corner).

## STEP 2 — Headphones pixel data (use verbatim)
An overlay grid **24 columns x 11 rows** drawn at **half-cell** resolution (each overlay pixel =
`SCALE/2` px). Cells: `0` = transparent, `1` = headphone -> color `#1A487C` (RGB 26, 72, 124).

```python
HEADPHONES = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0],
    [0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    [0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0],
    [0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0],
    [0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0],
    [0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
]
HEADPHONE_COLOR = "#1A487C"
```

Placement (relative to sprite origin), tunable constants near the top of the module:
```python
HEADPHONES_LEFT_CELLS = 0.0    # x offset from sprite left, in base cells
HEADPHONES_TOP_CELLS  = -2.0   # y offset from sprite top, in base cells (negative = above the head)
# overlay pixel size is SCALE/2 (half-cell). Draw with rounded boundaries (see below).
```

Render in `paintEvent`, AFTER the base sprite. Use rounded boundaries so half-cells tile seamlessly:
```python
ox = sprite_ox + HEADPHONES_LEFT_CELLS * SCALE
oy = sprite_oy + HEADPHONES_TOP_CELLS  * SCALE
cw = SCALE / 2.0; ch = SCALE / 2.0
for r, row in enumerate(HEADPHONES):
    for c, v in enumerate(row):
        if v == 0: continue
        x0 = round(ox + c*cw); x1 = round(ox + (c+1)*cw)
        y0 = round(oy + r*ch); y1 = round(oy + (r+1)*ch)
        painter.fillRect(x0, y0, x1-x0, y1-y0, QColor(HEADPHONE_COLOR))
```
Antialiasing off for these rects (crisp pixels). The `-2.0` top offset needs `MARGIN_CELLS >= 2`.

## STEP 3 — Layering / draw order
In `paintEvent`, draw in this order every frame:
1. base sprite (always)
2. headphones (only if `self.headphones_on`)  <- music-driven
3. sunglasses (only if `self.glasses_on`)      <- right-click driven
Headphones and sunglasses are independent booleans; any combination is valid and must render
correctly together (band above + cups on the sides don't overlap the lenses on the eyes).

## STEP 4 — Detect "a song is playing" with winsdk
Add `winsdk` to requirements (`pip install winsdk`; Windows 10+ only). Detection logic:

```python
# The exact symbol names below are the winsdk projections of the WinRT SMTC API.
# VERIFY names/casing/module path against the installed winsdk version — winsdk
# auto-generates Pythonic names and these can differ slightly between versions.
import asyncio
from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager,
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
)

async def _is_playing() -> bool:
    mgr = await MediaManager.request_async()
    session = mgr.get_current_session()
    if session is None:
        return False
    info = session.get_playback_info()
    return info.playback_status == PlaybackStatus.PLAYING
```

Poll it off the GUI thread and report changes back via a Qt signal:
```python
from PySide6.QtCore import QThread, Signal

class MusicWatcher(QThread):
    playing_changed = Signal(bool)
    POLL_MS = 2000
    def run(self):
        last = None
        while not self.isInterruptionRequested():
            try:
                playing = asyncio.run(_is_playing())
            except Exception:
                playing = False   # winsdk missing / no session / error -> treat as not playing
            if playing != last:
                self.playing_changed.emit(playing)
                last = playing
            self.msleep(self.POLL_MS)
```
- In the window: create the watcher, connect `playing_changed` to a slot that sets
  `self.headphones_on = value; self.update()`. Start it after the window shows.
- On quit: `watcher.requestInterruption(); watcher.wait()` before exiting so it stops cleanly.
- Playing = show headphones; Paused/Stopped/no-session = hide. (Only `PLAYING` counts.)

Notes to respect:
- **Graceful degradation:** wrap the `winsdk` import in try/except. If it fails (not installed or
  not Windows), skip the watcher entirely — the app runs normally, just never shows headphones.
- **Do not persist** `headphones_on` — it reflects live playback and should be recomputed each run.
  Glasses state persistence is unchanged.
- `asyncio.run` per poll (every 2s) is fine. If you prefer, subscribe to the session's
  playback-info-changed event instead of polling — optional, only if it's clean.

## Acceptance criteria
- [ ] All prior behavior intact: float/translucent/on-top, drag, tray Quit/Reset, remembered position, right-click sunglasses toggle, persisted glasses state.
- [ ] Window now has transparent margin; nothing about the base sprite or sunglasses looks shifted or clipped.
- [ ] Start playing a song (Spotify, a browser tab, any SMTC-aware app) -> headphones appear within ~2s.
- [ ] Pause/stop -> headphones disappear within ~2s.
- [ ] Sunglasses ON + music playing -> BOTH render correctly at once.
- [ ] Headphones match the grid: blue stepped headband over the top, cups down each side at eye level, orange head showing between them.
- [ ] Changing `SCALE` rescales sprite + sunglasses + headphones together, crisp, no seams.
- [ ] Quitting stops the watcher thread with no hang or error.
- [ ] If `winsdk` is unavailable, the app still launches and works (just no headphones).

## Out of scope
No song title/artist text, no animation, no other accessories, no Claude integration yet — later versions.

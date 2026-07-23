# Claude Code prompt — front laptop + typing animation for Claw'd (Windows)

Paste everything below into Claude Code, in the existing Claw'd project
(V1 base sprite + right-click sunglasses + music-activated headphones).

This REPLACES any earlier "laptop" work in progress. This is the final, confirmed design.

---

## Task
Add a **laptop** that appears **centered in front of Claw'd, resting on the ground**, whenever
I'm typing on the keyboard, with a small looping animation: mostly his hands sit typing
(invisible, blended into the keyboard color), and every few seconds he briefly **lifts his
hands and his eyes shift up** — like he's pausing to glance at the viewer — before returning
to typing. The laptop fades out shortly after I stop typing.

Must coexist correctly with the existing sunglasses (right-click) and headphones (music).
Keep ALL current behavior intact: frameless, translucent, always-on-top, drag-to-move, tray
Quit/Reset, remembered position, right-click sunglasses toggle + persisted glasses state,
music-driven headphones.

**No new window margin is needed for this accessory** — it fits entirely within the existing
12x8 sprite bounding box (reuse whatever `MARGIN_CELLS` / `sprite_ox` / `sprite_oy` the
headphones feature already set up; don't change them for this feature).

---

## STEP 1 — Laptop pixel data (use verbatim)
An overlay grid **18 columns x 10 rows**, drawn at **half-cell** resolution (`SCALE/2` px per
cell), same convention as the headphones/sunglasses. This is a plain grey laptop viewed from
behind the screen (we see the lid's back), with a small square logo — no orange, no branding
color, strictly greys.

Cells: `0` = transparent, `1` = bezel/hinge (dark grey), `2` = logo (light grey), `3` = keyboard
base (ash grey).

```python
LAPTOP = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
    [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
]

LAPTOP_COLORS = {
    1: "#2B2F3A",   # bezel / hinge (dark grey) — rows 0-7 are the solid lid-back + hinge
    2: "#C7CCD1",   # logo (light grey square, centered)
    3: "#4A5160",   # keyboard base (ash grey) — rows 8-9
}
```
No orange, no other colors anywhere in this asset.

## STEP 2 — Placement: centered in front, resting on the ground
```python
LAPTOP_LEFT_CELLS = 1.5    # x offset from sprite left, in base cells — centers the 9-cell-wide laptop under the 12-cell sprite
LAPTOP_TOP_CELLS  = 3.0    # y offset from sprite top, in base cells — puts the laptop's bottom exactly on the sprite's ground line (row 8)
# overlay pixel size is SCALE/2 (half-cell), same as headphones/sunglasses
```
This has been verified in pixel terms: the laptop is 9 cells wide / 5 cells tall, fits centered
under the 12-cell-wide sprite with no horizontal overflow, and its bottom edge lands exactly on
row 8 (the sprite's own ground line, where the legs end) — so the legs are fully hidden behind
it and there is no gap or clipping. Do not add extra window margin for this.

Render with rounded boundaries, same helper style as the other accessories:
```python
ox = sprite_ox + LAPTOP_LEFT_CELLS * SCALE
oy = sprite_oy + LAPTOP_TOP_CELLS  * SCALE
cw = ch = SCALE / 2.0
for r, row in enumerate(LAPTOP):
    for c, v in enumerate(row):
        if v == 0: continue
        x0 = round(ox + c*cw); x1 = round(ox + (c+1)*cw)
        y0 = round(oy + r*ch); y1 = round(oy + (r+1)*ch)
        painter.fillRect(x0, y0, x1-x0, y1-y0, QColor(LAPTOP_COLORS[v]))
```
Antialiasing off for these rects.

## STEP 3 — Hand animation frames (use verbatim)
Three small overlay frames, each **18 columns wide x 2 rows tall**, same half-cell grid as the
laptop, positioned as a sub-region within it. Hands are drawn in the **same ash-grey as the
keyboard base** (`#4A5160`) — this is intentional: while typing, hands sit on the keyboard and
visually blend in (invisible, since they're the same color as what's behind them). During the
"look up" pause, hands lift onto the darker hinge/bezel area, where the same grey now contrasts
and becomes visible — that contrast IS the "hands rising" effect.

```python
HAND_COLOR = "#4A5160"   # identical to the keyboard base color — see note above

TYPE_A = [
    [0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0],
]
TYPE_B = [
    [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0],
]
LOOKUP = [
    [0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]
```

Vertical placement within the laptop (local row offset, added to `LAPTOP_TOP_CELLS`'s pixel
origin the same way `LAPTOP` cells are drawn — same `ox,oy,cw,ch` as Step 2):
```python
HAND_ROW_OFFSET_TYPING = 8   # sits on the keyboard base (rows 8-9) — blends in
HAND_ROW_OFFSET_LOOKUP = 6   # sits up on the bezel/hinge (rows 6-7) — becomes visible
```
Draw whichever hand frame is active using the SAME `ox`/`cw`/`ch` as the laptop, but with
`y0 = round(oy + (HAND_ROW_OFFSET + r) * ch)` instead of `r` directly — i.e. hands are drawn as
their own pass, offset vertically within the laptop's coordinate space, in `HAND_COLOR`.

## STEP 4 — Eye-shift "look up" alternate sprite (use verbatim)
A second version of the BASE sprite (not an overlay — a full replacement grid for the sprite
layer itself) with the eyes shifted up one row, to suggest he glanced upward:

```python
SPRITE_LOOKUP = [
    [0, 0, 1, 2, 1, 1, 1, 1, 2, 1, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0],
    [0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0],
]
```
This is identical to the existing `SPRITE` except the eye cells moved from row 1 to row 0.
Store it in `sprite.py` next to `SPRITE`. When rendering the BASE layer (step 3 of the overall
draw order below), use `SPRITE_LOOKUP` instead of `SPRITE` only during the "look up" beat;
otherwise use the normal `SPRITE` as always.

## STEP 5 — Animation state machine
While `self.typing_on` is True, cycle through these beats on a repeating loop:

```python
TYPE_JITTER_MS  = 300     # how often TYPE_A/TYPE_B alternate while "typing"
LOOKUP_EVERY_MS = 3500    # how often a look-up pause happens
LOOKUP_HOLD_MS  = 700     # how long the look-up pause lasts
```

Implementation: a single `QTimer` driving a small state machine on the window:
- Track elapsed time (or use two timers) so that every `LOOKUP_EVERY_MS`, switch to the "looking
  up" beat for `LOOKUP_HOLD_MS`:
  - use `SPRITE_LOOKUP` for the base layer
  - use `LOOKUP` for the hand frame, at `HAND_ROW_OFFSET_LOOKUP`
- The rest of the time (the "typing" beat), alternate every `TYPE_JITTER_MS` between:
  - `SPRITE` (normal) for the base layer
  - `TYPE_A` / `TYPE_B` alternating, at `HAND_ROW_OFFSET_TYPING`
- Only repaint (`self.update()`) when the active frame actually changes.
- When `self.typing_on` becomes False (see keystroke detection below), stop the animation
  timer and simply don't draw the laptop/hands at all; base layer reverts to normal `SPRITE`.

## STEP 6 — Overall draw order in `paintEvent`
1. **Base layer** — `SPRITE_LOOKUP` if currently in the look-up beat AND `typing_on`, else `SPRITE`.
2. Headphones — if `self.headphones_on` (music)
3. Sunglasses — if `self.glasses_on` (right-click)
4. **Laptop** — if `self.typing_on`: draw `LAPTOP`, then the active hand frame at the
   appropriate row offset for the current beat. Laptop draws LAST (frontmost).

All of these are independent and must render correctly in any combination (e.g. typing +
headphones + sunglasses all together; look-up beat + headphones + sunglasses; etc).

## STEP 7 — Detect typing (privacy-conscious, unchanged from prior plan)
**Only detect THAT a key was pressed — never record, store, or log WHICH key.** No keystroke
content, no buffering, no writing anything to disk.

Preferred approach — poll `GetAsyncKeyState` via `ctypes`. No system-wide hook, no admin rights,
lower chance of an antivirus flag than a low-level hook:

```python
# VERIFY against current Win32 docs: GetAsyncKeyState's low-order bit is documented as
# "key was pressed since the previous call", but that bit is shared process-wide and its
# exact semantics can be surprising. Confirm behavior rather than assuming.
import ctypes

user32 = ctypes.windll.user32   # Windows only — guard this import

WATCHED_VKS = (
    [0x08, 0x09, 0x0D, 0x20]                            # backspace, tab, enter, space
    + list(range(0x30, 0x3A))                           # 0-9
    + list(range(0x41, 0x5B))                           # A-Z
    + list(range(0xBA, 0xC1)) + list(range(0xDB, 0xE0))  # punctuation
)

def any_key_pressed() -> bool:
    for vk in WATCHED_VKS:
        if user32.GetAsyncKeyState(vk) & 0x0001:
            return True
    return False
```

Poll off the GUI thread, signal the window:
```python
from PySide6.QtCore import QThread, Signal

class TypingWatcher(QThread):
    key_pressed = Signal()
    POLL_MS = 50
    def run(self):
        while not self.isInterruptionRequested():
            try:
                if any_key_pressed():
                    self.key_pressed.emit()
            except Exception:
                pass
            self.msleep(self.POLL_MS)
```

State machine in the window:
- Connect `key_pressed` to a slot that sets `self.typing_on = True` (start the animation timer
  from Step 5 if it wasn't already running), and **(re)starts a single-shot `QTimer`** with
  `TYPING_LINGER_MS = 2500`.
- When that linger timer fires: `self.typing_on = False`, stop the animation timer, `self.update()`.
- Alternative if `GetAsyncKeyState` proves unreliable: `pynput.keyboard.Listener` with an
  `on_press` callback that **ignores the key argument entirely** and just emits the signal.

Requirements to respect:
- **Graceful degradation:** wrap the Windows-only bits in try/except. If unavailable, the app
  runs normally and the laptop simply never appears.
- **Do not persist** `typing_on` or animation phase — all live state, recomputed each run.
  Glasses persistence is unchanged.
- On quit: `watcher.requestInterruption(); watcher.wait()`, alongside the existing music watcher
  shutdown, and stop the animation `QTimer` cleanly too.

## Acceptance criteria
- [ ] All prior behavior intact: float/translucent/on-top, drag, tray Quit/Reset, remembered position, right-click sunglasses, persisted glasses state, music headphones.
- [ ] Start typing anywhere on the system -> laptop appears centered in front of Claw'd, resting on the ground, almost immediately.
- [ ] While typing: hands are NOT visibly distinct from the keyboard (same grey, blended in) — no orange or contrasting hand shapes during normal typing.
- [ ] Every ~3.5s, for about 0.7s: hands become visible (lifted onto the darker hinge) AND his eyes shift up to the top of his head, then both revert.
- [ ] Stop typing -> laptop disappears entirely ~2.5s later, base sprite reverts to normal `SPRITE`.
- [ ] Typing + music playing + sunglasses on -> all render together correctly, laptop frontmost.
- [ ] Laptop is strictly grey-toned: dark bezel, light-grey square logo, ash-grey base — no orange or other colors in the asset itself.
- [ ] Laptop fits centered under the sprite with no clipping and no extra window resize.
- [ ] Changing `SCALE` rescales everything together, crisp, no seams.
- [ ] No key identity is ever stored, logged, or written anywhere.
- [ ] Idle CPU stays negligible (repaint only on actual frame change, not every poll/tick).
- [ ] Quitting stops both watcher threads and the animation timer with no hang or error.

## Out of scope
No song/typing-speed-based variation beyond what's specified, no other accessories, no Claude
integration yet.

# Claw'd — Desktop Companion (V1) — Build Spec for Claude Code

## 0. What you're building
A tiny always-on-top desktop pet for **Windows**, written in **Python + PySide6 (Qt)**.
V1 is deliberately minimal and *stable*: a single static pixel-art sprite ("Claw'd") that
floats over the desktop, can be dragged around, remembers where it was left, and can be quit
from a system-tray menu. **No animation, no activity-reactions, no Claude integration in V1** —
those are later versions. Build V1 so that the sprite is data-driven (a grid), which makes
adding animation frames later trivial.

> Note on API details: the Qt flags/classes below are the correct ones conceptually, but
> PySide6 has changed enum access between versions (some versions want the fully-qualified form
> like `Qt.WindowType.FramelessWindowHint`, older code used `Qt.FramelessWindowHint`). Please
> verify exact enum paths and method signatures against the installed PySide6 version's docs
> rather than assuming. If something doesn't import/run as written, trust the current docs.

---

## 1. Tech stack
- **Python 3.10+**
- **PySide6** (Qt for Python, LGPL). *PyQt6 is an acceptable drop-in if preferred; APIs are nearly identical.*
- No other runtime dependencies required for V1.
- Target OS: **Windows 10/11**. (Keep code reasonably cross-platform, but only Windows must be verified.)

---

## 2. The sprite — exact data (do NOT approximate; use these values verbatim)

The character is a **12 columns × 8 rows** pixel grid. Each cell is one of three states:

- `0` = transparent / empty
- `1` = body  → color `#F05B45` (RGB 240, 91, 69)
- `2` = eye   → color `#110C0A` (RGB 17, 12, 10), effectively near-black

```python
# rows top→bottom, each row left→right (12 wide, 8 tall)
SPRITE = [
    [0,0,1,1,1,1,1,1,1,1,0,0],
    [0,0,1,2,1,1,1,1,2,1,0,0],
    [1,1,1,1,1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,1,1,1],
    [0,0,1,1,1,1,1,1,1,1,0,0],
    [0,0,1,1,1,1,1,1,1,1,0,0],
    [0,0,1,0,1,0,0,1,0,1,0,0],
    [0,0,1,0,1,0,0,1,0,1,0,0],
]

COLORS = {
    1: "#F05B45",   # body
    2: "#110C0A",   # eyes
}
```

ASCII reference (for your sanity, `.`=empty `#`=body `O`=eye):
```
..########..
..#O####O#..
############
############
..########..
..########..
..#.#..#.#..
..#.#..#.#..
```
This is: rounded head, two eyes on row 2, side "arms" (the full-width rows 3–4),
lower body, and four legs with gaps. **No image file is needed** — this grid IS the sprite.

---

## 3. Rendering
- Render by drawing filled squares from `SPRITE` in a `QWidget.paintEvent` using `QPainter`.
- One grid cell → a `SCALE × SCALE` filled rectangle. Skip `0` cells entirely (they stay transparent).
- Use crisp edges (no antialiasing on the pixel rects) so it stays sharp when scaled.
- **`SCALE` is a top-of-file constant.** Default `SCALE = 14` → window content ≈ `168 × 112` px. Easy to change.
- The widget/window size must be exactly `12*SCALE` wide × `8*SCALE` tall (no extra padding), so the
  transparent margins around the sprite are just the empty grid cells.

---

## 4. Window behavior (V1 functional requirements)
1. **Frameless** — no title bar, no borders (`FramelessWindowHint`).
2. **Always on top** — floats above normal windows (`WindowStaysOnTopHint`).
3. **Translucent background** — only the sprite pixels are visible; everything else is fully
   transparent. Use `setAttribute(WA_TranslucentBackground)` and keep the widget's own background clear.
4. **No taskbar entry** — it's a floating pet, not an app window. Use the `Qt.Tool` window type
   (on Windows this keeps it out of the taskbar/alt-tab). Verify this behaves on Win11.
5. **Draggable** — left-click and drag anywhere on the sprite to move the whole window. Implement via
   `mousePressEvent` (record cursor-to-window offset) and `mouseMoveEvent` (`self.move(...)`).
   Only the visible sprite region should be draggable; clicking a transparent cell should ideally do
   nothing (acceptable for V1 if the whole bounding box is draggable, but prefer hit-testing to non-empty cells).
6. **System tray icon** (`QSystemTrayIcon`) with a right-click `QMenu` containing:
   - **Reset position** → move sprite back to a default spot (e.g., bottom-right, with a small margin).
   - **Quit** → cleanly exit the app.
   Use the sprite itself (rendered to a `QPixmap`/`QIcon`) as the tray icon so no external icon asset is needed.
7. **Remembers position** — persist the window's `(x, y)` on move/close and restore it on next launch.
   Use either `QSettings` (writes to the Windows registry automatically) **or** a small JSON file under
   `QStandardPaths.AppDataLocation`. Pick one; `QSettings` is simplest. On first run (no saved position),
   place it bottom-right with a ~40px margin from the screen edges.
8. Right-clicking the **sprite** may optionally also show the same context menu (nice-to-have, not required).

---

## 5. Project structure (suggested)
```
clawd/
├─ clawd/
│  ├─ __init__.py
│  ├─ __main__.py        # entry point: builds QApplication, shows the pet, runs event loop
│  ├─ sprite.py          # SPRITE grid + COLORS + a function/QWidget that paints it
│  ├─ pet_window.py      # the frameless translucent always-on-top draggable window
│  ├─ tray.py            # QSystemTrayIcon + menu (Reset position, Quit)
│  └─ settings.py        # load/save window position
├─ pyproject.toml        # or requirements.txt: just pyside6
├─ requirements.txt      # pyside6
└─ README.md             # install + run instructions
```
Keep `sprite.py` as the single source of truth for the pixel data so future animation frames
(V2+) slot in as additional grids without touching window logic.

---

## 6. Config constants (put at top of the relevant module)
```python
SCALE = 14                 # pixels per grid cell
ALWAYS_ON_TOP = True
DEFAULT_MARGIN = 40        # px from screen edge for first-run / reset placement
APP_NAME = "Clawd"
ORG_NAME = "Clawd"         # for QSettings
```

---

## 7. Run & package
- Dev run: `pip install pyside6` then `python -m clawd`.
- README should include those two lines plus a Python 3.10+ note.
- **Optional (only if asked):** a PyInstaller one-file build so it launches as a `.exe` without a
  console window (`--noconsole`/`--windowed`). Don't do this in V1 unless requested.

---

## 8. Acceptance criteria (V1 is "done" when all true)
- [ ] Launching shows Claw'd floating on the desktop, above other windows, with a transparent background (no visible box/frame).
- [ ] The sprite matches the grid in §2 exactly (colors and shape).
- [ ] Dragging the sprite moves it; it stays where dropped.
- [ ] It does not appear in the Windows taskbar or alt-tab.
- [ ] A tray icon exists; its menu offers Reset position and Quit; both work.
- [ ] Closing and relaunching restores the last position.
- [ ] `SCALE` can be changed in one place to resize the whole pet cleanly, staying crisp.
- [ ] No crashes/errors on Windows 10/11 at launch, drag, and quit.

---

## 9. Explicitly OUT OF SCOPE for V1 (do not build yet)
- Any animation (idle bob, blink, walk).
- Activity detection or activity-based sprite changes (coding / music / planning states).
- Task-status toast, live status line, spinner, or background-task dropdown.
- Any Claude / Claude Code integration or syncing.
- Sound, notifications, settings UI, multiple pets.

---

## 10. Forward-compat note (so V1 doesn't box us in)
Later versions will add animation frames, activity states, a status toast under the pet, and Claude Code
sync. To keep that cheap: keep the sprite as grid data (already done), keep the painter reading from a
"current frame" grid, and keep window/tray/settings logic separate from sprite data. Don't implement any
of it now — just don't hard-code assumptions that a single static frame is the only possibility.

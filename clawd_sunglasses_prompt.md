# Claude Code prompt — add "Deal With It" sunglasses accessory to Claw'd

Paste everything below into Claude Code, in the existing Claw'd project.

---

## Task
Add a **sunglasses accessory** to the existing Claw'd desktop pet. The sunglasses are a
pixel-art overlay drawn ON TOP of the current sprite, over the eyes. They are toggled by
**right-clicking the mascot** (right-click once = glasses appear, right-click again = glasses
disappear). Do not modify the base sprite; the glasses are a separate overlay layer.

This extends V1 — keep everything that already works (frameless, translucent, always-on-top,
drag-to-move, tray Quit/Reset, remembered position). Only ADD the glasses feature.

## The sunglasses — exact pixel data (use verbatim, do not redesign)
A **44 columns × 10 rows** overlay grid. Cell states:
- `0` = transparent (base sprite shows through — this includes the nose-bridge gap in the middle)
- `1` = frame → color `#0A0B1F` (RGB 10, 11, 31), dark navy
- `2` = highlight → color `#F5F5F5` (near-white, the checker glint inside each lens)

```python
SUNGLASSES = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 2, 2, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 2, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 2, 2, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 2, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [1, 1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
]

SUNGLASSES_COLORS = {1: "#0A0B1F", 2: "#F5F5F5"}
```

## Placement over the base sprite
The base sprite is a 12×8 grid drawn at `SCALE` px per cell, eyes at row 1 (cols 3 and 8).
Position the glasses overlay in **base-cell coordinates** (floats), so it scales with `SCALE`:

```python
# top-left of the glasses box, and its width, measured in BASE CELLS
GLASSES_LEFT_CELLS  = 1.6      # x offset from sprite left, in base cells
GLASSES_TOP_CELLS   = 0.5      # y offset from sprite top, in base cells
GLASSES_WIDTH_CELLS = 8.8      # box width in base cells; height derives from the grid aspect
```
- Box width in px = `GLASSES_WIDTH_CELLS * SCALE`.
- Glasses-pixels are **square**: `cell_px = (GLASSES_WIDTH_CELLS * SCALE) / 44`, and the box
  height in px = `cell_px * 10`.
- These three constants are tunable by eye — expose them near the top of the module.
  The given values center the lenses on the sprite's eyes and let the orange nose-bridge show
  through the middle gap (verified against the reference).

## Rendering the overlay (avoid seams at non-integer cell sizes)
Draw each glasses cell as a filled rect using **rounded boundaries** so adjacent cells tile with
no gaps, even when `cell_px` isn't an integer:

```python
ox = GLASSES_LEFT_CELLS * SCALE
oy = GLASSES_TOP_CELLS  * SCALE
cw = (GLASSES_WIDTH_CELLS * SCALE) / 44.0
ch = cw
for r, row in enumerate(SUNGLASSES):
    for c, v in enumerate(row):
        if v == 0:
            continue
        x0 = round(ox + c * cw);      x1 = round(ox + (c + 1) * cw)
        y0 = round(oy + r * ch);      y1 = round(oy + (r + 1) * ch)
        painter.fillRect(x0, y0, x1 - x0, y1 - y0, QColor(SUNGLASSES_COLORS[v]))
```
Draw the glasses in the SAME `paintEvent`, AFTER the base sprite, only when glasses are enabled.
Turn OFF antialiasing for these rects so edges stay crisp.

## Interaction
- **Right-click on the mascot toggles the glasses** (`mousePressEvent`, check for the right button;
  flip a `self.glasses_on` bool and call `self.update()`). Keep **left-click drag** working exactly
  as before — do not let the right-click interfere with dragging.
- Keep the existing tray menu (Reset position, Quit). Optionally also add a checkable
  "Sunglasses 😎" item to the tray menu that reflects/toggles the same `glasses_on` state.
- **Persist `glasses_on`** alongside the saved window position (same QSettings/JSON you already use),
  and restore it on launch, so Claw'd remembers whether the shades were on.

## Keep it data-driven
Store `SUNGLASSES` in `sprite.py` next to the base `SPRITE` grid. This is the first "accessory";
structure it so more accessories (hats, etc.) could be added later as additional overlay grids +
placement constants, without touching window/drag/tray logic. Do not build any other accessory now.

## Acceptance criteria
- [ ] App still launches with all V1 behavior intact (float, translucent, on-top, drag, tray, remembered position).
- [ ] Right-clicking Claw'd puts the sunglasses on; right-clicking again removes them.
- [ ] Glasses match the grid above: navy frame, white checker glints in each lens, transparent nose-bridge gap showing the orange body.
- [ ] Lenses sit centered over the sprite's eyes; frame spans the head as in the reference.
- [ ] Changing `SCALE` rescales sprite AND glasses together, staying crisp with no seams.
- [ ] Glasses on/off state survives a restart.
- [ ] Left-drag still moves the pet; right-click never triggers a drag.

## Out of scope
No animation, no other accessories, no activity reactions, no Claude integration — those are later versions.

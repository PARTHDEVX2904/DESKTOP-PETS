# Claw'd — Desktop Companion (V1)

A tiny always-on-top desktop pet for Windows. Claw'd is a single static pixel-art
sprite that floats over the desktop, can be dragged around, and can be quit from
a system-tray menu.

V1 is deliberately minimal and stable: no animation, no activity reactions, no
Claude integration — those are later versions. The sprite is stored as grid data,
so animation frames slot in later without touching the window logic.

## Requirements

- Python 3.10+
- [PySide6](https://pypi.org/project/PySide6/)

## Install & run

```bash
pip install pyside6
python -m clawd
```

Run both commands from this `PETS/` directory (the one containing the `clawd/`
package).

## Usage

- **Move it:** left-click and drag the sprite; it stays where you drop it for the
  rest of the session.
- **Tray menu:** right-click the system-tray icon (or right-click the sprite) for:
  - **Reset position** — send Claw'd back to the bottom-right corner.
  - **Quit** — exit the app.
- **Startup position:** Claw'd always opens in the bottom-right corner, just
  above the taskbar (it does not remember position between launches).

## Stopping the pet

The friendliest way to quit is the tray menu (right-click the tray icon → **Quit**).

If you started it from a terminal and it's still in the foreground, **`Ctrl+C`**
in that same terminal window stops it.

To stop it from another terminal (e.g. a separate VS Code terminal tab), first
find its process ID (PID), then kill that specific PID — killing by image name
(`python.exe`) would also kill any *other* unrelated Python process you have running.

**Git Bash / WSL:**
```bash
# Find the PID (look for the "-m clawd" command line)
wmic process where "name='python.exe'" get ProcessId,CommandLine

# Kill that specific PID
taskkill //F //PID <pid>
```

**PowerShell:**
```powershell
# Find the PID (look for the "-m clawd" command line)
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Select-Object ProcessId, CommandLine

# Kill that specific PID
Stop-Process -Id <pid> -Force
```

## Running it again

```bash
cd "PROJECTS/PETS"
python -m clawd
```

(In PowerShell, use `cd "PROJECTS\PETS"` — same command otherwise.)

**Or, from any Command Prompt window:** just type `wakeclawd`. `PETS\bin` is on this account's
PATH, so `wakeclawd` launches Claw'd with no console window, from any directory. Running it again
while he's already awake is a safe no-op (a single-instance lock prevents duplicate pets).

## Customizing size

`SCALE` (pixels per grid cell) is defined once at the top of `clawd/sprite.py`.
Change it to resize the whole pet cleanly; it stays crisp at any scale.
Default `SCALE = 14` → a `168 × 112` px pet.


## this is for how to push and pull from the github so that i can learn it manually
echo "# DESKTOP-PETS" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin git@github.com:PARTHDEVX2904/DESKTOP-PETS.git
git push -u origin main

## pull the commits
git remote add origin git@github.com:PARTHDEVX2904/DESKTOP-PETS.git
git branch -M main
git push -u origin main
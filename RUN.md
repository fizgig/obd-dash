# PiZero OBD dashboards

One car-diagnostics dashboard (live RPM / speed / coolant / battery gauges +
stored trouble codes), built **four ways** with four different UI stacks. All
four run on **dummy data out of the box** and share the same
`datasource.py` model, so swapping in a real Bluetooth ELM327 adapter is the
same drop-in change in every one.

Designed for the goodtft **3.5" TFT (480×320)** on a Raspberry Pi Zero, but each
previews on a desktop too.

## The four projects

| Project | UI stack | Design options | Docs |
|---------|----------|----------------|------|
| [obd-dash/](obd-dash/) | **pygame** (SDL2), framebuffer | — (the original) | [README](obd-dash/README.md) · [DESIGN](obd-dash/DESIGN.md) |
| [obd-dash-qt/](obd-dash-qt/) | **PySide6 / Qt Designer** | **5** themes × gauge modes | [README](obd-dash-qt/README.md) · [DESIGN](obd-dash-qt/DESIGN.md) |
| [obd-dash-nicegui/](obd-dash-nicegui/) | **NiceGUI** (web, UI-in-Python) | **4** variants | [README](obd-dash-nicegui/README.md) · [DESIGN](obd-dash-nicegui/DESIGN.md) |
| [obd-dash-eel/](obd-dash-eel/) | **Eel** (web, HTML/CSS/JS) | **6** designs (live switcher) | [README](obd-dash-eel/README.md) · [DESIGN](obd-dash-eel/DESIGN.md) |

## Which one?

- **obd-dash** — weakest hardware, full pixel control, one dependency. The proven
  build running on the Pi today (~10 fps, ~30 % CPU).
- **obd-dash-qt** — a polished *native desktop* app with real widgets and a
  visual form editor. Heaviest to install on the Pi (distro Qt, no ARMv6 wheels).
- **obd-dash-nicegui** — a live *web* UI written entirely in Python; also
  viewable from a phone/laptop at `http://pizero:8080`.
- **obd-dash-eel** — a *web* UI you write in HTML/CSS/JS with a tiny Python
  bridge; the richest set of switchable looks.

See each project's [DESIGN.md](obd-dash/DESIGN.md) for the "why" behind its
library choices.

## Quick start (desktop preview)

Each project is self-contained. From its folder:

```bash
# 1. pygame  (original)
python obd-dash/dashboard.py --windowed

# 2. Qt      (themes: slate | neon | amber | mono | nord)
python -m pip install -r obd-dash-qt/requirements.txt
python obd-dash-qt/main.py --theme amber

# 3. NiceGUI (variants: cluster | panel | neon | mono)  ->  http://localhost:8080
python -m pip install -r obd-dash-nicegui/requirements.txt
python obd-dash-nicegui/app.py --variant neon

# 4. Eel     (designs: cockpit | cluster | cards | retro | neon | hud; also a live dropdown)
python -m pip install -r obd-dash-eel/requirements.txt
python obd-dash-eel/main.py --design hud
```

> On Windows PowerShell these run the same; just note paths use `\`. Each app's
> README lists all flags (fullscreen, ports, native window, browser choice, etc.).

## Design options at a glance

**Qt** (`--theme`) — palette **+ gauge render mode** (so the *feel* changes):

| Theme | Gauge mode | Look |
|-------|-----------|------|
| `slate` | arc | dark cyan filled arcs (matches the original) |
| `neon` | arc | magenta/cyan glow on black |
| `amber` | ticks | retro amber tick-ring cluster |
| `mono` | bar | greyscale, big numbers + hairline meters |
| `nord` | arc | cool Nord blues |

**NiceGUI** (`--variant`):

| Variant | Look |
|---------|------|
| `cluster` | radial ECharts gauges, cyan instrument cluster |
| `panel` | stat cards with linear meters, violet |
| `neon` | radial ECharts gauges, black + magenta/cyan glow |
| `mono` | oversized light numbers over hairline meters, greyscale |

**Eel** (`--design`, or switch live from the header dropdown):

| Design | Look |
|--------|------|
| `cockpit` | 2×2 arcs + side DTC panel, slate/cyan |
| `cluster` | two big dials + two small + DTC ticker, near-black/red |
| `cards` | four stat cards + horizontal DTC strip, navy/violet |
| `retro` | segmented LCD bar meters, amber + scanlines |
| `neon` | single row of glowing arcs + ticker, synthwave grid |
| `hud` | giant central speed, RPM bar, corner readouts, green HUD |

## Deploying to the Pi

The Pi logs in as `admin@pizero` (see [README.md](README.md)). Copy a project
folder to the Pi's home directory, e.g. with `scp`:

```bash
scp -r obd-dash admin@pizero:~/            # or obd-dash-qt / obd-dash-nicegui / obd-dash-eel
```

Or with `rsync` (faster on re-copies):

```bash
rsync -av --exclude 'docs-preview.png' obd-dash/ admin@pizero:~/obd-dash/
```

Then follow the **Run on the Pi** and **Autostart on boot (systemd)** sections in
that project's README — each documents the right install packages, display path
(framebuffer / `linuxfb` / kiosk browser), and a ready-to-use systemd unit:

- [obd-dash](obd-dash/README.md#autostart-on-boot) — writes RGB565 frames to `/dev/fb1`
- [obd-dash-qt](obd-dash-qt/README.md#run-on-the-pis-35-tft) — Qt `linuxfb` platform plugin
- [obd-dash-nicegui](obd-dash-nicegui/README.md#run-on-the-pis-35-tft) — kiosk Chromium at `localhost`
- [obd-dash-eel](obd-dash-eel/README.md#run-on-the-pis-35-tft) — Chromium app/kiosk mode

## Connecting a real ELM327 adapter

Identical across all four (the UI only depends on the `DataSource` interface):

1. `pip install obd`
2. Pair the adapter and bind it: `sudo rfcomm bind rfcomm0 <ADAPTER_MAC> 1`
3. Uncomment `OBDDataSource` at the bottom of that project's `datasource.py`.
4. Swap `DummyDataSource()` for `OBDDataSource("/dev/rfcomm0")` in its entry point.

Nothing in the rendering code changes.

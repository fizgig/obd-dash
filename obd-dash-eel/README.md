# PiZero OBD Dashboard — Eel edition

The same 480×320 car-diagnostics dashboard as [`../obd-dash`](../obd-dash), built
with **[Eel](https://github.com/python-eel/Eel)** — a tiny Python backend paired
with an HTML/JS/CSS frontend over a websocket. Python advances the shared data
model at 10 fps and pushes each frame to the browser; all rendering lives in
`web/`.

Runs on **dummy data out of the box**. The data model
([`datasource.py`](datasource.py)) is copied unchanged from the original, so a
real Bluetooth ELM327 adapter drops in the same way.

## Six design options (colour **and** layout)

Pick one at launch with `--design`, or switch **live** from the dropdown in the
header — no restart needed.

| Design    | Colour                            | Layout                                                   |
|-----------|-----------------------------------|----------------------------------------------------------|
| `cockpit` | Slate + cyan (like original)      | 2×2 arc gauges on the left, trouble-codes panel on right |
| `cluster` | Near-black + red performance      | Two **big** arc dials (RPM/SPEED), two small, DTC ticker |
| `cards`   | Navy + violet                     | Four stat cards with linear meters, horizontal DTC strip |
| `retro`   | Amber LCD, monospace + scanlines  | Stacked segmented-bar meters, side fault list            |
| `neon`    | Synthwave purple + magenta/cyan glow, grid backdrop | Single row of four glowing arcs + DTC ticker |
| `hud`     | Green heads-up display            | Giant central speed, RPM bar on top, corner readouts     |

Each design is a CSS palette (`theme-*` on `<body>`) plus a layout (`layout-*` on
`#stage`); [`web/app.js`](web/app.js) builds the matching DOM and returns an
`update(data)` function.

## Files

| File              | Purpose                                                     |
|-------------------|-------------------------------------------------------------|
| `main.py`         | Eel backend — pushes 10 fps snapshots, serves `web/`        |
| `web/index.html`  | Page shell (header / stage / footer + the design dropdown)  |
| `web/style.css`   | The four palettes + all component and layout styles         |
| `web/app.js`      | Gauge/meter/segment widgets, the 4 layout builders, bridge  |
| `datasource.py`   | `VehicleData` / `DTC` model + `DummyDataSource` (shared, unchanged) |

## Run (desktop)

```bash
python -m pip install -r requirements.txt      # installs Eel
python main.py                                 # opens Chrome in app mode, cockpit design
python main.py --design retro                  # start on a different design
python main.py --browser edge                  # use Edge instead of Chrome
python main.py --browser none --port 8100      # just serve; open http://localhost:8100 yourself
```

Eel opens a **Chromium browser (Chrome or Edge) in app mode** — a clean,
chromeless window. Close the window to quit (or Ctrl-C in the terminal). Use
`--browser none` if you don't have a Chromium browser or want to open the URL
manually.

## Run on the Pi's 3.5" TFT

Eel is pure Python and installs fine on the Pi Zero:

```bash
pip3 install eel
python3 main.py --browser chromium-browser     # Raspberry Pi OS ships Chromium
```

If app mode misbehaves on the Pi, serve headless and point a kiosk browser at it:

```bash
python3 main.py --browser none &
chromium-browser --kiosk --window-size=480,320 http://localhost:8100/index.html
```

### Autostart on boot (systemd)

```ini
[Unit]
Description=PiZero OBD Dashboard (Eel)
After=network.target

[Service]
User=admin
WorkingDirectory=/home/admin/obd-dash-eel
ExecStart=/usr/bin/python3 /home/admin/obd-dash-eel/main.py --browser none --port 8100
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
```

(Then a `chromium --kiosk http://localhost:8100/index.html` entry in the desktop
autostart to display it on the TFT.)

## Connecting a real adapter

Identical to the original: `pip install obd`, bind the ELM327 to
`/dev/rfcomm0`, uncomment `OBDDataSource` at the bottom of `datasource.py`, and
swap `DummyDataSource()` for `OBDDataSource("/dev/rfcomm0")` near the top of
`main.py`. Nothing in the frontend changes.

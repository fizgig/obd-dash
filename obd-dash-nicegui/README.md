# PiZero OBD Dashboard — NiceGUI (web) edition

The same 480×320 car-diagnostics dashboard as [`../obd-dash`](../obd-dash), served
as a web page by **[NiceGUI](https://nicegui.io)**. Open it in any browser, or run
it fullscreen/kiosk on the Pi. Live gauges (RPM / speed / coolant / battery) plus
stored trouble codes, updated at 10 fps over NiceGUI's websocket.

Runs on **dummy data out of the box**. The data model
([`datasource.py`](datasource.py)) is copied unchanged from the original, so a
real Bluetooth ELM327 adapter drops in the same way.

## Four design variants

| Variant   | Look                                                              | Command                         |
|-----------|------------------------------------------------------------------|---------------------------------|
| `cluster` | Radial ECharts gauges — dark cyan "instrument cluster"           | `python app.py`                 |
| `panel`   | Stat cards with linear meters — violet/amber "control panel"     | `python app.py --variant panel` |
| `neon`    | Radial ECharts gauges — black with magenta/cyan glow             | `python app.py --variant neon`  |
| `mono`    | Minimalist — oversized light numbers over hairline meters, greyscale | `python app.py --variant mono` |

Everything is one page in [`app.py`](app.py); the variant swaps the gauge
builder and the colour palette (see the `VARIANTS` dict). The layout is framed to
the real 480×320 TFT size so it looks like the device in the browser.

## Files

| File            | Purpose                                                        |
|-----------------|----------------------------------------------------------------|
| `app.py`        | The whole NiceGUI app — page, both gauge styles, 10 fps timer  |
| `datasource.py` | `VehicleData` / `DTC` model + `DummyDataSource` (shared, unchanged) |

## Run (desktop)

```bash
python -m pip install -r requirements.txt      # installs NiceGUI
python app.py                                  # cluster variant
python app.py --variant panel                  # panel variant
python app.py --port 9000                       # different port
python app.py --no-show                          # don't auto-open a browser tab
```

Then open **http://localhost:8080** (it also opens automatically unless
`--no-show`). Stop with **Ctrl-C**.

Prefer a native desktop window instead of a browser tab:

```bash
python -m pip install pywebview
python app.py --native
```

## Run on the Pi's 3.5" TFT

NiceGUI is pure Python and installs fine on the Pi Zero:

```bash
pip3 install nicegui
python3 app.py                     # serves on http://<pi>:8080
```

Show it on the TFT by pointing a kiosk browser at localhost. With the display
mirrored to the framebuffer/X, e.g.:

```bash
chromium-browser --kiosk --window-size=480,320 --window-position=0,0 \
    --app=http://localhost:8080
```

> Because it's just a web page, you can also leave the Pi headless and open the
> dashboard from your phone or laptop at `http://pizero:8080` — handy for a
> glance at the car from outside it.

### Autostart on boot (systemd)

```ini
[Unit]
Description=PiZero OBD Dashboard (NiceGUI)
After=network.target

[Service]
User=admin
WorkingDirectory=/home/admin/obd-dash-nicegui
ExecStart=/usr/bin/python3 /home/admin/obd-dash-nicegui/app.py --variant cluster
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
```

(Then a second unit, or a `chromium --kiosk` entry in the desktop autostart, to
display it on the TFT.)

## Connecting a real adapter

Identical to the original: `pip install obd`, bind the ELM327 to
`/dev/rfcomm0`, uncomment `OBDDataSource` at the bottom of `datasource.py`, and
swap `DummyDataSource()` for `OBDDataSource("/dev/rfcomm0")` near the top of
`app.py`. Nothing in the UI changes.

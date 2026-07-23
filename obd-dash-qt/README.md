# PiZero OBD Dashboard — Qt / Qt Designer edition

The same 480×320 car-diagnostics dashboard as [`../obd-dash`](../obd-dash) (live
RPM / speed / coolant / battery gauges + stored trouble codes), rebuilt on
**PySide6 (Qt for Python)** with the layout authored in **Qt Designer**.

Runs on **dummy data out of the box**. The data model
([`datasource.py`](datasource.py)) is copied unchanged from the original, so a
real Bluetooth ELM327 adapter drops in the same way.

## Five design options

Selected with `--theme`. Each is a QSS palette **plus a gauge render mode**, so
the look *and* feel differ — not just the colours.

| Theme   | Gauge mode | Look                                                   | Command                      |
|---------|------------|--------------------------------------------------------|------------------------------|
| `slate` | arc        | Calm dark automotive, cyan filled arcs (the original)  | `python main.py`             |
| `neon`  | arc        | High-contrast night look, magenta/cyan glow            | `python main.py --theme neon` |
| `amber` | ticks      | Retro instrument cluster, warm amber **tick-ring** dials | `python main.py --theme amber` |
| `mono`  | bar        | Minimalist greyscale, big numbers + **hairline bar** meters | `python main.py --theme mono` |
| `nord`  | arc        | Cool "Nord" blues, filled arcs                         | `python main.py --theme nord` |

All share one Qt Designer form ([`dashboard.ui`](dashboard.ui)); each option is a
QSS stylesheet + gauge palette + mode in [`themes.py`](themes.py). The three
gauge modes (`arc` / `ticks` / `bar`) are painted by `ArcGauge` in
[`gauge.py`](gauge.py).

## Files

| File            | Purpose                                                        |
|-----------------|----------------------------------------------------------------|
| `dashboard.ui`  | The form — **open this in Qt Designer** to edit the layout     |
| `gauge.py`      | `ArcGauge`, a custom-painted widget promoted inside the form   |
| `themes.py`     | The two design variants (QSS + palette)                        |
| `main.py`       | Loads the `.ui`, wires it to data, runs a 10 fps `QTimer`      |
| `datasource.py` | `VehicleData` / `DTC` model + `DummyDataSource` (shared, unchanged) |

## How the Qt Designer form works

The four gauges are **promoted widgets**: in Qt Designer they're plain
`QWidget` placeholders promoted to class `ArcGauge` (header `gauge.h`). At
startup `main.py` registers the real class with `QUiLoader`
(`loader.registerCustomWidget(ArcGauge)`) so the placeholders become live,
hand-painted dials. Everything else (header, footer, the trouble-codes panel) is
ordinary Qt widgets styled by object name in the QSS.

## Run (desktop preview)

```bash
python -m pip install -r requirements.txt      # installs PySide6
python main.py                                 # windowed, slate theme
python main.py --theme neon                    # neon variant
python main.py --fullscreen                    # borderless fullscreen
```

Press **ESC** or **Q** to quit.

Edit the design live:

```bash
pyside6-designer dashboard.ui        # the Qt Designer GUI ships with PySide6
```

## Run on the Pi's 3.5" TFT

PySide6 wheels aren't available for the Pi Zero's ARMv6, so use the distro Qt:

```bash
sudo apt install -y python3-pyside6.qtwidgets python3-pyside6.qtuitools
```

Qt can drive the framebuffer directly (no X needed) via its `linuxfb` platform
plugin — point it at the TFT device and run fullscreen:

```bash
QT_QPA_PLATFORM=linuxfb:fb=/dev/fb1 python3 main.py --fullscreen
```

> If the panel stays blank, confirm the device with `ls /dev/fb*`
> (`/dev/fb1` = the SPI TFT, `/dev/fb0` = HDMI) and check `fbset -fb /dev/fb1`.
> On some builds `eglfs` or `linuxfb:fb=/dev/fb1:size=480x320` is needed.

### Autostart on boot (systemd)

```ini
[Unit]
Description=PiZero OBD Dashboard (Qt)
After=multi-user.target

[Service]
User=admin
WorkingDirectory=/home/admin/obd-dash-qt
Environment=QT_QPA_PLATFORM=linuxfb:fb=/dev/fb1
ExecStart=/usr/bin/python3 /home/admin/obd-dash-qt/main.py --fullscreen
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
```

## Connecting a real adapter

Identical to the original: `pip install obd`, bind the ELM327 to
`/dev/rfcomm0`, uncomment `OBDDataSource` at the bottom of `datasource.py`, and
swap `DummyDataSource()` for `OBDDataSource("/dev/rfcomm0")` in `main.py`.
Nothing in the UI changes.

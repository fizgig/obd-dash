#!/usr/bin/env python3
"""PiZero OBD dashboard -- Eel edition.

Eel pairs a Python backend with an HTML/JS/CSS frontend over a websocket. The
backend here is tiny: it advances the shared ``DummyDataSource`` at 10 fps and
pushes each snapshot to the browser (``eel.push_data(...)``). All rendering --
and all four design options -- live in ``web/`` (see app.js).

    python main.py                    # opens Chrome in app mode, "cockpit" design
    python main.py --design retro     # start on a different design
    python main.py --browser edge     # use Edge instead of Chrome
    python main.py --browser none     # just serve; open the URL yourself
    python main.py --port 8100

Four design options (colour + layout), also switchable live from the dropdown
in the header:  cockpit · cluster · cards · retro
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import eel

from datasource import DummyDataSource

HERE = Path(__file__).resolve().parent
WEB = HERE / "web"
FPS = 10
DESIGNS = ("cockpit", "cluster", "cards", "retro", "neon", "hud")


def pick(argv, flag, default=None):
    if flag in argv:
        i = argv.index(flag)
        if i + 1 < len(argv):
            return argv[i + 1]
    return default


DESIGN = pick(sys.argv, "--design", "cockpit")
if DESIGN not in DESIGNS:
    DESIGN = "cockpit"

src = DummyDataSource()
src.update(0.0)


def snapshot() -> dict:
    """A plain-dict view of the vehicle data, ready to JSON over the socket."""
    d = src.data
    return {
        "rpm": d.rpm, "speed": d.speed, "coolant": d.coolant,
        "voltage": d.voltage, "throttle": d.throttle,
        "connected": d.connected, "vehicle": d.vehicle, "vin": d.vin,
        "clock": time.strftime("%H:%M"),
        "dtcs": [{"code": x.code, "desc": x.desc, "severity": x.severity}
                 for x in d.dtcs],
    }


@eel.expose
def get_config() -> dict:
    """Called once by the frontend on load."""
    return {"design": DESIGN, "designs": list(DESIGNS)}


@eel.expose
def get_snapshot() -> dict:
    """Fallback pull path if the browser prefers to poll."""
    return snapshot()


def push_loop():
    """Advance the model and push each frame to the browser."""
    while True:
        src.update(1.0 / FPS)
        try:
            eel.push_data(snapshot())      # JS-exposed function (see app.js)
        except Exception:
            pass                            # no client connected yet
        eel.sleep(1.0 / FPS)


def main():
    browser = pick(sys.argv, "--browser", "chrome")
    port = int(pick(sys.argv, "--port", "8100"))
    eel.init(str(WEB))
    eel.spawn(push_loop)

    mode = None if browser in ("none", "off") else browser
    size = (560, 400)
    start = dict(mode=mode, port=port, size=size, block=True)
    try:
        eel.start("index.html", **start)
    except (SystemExit, KeyboardInterrupt):
        pass
    except Exception as exc:
        # Chosen browser not found -> keep serving so the user can open it.
        print(f"[eel] could not launch '{browser}' ({exc}).")
        print(f"[eel] serving at http://localhost:{port}/index.html — open it in any browser.")
        try:
            eel.start("index.html", mode=None, port=port, block=True)
        except (SystemExit, KeyboardInterrupt):
            pass


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""PiZero OBD dashboard -- NiceGUI (web) edition.

The same 480x320 car-diagnostics dashboard as ../obd-dash, served as a web page
by NiceGUI. Open it in any browser, or run it kiosk/fullscreen on the Pi. Data
comes from the shared ``DummyDataSource`` (copied unchanged from the original),
pushed to the browser on a 10 fps ``ui.timer``.

    python app.py                    # "cluster" variant, http://localhost:8080
    python app.py --variant panel    # the alternate "panel" design
    python app.py --port 9000        # serve on another port
    python app.py --native           # desktop window (needs: pip install pywebview)

Design variants (see VARIANTS below):
    cluster  radial ECharts gauges, dark cyan instrument cluster
    panel    stat cards with linear meters, violet/amber control-panel look
    neon     radial ECharts gauges, black + magenta/cyan glow
    mono     minimalist: oversized light numbers over hairline meters, greyscale
"""
from __future__ import annotations

import sys
import time

from nicegui import ui, app

from datasource import DummyDataSource

FPS = 10
DEVICE_W, DEVICE_H = 480, 320

# (data attr, label, vmin, vmax, unit, python-format, warn, danger)
GAUGES = [
    ("rpm",     "RPM",     0,  8000, "rpm",   "{:.0f}", 6000, 7000),
    ("speed",   "SPEED",   0,  160,  "mph",   "{:.0f}", None, None),
    ("coolant", "COOLANT", 40, 130,  "°C", "{:.0f}", 105, 115),
    ("voltage", "BATTERY", 10, 16,   "volts", "{:.1f}", None, None),
]

# --- Two design variants -----------------------------------------------------
VARIANTS = {
    "cluster": {
        "bg": "#0e1116", "panel": "#161b22", "stroke": "#2c343f",
        "track": "#263137", "text": "#e6edf3", "muted": "#8b949e",
        "accent": "#22d3ee", "amber": "#f59e0b", "red": "#ef4444",
        "green": "#22c55e", "info": "#22d3ee", "pending": "#a78bfa",
        "accent_label": "#22d3ee",
    },
    "panel": {
        "bg": "#0b1020", "panel": "#151a2e", "stroke": "#26304d",
        "track": "#26304d", "text": "#eef2ff", "muted": "#94a3c4",
        "accent": "#a78bfa", "amber": "#fbbf24", "red": "#fb7185",
        "green": "#34d399", "info": "#38bdf8", "pending": "#f472b6",
        "accent_label": "#a78bfa",
    },
    "neon": {
        "bg": "#05070d", "panel": "#0b0f1a", "stroke": "#1b2440",
        "track": "#1b2440", "text": "#f5f3ff", "muted": "#7dd3fc",
        "accent": "#22d3ee", "amber": "#fbbf24", "red": "#fb7185",
        "green": "#34d399", "info": "#22d3ee", "pending": "#e879f9",
        "accent_label": "#e879f9",
    },
    "mono": {
        "bg": "#0d0d0f", "panel": "#131317", "stroke": "#26262c",
        "track": "#2a2a30", "text": "#f0f0f2", "muted": "#8a8a92",
        "accent": "#e5e5ea", "amber": "#c9c9cf", "red": "#ff5a5a",
        "green": "#cfcfd4", "info": "#e5e5ea", "pending": "#9a9aa2",
        "accent_label": "#f0f0f2",
    },
}


def pick(argv, flag, default=None):
    if flag in argv:
        i = argv.index(flag)
        if i + 1 < len(argv):
            return argv[i + 1]
    return default


VARIANT = pick(sys.argv, "--variant", "cluster")
if VARIANT not in VARIANTS:
    VARIANT = "cluster"
T = VARIANTS[VARIANT]

src = DummyDataSource()
src.update(0.0)


def value_color(value, warn, danger):
    if danger is not None and value >= danger:
        return T["red"]
    if warn is not None and value >= warn:
        return T["amber"]
    return T["accent"]


def sev_color(sev):
    return {"critical": T["red"], "warning": T["amber"],
            "info": T["info"], "pending": T["pending"]}.get(sev, T["muted"])


# --- Trouble-codes panel (re-rendered only when the list changes) ------------
@ui.refreshable
def dtc_list(dtcs):
    if not dtcs:
        ui.label("No faults stored").style(f"color:{T['muted']}; font-size:12px")
        return
    for d in dtcs:
        col = sev_color(d.severity)
        with ui.element("div").style(
            f"background:{T['bg']}; border-left:3px solid {col};"
            f"border-radius:6px; padding:5px 8px; margin-bottom:6px"
        ):
            with ui.row().style("width:100%; justify-content:space-between; align-items:center; gap:4px"):
                ui.label(d.code).style(f"color:{T['text']}; font-size:14px; font-weight:700")
                ui.label(d.severity.upper()).style(f"color:{col}; font-size:9px; font-weight:700")
            ui.label(d.desc).style(f"color:{T['muted']}; font-size:10px; line-height:1.1")


# --- Gauge builders (one per variant) ----------------------------------------
gauge_updaters = []   # list of callables: (data) -> None


def build_gauge_cluster(container, attr, label, vmin, vmax, unit, fmt, warn, danger):
    """Radial ECharts gauge."""
    v0 = getattr(src.data, attr)
    with container:
        chart = ui.echart({
            "series": [{
                "type": "gauge", "startAngle": 225, "endAngle": -45,
                "min": vmin, "max": vmax, "radius": "94%", "center": ["50%", "54%"],
                "progress": {"show": True, "width": 9, "roundCap": True,
                             "itemStyle": {"color": value_color(v0, warn, danger)}},
                "pointer": {"show": False}, "anchor": {"show": False},
                "axisLine": {"lineStyle": {"width": 9, "color": [[1, T["track"]]]}},
                "axisTick": {"show": False}, "splitLine": {"show": False},
                "axisLabel": {"show": False},
                "title": {"show": True, "offsetCenter": [0, "-30%"],
                          "color": T["muted"], "fontSize": 10, "fontWeight": "bold"},
                "detail": {"valueAnimation": False, "offsetCenter": [0, "6%"],
                           "color": T["text"], "fontSize": 22, "fontWeight": "bold",
                           "formatter": "{value}"},
                "data": [{"value": float(fmt.format(v0)), "name": f"{label}  {unit}"}],
            }],
        }).style("width:100%; height:100%")

    def update(d):
        v = getattr(d, attr)
        s = chart.options["series"][0]
        s["data"][0]["value"] = float(fmt.format(v))
        s["progress"]["itemStyle"]["color"] = value_color(v, warn, danger)
        chart.update()

    gauge_updaters.append(update)


def build_gauge_panel(container, attr, label, vmin, vmax, unit, fmt, warn, danger):
    """Stat card: big number + a horizontal meter bar."""
    v0 = getattr(src.data, attr)
    with container:
        ui.label(label).style(f"color:{T['muted']}; font-size:10px; font-weight:700; letter-spacing:1px")
        with ui.row().style("align-items:baseline; gap:4px; margin:2px 0"):
            num = ui.label(fmt.format(v0)).style(f"color:{T['text']}; font-size:26px; font-weight:700; line-height:1")
            ui.label(unit).style(f"color:{T['muted']}; font-size:10px")
        with ui.element("div").style(
            f"width:100%; height:7px; background:{T['track']}; border-radius:4px; overflow:hidden"
        ):
            fill = ui.element("div").style(
                f"height:100%; width:0%; border-radius:4px; background:{value_color(v0, warn, danger)};"
                "transition:width .15s linear"
            )

    span = vmax - vmin

    def update(d):
        v = getattr(d, attr)
        num.text = fmt.format(v)
        pct = 0 if span == 0 else max(0.0, min(1.0, (v - vmin) / span)) * 100
        fill.style(f"width:{pct:.1f}%; background:{value_color(v, warn, danger)}")

    gauge_updaters.append(update)


def build_gauge_mono(container, attr, label, vmin, vmax, unit, fmt, warn, danger):
    """Minimalist: an oversized light-weight number over a hairline meter."""
    v0 = getattr(src.data, attr)
    with container:
        ui.label(label).style(f"color:{T['muted']}; font-size:9px; font-weight:700; letter-spacing:2px")
        with ui.row().style("align-items:baseline; gap:5px; margin:4px 0 8px"):
            num = ui.label(fmt.format(v0)).style(
                f"color:{T['text']}; font-size:34px; font-weight:300; line-height:1")
            ui.label(unit).style(f"color:{T['muted']}; font-size:10px")
        with ui.element("div").style(f"width:100%; height:2px; background:{T['track']}"):
            fill = ui.element("div").style(
                f"height:100%; width:0%; background:{value_color(v0, warn, danger)};"
                "transition:width .15s linear")

    span = vmax - vmin

    def update(d):
        v = getattr(d, attr)
        num.text = fmt.format(v)
        pct = 0 if span == 0 else max(0.0, min(1.0, (v - vmin) / span)) * 100
        fill.style(f"width:{pct:.1f}%; background:{value_color(v, warn, danger)}")

    gauge_updaters.append(update)


# variant -> gauge builder (neon reuses the radial ECharts look, recoloured)
GAUGE_BUILDERS = {
    "cluster": build_gauge_cluster, "neon": build_gauge_cluster,
    "panel": build_gauge_panel, "mono": build_gauge_mono,
}


# --- Page --------------------------------------------------------------------
ui.dark_mode(True)
ui.add_head_html("<style>body{margin:0} .nicegui-content{padding:0}</style>")
ui.query("body").style(
    f"background:#05070c; display:flex; align-items:center; justify-content:center;"
    f"min-height:100vh; font-family:'DejaVu Sans',system-ui,sans-serif"
)

# The "device" frame: exactly the 480x320 of the TFT, centred on the page.
with ui.element("div").style(
    f"width:{DEVICE_W}px; height:{DEVICE_H}px; background:{T['bg']}; overflow:hidden;"
    f"display:flex; flex-direction:column; border-radius:10px;"
    f"box-shadow:0 10px 40px rgba(0,0,0,.6)"
):
    # Header
    with ui.row().style(
        f"width:100%; height:34px; min-height:34px; align-items:center; gap:8px;"
        f"padding:0 12px; background:{T['panel']}; border-bottom:1px solid {T['stroke']}"
    ):
        ui.label("PiZero  OBD").style(
            f"color:{T['accent_label']}; font-size:15px; font-weight:700; letter-spacing:.5px")
        ui.element("div").style("flex:1")
        link = ui.label("BT LINK").style(
            f"color:{T['bg']}; background:{T['green']}; border-radius:10px;"
            f"padding:2px 10px; font-size:10px; font-weight:700")
        clock = ui.label("--:--").style(f"color:{T['muted']}; font-size:12px; font-weight:700")

    # Body: gauges (left) + trouble codes (right)
    with ui.row().style("flex:1; width:100%; gap:6px; padding:6px; box-sizing:border-box; min-height:0"):
        build_gauge = GAUGE_BUILDERS.get(VARIANT, build_gauge_cluster)
        with ui.grid(columns=2).style("gap:6px; flex:0 0 258px; height:100%"):
            for attr, label, vmin, vmax, unit, fmt, warn, danger in GAUGES:
                cell = ui.element("div").style(
                    f"background:{T['panel']}; border:1px solid {T['stroke']}; border-radius:8px;"
                    f"padding:8px; display:flex; flex-direction:column; justify-content:center;"
                    f"min-height:0; overflow:hidden"
                )
                build_gauge(cell, attr, label, vmin, vmax, unit, fmt, warn, danger)

        with ui.element("div").style(
            f"flex:1; background:{T['panel']}; border:1px solid {T['stroke']}; border-radius:8px;"
            f"padding:8px 10px; display:flex; flex-direction:column; min-height:0; overflow:hidden"
        ):
            with ui.row().style("width:100%; align-items:center; justify-content:space-between; margin-bottom:4px"):
                ui.label("TROUBLE CODES").style(f"color:{T['text']}; font-size:12px; font-weight:700")
                badge = ui.label("0").style(
                    f"color:{T['bg']}; background:{T['green']}; border-radius:9px;"
                    f"min-width:18px; text-align:center; padding:0 6px; font-size:11px; font-weight:700")
            ui.element("div").style(f"height:1px; background:{T['stroke']}; margin-bottom:6px")
            with ui.column().style("flex:1; overflow:auto; gap:0; width:100%"):
                dtc_list(src.data.dtcs)

    # Footer
    with ui.row().style(
        f"width:100%; height:22px; min-height:22px; align-items:center; justify-content:space-between;"
        f"padding:0 12px; background:{T['panel']}; border-top:1px solid {T['stroke']}"
    ):
        ui.label(src.data.vehicle).style(f"color:{T['muted']}; font-size:10px")
        ui.label("VIN " + src.data.vin).style(f"color:{T['muted']}; opacity:.7; font-size:10px")


_dtc_sig = None


def tick():
    global _dtc_sig
    src.update(1.0 / FPS)
    d = src.data
    for update in gauge_updaters:
        update(d)
    clock.text = time.strftime("%H:%M")
    if d.connected:
        link.text = "BT LINK"
        link.style(f"background:{T['green']}")
    else:
        link.text = "NO LINK"
        link.style(f"background:{T['red']}")

    sig = tuple((x.code, x.severity) for x in d.dtcs)
    if sig != _dtc_sig:
        _dtc_sig = sig
        badge.text = str(len(d.dtcs))
        badge.style(f"background:{T['red'] if d.dtcs else T['green']}")
        dtc_list.refresh(d.dtcs)


ui.timer(1.0 / FPS, tick)


if __name__ in {"__main__", "__mp_main__"}:
    port = int(pick(sys.argv, "--port", "8080"))
    native = "--native" in sys.argv
    show = not native and "--no-show" not in sys.argv
    ui.run(title=f"PiZero OBD ({VARIANT})", dark=True, reload=False,
           port=port, native=native, show=show,
           window_size=(DEVICE_W + 40, DEVICE_H + 60) if native else None)

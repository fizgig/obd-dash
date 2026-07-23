# Design libraries — `obd-dash-nicegui` (NiceGUI)

A web dashboard where the **UI is written in Python** — no HTML templates, no
separate frontend build. NiceGUI renders the widgets in the browser and keeps
them in sync with the server over a websocket.

## Main libraries

| Library    | Version         | Role                                                       |
|------------|-----------------|------------------------------------------------------------|
| **NiceGUI** | `>=1.4` (tested on 3.15) | Python-defined UI: elements, layout, styling, live updates |
| **Apache ECharts** | (bundled in NiceGUI) | The radial gauge charts, via `ui.echart(...)`      |
| **Quasar + Vue**   | (bundled)     | The component/rendering layer NiceGUI builds on            |
| **FastAPI + Uvicorn** | (bundled)  | The ASGI web server NiceGUI runs on                        |
| **pywebview** (optional) | `>=4.4` | Wraps the page in a native desktop window (`--native`)     |

You interact only with the `nicegui` API; everything below it (Vue, Quasar,
FastAPI, the websocket) is managed for you.

## Why NiceGUI

- **One language, one file.** The entire UI, styling, and update logic live in
  [`app.py`](app.py). No HTML/JS toolchain, no `npm`, no template files.
- **Live updates for free.** Mutate a Python object and call `.update()` /
  `.refresh()`; NiceGUI diffs and pushes just the change over the websocket —
  perfect for a 10 fps telemetry feed.
- **Batteries-included widgets.** Charts (ECharts), rows/columns/grids, labels,
  timers — enough to build a good-looking dashboard without hand-rolling
  components.
- **Pure Python install.** `pip install nicegui` works on the Pi Zero (unlike the
  Qt wheels), and because it's just a web page you can also view the dashboard
  from a phone or laptop at `http://pizero:8080`.
- **Deploys three ways from the same code:** a browser tab, a kiosk browser on
  the TFT, or a native window via pywebview.

Trade-off: it needs a running web server and a browser, and it's heavier than
pygame. For a glanceable, remotely-viewable dashboard that's usually worth it.

## How it's used

### Defining UI in Python
Elements are created with context managers and styled with Tailwind-ish
`.classes(...)` / raw `.style(...)`. The whole page is framed to the 480×320 TFT
size so it looks like the device ([`app.py`](app.py)):

```python
with ui.row().style("height:34px; background:...; align-items:center"):
    ui.label("PiZero  OBD").style("color:var(--accent); font-weight:700")
    ui.element("div").style("flex:1")
    clock = ui.label("--:--")
```

### Gauges with ECharts
The `cluster` / `neon` variants use a native ECharts gauge series through
`ui.echart(...)`. NiceGUI hands the option dict straight to ECharts:

```python
chart = ui.echart({"series": [{
    "type": "gauge", "startAngle": 225, "endAngle": -45,
    "progress": {"show": True, "itemStyle": {"color": accent}},
    "data": [{"value": v0, "name": f"{label}  {unit}"}],
}]})
```

To update, mutate `chart.options` and call `.update()`:

```python
chart.options["series"][0]["data"][0]["value"] = float(fmt.format(v))
chart.options["series"][0]["progress"]["itemStyle"]["color"] = value_color(v, ...)
chart.update()
```

The `panel` / `mono` variants skip charts entirely and use plain styled `div`
meters — showing you don't *have* to use ECharts for every gauge.

### The four design variants
[`app.py`](app.py) keeps a `VARIANTS` dict of colour palettes and a
`GAUGE_BUILDERS` map (`cluster`/`neon` → ECharts builder, `panel`/`mono` →
meter builders). `--variant NAME` picks the palette + builder at launch.

### Live refresh
- Values: a `ui.timer(0.1, tick)` pulls a snapshot from `DummyDataSource` and
  calls each gauge's `update`.
- Trouble codes: a `@ui.refreshable` function is re-run with `dtc_list.refresh(...)`
  only when the code list changes.

```python
@ui.refreshable
def dtc_list(dtcs): ...      # builds the rows
ui.timer(1/FPS, tick)        # tick() calls dtc_list.refresh(d.dtcs) on change
```

### Running it
`ui.run(...)` starts the server. `--native` swaps the browser tab for a pywebview
window; `--no-show` serves without opening anything (handy on a headless Pi).

## Files that own the "design"

| File       | Design responsibility                                          |
|------------|----------------------------------------------------------------|
| `app.py`   | Entire UI: palettes, gauge builders, layout, refresh, `ui.run` |

## When to reach for NiceGUI

Choose NiceGUI when you want a **modern, live-updating web UI defined entirely in
Python**, especially if you value remote/phone access and want to avoid a JS
build step. If you'd rather own the HTML/CSS/JS directly, see
[`../obd-dash-eel`](../obd-dash-eel); for a native desktop app, see
[`../obd-dash-qt`](../obd-dash-qt).

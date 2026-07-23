# Design libraries — `obd-dash-eel` (Eel)

A web dashboard where **you write the frontend yourself** in plain HTML/CSS/JS,
and **Eel** glues it to a small Python backend over a websocket. Python owns the
data; the browser owns the look.

## Main libraries

| Library         | Version   | Role                                                          |
|-----------------|-----------|---------------------------------------------------------------|
| **Eel**         | `>=0.16` (installed 0.18.2) | Python↔JS bridge; serves `web/` and opens a browser window |
| **Bottle + gevent-websocket** | (bundled in Eel) | The tiny web server / websocket transport underneath |
| **Vanilla HTML / CSS / JS** | — | The entire UI: layout, six themes, gauges, DTC lists    |
| **SVG** (browser built-in)  | — | The arc gauges are drawn as SVG `<circle>` strokes      |
| **Chrome / Edge (Chromium)** | any | Eel launches one in "app mode" for a chromeless window  |

There is **no UI framework** here (no React/Vue/Tailwind) — just the platform.
Eel's only job is transport and window management.

## Why Eel

- **Full control of the frontend.** Unlike NiceGUI (UI-in-Python), Eel lets you
  write real HTML/CSS/JS. That made the **six distinct designs with a live
  dropdown switcher** natural — each design is a CSS palette + a JS layout
  builder, swapped without a reload.
- **Trivial Python↔JS bridge.** Expose a Python function with `@eel.expose` and
  call it from JS as `eel.fn()`; expose a JS function and call it from Python as
  `eel.fn()`. That's the whole API.
- **Chromeless app window.** Eel opens Chrome/Edge in app mode, so it looks like
  a kiosk display, not a browser tab.
- **Pure Python + zero frontend build.** `pip install eel`, drop static files in
  `web/`. Installs fine on the Pi Zero; no `npm`, bundler, or transpiler.
- **Web skills transfer directly.** Anyone who knows CSS can add a theme; the
  gauges are ordinary SVG.

Trade-off: you implement the UI plumbing yourself (DOM building, update
throttling) and you need a Chromium browser for app mode (use `--browser none`
to just serve the URL otherwise).

## How it's used

### The bridge (Python → browser, 10 fps push)
[`main.py`](main.py) advances the shared `DummyDataSource` and **pushes** each
snapshot to a JS function:

```python
eel.init(str(WEB))                 # serve the web/ folder

@eel.expose                        # callable from JS as eel.get_config()
def get_config():
    return {"design": DESIGN, "designs": list(DESIGNS)}

def push_loop():
    while True:
        src.update(1/FPS)
        eel.push_data(snapshot())  # calls the JS-exposed push_data(...)
        eel.sleep(1/FPS)
```

On the JS side ([`web/app.js`](web/app.js)) the receiver is registered with
`eel.expose`, and the initial design is fetched with a callback:

```javascript
eel.expose(onData, 'push_data');                 // Python -> JS frames
eel.get_config()((cfg) => setDesign(cfg.design)); // JS -> Python, then callback
```

`index.html` pulls in the bridge with `<script src="/eel.js">`, which Eel serves
automatically.

### Six designs = palette + layout builder
Each design is two things:
- a **CSS palette** — a `theme-*` class on `<body>` that sets custom properties
  (`--bg`, `--accent`, `--track`, ...) in [`web/style.css`](web/style.css);
- a **layout builder** — `BUILDERS[name](stage)` in `app.js` that constructs the
  DOM and returns an `update(data)` closure.

Switching design (dropdown or `--design`) just swaps both and rebuilds:

```javascript
function setDesign(name) {
  document.body.className = 'theme-' + name;   // colours
  stage.className = 'layout-' + name;          // layout (CSS grid)
  stage.innerHTML = '';
  updater = BUILDERS[name](stage);             // build DOM, get an updater
}
```

Because everything reads CSS variables, components are theme-agnostic — a new
colourway is a `theme-*` block, nothing more.

### Reusable gauge primitives (SVG + DOM)
`app.js` defines small factories reused across designs, each returning
`{ el, set(value) }`:

- `makeArc` — a 270° gauge as two SVG `<circle>`s using `stroke-dasharray`
  (track + value); colour set via `.style.stroke` so CSS `var()` themes apply.
- `makeMeter` — a card with a big number + horizontal fill bar.
- `makeSeg` — a segmented "LCD" bar (retro design).
- `makeDtcList` / `makeTicker` — trouble-code list/ticker, rebuilt only when the
  code signature changes (cheap on the Pi).

### Running it
`eel.start("index.html", mode=..., port=...)` opens the window. `--browser edge`,
`--browser none` (serve only), `--design NAME`, and `--port` are handled in
`main.py`.

## Files that own the "design"

| File             | Design responsibility                                    |
|------------------|----------------------------------------------------------|
| `web/style.css`  | The six palettes + all component and layout CSS          |
| `web/app.js`     | Gauge/meter/segment widgets, the six layout builders, bridge |
| `web/index.html` | Page shell (header, `#stage`, footer, design dropdown)   |
| `main.py`        | Backend: 10 fps push, config, serving `web/`             |

## When to reach for Eel

Choose Eel when you want to **write the UI in HTML/CSS/JS** (existing web skills,
full styling control, easy multi-theme work) but keep the logic in Python with a
dead-simple bridge. If you'd rather define the UI *in Python*, use
[`../obd-dash-nicegui`](../obd-dash-nicegui); for a native desktop toolkit, see
[`../obd-dash-qt`](../obd-dash-qt).

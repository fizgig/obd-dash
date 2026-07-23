# Design libraries — `obd-dash-qt` (Qt for Python)

A native desktop UI built on **Qt**, with the layout authored visually in **Qt
Designer** and the gauges hand-painted with `QPainter`.

## Main libraries

| Library / tool     | Version   | Role                                                        |
|--------------------|-----------|-------------------------------------------------------------|
| **PySide6**        | `>=6.5`   | Official Python bindings for Qt 6 (Widgets, GUI, Core)      |
| **Qt Widgets**     | (in Qt 6) | The retained-mode widget toolkit (frames, labels, layouts)  |
| **Qt Designer**    | (ships with PySide6) | Visual `.ui` form editor (`pyside6-designer`)    |
| **QPainter**       | (in Qt 6) | 2-D vector painting for the custom `ArcGauge`               |
| **Qt Style Sheets (QSS)** | (in Qt 6) | CSS-like theming, one stylesheet per design option   |

## Why PySide6 + Qt Designer

- **Official & permissively licensed.** PySide6 is Qt's own binding (LGPL), so
  it's a safe long-term choice versus third-party alternatives.
- **A real widget toolkit.** Layouts, frames, scroll areas, and DPI handling come
  for free — no re-implementing box models or clipping like the pygame version.
- **Designer separates layout from logic.** The screen structure lives in an XML
  `.ui` file you edit in a GUI; Python only wires up data. Designers and
  developers can work on the same screen without touching each other's code.
- **QSS gives cheap re-skinning.** Each of the five themes is just a stylesheet +
  a palette, so "look and feel" changes never touch layout code.
- **QPainter for the custom bits.** Anything Qt doesn't ship (a 270° automotive
  gauge) is a normal painted widget, and — via **promotion** — it drops straight
  into the Designer form.

Trade-off: PySide6 is a big dependency and there are **no prebuilt wheels for the
Pi Zero's ARMv6**, so on the Pi you install Qt from apt (`python3-pyside6.*`) and
render through the `linuxfb` platform plugin. See the README's Pi section.

## How it's used

### The Designer form + promoted widgets
[`dashboard.ui`](dashboard.ui) is a standard Qt Designer file: a header
`QFrame`, a `QGridLayout` of gauges, a `QScrollArea` for the DTC list, and a
footer. The four gauges are plain `QWidget` placeholders **promoted** to the
custom class `ArcGauge`:

```xml
<widget class="ArcGauge" name="gaugeRpm" native="true"/>
...
<customwidget>
  <class>ArcGauge</class><extends>QWidget</extends><header>gauge.h</header>
</customwidget>
```

At startup [`main.py`](main.py) loads the form and registers the real class so
the placeholders become live gauges — no code-gen step needed:

```python
loader = QUiLoader()
loader.registerCustomWidget(ArcGauge)   # resolves class="ArcGauge" in the .ui
window = loader.load(ui_file)
gauge = window.findChild(ArcGauge, "gaugeRpm")
```

> `QUiLoader` loads the `.ui` at runtime. The alternative is compiling it with
> `pyside6-uic dashboard.ui -o ui_dashboard.py`; we use the loader to keep the
> `.ui` the single source of truth.

### The custom gauge — `QPainter`
[`gauge.py`](gauge.py) paints the dial in `paintEvent`. It supports three
**render modes** so themes differ in feel, not just colour:

- `arc` — a filled 270° arc via `QPainter.drawArc` (slate, neon, nord)
- `ticks` — a ring of radial tick marks via `drawLine` (amber cluster look)
- `bar` — a big number over a rounded `drawRoundedRect` meter (mono/minimal)

Values are pushed in with `set_value()`, which calls `update()` to schedule a
repaint. Colours come from a `Palette` the app hands over per theme.

### Theming with QSS
[`themes.py`](themes.py) holds five bundles of *(QSS stylesheet, gauge palette,
gauge mode, DTC row colours)*. The stylesheet targets Designer object names:

```css
#dtcPanel { background:#161b22; border:1px solid #2c343f; border-radius:8px; }
#linkPill { color:#22c55e; background:#1e252e; border-radius:10px; }
```

`main.py` applies the chosen one with `window.setStyleSheet(theme["qss"])` and
calls `gauge.set_mode(...)` / `gauge.set_palette(...)`.

### The update loop
A `QTimer` at 10 fps ([`main.py`](main.py) `Dashboard.tick`) pulls a snapshot
from the shared `DummyDataSource`, updates the gauges, and rebuilds the DTC rows
only when the code list changes.

## Files that own the "design"

| File            | Design responsibility                                   |
|-----------------|---------------------------------------------------------|
| `dashboard.ui`  | Screen layout (edit in Qt Designer)                     |
| `gauge.py`      | Custom `ArcGauge` painting + the three render modes     |
| `themes.py`     | The five design options (QSS + palette + mode)          |
| `main.py`       | Loads the form, applies a theme, runs the timer         |

## When to reach for Qt

Choose Qt/PySide6 when you want a **polished native desktop app** with real
widgets, layouts, and designer tooling, and you're OK with a heavier runtime.
Prefer [`../obd-dash`](../obd-dash) for the weakest hardware, or the browser-based
[`../obd-dash-nicegui`](../obd-dash-nicegui) / [`../obd-dash-eel`](../obd-dash-eel)
when you'd rather build the UI with HTML/CSS.

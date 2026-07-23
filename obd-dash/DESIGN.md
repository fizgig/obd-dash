# Design libraries — `obd-dash` (pygame)

The original dashboard. A single dependency does everything: drawing, fonts,
timing, and input.

## Main library

| Library  | Version    | Role                                        |
|----------|------------|---------------------------------------------|
| **pygame** | `>=2.1` (SDL2) | 2-D drawing, fonts, event loop, framebuffer bytes |

pygame is a thin Python wrapper over **SDL2**. Everything on screen — arcs,
panels, text, the DTC list — is drawn with `pygame.draw.*` and
`pygame.font.Font.render`. There is no widget toolkit; the app owns every pixel.

## Why pygame

- **Runs on an ARMv6 Pi Zero.** `python3-pygame` is in Raspberry Pi OS's apt repo
  as a prebuilt package — no compiling, no wheels-that-don't-exist problems.
- **No GPU / compositor needed.** The Pi's cheap ili9486 SPI panel has no
  accelerated driver. pygame lets us render to an ordinary in-memory surface and
  push the bytes ourselves, which is the only thing that works on this hardware
  (see below).
- **Full pixel control at low cost.** A custom automotive gauge look (270° arcs,
  colour thresholds) is trivial to draw and easy to make cheap — important on a
  single 1 GHz core.
- **Tiny footprint.** One dependency, ~10 fps, ~30 % CPU on the Pi Zero.

The trade-off: you build *everything* yourself (no buttons, layouts, or CSS).
For a fixed, full-screen, read-only gauge cluster that is a feature, not a cost.

## How it's used

### Driving the SPI TFT directly
This Pi's SDL2 build has no `fbcon`/`kmsdrm` driver for the panel, so we can't
just open a normal SDL window. Instead we use the **dummy video driver** and
write raw **RGB565** frames straight to `/dev/fb1`
([`FramebufferOutput`](dashboard.py) in `dashboard.py`):

```python
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")   # no real window
self._surf16 = pygame.Surface(size, depth=16)        # 16-bit == RGB565 layout
self._fb = open("/dev/fb1", "wb", buffering=0)
# each frame:
self._surf16.blit(surf, (0, 0))
self._fb.write(self._surf16.get_buffer().raw)        # push bytes to the panel
```

`--windowed` uses a normal SDL window instead, for desktop preview.

### Performance patterns (the interesting part)
The Pi Zero can't repaint the whole scene every frame, so the code is split into
**static** (baked once) and **dynamic** (per-frame) pieces — see
[`widgets.py`](widgets.py):

- **Baked background** — header, footer, gauge tracks and labels are drawn *once*
  into a single surface (`build_background`) and blitted each frame.
- **Pre-rendered arcs** — `ArcGauge` renders the value arc at every fill level up
  front as **colorkey blits**, so a live gauge update is one `blit`, not hundreds
  of `draw.circle` calls.
- **Text cache** — rendered numbers/strings are memoised (`TextCache`) so
  unchanged text isn't re-rasterised.
- **DTC panel cache** — the trouble-code panel is re-rendered only when the code
  list actually changes (`DtcPanelCache`).

### Fonts, colours, geometry
Centralised in [`theme.py`](theme.py): the palette, a lazily-built `Fonts` set
(prefers bundled DejaVu, falls back to a system font on desktop), and the
480×320 screen constants.

## Files that own the "design"

| File          | Design responsibility                          |
|---------------|------------------------------------------------|
| `theme.py`    | Colours, fonts, screen geometry                |
| `widgets.py`  | Arc gauges, DTC panel, header/footer drawing   |
| `dashboard.py`| Layout rects + the render loop                 |

## When to reach for this approach

Choose pygame when you need **full control of a fixed-size embedded display**,
must run on weak hardware without a GUI stack, or want to hand-tune every frame.
Reach for one of the sibling projects instead if you want real widgets and
layouts ([`../obd-dash-qt`](../obd-dash-qt)) or a browser-based UI
([`../obd-dash-nicegui`](../obd-dash-nicegui), [`../obd-dash-eel`](../obd-dash-eel)).

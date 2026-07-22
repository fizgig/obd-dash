#!/usr/bin/env python3
"""PiZero OBD dashboard -- fullscreen car-diagnostics display for the 3.5" TFT.

    python3 dashboard.py            # auto: writes to /dev/fb1 on the Pi's TFT
    python3 dashboard.py --fb /dev/fb1   # force framebuffer output to a device
    python3 dashboard.py --windowed # windowed SDL window, for desktop testing

Keys (windowed only):  ESC / Q  quit    (framebuffer mode: Ctrl-C)
"""
import os
import sys
import time
import pygame

import theme as T
import widgets as W
from datasource import DummyDataSource


class FramebufferOutput:
    """Render offscreen and push raw RGB565 frames to a Linux fbdev.

    Needed because this Pi's SDL2 build has no fbcon/kmsdrm driver for the
    ili9486 SPI panel -- so we draw to an in-memory surface and write the bytes
    to /dev/fb1 ourselves. pygame does the fast RGB565 conversion via a 16-bit
    surface whose memory layout already matches the framebuffer (stride = w*2).
    """

    def __init__(self, dev="/dev/fb1", size=(T.WIDTH, T.HEIGHT)):
        self.w, self.h = size
        self._surf16 = pygame.Surface(size, depth=16)  # RGB565 on little-endian
        self._fb = open(dev, "wb", buffering=0)

    def present(self, surf):
        self._surf16.blit(surf, (0, 0))
        self._fb.seek(0)
        self._fb.write(self._surf16.get_buffer().raw)

    def close(self):
        try:
            self._fb.close()
        except Exception:
            pass


def make_target(mode, fb_dev):
    """Return (draw_surface, fb_output_or_None). fb_output is set in fb mode."""
    if mode == "fb":
        # No real window: dummy video driver + direct framebuffer writes.
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        pygame.display.init()
        surface = pygame.Surface((T.WIDTH, T.HEIGHT))
        return surface, FramebufferOutput(fb_dev)

    pygame.display.init()
    pygame.display.set_caption("PiZero OBD")
    flags = 0 if mode == "windowed" else pygame.FULLSCREEN
    screen = pygame.display.set_mode((T.WIDTH, T.HEIGHT), flags)
    pygame.mouse.set_visible(mode == "windowed")
    return screen, None


def layout():
    """Compute the body rects (below header, above footer)."""
    top = T.HEADER_H + 6
    bottom = T.HEIGHT - T.FOOTER_H - 6
    body_h = bottom - top

    gauges_w = 258
    gap = 6
    # 2x2 grid of gauges in the left region
    gx, gy = 6, top
    cw = (gauges_w - gap) // 2
    ch = (body_h - gap) // 2
    gauge_rects = [
        pygame.Rect(gx,               gy,               cw, ch),
        pygame.Rect(gx + cw + gap,    gy,               cw, ch),
        pygame.Rect(gx,               gy + ch + gap,    cw, ch),
        pygame.Rect(gx + cw + gap,    gy + ch + gap,    cw, ch),
    ]
    dtc_rect = pygame.Rect(gx + gauges_w + gap, top,
                           T.WIDTH - (gx + gauges_w + gap) - 6, body_h)
    return gauge_rects, dtc_rect


# Gauge definitions: (data attr, label, vmin, vmax, unit, fmt, warn, danger)
GAUGE_DEFS = [
    ("rpm",     "RPM",     0,  8000, "rpm",    "{:.0f}", 6000, 7000),
    ("speed",   "SPEED",   0,  160,  "mph",    "{:.0f}", None, None),
    ("coolant", "COOLANT", 40, 130,  "°C", "{:.0f}", 105,  115),
    ("voltage", "BATTERY", 10, 16,   "volts",  "{:.1f}", None, None),
]


def build_background(fonts, gauge_rects, data):
    """Bake everything that never changes into one surface (drawn once)."""
    bg = pygame.Surface((T.WIDTH, T.HEIGHT))
    bg.fill(T.BG)
    W.draw_header_static(bg, fonts)
    W.draw_footer(bg, fonts, data)
    for spec, rect in zip(GAUGE_DEFS, gauge_rects):
        W.draw_gauge_static(bg, fonts, rect, spec[1], spec[4])
    return bg


def build_gauges(gauge_rects):
    """Pre-render the value arcs for each gauge (colors it can display)."""
    gauges = []
    for spec, rect in zip(GAUGE_DEFS, gauge_rects):
        warn, danger = spec[6], spec[7]
        colors = [T.ACCENT]
        if warn is not None or danger is not None:
            colors += [T.AMBER, T.RED]
        gauges.append(W.ArcGauge(rect, colors))
    return gauges


def draw_frame(screen, bg, fonts, src, gauges, gauge_rects, dtc_rect, dtc_cache, num_cache):
    """Per-frame: blit the baked background, then only the live bits."""
    d = src.data
    screen.blit(bg, (0, 0))
    for spec, rect, gauge in zip(GAUGE_DEFS, gauge_rects, gauges):
        value = getattr(d, spec[0])
        gauge.blit(screen, value, spec[2], spec[3], spec[6], spec[7])
        cx, cy, _ = W.gauge_geom(rect)
        num = num_cache.render(spec[5].format(value))
        screen.blit(num, num.get_rect(center=(cx, cy - 2)))
    screen.blit(dtc_cache.get(d.dtcs), dtc_rect.topleft)
    W.draw_header_live(screen, fonts, d, time.strftime("%H:%M"))


def pick_mode(argv):
    """Decide render mode and framebuffer device from args / environment."""
    if "--windowed" in argv or "-w" in argv:
        return "windowed", None
    fb_dev = "/dev/fb1"
    if "--fb" in argv:
        i = argv.index("--fb")
        if i + 1 < len(argv) and not argv[i + 1].startswith("-"):
            fb_dev = argv[i + 1]
        return "fb", fb_dev
    # Auto: use the framebuffer if it exists (i.e. we're on the Pi's TFT).
    if os.path.exists(fb_dev):
        return "fb", fb_dev
    return "fullscreen", None


def main():
    mode, fb_dev = pick_mode(sys.argv)
    pygame.init()
    pygame.font.init()
    screen, fb = make_target(mode, fb_dev)
    fonts = T.Fonts()
    clock = pygame.time.Clock()

    src = DummyDataSource()
    gauge_rects, dtc_rect = layout()
    src.update(0.0)  # populate initial data before baking the background
    background = build_background(fonts, gauge_rects, src.data)
    gauges = build_gauges(gauge_rects)
    dtc_cache = W.DtcPanelCache(fonts, (dtc_rect.w, dtc_rect.h))
    num_cache = W.TextCache(fonts.big, T.TEXT)

    running = True
    while running:
        dt = clock.tick(T.FPS) / 1000.0
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_q):
                running = False

        src.update(dt)
        draw_frame(screen, background, fonts, src, gauges,
                   gauge_rects, dtc_rect, dtc_cache, num_cache)
        if fb is not None:
            fb.present(screen)      # push RGB565 frame to /dev/fb1
        else:
            pygame.display.flip()

    if fb is not None:
        fb.close()
    pygame.quit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pygame.quit()

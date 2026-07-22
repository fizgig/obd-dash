"""Reusable draw helpers: panels, arc gauges, header, footer, DTC list.

Split into *static* pieces (drawn once onto a cached background) and *dynamic*
pieces (redrawn each frame). The Pi Zero can't afford to redraw the whole scene
per frame, so only values/arcs/clock are live; everything else is baked in.
"""
import math
import pygame
import theme as T


def draw_panel(surf, rect, fill=T.PANEL, border=T.STROKE, radius=8):
    pygame.draw.rect(surf, fill, rect, border_radius=radius)
    if border:
        pygame.draw.rect(surf, border, rect, width=1, border_radius=radius)


def draw_arc(surf, center, radius, start_deg, end_deg, color, width, steps_per_deg=1.3):
    """Thick arc drawn as overlapping filled dots (pygame.draw.arc is too thin).

    steps_per_deg is kept modest -- the Pi Zero pays for every circle blit.
    """
    cx, cy = center
    span = end_deg - start_deg
    steps = max(2, int(abs(span) * steps_per_deg))
    r_dot = width // 2
    for i in range(steps + 1):
        a = math.radians(start_deg + span * (i / steps))
        x = cx + radius * math.cos(a)
        y = cy + radius * math.sin(a)
        pygame.draw.circle(surf, color, (int(x), int(y)), r_dot)


# Arc sweep: 135deg (bottom-left) clockwise to 45deg (bottom-right) = 270deg span.
_ARC_START = 135
_ARC_SPAN = 270


def gauge_geom(rect):
    cx = rect.x + rect.w // 2
    cy = rect.y + rect.h // 2 + 6
    radius = min(rect.w, rect.h) // 2 - 16
    return cx, cy, radius


def gauge_color(value, warn, danger):
    if danger is not None and value >= danger:
        return T.RED
    if warn is not None and value >= warn:
        return T.AMBER
    return T.ACCENT


def draw_gauge_static(surf, fonts, rect, label, unit):
    """Baked once: the unfilled track, the label, and the unit caption."""
    cx, cy, radius = gauge_geom(rect)
    draw_arc(surf, (cx, cy), radius, _ARC_START, _ARC_START + _ARC_SPAN, T.TRACK, 7)
    lab = fonts.label.render(label, True, T.MUTED)
    surf.blit(lab, lab.get_rect(center=(cx, rect.y + 12)))
    u = fonts.unit.render(unit, True, T.MUTED)
    surf.blit(u, u.get_rect(center=(cx, cy + 20)))


class ArcGauge:
    """Pre-renders the filled value arc at every level/color once, up front.

    Drawing the arc as hundreds of dots per frame costs ~25 ms *per gauge* on the
    Pi Zero. Instead we bake one surface per (color, level) at startup, so the
    per-frame cost is a single blit. `levels` sets the fill granularity.
    """

    # Transparent key color for fast colorkey blits. Never equals a gauge color.
    _KEY = (255, 0, 255)

    def __init__(self, rect, colors, levels=60, width=7):
        self.rect = rect
        self.levels = levels
        cx, cy, radius = gauge_geom(rect)
        lx, ly = cx - rect.x, cy - rect.y      # center in surface-local coords
        self._frames = {}                       # color -> [levels+1] surfaces
        for color in colors:
            frames = []
            # Colorkey (with RLE) blits are far cheaper on the Pi Zero than
            # per-pixel alpha, and the dots have hard edges so no alpha is lost.
            acc = pygame.Surface((rect.w, rect.h))
            acc.fill(self._KEY)
            acc.set_colorkey(self._KEY, pygame.RLEACCEL)
            prev = _ARC_START
            for k in range(levels + 1):
                end = _ARC_START + _ARC_SPAN * (k / levels)
                if end > prev:
                    draw_arc(acc, (lx, ly), radius, prev, end, color, width)
                    prev = end
                snap = acc.copy()
                snap.set_colorkey(self._KEY, pygame.RLEACCEL)
                frames.append(snap)
            self._frames[color] = frames

    def blit(self, surf, value, vmin, vmax, warn, danger):
        frac = 0.0 if vmax == vmin else (value - vmin) / (vmax - vmin)
        frac = max(0.0, min(1.0, frac))
        color = gauge_color(value, warn, danger)
        idx = int(round(frac * self.levels))
        surf.blit(self._frames[color][idx], self.rect.topleft)


class TextCache:
    """Caches rendered text surfaces so unchanged strings aren't re-rendered."""

    def __init__(self, font, color, max_entries=512):
        self.font = font
        self.color = color
        self.max_entries = max_entries
        self._cache = {}

    def render(self, text):
        surf = self._cache.get(text)
        if surf is None:
            if len(self._cache) >= self.max_entries:
                self._cache.clear()
            surf = self.font.render(text, True, self.color)
            self._cache[text] = surf
        return surf


def draw_header_static(surf, fonts):
    """Baked once: the header bar + title."""
    pygame.draw.rect(surf, T.PANEL, (0, 0, T.WIDTH, T.HEADER_H))
    pygame.draw.line(surf, T.STROKE, (0, T.HEADER_H), (T.WIDTH, T.HEADER_H))
    title = fonts.title.render("PiZero  OBD", True, T.TEXT)
    surf.blit(title, (12, T.HEADER_H // 2 - title.get_height() // 2))


def draw_header_live(surf, fonts, data, clock_str):
    """Live per frame: clock + Bluetooth link pill (drawn over the baked bar)."""
    clk = fonts.clock.render(clock_str, True, T.MUTED)
    surf.blit(clk, (T.WIDTH - clk.get_width() - 12, T.HEADER_H // 2 - clk.get_height() // 2))

    col = T.GREEN if data.connected else T.RED
    label = "BT LINK" if data.connected else "NO LINK"
    txt = fonts.small.render(label, True, col)
    pill_w = txt.get_width() + 30
    pill_x = T.WIDTH - clk.get_width() - 24 - pill_w
    pill = pygame.Rect(pill_x, 7, pill_w, T.HEADER_H - 14)
    pygame.draw.rect(surf, T.PANEL_HI, pill, border_radius=10)
    pygame.draw.circle(surf, col, (pill.x + 12, pill.centery), 4)
    surf.blit(txt, (pill.x + 22, pill.centery - txt.get_height() // 2))


def draw_footer(surf, fonts, data):
    y = T.HEIGHT - T.FOOTER_H
    pygame.draw.rect(surf, T.PANEL, (0, y, T.WIDTH, T.FOOTER_H))
    pygame.draw.line(surf, T.STROKE, (0, y), (T.WIDTH, y))
    left = fonts.small.render(data.vehicle, True, T.MUTED)
    surf.blit(left, (12, y + T.FOOTER_H // 2 - left.get_height() // 2))
    right = fonts.small.render("VIN " + data.vin, True, T.FAINT)
    surf.blit(right, (T.WIDTH - right.get_width() - 12,
                      y + T.FOOTER_H // 2 - right.get_height() // 2))


def render_dtc_panel(fonts, size, dtcs):
    """Render the whole trouble-codes panel to its own surface.

    Called only when the code list changes (see DtcPanelCache), so per-frame
    cost is just one blit.
    """
    surf = pygame.Surface(size)
    surf.fill(T.BG)
    rect = pygame.Rect(0, 0, *size)
    draw_panel(surf, rect)
    pad = 10

    count = len(dtcs)
    head = fonts.h2.render("TROUBLE CODES", True, T.TEXT)
    surf.blit(head, (pad, pad))

    badge_col = T.RED if count else T.GREEN
    btxt = fonts.small.render(str(count), True, T.BG)
    bw = max(20, btxt.get_width() + 12)
    brect = pygame.Rect(rect.right - pad - bw, pad - 1, bw, 18)
    pygame.draw.rect(surf, badge_col, brect, border_radius=9)
    surf.blit(btxt, btxt.get_rect(center=brect.center))

    pygame.draw.line(surf, T.STROKE, (pad, 32), (rect.right - pad, 32))

    if not dtcs:
        ok = fonts.desc.render("No faults stored", True, T.MUTED)
        surf.blit(ok, (pad, 44))
        return surf

    row_h = 40
    y = 40
    for dtc in dtcs:
        if y + row_h > rect.bottom - 6:
            surf.blit(fonts.small.render("+ more", True, T.FAINT), (pad, y + 2))
            break
        col = T.SEVERITY_COLORS.get(dtc.severity, T.MUTED)
        pygame.draw.rect(surf, col, (pad, y + 4, 3, row_h - 12), border_radius=2)
        surf.blit(fonts.code.render(dtc.code, True, T.TEXT), (pad + 12, y + 2))
        sev = fonts.small.render(dtc.severity.upper(), True, col)
        surf.blit(sev, (rect.right - pad - sev.get_width(), y + 5))
        desc = _truncate(dtc.desc, fonts.desc, rect.w - 2 * pad - 12)
        surf.blit(fonts.desc.render(desc, True, T.MUTED), (pad + 12, y + 21))
        y += row_h
    return surf


class DtcPanelCache:
    """Re-renders the DTC panel surface only when the code list changes."""

    def __init__(self, fonts, size):
        self.fonts = fonts
        self.size = size
        self._sig = None
        self._surf = None

    def get(self, dtcs):
        sig = tuple((d.code, d.severity) for d in dtcs)
        if sig != self._sig:
            self._sig = sig
            self._surf = render_dtc_panel(self.fonts, self.size, dtcs)
        return self._surf


def _truncate(text, font, max_w):
    if font.size(text)[0] <= max_w:
        return text
    while text and font.size(text + "...")[0] > max_w:
        text = text[:-1]
    return text + "..."

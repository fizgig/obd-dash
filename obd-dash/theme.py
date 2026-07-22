"""Visual theme: colors, fonts, and screen geometry for the OBD dashboard.

Tuned for the goodtft 3.5" TFT (480x320, landscape).
"""
import os
import pygame

# --- Screen geometry ---------------------------------------------------------
WIDTH, HEIGHT = 480, 320
HEADER_H = 34
FOOTER_H = 22
FPS = 10  # the Pi Zero is weak; 10 fps keeps CPU low and gauges smooth enough

# --- Palette (dark automotive) ----------------------------------------------
BG        = (14, 17, 22)     # app background
PANEL     = (22, 27, 34)     # card / panel fill
PANEL_HI  = (30, 37, 46)     # panel highlight / row hover
STROKE    = (44, 52, 63)     # hairline borders
TRACK     = (38, 45, 55)     # gauge track (unfilled arc)

TEXT      = (230, 237, 243)  # primary text
MUTED     = (139, 148, 158)  # secondary text
FAINT     = (88, 96, 105)    # tertiary text

ACCENT    = (34, 211, 238)   # cyan  - primary accent / nominal
GREEN     = (34, 197, 94)    # ok
AMBER     = (245, 158, 11)   # warning
RED       = (239, 68, 68)    # danger / active fault
PURPLE    = (167, 139, 250)  # info

# Severity -> color for diagnostic trouble codes
SEVERITY_COLORS = {
    "critical": RED,
    "warning":  AMBER,
    "info":     ACCENT,
    "pending":  PURPLE,
}


def _load_font(size, bold=False):
    """Prefer bundled DejaVu (present on Raspberry Pi OS); fall back to default."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else ""),
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono%s.ttf" % ("-Bold" if bold else ""),
    ]
    for path in candidates:
        if os.path.exists(path):
            return pygame.font.Font(path, size)
    # Cross-platform fallback (works when testing on a desktop)
    return pygame.font.SysFont("dejavusans,arial", size, bold=bold)


class Fonts:
    """Lazily-built font set (pygame.font must be initialised first)."""

    def __init__(self):
        self.title   = _load_font(18, bold=True)
        self.h2      = _load_font(13, bold=True)
        self.big     = _load_font(30, bold=True)   # gauge value
        self.unit    = _load_font(11)
        self.label   = _load_font(11, bold=True)
        self.code    = _load_font(17, bold=True)   # DTC code
        self.desc    = _load_font(11)
        self.small   = _load_font(11)
        self.clock   = _load_font(14, bold=True)

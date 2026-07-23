"""Custom-painted widgets for the Qt OBD dashboard.

`ArcGauge` is a hand-painted gauge. It is designed to be used as a **promoted
widget** in Qt Designer: drop a plain ``QWidget`` onto the form, then "Promote
to..." with class ``ArcGauge`` and header ``gauge.h`` (or just ``gauge``). At
load time ``main.py`` registers this class with the ``QUiLoader`` so the
placeholders become live gauges.

It renders in one of three **modes**, which is how the themes get different
looks and feels:

    "arc"    a 270-degree filled arc          (slate, neon, nord)
    "ticks"  a ring of tick marks             (amber -- instrument cluster)
    "bar"    a big number + horizontal meter  (mono -- minimalist)

Nothing here depends on the data model -- the app pushes values in with
``set_value()`` and the widget repaints itself.
"""
from __future__ import annotations

import math

from PySide6.QtCore import Qt, QRectF, QPointF, QSize
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QBrush
from PySide6.QtWidgets import QWidget


# The dial sweeps 270 degrees: from 135 deg (lower-left) clockwise to 405 deg
# (lower-right), leaving the gap at the bottom. Angles below are in screen space
# (y points down), used directly with cos/sin.
_START_DEG = 135
_SPAN_DEG = 270


class Palette:
    """A small colour bundle the app hands to every gauge for the active theme."""

    def __init__(self, track, accent, amber, red, text, muted):
        self.track = QColor(track)
        self.accent = QColor(accent)
        self.amber = QColor(amber)
        self.red = QColor(red)
        self.text = QColor(text)
        self.muted = QColor(muted)


class ArcGauge(QWidget):
    """A themed gauge with a big centred value, label and unit."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Sensible defaults so the widget still previews inside Qt Designer.
        self._label = "RPM"
        self._unit = "rpm"
        self._fmt = "{:.0f}"
        self._vmin, self._vmax = 0.0, 8000.0
        self._value = 0.0
        self._warn = None
        self._danger = None
        self._mode = "arc"
        self._pal = Palette("#263137", "#22d3ee", "#f59e0b",
                            "#ef4444", "#e6edf3", "#8b949e")
        self.setMinimumSize(112, 108)

    # -- configuration ------------------------------------------------------
    def configure(self, label, unit, vmin, vmax, fmt="{:.0f}",
                  warn=None, danger=None):
        self._label, self._unit, self._fmt = label, unit, fmt
        self._vmin, self._vmax = float(vmin), float(vmax)
        self._warn, self._danger = warn, danger
        self.update()

    def set_palette(self, pal: Palette):
        self._pal = pal
        self.update()

    def set_mode(self, mode: str):
        self._mode = mode if mode in ("arc", "ticks", "bar") else "arc"
        self.update()

    def set_value(self, value: float):
        if value != self._value:
            self._value = float(value)
            self.update()

    def sizeHint(self) -> QSize:
        return QSize(128, 120)

    # -- helpers ------------------------------------------------------------
    def _value_color(self) -> QColor:
        if self._danger is not None and self._value >= self._danger:
            return self._pal.red
        if self._warn is not None and self._value >= self._warn:
            return self._pal.amber
        return self._pal.accent

    def _frac(self) -> float:
        span = self._vmax - self._vmin
        if span == 0:
            return 0.0
        return max(0.0, min(1.0, (self._value - self._vmin) / span))

    # -- painting -----------------------------------------------------------
    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        if self._mode == "bar":
            self._paint_bar(p)
        elif self._mode == "ticks":
            self._paint_ticks(p)
        else:
            self._paint_arc(p)
        p.end()

    def _draw_label(self, p, cx, top_y, side):
        f = QFont(self.font())
        f.setPointSize(max(7, side // 15))
        f.setBold(True)
        p.setFont(f)
        p.setPen(self._pal.muted)
        p.drawText(QRectF(0, top_y, self.width(), 16),
                   Qt.AlignHCenter | Qt.AlignTop, self._label)

    def _draw_value(self, p, rect, side, big=True):
        f = QFont(self.font())
        f.setPointSize(max(13, side // (4 if big else 6)))
        f.setBold(True)
        p.setFont(f)
        p.setPen(self._pal.text)
        p.drawText(rect, Qt.AlignCenter, self._fmt.format(self._value))

    def _paint_arc(self, p):
        side = min(self.width(), self.height() - 6)
        stroke = max(6, side // 14)
        pad = stroke // 2 + 4
        cx = self.width() / 2
        cy = self.height() / 2 + 4
        r = side / 2 - pad
        arc_rect = QRectF(cx - r, cy - r, 2 * r, 2 * r)

        # Qt drawArc uses 1/16 deg, CCW from 3 o'clock, so negate our CW sweep.
        pen = QPen(self._pal.track, stroke, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        p.drawArc(arc_rect, -_START_DEG * 16, -_SPAN_DEG * 16)
        frac = self._frac()
        if frac > 0:
            pen.setColor(self._value_color())
            p.setPen(pen)
            p.drawArc(arc_rect, -_START_DEG * 16, int(-_SPAN_DEG * frac) * 16)

        self._draw_label(p, cx, cy - r - 2, side)
        self._draw_value(p, QRectF(0, cy - r + 6, self.width(), 2 * r - 12), side)
        f = QFont(self.font())
        f.setPointSize(max(7, side // 16))
        p.setFont(f)
        p.setPen(self._pal.muted)
        p.drawText(QRectF(0, cy + r * 0.28, self.width(), 16),
                   Qt.AlignHCenter | Qt.AlignTop, self._unit)

    def _paint_ticks(self, p):
        side = min(self.width(), self.height() - 6)
        cx = self.width() / 2
        cy = self.height() / 2 + 4
        r = side / 2 - 8
        n = 34
        frac = self._frac()
        lit_color = self._value_color()
        tick_len = max(6, side // 12)
        for i in range(n):
            a = math.radians(_START_DEG + _SPAN_DEG * (i / (n - 1)))
            ca, sa = math.cos(a), math.sin(a)
            outer = QPointF(cx + r * ca, cy + r * sa)
            inner = QPointF(cx + (r - tick_len) * ca, cy + (r - tick_len) * sa)
            lit = (i / (n - 1)) <= frac
            pen = QPen(lit_color if lit else self._pal.track, 3, Qt.SolidLine, Qt.RoundCap)
            p.setPen(pen)
            p.drawLine(inner, outer)

        self._draw_label(p, cx, cy - r + tick_len, side)
        self._draw_value(p, QRectF(0, cy - r * 0.35, self.width(), r * 0.7), side)
        f = QFont(self.font())
        f.setPointSize(max(7, side // 16))
        p.setFont(f)
        p.setPen(self._pal.muted)
        p.drawText(QRectF(0, cy + r * 0.3, self.width(), 16),
                   Qt.AlignHCenter | Qt.AlignTop, self._unit)

    def _paint_bar(self, p):
        w, h = self.width(), self.height()
        side = min(w, h)
        pad = 14

        # Label (top-left).
        f = QFont(self.font())
        f.setPointSize(max(8, side // 12))
        f.setBold(True)
        p.setFont(f)
        p.setPen(self._pal.muted)
        p.drawText(QRectF(pad, 8, w - 2 * pad, 18),
                   Qt.AlignLeft | Qt.AlignTop, self._label)

        # Big value (left) + unit.
        f.setPointSize(max(20, side // 4))
        p.setFont(f)
        p.setPen(self._pal.text)
        p.drawText(QRectF(pad, 20, w - 2 * pad, h - 56),
                   Qt.AlignLeft | Qt.AlignVCenter, self._fmt.format(self._value))
        f.setBold(False)
        f.setPointSize(max(8, side // 14))
        p.setFont(f)
        p.setPen(self._pal.muted)
        p.drawText(QRectF(pad, 20, w - 2 * pad, h - 56),
                   Qt.AlignRight | Qt.AlignVCenter, self._unit)

        # Horizontal meter along the bottom.
        bar_h = max(7, side // 14)
        bar_y = h - pad - bar_h
        track = QRectF(pad, bar_y, w - 2 * pad, bar_h)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(self._pal.track))
        p.drawRoundedRect(track, bar_h / 2, bar_h / 2)
        fw = (w - 2 * pad) * self._frac()
        if fw > 0:
            p.setBrush(QBrush(self._value_color()))
            p.drawRoundedRect(QRectF(pad, bar_y, max(bar_h, fw), bar_h),
                              bar_h / 2, bar_h / 2)

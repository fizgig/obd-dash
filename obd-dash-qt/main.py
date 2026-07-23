#!/usr/bin/env python3
"""PiZero OBD dashboard -- Qt / Qt Designer edition.

The layout lives in `dashboard.ui` (editable in Qt Designer). The four gauges
are promoted ``ArcGauge`` widgets (see gauge.py). This file loads the form with
``QUiLoader``, applies one of two design themes, and drives it from the shared
``DummyDataSource`` on a 10 fps ``QTimer``.

    python main.py                     # windowed, "slate" theme (desktop preview)
    python main.py --theme amber       # a different design (slate|neon|amber|mono|nord)
    python main.py --fullscreen        # borderless fullscreen (e.g. the Pi TFT)

Edit the design:  open dashboard.ui in Qt Designer  (`pyside6-designer`).

Keys:  ESC / Q  quit.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QFile
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QVBoxLayout,
                               QHBoxLayout, QWidget)
from PySide6.QtUiTools import QUiLoader

from gauge import ArcGauge
from datasource import DummyDataSource
from themes import THEMES

HERE = Path(__file__).resolve().parent
UI_FILE = HERE / "dashboard.ui"
FPS = 10

# (gauge objectName, data attr, label, vmin, vmax, unit, fmt, warn, danger)
GAUGES = [
    ("gaugeRpm",     "rpm",     "RPM",     0,  8000, "rpm",   "{:.0f}", 6000, 7000),
    ("gaugeSpeed",   "speed",   "SPEED",   0,  160,  "mph",   "{:.0f}", None, None),
    ("gaugeCoolant", "coolant", "COOLANT", 40, 130,  "°C", "{:.0f}", 105, 115),
    ("gaugeVoltage", "voltage", "BATTERY", 10, 16,   "volts", "{:.1f}", None, None),
]


def load_ui() -> QWidget:
    """Load dashboard.ui, registering the promoted ArcGauge widget first."""
    loader = QUiLoader()
    loader.registerCustomWidget(ArcGauge)
    f = QFile(str(UI_FILE))
    f.open(QFile.ReadOnly)
    try:
        window = loader.load(f)
    finally:
        f.close()
    if window is None:
        raise RuntimeError(f"Failed to load {UI_FILE}:\n{loader.errorString()}")
    return window


def make_dtc_row(dtc, theme) -> QFrame:
    """Build one styled trouble-code row (code + description + severity chip)."""
    color = theme["severity"].get(dtc.severity, theme["muted"])
    row = QFrame()
    row.setStyleSheet(
        f"background:{theme['row_bg']}; border-radius:6px;"
        f"border-left:3px solid {color};"
    )
    outer = QVBoxLayout(row)
    outer.setContentsMargins(8, 5, 8, 6)
    outer.setSpacing(1)

    top = QHBoxLayout()
    top.setContentsMargins(0, 0, 0, 0)
    code = QLabel(dtc.code)
    code.setStyleSheet(f"color:{theme['text']}; font-size:14px; font-weight:700;")
    sev = QLabel(dtc.severity.upper())
    sev.setStyleSheet(f"color:{color}; font-size:9px; font-weight:700;")
    top.addWidget(code)
    top.addStretch(1)
    top.addWidget(sev)

    desc = QLabel(dtc.desc)
    desc.setStyleSheet(f"color:{theme['muted']}; font-size:10px;")
    desc.setWordWrap(True)

    outer.addLayout(top)
    outer.addWidget(desc)
    return row


class Dashboard:
    """Wires the loaded .ui form to live data."""

    def __init__(self, window: QWidget, theme: dict):
        self.win = window
        self.theme = theme
        self.src = DummyDataSource()
        self.src.update(0.0)

        # Configure the four promoted gauges from the spec table.
        self.gauges = []
        for name, attr, label, vmin, vmax, unit, fmt, warn, danger in GAUGES:
            g: ArcGauge = window.findChild(ArcGauge, name)
            g.configure(label, unit, vmin, vmax, fmt, warn, danger)
            g.set_palette(theme["palette"])
            g.set_mode(theme.get("mode", "arc"))
            self.gauges.append((g, attr))

        self.dtc_layout: QVBoxLayout = window.findChild(QWidget, "dtcContainer").layout()
        self.dtc_badge: QLabel = window.findChild(QLabel, "dtcBadge")
        self.link_pill: QLabel = window.findChild(QLabel, "linkPill")
        self.clock: QLabel = window.findChild(QLabel, "clock")
        self.vehicle: QLabel = window.findChild(QLabel, "vehicle")
        self.vin: QLabel = window.findChild(QLabel, "vin")

        self.vehicle.setText(self.src.data.vehicle)
        self.vin.setText("VIN " + self.src.data.vin)
        self._dtc_sig = None

        self.timer = QTimer(window)
        self.timer.timeout.connect(self.tick)
        self.timer.start(int(1000 / FPS))

    def tick(self):
        self.src.update(1.0 / FPS)
        d = self.src.data
        for g, attr in self.gauges:
            g.set_value(getattr(d, attr))

        self.clock.setText(time.strftime("%H:%M"))
        self.link_pill.setText(" BT LINK " if d.connected else " NO LINK ")

        sig = tuple((x.code, x.severity) for x in d.dtcs)
        if sig != self._dtc_sig:
            self._dtc_sig = sig
            self._rebuild_dtcs(d.dtcs)

    def _rebuild_dtcs(self, dtcs):
        self.dtc_badge.setText(f" {len(dtcs)} ")
        badge_col = self.theme["severity"]["critical"] if dtcs else "#22c55e"
        self.dtc_badge.setStyleSheet(
            f"color:#0e1116; background:{badge_col}; border-radius:9px;"
            f"min-width:18px; padding:1px 4px; font-size:11px; font-weight:700;"
        )
        # Clear existing rows (keep the trailing stretch spacer, item 0-based last).
        while self.dtc_layout.count() > 1:
            item = self.dtc_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        if not dtcs:
            empty = QLabel("No faults stored")
            empty.setStyleSheet(f"color:{self.theme['muted']}; font-size:11px;")
            self.dtc_layout.insertWidget(0, empty)
            return
        for i, dtc in enumerate(dtcs):
            self.dtc_layout.insertWidget(i, make_dtc_row(dtc, self.theme))


def main():
    argv = sys.argv
    theme_name = "slate"
    if "--theme" in argv:
        i = argv.index("--theme")
        if i + 1 < len(argv):
            theme_name = argv[i + 1]
    theme = THEMES.get(theme_name, THEMES["slate"])

    app = QApplication(argv)
    window = load_ui()
    window.setStyleSheet(theme["qss"])

    # Attach to the window so it isn't garbage-collected.
    window._dashboard = Dashboard(window, theme)

    for seq in ("Escape", "Q"):
        QShortcut(QKeySequence(seq), window, activated=app.quit)

    if "--fullscreen" in argv:
        window.showFullScreen()
    else:
        window.setFixedSize(480, 320)
        window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

"""Design options for the Qt dashboard.

Each theme is a bundle of: a QSS stylesheet (targets the object names in
``dashboard.ui`` -- ``#header``, ``#dtcPanel`` ...), a gauge ``Palette``, a
gauge ``mode`` ("arc" | "ticks" | "bar", see gauge.py), and the colours used to
build the trouble-code rows in code. Switch at launch with ``--theme <name>``.

    slate   calm dark automotive, cyan filled arcs (matches the pygame original)
    neon    high-contrast night look, magenta/cyan glow, filled arcs
    amber    retro instrument cluster, warm amber tick-ring gauges
    mono    minimalist greyscale, big numbers + hairline bar meters
    nord    cool "nord" blues, filled arcs
"""
from gauge import Palette


def _theme(qss, palette, mode, row_bg, severity, text, muted):
    return {"qss": qss, "palette": palette, "mode": mode, "row_bg": row_bg,
            "severity": severity, "text": text, "muted": muted}


# --- 1. Slate ---------------------------------------------------------------
SLATE_QSS = """
#Dashboard { background: #0e1116; }
#header, #footer { background: #161b22; border: none; }
#header { border-bottom: 1px solid #2c343f; }
#footer { border-top: 1px solid #2c343f; }
#title { color: #e6edf3; font-size: 15px; font-weight: 700; }
#clock { color: #8b949e; font-size: 12px; font-weight: 700; }
#linkPill { color: #22c55e; background: #1e252e; border-radius: 10px; padding: 2px 10px; font-size: 10px; font-weight: 700; }
#vehicle { color: #8b949e; font-size: 10px; }
#vin { color: #586069; font-size: 10px; }
#dtcPanel { background: #161b22; border: 1px solid #2c343f; border-radius: 8px; }
#dtcTitle { color: #e6edf3; font-size: 12px; font-weight: 700; }
#dtcBadge { color: #0e1116; background: #22c55e; border-radius: 9px; min-width: 18px; padding: 1px 4px; font-size: 11px; font-weight: 700; }
#dtcRule { color: #2c343f; }
QScrollArea, #dtcContainer { background: transparent; border: none; }
"""

# --- 2. Neon ----------------------------------------------------------------
NEON_QSS = """
#Dashboard { background: #05070d; }
#header, #footer { background: #0b0f1a; border: none; }
#header { border-bottom: 1px solid #1b2440; }
#footer { border-top: 1px solid #1b2440; }
#title { color: #e879f9; font-size: 15px; font-weight: 700; letter-spacing: 1px; }
#clock { color: #67e8f9; font-size: 12px; font-weight: 700; }
#linkPill { color: #05070d; background: #22d3ee; border-radius: 10px; padding: 2px 10px; font-size: 10px; font-weight: 700; }
#vehicle { color: #7dd3fc; font-size: 10px; }
#vin { color: #475569; font-size: 10px; }
#dtcPanel { background: #0b0f1a; border: 1px solid #1b2440; border-radius: 8px; }
#dtcTitle { color: #e879f9; font-size: 12px; font-weight: 700; letter-spacing: 1px; }
#dtcBadge { color: #05070d; background: #f472b6; border-radius: 9px; min-width: 18px; padding: 1px 4px; font-size: 11px; font-weight: 700; }
#dtcRule { color: #1b2440; }
QScrollArea, #dtcContainer { background: transparent; border: none; }
"""

# --- 3. Amber (retro cluster) -----------------------------------------------
AMBER_QSS = """
#Dashboard { background: #14100a; }
#header, #footer { background: #1e1710; border: none; }
#header { border-bottom: 1px solid #3a2c12; }
#footer { border-top: 1px solid #3a2c12; }
#title { color: #f59e0b; font-size: 15px; font-weight: 700; letter-spacing: 2px; }
#clock { color: #b08040; font-size: 12px; font-weight: 700; }
#linkPill { color: #14100a; background: #f59e0b; border-radius: 10px; padding: 2px 10px; font-size: 10px; font-weight: 700; }
#vehicle { color: #b08040; font-size: 10px; }
#vin { color: #7a5a28; font-size: 10px; }
#dtcPanel { background: #1e1710; border: 1px solid #3a2c12; border-radius: 8px; }
#dtcTitle { color: #f59e0b; font-size: 12px; font-weight: 700; letter-spacing: 1px; }
#dtcBadge { color: #14100a; background: #f59e0b; border-radius: 9px; min-width: 18px; padding: 1px 4px; font-size: 11px; font-weight: 700; }
#dtcRule { color: #3a2c12; }
QScrollArea, #dtcContainer { background: transparent; border: none; }
"""

# --- 4. Mono (minimalist greyscale) -----------------------------------------
MONO_QSS = """
#Dashboard { background: #0d0d0f; }
#header, #footer { background: #131317; border: none; }
#header { border-bottom: 1px solid #2a2a30; }
#footer { border-top: 1px solid #2a2a30; }
#title { color: #f0f0f2; font-size: 15px; font-weight: 700; letter-spacing: 3px; }
#clock { color: #8a8a92; font-size: 12px; font-weight: 700; }
#linkPill { color: #0d0d0f; background: #e5e5ea; border-radius: 10px; padding: 2px 10px; font-size: 10px; font-weight: 700; }
#vehicle { color: #8a8a92; font-size: 10px; }
#vin { color: #55555c; font-size: 10px; }
#dtcPanel { background: #131317; border: 1px solid #2a2a30; border-radius: 8px; }
#dtcTitle { color: #f0f0f2; font-size: 12px; font-weight: 700; letter-spacing: 1px; }
#dtcBadge { color: #0d0d0f; background: #e5e5ea; border-radius: 9px; min-width: 18px; padding: 1px 4px; font-size: 11px; font-weight: 700; }
#dtcRule { color: #2a2a30; }
QScrollArea, #dtcContainer { background: transparent; border: none; }
"""

# --- 5. Nord (cool blues) ---------------------------------------------------
NORD_QSS = """
#Dashboard { background: #2e3440; }
#header, #footer { background: #3b4252; border: none; }
#header { border-bottom: 1px solid #4c566a; }
#footer { border-top: 1px solid #4c566a; }
#title { color: #eceff4; font-size: 15px; font-weight: 700; }
#clock { color: #9aa5b8; font-size: 12px; font-weight: 700; }
#linkPill { color: #2e3440; background: #a3be8c; border-radius: 10px; padding: 2px 10px; font-size: 10px; font-weight: 700; }
#vehicle { color: #9aa5b8; font-size: 10px; }
#vin { color: #6a748a; font-size: 10px; }
#dtcPanel { background: #3b4252; border: 1px solid #4c566a; border-radius: 8px; }
#dtcTitle { color: #eceff4; font-size: 12px; font-weight: 700; }
#dtcBadge { color: #2e3440; background: #a3be8c; border-radius: 9px; min-width: 18px; padding: 1px 4px; font-size: 11px; font-weight: 700; }
#dtcRule { color: #4c566a; }
QScrollArea, #dtcContainer { background: transparent; border: none; }
"""


THEMES = {
    "slate": _theme(
        SLATE_QSS, Palette("#263137", "#22d3ee", "#f59e0b", "#ef4444", "#e6edf3", "#8b949e"),
        "arc", "#1e252e",
        {"critical": "#ef4444", "warning": "#f59e0b", "info": "#22d3ee", "pending": "#a78bfa"},
        "#e6edf3", "#8b949e"),
    "neon": _theme(
        NEON_QSS, Palette("#1b2440", "#22d3ee", "#fbbf24", "#fb7185", "#f5f3ff", "#7dd3fc"),
        "arc", "#111827",
        {"critical": "#fb7185", "warning": "#fbbf24", "info": "#22d3ee", "pending": "#e879f9"},
        "#f0abfc", "#7dd3fc"),
    "amber": _theme(
        AMBER_QSS, Palette("#3a2c12", "#f59e0b", "#f97316", "#ef4444", "#ffcf8a", "#b08040"),
        "ticks", "#241a0d",
        {"critical": "#ef4444", "warning": "#f97316", "info": "#f59e0b", "pending": "#fbbf24"},
        "#ffcf8a", "#b08040"),
    "mono": _theme(
        MONO_QSS, Palette("#2a2a30", "#e5e5ea", "#c9c9cf", "#ff5a5a", "#f0f0f2", "#8a8a92"),
        "bar", "#1c1c22",
        {"critical": "#ff5a5a", "warning": "#c9c9cf", "info": "#e5e5ea", "pending": "#9a9aa2"},
        "#f0f0f2", "#8a8a92"),
    "nord": _theme(
        NORD_QSS, Palette("#434c5e", "#88c0d0", "#ebcb8b", "#bf616a", "#eceff4", "#9aa5b8"),
        "arc", "#434c5e",
        {"critical": "#bf616a", "warning": "#ebcb8b", "info": "#88c0d0", "pending": "#b48ead"},
        "#eceff4", "#9aa5b8"),
}

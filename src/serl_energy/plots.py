"""Shared figure theme, read from design/tokens.json (the same file the dashboard uses).

Call `use_theme()` once at the top of a notebook. Colours have fixed meanings
across the project, so look them up by role rather than picking hexes:

    COLORS["electricity"], COLORS["gas"], COLORS["agile"], COLORS["flat_tariff"],
    COLORS["vulnerable"], COLORS["comparator"], YEAR_COLORS[2023], CATEGORICAL[i]

Rules the theme follows (validated with the dataviz palette checker):
- categorical colours are used in fixed order, never cycled past eight;
- sequential = one hue light to dark (`SEQUENTIAL_CMAP`), diverging = blue / grey / red (`DIVERGING_CMAP`);
- status colours are reserved for good / warning / serious / critical states;
- one y-axis per chart; text stays in ink colours, not series colours.
"""
from __future__ import annotations

import json
from typing import Iterable, Sequence

import matplotlib as mpl
import numpy as np
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap

from .config import DESIGN_FONTS_DIR, DESIGN_TOKENS

TOKENS = json.loads(DESIGN_TOKENS.read_text())

# filled in by use_theme(); kept as the same objects so imported names stay valid
COLORS: dict[str, str] = {}
INK: dict[str, str] = {}
CATEGORICAL: list[str] = []
YEAR_COLORS: dict[int, str] = {}
SEQUENTIAL = [TOKENS["sequential_blue"][k] for k in sorted(TOKENS["sequential_blue"], key=int)]
SEQUENTIAL_CMAP = LinearSegmentedColormap.from_list("serl_sequential", SEQUENTIAL)
DIVERGING_CMAP: LinearSegmentedColormap | None = None
ROLE_COLORS: dict[str, str] = {}

# Inter ships in design/fonts (SIL Open Font Licence) so figures match the dashboard on any machine;
# DejaVu Sans fills the few symbols Inter lacks
for _ttf in sorted(DESIGN_FONTS_DIR.glob("*.ttf")):
    font_manager.fontManager.addfont(str(_ttf))
_AVAILABLE = {f.name for f in font_manager.fontManager.ttflist}
FONT = [f for f in TOKENS["font"]["family"] if f in _AVAILABLE] + ["DejaVu Sans"]
TITLE_WEIGHT = "semibold"


def _load(mode: str) -> None:
    """Fill the colour lookups for `mode` ("light" or "dark") without touching matplotlib."""
    global DIVERGING_CMAP
    m = TOKENS[mode]
    CATEGORICAL[:] = m["categorical"]
    INK.clear()
    INK.update(m["ink"])
    COLORS.clear()
    for role, slot in TOKENS["semantic"].items():
        if role.startswith("$"):
            continue
        COLORS[role] = INK["muted"] if slot == "muted" else CATEGORICAL[slot - 1]
    COLORS.update(surface=m["surface"], page=m["page"], grid=m["grid"], axis=m["axis"])
    YEAR_COLORS.clear()
    YEAR_COLORS.update({int(y): c for y, c in TOKENS["ordinal_years"][mode].items()})
    ROLE_COLORS.clear()
    ROLE_COLORS.update(vulnerable=COLORS["vulnerable"], comparator=COLORS["comparator"], other=m["axis"])
    d = TOKENS["diverging"]
    DIVERGING_CMAP = LinearSegmentedColormap.from_list(
        "serl_diverging", [d["negative"], d["neutral_light" if mode == "light" else "neutral_dark"], d["positive"]])


def use_theme(mode: str = "light") -> None:
    """Apply the project theme to matplotlib (and seaborn, which reads rcParams)."""
    _load(mode)
    m = TOKENS[mode]
    mpl.rcParams.update({
        "font.family": FONT, "font.size": 10,
        "axes.titlesize": 12, "axes.titleweight": TITLE_WEIGHT, "axes.titlelocation": "left", "axes.titlepad": 10,
        "axes.labelsize": 10, "axes.labelcolor": INK["secondary"], "text.color": INK["primary"],
        "xtick.color": INK["muted"], "ytick.color": INK["muted"], "xtick.labelcolor": INK["secondary"],
        "ytick.labelcolor": INK["secondary"], "xtick.labelsize": 9, "ytick.labelsize": 9,
        "axes.edgecolor": m["axis"], "axes.linewidth": 0.8, "axes.facecolor": m["surface"],
        "figure.facecolor": m["page"], "savefig.facecolor": m["page"],
        "axes.grid": True, "grid.color": m["grid"], "grid.linewidth": 0.8, "axes.axisbelow": True,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.prop_cycle": mpl.cycler(color=CATEGORICAL),
        "lines.linewidth": 2, "lines.markersize": 6, "patch.edgecolor": m["surface"],
        "legend.frameon": False, "legend.fontsize": 9, "legend.title_fontsize": 9,
        "figure.dpi": 110, "savefig.dpi": 300, "savefig.bbox": "tight",
        "figure.titlesize": 14, "figure.titleweight": TITLE_WEIGHT,
        "image.cmap": "serl_sequential", "axes.unicode_minus": True,
    })
    for cmap in (SEQUENTIAL_CMAP, DIVERGING_CMAP):
        if cmap.name in mpl.colormaps:
            mpl.colormaps.unregister(cmap.name)
        mpl.colormaps.register(cmap)


def title(ax, text: str, subtitle: str | None = None) -> None:
    """Left-aligned bold title with an optional muted subtitle that says what to look for."""
    if subtitle:
        ax.set_title(subtitle, loc="left", fontsize=9.5, fontweight="normal", color=INK["secondary"], pad=6)
        ax.annotate(text, xy=(0, 1), xycoords="axes fraction", xytext=(0, 22), textcoords="offset points",
                    fontsize=12, fontweight=TITLE_WEIGHT, color=INK["primary"], va="bottom", ha="left")
    else:
        ax.set_title(text, loc="left")


def figure_title(fig, text: str, subtitle: str | None = None) -> None:
    """Left-aligned title (and subtitle) for a multi-panel figure; call it last, it also lays out the panels.

    Space is reserved in inches, so the gap under the title is the same for short and tall figures.
    """
    height = fig.get_figheight()
    fig.text(0.01, 1 - 0.10 / height, text, ha="left", va="top", fontsize=14, fontweight=TITLE_WEIGHT,
             color=INK["primary"])
    if subtitle:
        fig.text(0.01, 1 - 0.42 / height, subtitle, ha="left", va="top", fontsize=10, color=INK["secondary"])
    fig.tight_layout(rect=(0, 0, 1, 1 - (0.75 if subtitle else 0.45) / height))


def label_line_ends(ax, series: Sequence[tuple[str, Sequence[float], str]], x_end: float,
                    min_gap: float = 0.045) -> None:
    """Direct labels at the right end of lines, nudged apart so they do not overlap.

    `series` is a list of (label, y values, colour). The text stays in ink colour;
    a dot in the series colour carries identity. `min_gap` is a fraction of the y-range.
    """
    lo, hi = ax.get_ylim()
    gap = (hi - lo) * min_gap
    ends = sorted(((float(np.asarray(y)[-1]), label, color) for label, y, color in series), key=lambda t: t[0])
    placed: list[float] = []
    for y, _, _ in ends:
        placed.append(max(y, placed[-1] + gap) if placed else y)
    for (y, label, color), y_text in zip(ends, placed):
        ax.annotate("●", xy=(x_end, y), xytext=(5, 0), textcoords="offset points", va="center", ha="left",
                    fontsize=7, color=color, annotation_clip=False)
        ax.annotate(label, xy=(x_end, y_text), xytext=(14, 0), textcoords="offset points", va="center",
                    ha="left", fontsize=9, color=INK["secondary"], annotation_clip=False)


def half_hour_axis(ax, step_hours: int = 3) -> None:
    """X axis for 48 half-hour slots (0 = 00:00), labelled every `step_hours`."""
    ax.set_xlim(0, 47)
    ax.set_xticks(range(0, 48, 2 * step_hours), [f"{h:02d}:00" for h in range(0, 24, step_hours)])


def year_axis(ax, fmt: str = "%Y") -> None:
    """Date x axis with one tick per year (avoids crowded month labels on small panels)."""
    import matplotlib.dates as mdates
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter(fmt))


def month_axis(ax, months: Iterable[int] = range(1, 13)) -> None:
    """X axis of calendar months 1–12 with short names."""
    names = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    months = list(months)
    ax.set_xticks(months, [names[m - 1] for m in months])


def bar_labels(ax, bars, fmt: str = "{:.1f}", **kwargs) -> None:
    """Value labels on bars in ink colour (use selectively: only where the exact number matters)."""
    ax.bar_label(bars, fmt=fmt, padding=3, fontsize=8.5, color=INK["secondary"], **kwargs)


_load("light")

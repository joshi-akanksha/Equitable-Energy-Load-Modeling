"""Save figures and results tables with consistent names and locations.

    reporter = Reporter("1.1-eda-univariate")
    reporter.save_fig(fig, "daily-profile-by-year")    # reports/figures/1.1-eda-univariate/daily-profile-by-year.png + .svg
    reporter.save_table(df, "covariate_gradients_2023") # reports/tables/1.1-eda-univariate/covariate_gradients_2023.csv

Naming rules (checked here so they cannot drift): figure names are kebab-case,
table names and every column / index name are snake_case starting with a
letter, so tables load cleanly into code and the dashboard. Readable labels belong on charts only.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .config import FIGURES_DIR, TABLES_DIR

_KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_SYMBOLS = {"%": " pct ", "£": " gbp ", "→": " to ", "–": " to ", "/": " per ", "²": "2", "+": " plus ", "−": " minus "}
_SNAKE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")      # leading letter: safe as a JS / pandas attribute
_NOTEBOOK = re.compile(r"^\d+\.\d+-[a-z0-9-]+$")


def to_snake_case(name) -> str:
    """Machine-readable column name from a readable one, e.g. 'Agile saving %' -> 'agile_saving_pct'."""
    text = str(name)
    for symbol, word in _SYMBOLS.items():
        text = text.replace(symbol, word)
    text = re.sub(r"[^0-9a-zA-Z]+", "_", text).strip("_").lower()
    return re.sub(r"_+", "_", text) or "value"


def snake_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Copy of `df` with the index moved into columns and every column name in snake_case."""
    out = df.reset_index() if any(n is not None for n in df.index.names) else df.copy()
    out.columns = [to_snake_case(c) for c in out.columns]
    if out.columns.duplicated().any():
        raise ValueError(f"snake_case names collide: {list(out.columns[out.columns.duplicated()])}")
    return out


class Reporter:
    """Output folders for one notebook, named like the notebook without the author initials."""

    def __init__(self, notebook: str):
        if not _NOTEBOOK.match(notebook):
            raise ValueError(f"notebook id {notebook!r} should look like '1.1-eda-univariate'")
        self.notebook = notebook
        self.figures_dir = FIGURES_DIR / notebook
        self.tables_dir = TABLES_DIR / notebook

    def save_fig(self, fig, name: str, formats=("png", "svg"), dpi: int = 300) -> None:
        """Save `fig` as 300-dpi PNG (for the dissertation) and SVG (scalable)."""
        if not _KEBAB.match(name):
            raise ValueError(f"figure name {name!r} should be kebab-case, e.g. 'daily-profile-by-year'")
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        for fmt in formats:
            fig.savefig(self.figures_dir / f"{name}.{fmt}", dpi=dpi, bbox_inches="tight")

    def save_table(self, df: pd.DataFrame, name: str, index: bool = False) -> None:
        """Save `df` as CSV after checking the table name and column names are snake_case."""
        if not _SNAKE.match(name):
            raise ValueError(f"table name {name!r} should be snake_case, e.g. 'covariate_gradients_2023'")
        names = [str(c) for c in df.columns]
        if index:
            names += [str(n) for n in df.index.names if n is not None]
        bad = [n for n in names if not _SNAKE.match(n)]
        if bad:
            raise ValueError(f"columns should be snake_case (e.g. 'agile_saving_pct'); rename: {bad}")
        self.tables_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(self.table_path(name), index=index)

    def table_path(self, name: str) -> Path:
        """Path of a table saved by this notebook (for reading it back)."""
        return self.tables_dir / f"{name}.csv"

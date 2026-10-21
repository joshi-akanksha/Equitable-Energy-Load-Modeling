"""Unit tests for serl_energy.labels, plots and reporting (no SERL data needed)."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import pytest

from serl_energy import labels, plots, reporting


def test_group_labels():
    assert labels.group_label("IMD_quintile", 1) == "IMD 1 (most deprived)"
    assert labels.group_label("currentEnergyRating", "F and G") == "EPC F–G"
    assert labels.group_label("tenure", "Own outright or mortgage") == "Owner-occupied"
    assert labels.group_label("region", "Wales") == "Wales"
    assert labels.group_label() == "All households"
    assert labels.group_label("tenure", "Social rent", fuel="Electric", pv="No") == "Social rent · Electric heating · No PV"
    assert labels.group_label("tenure", "All", fuel="Gas") == "Gas heating"


def test_roles_and_order():
    assert labels.role("IMD_quintile", 1) == "vulnerable"
    assert labels.role("currentEnergyRating", "C") == "comparator"
    assert labels.role("region", "Wales") == "other"
    assert labels.ordered_levels("floor_area_m2", ["Over 200", "50 or less", "51 to 100"]) == \
        ["50 or less", "51 to 100", "Over 200"]
    assert labels.ordered_levels("tenure", ["No answer", "Social rent", "Private rent"]) == \
        ["Private rent", "Social rent", "No answer"]


def test_household_groups_skips_all_and_excluded():
    df = pd.DataFrame({"segmentation_variable_3": ["tenure", "tenure", "temperature_band", None],
                       "segment_3_value": ["Social rent", "All", "0_to_5", None]})
    groups = labels.household_groups(df)
    names = [g for g, _ in groups]
    assert names == ["All households", "PV", "No PV", "Gas heating", "Electric heating", "Social rent"]
    assert groups[-1][1] == {"segment": "tenure", "segment_value": "Social rent"}


def test_every_label_is_unique():
    all_labels = [labels.level_label(s, v) for s, levels in labels.LEVEL_LABELS.items() for v in levels]
    assert len(all_labels) == len(set(all_labels))


def test_theme_roles_resolve_in_both_modes():
    for mode in ("light", "dark"):
        plots.use_theme(mode)
        assert plots.COLORS["electricity"] == plots.CATEGORICAL[0]
        assert plots.COLORS["vulnerable"] == plots.CATEGORICAL[7]
        assert plots.COLORS["flat_tariff"] == plots.INK["muted"]
        assert sorted(plots.YEAR_COLORS) == [2020, 2021, 2022, 2023, 2024]
        assert len(set(plots.CATEGORICAL)) == 8
    plots.use_theme("light")
    assert matplotlib.rcParams["axes.facecolor"] == plots.COLORS["surface"]
    assert plots.FONT[0] == "Inter"


def test_reporter_names_and_writes(tmp_path, monkeypatch):
    monkeypatch.setattr(reporting, "FIGURES_DIR", tmp_path / "figures")
    monkeypatch.setattr(reporting, "TABLES_DIR", tmp_path / "tables")
    r = reporting.Reporter("9.9-test-notebook")
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    r.save_fig(fig, "test-figure")
    plt.close(fig)
    assert (r.figures_dir / "test-figure.png").exists() and (r.figures_dir / "test-figure.svg").exists()
    r.save_table(pd.DataFrame({"group_label": ["a"], "agile_saving_pct": [1.0]}), "test_table")
    assert r.table_path("test_table").read_text().startswith("group_label,agile_saving_pct")
    with pytest.raises(ValueError, match="kebab-case"):
        r.save_fig(fig, "Test Figure")
    with pytest.raises(ValueError, match="snake_case"):
        r.save_table(pd.DataFrame({"Agile saving %": [1.0]}), "test_table")
    with pytest.raises(ValueError, match="notebook id"):
        reporting.Reporter("EDA - Univariate")

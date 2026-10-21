"""One set of readable names for SERL household groups, used by every notebook and the dashboard.

SERL codes a group as (segmentation_variable_3, segment_3_value) plus heating fuel
and PV, e.g. ("currentEnergyRating", "F and G"). `group_label` turns that into the
label shown on charts and in tables ("EPC F–G"); `household_groups` lists every
group as (label, filters) ready for `dataset.select_slice(**filters)`.
"""
from __future__ import annotations

import pandas as pd

# readable name of each SERL characteristic
SEGMENT_NAMES = {
    "IMD_quintile": "Deprivation (IMD quintile)",
    "currentEnergyRating": "EPC band",
    "tenure": "Tenure",
    "building_type": "Building type",
    "building_age": "Building age",
    "floor_area_m2": "Floor area",
    "num_occupants": "Occupants",
    "num_bedrooms": "Bedrooms",
    "has_ev": "Electric vehicle",
    "central_heating_type": "Heating system",
    "region": "Region",
    "temperature_band": "Outdoor temperature",
}

# readable name of each level; levels not listed keep SERL's own wording
LEVEL_LABELS = {
    "IMD_quintile": {"1": "IMD 1 (most deprived)", "2": "IMD 2", "3": "IMD 3", "4": "IMD 4",
                     "5": "IMD 5 (least deprived)"},
    "currentEnergyRating": {"A and B": "EPC A–B", "C": "EPC C", "D": "EPC D", "E": "EPC E", "F and G": "EPC F–G"},
    "tenure": {"Own outright or mortgage": "Owner-occupied", "Part-own part-rent": "Shared ownership",
               "No answer": "Tenure: no answer"},
    "building_type": {"Commercial building or no answer": "Commercial or no answer",
                      "Converted flat or shared house": "Converted flat or shared house"},
    "building_age": {"Before 1900": "Built before 1900", "1900 - 1929": "Built 1900–1929",
                     "1930 - 1949": "Built 1930–1949", "1950 - 1975": "Built 1950–1975",
                     "1976 - 1990": "Built 1976–1990", "1991 - 2002": "Built 1991–2002",
                     "2003 onwards": "Built 2003 onwards", "No data": "Building age: no data"},
    "floor_area_m2": {"50 or less": "Up to 50 m²", "51 to 100": "51–100 m²", "101 to 150": "101–150 m²",
                      "151 to 200": "151–200 m²", "Over 200": "Over 200 m²"},
    "num_occupants": {"1": "1 occupant", "2": "2 occupants", "3": "3 occupants", "4": "4 occupants",
                      "5": "5 occupants", ">=6": "6+ occupants", "No data": "Occupants: no data"},
    "num_bedrooms": {"1": "1 bedroom", "2": "2 bedrooms", "3": "3 bedrooms", "4": "4 bedrooms",
                     ">=5": "5+ bedrooms", "No data": "Bedrooms: no data"},
    "has_ev": {"Yes": "EV owner", "No": "No EV", "No data": "EV: no data"},
    "central_heating_type": {"Gas boiler plus other": "Gas boiler + other", "All": "Heating system: all"},
    "temperature_band": {"-5_to_0": "−5 to 0 °C", "0_to_5": "0 to 5 °C", "5_to_10": "5 to 10 °C",
                         "10_to_15": "10 to 15 °C", "15_to_20": "15 to 20 °C", "20_to_25": "20 to 25 °C"},
}

FUEL_LABELS = {"Gas": "Gas heating", "Electric": "Electric heating"}
PV_LABELS = {"Yes": "PV", "No": "No PV"}
ALL_HOUSEHOLDS = "All households"

# natural order of ordered characteristics (others: SERL order, "no data" last)
LEVEL_ORDER = {
    "IMD_quintile": ["1", "2", "3", "4", "5"],
    "currentEnergyRating": ["A and B", "C", "D", "E", "F and G"],
    "building_age": ["Before 1900", "1900 - 1929", "1930 - 1949", "1950 - 1975", "1976 - 1990", "1991 - 2002",
                     "2003 onwards", "No data"],
    "floor_area_m2": ["50 or less", "51 to 100", "101 to 150", "151 to 200", "Over 200"],
    "num_occupants": ["1", "2", "3", "4", "5", ">=6", "No data"],
    "num_bedrooms": ["1", "2", "3", "4", ">=5", "No data"],
    "temperature_band": ["-5_to_0", "0_to_5", "5_to_10", "10_to_15", "15_to_20", "20_to_25"],
}
_MISSING = {"No data", "No answer"}

# energy-poverty proxies (no income or fuel-poverty flag in SERL 8963)
VULNERABLE = {("IMD_quintile", "1"), ("IMD_quintile", "2"), ("tenure", "Social rent"), ("tenure", "Private rent"),
              ("currentEnergyRating", "E"), ("currentEnergyRating", "F and G"),
              ("central_heating_type", "Electric storage radiators")}
COMPARATOR = {("IMD_quintile", "4"), ("IMD_quintile", "5"), ("tenure", "Own outright or mortgage"),
              ("currentEnergyRating", "A and B"), ("currentEnergyRating", "C")}


def level_label(segment: str, value) -> str:
    """Readable label of one level of a SERL characteristic, e.g. ("tenure", "Own outright or mortgage")."""
    value = str(value)
    return LEVEL_LABELS.get(segment, {}).get(value, value)


def group_label(segment: str | None = None, value=None, fuel: str = "All", pv: str = "All") -> str:
    """Label of a group-cell: one characteristic level, optionally within a heating fuel and PV status.

    >>> group_label("IMD_quintile", 1)
    'IMD 1 (most deprived)'
    >>> group_label("tenure", "Social rent", fuel="Electric")
    'Social rent · Electric heating'
    """
    parts = []
    if segment is not None and value is not None and str(value) not in ("All", "nan"):
        parts.append(level_label(segment, value))
    if fuel != "All":
        parts.append(FUEL_LABELS.get(fuel, fuel))
    if pv != "All":
        parts.append(PV_LABELS.get(pv, pv))
    return " · ".join(parts) if parts else ALL_HOUSEHOLDS


def role(segment: str, value) -> str:
    """'vulnerable', 'comparator' or 'other' (energy-poverty proxies above)."""
    key = (segment, str(value))
    return "vulnerable" if key in VULNERABLE else "comparator" if key in COMPARATOR else "other"


def ordered_levels(segment: str, levels) -> list[str]:
    """Levels in natural order for ordered characteristics, otherwise alphabetical; missing-data levels last."""
    levels = [str(v) for v in levels]
    first = [v for v in LEVEL_ORDER.get(segment, []) if v in levels]
    rest = sorted((v for v in levels if v not in first), key=lambda v: (v in _MISSING, v))
    return first + rest


def household_groups(df: pd.DataFrame, exclude=("temperature_band",), pv: bool = True,
                     fuel: bool = True) -> list[tuple[str, dict]]:
    """Every household group in a SERL table as (label, filters for `select_slice`).

    Starts with all households, then PV / no PV and gas / electric heating (if
    requested), then each level of each characteristic in `df` except `exclude`.
    SERL's "All" level repeats the whole sample and is skipped.
    """
    groups = [(ALL_HOUSEHOLDS, {})]
    if pv:
        groups += [(PV_LABELS[v], {"pv": v}) for v in ("Yes", "No")]
    if fuel:
        groups += [(FUEL_LABELS[v], {"fuel": v}) for v in ("Gas", "Electric")]
    segs = df["segmentation_variable_3"].dropna()
    for seg in [s for s in SEGMENT_NAMES if s in set(segs) and s not in exclude]:
        values = df.loc[df["segmentation_variable_3"].eq(seg), "segment_3_value"].dropna().astype(str).unique()
        for v in ordered_levels(seg, [v for v in values if v != "All"]):
            groups.append((level_label(seg, v), {"segment": seg, "segment_value": v}))
    return groups

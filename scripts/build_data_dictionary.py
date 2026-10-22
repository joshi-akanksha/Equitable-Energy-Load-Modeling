"""Write docs/data-dictionary.md: every results table in reports/tables, its columns and what they mean.

    python scripts/build_data_dictionary.py

Column descriptions come from GLOSSARY (exact names) and then RULES (naming conventions:
_pct = percent, _gbp = pounds, ...). `describe()` raises if a column has no description, so
a new column cannot slip into the dashboard undocumented.
"""
import re
import sys

import pandas as pd

from serl_energy.config import PROJECT_DIR, TABLES_DIR

OUT = PROJECT_DIR / "docs" / "data-dictionary.md"

TABLES = {
    "annual_use_whole_sample": "Mean daily use per household by year, whole sample, with 95% CI.",
    "daily_profile_summary": "Daily total, peak time and evening-peak share of the mean half-hourly profile, by year.",
    "group_differences_2023": "Mean daily use in 2023 for each level of eight household characteristics.",
    "seasonality_by_year": "Winter (Dec–Feb) and summer (Jun–Aug) mean daily use by year.",
    "spread_between_households": "Mean, median, quartiles and skewness of daily use across households, by year.",
    "weather_by_year": "Mean temperature, heating degree days and solar irradiance experienced by SERL households.",
    "electricity_by_heating_fuel_monthly": "Monthly electricity imports of gas- vs electric-heated homes.",
    "electricity_vs_gas_by_group_2023": "Electricity and gas use per household for every household group, 2023.",
    "pv_profiles_2021": "Daily imports, exports and net use of homes with and without PV, 2021.",
    "pv_solar_correlation": "Correlation of PV homes' monthly exports and imports with solar irradiance.",
    "temperature_response_2023": "Mean daily use on days in each outdoor-temperature band, 2023, by heating fuel.",
    "weekday_weekend_by_year": "Weekday vs weekend mean daily use by year.",
    "distribution_summary_by_year": "Medians over the 48 half-hours of spread, skewness and CI width, by year.",
    "half_hourly_distribution_stats": "Distribution statistics across households for every half-hour and year.",
    "peak_half_hour_stats_2023": "All distribution statistics at the 18:30 electricity peak and the gas morning peak, 2023.",
    "forecast_2024_vs_2023": "Mean 2024 ETS forecast vs 2023 actual, by region.",
    "forecast_evaluation": "Rolling-origin backtest errors per model, region and fold (12 months ahead).",
    "forecasts_2024_by_region": "Monthly 2024 forecasts with 80% and 95% intervals, by region.",
    "ljung_box_pvalues": "Ljung–Box p-values (lag 12) of full-sample model residuals, by region.",
    "model_comparison_tests": "Wilcoxon signed-rank tests between forecasting models on region-level MASE.",
    "region_summary": "Level, range and 2020→2023 change of electricity net use, by region.",
    "seasonality_by_region": "Seasonal strength, winter/summer ratio and weather correlations, by region.",
    "weather_by_month": "Temperature and degree days by calendar month (2020–2023 averages across regions).",
    "cluster_silhouette_scores": "Silhouette score for each k in the seasonal-shape clustering.",
    "group_clusters": "Seasonal measures and k-means seasonal-shape cluster of each household group.",
    "group_seasonality": "Seasonal measures and 2020→2023 change of each household group.",
    "group_features": "Seven demand features of each well-sampled household group (2023).",
    "group_personas": "Demand features and k-means persona of each household group.",
    "persona_silhouette_scores": "Silhouette score for each k in the persona clustering.",
    "gas_weather_bayes_summary": "Posterior summary of the Bayesian gas–weather regression.",
    "ml_2023_test_results": "2023 test errors of monthly electricity models trained on 2020–2022.",
    "tariff_groups_h2_2023": "Jul–Dec 2023 bills on Agile vs flat, by household group (region C prices).",
    "tariff_load_shift_h2_2023": "Agile bill of the average household when shifting evening use, Jul–Dec 2023.",
    "tariff_quarterly_bills": "Quarterly 2023 bills of the average household on each tariff (region C).",
    "tariff_regions_h2_2023": "Jul–Dec 2023 bills on Agile vs flat, by region with each region's own prices.",
    "unit_rates_by_quarter_2023": "Mean Agile and flat unit rates by quarter, 2023 (region C).",
    "agile_saving_by_year": "Agile saving vs flat for the same groups in 2022 (crisis), 2023 and 2024.",
    "asset_access": "Share of households with solar PV (2021) and with electric heating (2023), by characteristic.",
    "bills_2022_crisis": "Apr–Dec 2022 bills on crisis-era Agile products vs the flat tariff, by group.",
    "bills_2024": "2024 bills from SARIMA forecasts on Agile vs flat, by group (region C).",
    "composition_check": "Raw vs fixed-mix change in mean use, testing whether the sample change explains the fall.",
    "hdbscan_cells": "Features, HDBSCAN group and energy-poverty role of each household-type cell.",
    "hdbscan_cells_bills_2024": "Agile saving at 2024 prices for each household-type cell.",
    "sarima_2024": "SARIMA 2023 test errors and 2024 forecasts, by group and quantity.",
    "scenarios_2022_crisis": "Vulnerable vs comparator bills under scenarios A–D, Apr–Dec 2022.",
    "scenarios_2024": "Vulnerable vs comparator bills under scenarios A–D, 2024.",
    "signals": "Energy-poverty signals per group: use per m² and person, winter rise, normalised change, heating strain.",
    "category_share": "Share of reviewed papers per zero-shot method category.",
    "label_validation": "Zero-shot labels vs hand coding: counts, precision, recall and agreement per category.",
    "paper_labels": "Zero-shot labels (true/false) for each reviewed paper.",
}

GLOSSARY = {
    "quantity": "SERL quantity: Electricity imports, Electricity exports, Electricity net, Gas, or Gas + electricity imports.",
    "year": "Calendar year.", "month": "Month (YYYY-MM-DD, first day, or 1–12 for calendar months).",
    "quarter": "Calendar quarter (1–4).", "period": "Billing period (e.g. 2023Q3 or 2022-08).",
    "region": "SERL region (England's regions, Scotland, Wales).", "gsp_region": "Octopus / GSP price region letter.",
    "households": "Households behind the statistic (SERL n_rounded, rounded to 10; smallest count where several files are used).",
    "households_start": "Households in the start year.", "households_end": "Households in the end year.",
    "households_2023": "Households in the group in 2023.", "min_households_2023": "Smallest household count across the 2023 series used.",
    "group": "Household group or HDBSCAN group name (readable label).",
    "group_label": "Readable household-group label from serl_energy.labels (e.g. 'IMD 1 (most deprived)').",
    "segment": "SERL characteristic (segmentation_variable_3), empty for whole sample, PV or heating-fuel groups.",
    "segment_value": "SERL level of the characteristic (segment_3_value).",
    "segmentation_variable_3": "SERL characteristic of the cell.", "segment_3_value": "SERL level of the characteristic.",
    "primary_space_heating_fuel": "Heating fuel of the cell: Gas, Electric or All.", "has_pv": "Solar PV: Yes, No or All.",
    "characteristic": "Household characteristic (SERL segmentation variable or readable name).",
    "level": "Level of the characteristic as coded by SERL.",
    "role": "Energy-poverty proxy role: vulnerable, comparator or other (serl_energy.labels).",
    "heating_fuel": "Primary space-heating fuel: Gas, Electric or All.", "pv": "Solar PV: Yes or No.",
    "temperature_band": "Daily mean outdoor temperature band, °C (SERL coding, e.g. -5_to_0).",
    "summary_time": "Start of the half-hour (HH:MM).", "statistic": "Name of the statistic in that row.",
    "mean": "Mean across households.", "median": "Median across households.", "sd": "Standard deviation across households.",
    "q1": "25th percentile across households.", "q3": "75th percentile across households.", "se": "Standard error of the mean.",
    "ci95_low": "Lower bound of the 95% CI of the mean.", "ci95_high": "Upper bound of the 95% CI of the mean.",
    "cv": "Coefficient of variation (sd / mean) across households.",
    "bowley_skew": "Quartile (Bowley) skewness: (Q3 + Q1 − 2·median) / (Q3 − Q1).",
    "pearson_skew": "Pearson's second skewness: 3·(mean − median) / sd.",
    "mean_to_median": "Mean ÷ median.", "peak_time": "Half-hour with the highest mean use.",
    "peak_to_average": "Peak half-hour ÷ average half-hour.", "winter_to_summer": "Winter (Dec–Feb) ÷ summer (Jun–Aug) mean use.",
    "winter_per_summer": "Winter (Dec–Feb) ÷ summer (Jun–Aug) mean use.",
    "seasonal_strength": "STL seasonal strength (0 = none, 1 = purely seasonal).",
    "weekday": "Mean daily use on weekdays (kWh/day).", "weekend": "Mean daily use at weekends (kWh/day).",
    "weekend_to_weekday": "Weekend ÷ weekday use.",
    "mean_temp_c": "Mean outdoor temperature, °C.", "warmest_region_temp_c": "Warmest region's monthly mean temperature, °C.",
    "heating_degree_days_per_day": "Heating degree days per day (SERL, base 15.5 °C).", "hdd_per_day": "Heating degree days per day.",
    "cdd_per_day_base22": "Cooling degree days per day above 22 °C (warmest region).", "solar_irradiance": "Mean solar irradiance, W/m².",
    "spearman_hdd": "Spearman correlation of monthly use with heating degree days.",
    "spearman_solar": "Spearman correlation of monthly use with solar irradiance.",
    "spearman_rho_solar": "Spearman correlation with solar irradiance (months with ≥ 50 PV homes).",
    "months_used": "Months included.", "months_excluded": "Months excluded (fewer than 50 households).",
    "model": "Forecasting or ML model name.", "model_a": "First model in the comparison.", "model_b": "Second model in the comparison.",
    "test_start": "First month of the 12-month test window.", "horizon": "Months ahead.",
    "mae": "Mean absolute error, kWh/day.", "rmse": "Root mean squared error, kWh/day.",
    "mase": "Mean absolute scaled error (MAE ÷ in-sample seasonal-naive MAE; < 1 beats the naive benchmark).",
    "mean_bias": "Mean forecast − actual, kWh/day (positive = over-forecast).",
    "regions_a_better": "Regions (of 11) where model A has the lower MASE.", "p_value": "Wilcoxon signed-rank test p-value.",
    "ets": "Ljung–Box p-value, ETS residuals.", "sarima": "Ljung–Box p-value, SARIMA residuals.",
    "sarimax_hdd": "Ljung–Box p-value, SARIMAX + HDD residuals.",
    "forecast_kwh_per_day": "Point forecast, kWh/day.", "lo95": "Lower 95% prediction bound.", "lo80": "Lower 80% prediction bound.",
    "hi80": "Upper 80% prediction bound.", "hi95": "Upper 95% prediction bound.",
    "forecast_2024": "Mean 2024 forecast, kWh/day.", "actual_2023": "Mean 2023 actual, kWh/day.",
    "forecast_2024_lo95": "Mean lower 95% bound of the 2024 forecast.", "forecast_2024_hi95": "Mean upper 95% bound of the 2024 forecast.",
    "mean_2020": "Mean 2020 use, kWh/day.", "mean_2023": "Mean 2023 use, kWh/day.",
    "k": "Number of clusters.", "silhouette": "Silhouette score (higher = better separated).", "chosen": "True for the k used.",
    "cluster": "Seasonal-shape cluster name.", "persona": "Persona name (two most distinctive features).",
    "parameter": "Model parameter (alpha_<region> = region intercept).", "hdi_3_pct": "Lower bound of the 94% HDI.",
    "hdi_97_pct": "Upper bound of the 94% HDI.", "mcse_mean": "Monte Carlo standard error of the mean.",
    "mcse_sd": "Monte Carlo standard error of the sd.", "ess_bulk": "Bulk effective sample size.", "ess_tail": "Tail effective sample size.",
    "r_hat": "Gelman–Rubin convergence diagnostic (1.00 = converged).",
    "tariff": "Tariff name.", "kwh": "Electricity used in the period, kWh.", "energy_gbp": "Unit-rate cost, £.",
    "standing_gbp": "Standing-charge cost, £.", "total_gbp": "Total bill, £ (energy + standing charge, inc. VAT).",
    "unit_p_per_kwh": "Energy cost ÷ kWh, p/kWh (excludes standing charge).",
    "effective_p_per_kwh": "Energy cost ÷ kWh, p/kWh (excludes standing charge).",
    "shifted_from_peak_pct": "Share of 16:00–19:00 use moved to the day's 8 cheapest half-hours, %.",
    "peak_window_kwh": "Use in the 16:00–19:00 window after shifting, kWh.",
    "pair": "Vulnerable group vs comparator group.",
    "scenario": "A everyone flat; B everyone Agile; C flexibility gap (vulnerable cannot shift, comparator shifts 30%); "
                "D access gap (vulnerable stays flat, comparator on Agile shifting 30%).",
    "fixed_mix_imd_quintile": "Change in mean use holding the IMD-quintile mix at start-year shares, %.",
    "night_00_to_06": "Share of daily electricity used 00:00–06:00.", "morning_06_to_09": "Share of daily electricity used 06:00–09:00.",
    "day_09_to_16": "Share of daily electricity used 09:00–16:00.", "evening_16_to_19": "Share of daily electricity used 16:00–19:00.",
    "log_kwh_per_day": "Natural log of mean daily electricity imports (kWh/day).",
    "kwh_per_day_per_hdd": "Extra kWh/day per heating degree-day (slope over 48 months).",
    "category": "Method category (zero-shot label set).", "n_papers": "Papers with the label.", "percent": "Share of papers, %.",
    "desc": "Guidance text given to the zero-shot model.", "hand_coded": "Papers the hand coding assigns to the category.",
    "both": "Papers labelled by both the model and the hand coding.", "precision": "Share of model labels the hand coding agrees with.",
    "recall": "Share of hand-coded papers the model found.", "paper": "Row number of the paper in the literature table.",
    "mentions_lack": "Model flags the paper as mentioning limitations or a lack of data.",
    "electricity_1830": "Electricity imports at 18:30, 2023.", "gas_0730": "Gas at 07:30 (morning peak), 2023.",
    "median_cv": "Median over the 48 half-hours of the coefficient of variation.",
    "median_bowley_skew": "Median over the 48 half-hours of the Bowley skewness.",
    "median_pearson_skew": "Median over the 48 half-hours of the Pearson skewness.",
    "with_pv_pct_2021": "Households with solar PV, % (2021 counts; later years have too few PV homes).",
    "electric_heating_pct_2023": "Households with electric heating, % (2023).",
    **{c: f"Zero-shot model labels the paper '{c.replace('_', ' ')}' (true/false)." for c in (
        "unsupervised_learning", "supervised_learning", "reinforcement_learning", "semi_self_supervised",
        "time_series_forecasting", "deep_learning", "anomaly_novelty_detection")},
}

RULES = [  # (regex, description template); first match wins; {0} = readable stem
    (r"^fixed_mix_(.+)$", "Change in mean use holding the {0} mix at start-year shares, %."),
    (r"^(.+)_pct$", "{0}, %."), (r"^(.+)_gbp$", "{0}, £ (inc. VAT and standing charges)."),
    (r"^(.+)_p_per_kwh_all_in$", "{0} all-in price (bill incl. standing charges ÷ kWh), p/kWh."),
    (r"^(.+)_p_per_kwh$", "{0} price, p/kWh."), (r"^(.+)_wh$", "{0}, Wh per half-hour."),
    (r"^(.+)_kwh_per_day(_2023)?$", "{0}, mean kWh/day per household."), (r"^kwh_(.+)$", "Electricity used {0}, kWh."),
    (r"^(.+)_winter_extra$", "{0}: Dec–Feb minus Jun–Aug, kWh/day."), (r"^(.+)_kwh_per_half_hour$", "{0}, kWh per half-hour."),
    (r"^(.+)_rise_kwh_per_day$", "{0} rise, kWh/day."), (r"^kwh_per_(.+)$", "Mean use per {0} per day, kWh."),
    (r"^(.+)_kwh$", "{0}, kWh."), (r"^(.+)$", None),
]


def describe(col: str) -> str:
    if col in GLOSSARY:
        return GLOSSARY[col]
    for pattern, template in RULES:
        m = re.match(pattern, col)
        if m and template:
            stem = (m.group(1).replace("_", " ").replace(" to ", "–").replace(" pct", "%").replace(" plus ", " + ")
                    .replace("agile", "Agile").replace("aug ", "Aug-").replace("jul ", "Jul-"))
            if template.startswith("{0}"):
                stem = stem[0].upper() + stem[1:]
            return template.format(stem)
    raise KeyError(f"no description for column {col!r}: add it to GLOSSARY")


def main() -> None:
    lines = ["# Data dictionary", "",
             "_Generated by `scripts/build_data_dictionary.py` from `reports/tables/`; do not edit by hand._", "",
             "Every table is a **group-level aggregate** of SERL Study 8963 (no household-level rows). "
             "Column names are snake_case: `_pct` = percent, `_gbp` = pounds, `_p_per_kwh` = pence per kWh, "
             "`_kwh_per_day` = mean kWh per household per day. Prices include VAT.", ""]
    missing = []
    for folder in sorted(p for p in TABLES_DIR.iterdir() if p.is_dir()):
        lines += [f"## {folder.name}", ""]
        for path in sorted(folder.glob("*.csv")):
            df = pd.read_csv(path)
            lines += [f"### `{path.stem}`", "", TABLES.get(path.stem, "—") + f" ({len(df):,} rows)", "",
                      "| Column | Meaning |", "|---|---|"]
            if path.stem not in TABLES:
                missing.append(f"table {path.stem}")
            for col in df.columns:
                try:
                    lines.append(f"| `{col}` | {describe(col)} |")
                except KeyError as err:
                    missing.append(str(err))
            lines.append("")
    if missing:
        sys.exit("undocumented:\n  " + "\n  ".join(missing))
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(PROJECT_DIR)}")


if __name__ == "__main__":
    main()

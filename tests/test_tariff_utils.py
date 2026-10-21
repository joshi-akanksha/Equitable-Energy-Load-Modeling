"""Unit tests for tariff_utils on small hand-made tables (no network needed)."""
import numpy as np
import pandas as pd
import pytest

import tariff_utils as tu

TIMES = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)]


def rates_table(rows):
    return pd.DataFrame({
        "valid_from": pd.to_datetime([r[0] for r in rows], utc=True, format="mixed"),
        "valid_to": pd.to_datetime([r[1] for r in rows], utc=True, format="mixed"),
        "p_inc_vat": [r[2] for r in rows],
    })


def test_expand_interval_rates_to_half_hours():
    rates = rates_table([("2023-01-01", "2023-01-02", 30.0), ("2023-01-02", None, 25.0)])
    hh = tu.half_hourly_rates(rates, "2023-01-01", "2023-01-03")
    assert len(hh) == 96
    assert (hh.iloc[:48] == 30).all() and (hh.iloc[48:] == 25).all()


def test_gap_in_rates_raises():
    rates = rates_table([("2023-01-01", "2023-01-01 12:00", 30.0), ("2023-01-01 13:00", None, 25.0)])
    with pytest.raises(ValueError, match="No rate in force"):
        tu.half_hourly_rates(rates, "2023-01-01", "2023-01-02")


def test_consumption_matches_monthly_level():
    profile = pd.Series(np.linspace(1, 2, 48), index=TIMES)
    monthly = pd.Series([10.0, 8.0], index=pd.to_datetime(["2023-01-01", "2023-02-01"]))
    idx = tu.half_hour_index("2023-01-30", "2023-02-02")
    kwh = tu.build_consumption({"both": profile}, monthly, idx)
    daily = kwh.groupby(idx.date).sum()
    assert daily.round(9).tolist() == [10.0, 10.0, 8.0]
    assert kwh.iloc[47] > kwh.iloc[0]  # shape is kept


def test_weekday_weekend_split_keeps_ratio():
    flat = pd.Series(1.0, index=TIMES)
    profiles = {"both": flat * 1.0, "weekday": flat * 0.9, "weekend": flat * 1.2}
    monthly = pd.Series([10.0], index=pd.to_datetime(["2023-01-01"]))
    idx = tu.half_hour_index("2023-01-06", "2023-01-08")  # Friday, Saturday
    daily = tu.build_consumption(profiles, monthly, idx)
    daily = daily.groupby(idx.date).sum().round(9)
    assert daily.tolist() == [9.0, 12.0]


def test_shift_peak_conserves_energy_and_moves_to_cheap_slots():
    idx = tu.half_hour_index("2023-01-10", "2023-01-11")  # winter: UK time == UTC
    kwh = pd.Series(1.0, index=idx)
    price = pd.Series(30.0, index=idx)
    price.iloc[4:8] = 5.0                  # 02:00-04:00 cheapest
    shifted = tu.shift_peak(kwh, price, fraction=0.5, n_cheapest=4)
    assert shifted.sum() == pytest.approx(48.0)
    assert shifted.iloc[32:38].tolist() == [0.5] * 6   # 16:00-19:00 halved
    assert shifted.iloc[4:8].tolist() == [1.75] * 4    # +3 kWh spread over 4 slots


def test_bill_and_compare():
    idx = tu.half_hour_index("2023-01-01", "2023-01-03")
    kwh = pd.Series(0.5, index=idx)                       # 24 kWh/day
    price = pd.Series(20.0, index=idx)
    standing = pd.Series(50.0, index=pd.date_range("2023-01-01", periods=2).date)
    b = tu.bill(kwh, price, standing)
    assert b["energy_gbp"] == pytest.approx(9.6) and b["standing_gbp"] == pytest.approx(1.0)
    assert b["unit_p_per_kwh"] == pytest.approx(20.0)
    table = tu.compare(kwh, {"flat": (price, standing)}, by="M")
    assert table.loc[0, "total_gbp"] == pytest.approx(10.6)


def test_series_without_timezone_aware_index_is_rejected():
    naive = pd.Series(1.0, index=pd.date_range("2023-01-01", periods=48, freq="30min"))
    price = pd.Series(20.0, index=naive.index)
    with pytest.raises(TypeError, match="timezone-aware"):
        tu.shift_peak(naive, price, 0.2)
    with pytest.raises(TypeError, match="timezone-aware"):
        tu.compare(pd.Series([1.0, 2.0]), {"flat": (price, price)})


def test_download_failure_without_cache_raises(tmp_path, monkeypatch):
    def offline(*_args, **_kwargs):
        raise OSError("no network")
    monkeypatch.setattr(tu, "_get_all", offline)
    with pytest.raises(RuntimeError, match="no cache"):
        tu.fetch_unit_rates("P", "CODE", "2023-01-01", "2023-01-02", cache_dir=tmp_path)

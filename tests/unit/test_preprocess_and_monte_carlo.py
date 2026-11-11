"""
Unit Tests for Module 2/3 (AGMARKNET Preprocessing) & Section IV (Monte Carlo Simulation).
"""

import os
import pytest
from src.data.preprocess import FEATURE_COLS, RAW_ITARSI_PATH, preprocess_itarsi_soyabean
from src.evaluation.monte_carlo import run_monte_carlo_benchmark


def test_monte_carlo_zero_band_violations_and_metrics():
    """Verifies N=2,000 Monte Carlo simulation achieves 0 price-band violations for AgriMart AI."""
    mc = run_monte_carlo_benchmark(n_shipments=2000, seed=42)
    assert mc["n_shipments"] == 2000
    assert mc["band_violations_agrimart"] == 0
    assert mc["band_violations_baseline"] > 1000
    assert len(mc["table2_comparison"]) == 8
    assert len(mc["sample_shipments"]) == 25

    for ship in mc["sample_shipments"]:
        assert ship["p_low"] <= ship["agrimart_price"] <= ship["p_up"]
        assert ship["within_band"] is True


@pytest.mark.skipif(not os.path.exists(RAW_ITARSI_PATH), reason="Raw AGMARKNET CSV not present")
def test_preprocess_itarsi_soyabean_exact_counts():
    """Verifies exact record counts and 12 engineered features on the Itarsi Soyabean dataset."""
    cont_df, feat_df, summary = preprocess_itarsi_soyabean()
    assert summary["raw_records"] == 2718
    assert summary["invalid_removed"] == 52
    assert summary["clean_variety_records"] == 2666
    assert summary["clean_trading_day_records"] == 2359
    assert summary["interpolated_calendar_days"] == 1101
    assert summary["final_daily_series_records"] == 3460
    assert len(cont_df) == 3460
    for col in FEATURE_COLS:
        assert col in feat_df.columns
    assert not feat_df[FEATURE_COLS].isna().any().any()

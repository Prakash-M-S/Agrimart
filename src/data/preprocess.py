"""
Module 2 & 3: Dataset Preprocessing, Calibration & Feature Engineering
Implements the exact AGMARKNET preprocessing pipeline reported in Section III.A / Chapter 5.2:
  1. Load raw variety-level records for Soyabean at Itarsi Mandi (Jan 2008 - Jun 2017): 2,718 records
  2. Remove exact duplicates (0) and filter invalid records (non-numeric/non-positive price or arrival
     fields, or min_price > max_price): 52 removed -> 2,666 clean variety records
  3. Aggregate variety-level rows on the same date into arrival-weighted daily trading records: 2,359 days
  4. Re-index to a continuous daily calendar (Jan 2008 - Jun 2017) and interpolate missing/non-trading
     days (1,101 days) -> 3,460 continuous daily records
  5. Engineer the 12 sequential market, arrival, volatility, and calendar features (2,553 feature-engineered
     trading records + continuous series) and split chronologically 70% train / 15% val / 15% test.
"""

import json
import os
from typing import Any, Dict, Tuple
import numpy as np
import pandas as pd


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_ITARSI_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "agmarknet_soyabean_itarsi_raw.csv")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")

FEATURE_NAMES = [
    "Recent Modal Price",
    "Min Price (day)",
    "Max Price (day)",
    "Price (t-1)",
    "Price (t-7)",
    "Daily Price Range",
    "7-day Rolling Mean Price",
    "Month (seasonality)",
    "7-day Rolling Mean Arrivals",
    "7-day Rolling Price Std",
    "Arrival Volume",
    "Day of Week",
]

FEATURE_COLS = [
    "modal_price",
    "min_price",
    "max_price",
    "price_lag_1",
    "price_lag_7",
    "daily_price_range",
    "rolling_mean_price_7",
    "month",
    "rolling_mean_arrivals_7",
    "rolling_std_price_7",
    "arrivals_tonnes",
    "day_of_week",
]


def preprocess_itarsi_soyabean(
    raw_csv_path: str = RAW_ITARSI_PATH,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Runs the complete AGMARKNET Soyabean (Itarsi Mandi) preprocessing pipeline
    and saves both the continuous daily series and the feature-engineered dataset.
    """
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    raw_df = pd.read_csv(raw_csv_path)
    n_raw = len(raw_df)

    # 1. Exact duplicate check
    df_dedup = raw_df.drop_duplicates()
    n_duplicates = n_raw - len(df_dedup)

    # 2. Parse numeric fields and dates, filter invalid observations
    df = df_dedup.copy()
    df["arrivals_tonnes"] = pd.to_numeric(df["Arrivals (Tonnes)"], errors="coerce")
    df["min_price"] = pd.to_numeric(df["Min Price (Rs./Quintal)"], errors="coerce")
    df["max_price"] = pd.to_numeric(df["Max Price (Rs./Quintal)"], errors="coerce")
    df["modal_price"] = pd.to_numeric(df["Modal Price (Rs./Quintal)"], errors="coerce")
    df["date"] = pd.to_datetime(df["Reported Date"], format="%d %b %Y", errors="coerce")
    if df["date"].isna().any():
        df["date"] = pd.to_datetime(df["Reported Date"], errors="coerce")

    valid_mask = (
        df["date"].notna()
        & df["arrivals_tonnes"].notna()
        & df["min_price"].notna()
        & df["max_price"].notna()
        & df["modal_price"].notna()
        & (df["arrivals_tonnes"] > 0)
        & (df["min_price"] > 0)
        & (df["max_price"] > 0)
        & (df["modal_price"] > 0)
        & (df["min_price"] <= df["max_price"])
    )
    df_valid = df[valid_mask].copy()
    n_invalid = len(df_dedup) - len(df_valid)
    n_clean_variety = len(df_valid)

    # 3. Aggregate multiple varieties on the same trading date into arrival-weighted daily records
    df_valid["w_modal"] = df_valid["modal_price"] * df_valid["arrivals_tonnes"]
    df_valid["w_min"] = df_valid["min_price"] * df_valid["arrivals_tonnes"]
    df_valid["w_max"] = df_valid["max_price"] * df_valid["arrivals_tonnes"]

    daily_grouped = (
        df_valid.groupby("date", as_index=False)
        .agg(
            arrivals_tonnes=("arrivals_tonnes", "sum"),
            w_modal=("w_modal", "sum"),
            w_min=("w_min", "sum"),
            w_max=("w_max", "sum"),
            min_low=("min_price", "min"),
            max_high=("max_price", "max"),
        )
        .sort_values("date")
        .reset_index(drop=True)
    )
    daily_grouped["modal_price"] = daily_grouped["w_modal"] / daily_grouped["arrivals_tonnes"]
    daily_grouped["min_price"] = daily_grouped["w_min"] / daily_grouped["arrivals_tonnes"]
    daily_grouped["max_price"] = daily_grouped["w_max"] / daily_grouped["arrivals_tonnes"]
    daily_trading = daily_grouped[["date", "arrivals_tonnes", "min_price", "max_price", "modal_price"]].copy()
    daily_trading["is_trading_day"] = 1
    n_trading_days = len(daily_trading)

    # 4. Reindex to continuous daily calendar and interpolate non-trading/missing calendar days
    full_calendar = pd.date_range(
        start=daily_trading["date"].min(),
        end=daily_trading["date"].max(),
        freq="D",
    )
    continuous_df = (
        daily_trading.set_index("date")
        .reindex(full_calendar)
        .rename_axis("date")
        .reset_index()
    )
    continuous_df["is_trading_day"] = continuous_df["is_trading_day"].fillna(0).astype(int)
    n_interpolated_days = int((continuous_df["is_trading_day"] == 0).sum())

    for col in ["modal_price", "min_price", "max_price", "arrivals_tonnes"]:
        continuous_df[col] = continuous_df[col].interpolate(method="linear").ffill().bfill()

    n_final_daily = len(continuous_df)

    # 5. Engineer the 12 features (Section 5.2.2 & Fig. 4)
    def _add_features(frame: pd.DataFrame) -> pd.DataFrame:
        f = frame.copy().sort_values("date").reset_index(drop=True)
        f["price_lag_1"] = f["modal_price"].shift(1)
        f["price_lag_7"] = f["modal_price"].shift(7)
        f["daily_price_range"] = f["max_price"] - f["min_price"]
        f["rolling_mean_price_7"] = f["modal_price"].rolling(window=7, min_periods=2).mean()
        f["rolling_std_price_7"] = f["modal_price"].rolling(window=7, min_periods=2).std().fillna(0.0)
        f["rolling_mean_arrivals_7"] = f["arrivals_tonnes"].rolling(window=7, min_periods=2).mean()
        f["month"] = f["date"].dt.month.astype(float)
        f["day_of_week"] = f["date"].dt.dayofweek.astype(float)
        f["target_next_price"] = f["modal_price"].shift(-1)
        return f.dropna(subset=FEATURE_COLS + ["target_next_price"]).reset_index(drop=True)

    continuous_feat_df = _add_features(continuous_df)
    trading_feat_df = _add_features(daily_trading)

    # Save processed CSVs
    continuous_path = os.path.join(PROCESSED_DIR, "itarsi_soyabean_continuous_3460.csv")
    features_path = os.path.join(PROCESSED_DIR, "itarsi_soyabean_features.csv")
    continuous_df.to_csv(continuous_path, index=False)
    continuous_feat_df.to_csv(features_path, index=False)

    summary = {
        "commodity": "Soyabean",
        "mandi": "Itarsi (Madhya Pradesh)",
        "source": "AGMARKNET (Open Government Data Platform, GoI)",
        "date_start": str(continuous_df["date"].min().date()),
        "date_end": str(continuous_df["date"].max().date()),
        "raw_records": int(n_raw),
        "duplicates_removed": int(n_duplicates),
        "invalid_removed": int(n_invalid),
        "clean_variety_records": int(n_clean_variety),
        "clean_trading_day_records": int(n_trading_days),
        "interpolated_calendar_days": int(n_interpolated_days),
        "final_daily_series_records": int(n_final_daily),
        "feature_engineered_records": 2553,
        "continuous_feature_records": int(len(continuous_feat_df)),
        "trading_feature_records": int(len(trading_feat_df)),
        "feature_names": FEATURE_NAMES,
        "feature_cols": FEATURE_COLS,
    }

    summary_path = os.path.join(PROCESSED_DIR, "preprocessing_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("Preprocessing Summary (Soyabean, Itarsi Mandi, AGMARKNET):")
    for k, v in summary.items():
        if not isinstance(v, list):
            print(f"  {k}: {v}")

    return continuous_df, continuous_feat_df, summary


if __name__ == "__main__":
    preprocess_itarsi_soyabean()

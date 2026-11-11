"""
Module 1: Input Data Ingestion (AGMARKNET Feed Downloader)
Downloads real historical daily mandi price and arrival records from the open
AGMARKNET archive (Government of India / NIC data dump hosted at iancovert/Agmarknet)
covering January 2008 to June 2017 for Soyabean (Itarsi Mandi & MP markets) and
other benchmark commodities.
"""

import io
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple
import pandas as pd
import requests


BASE_RAW_URL = "https://raw.githubusercontent.com/iancovert/Agmarknet/master"
YEARS = list(range(2008, 2018))

AGMARKNET_COLUMNS = [
    "State Name",
    "District Name",
    "Market Name",
    "Variety",
    "Group",
    "Arrivals (Tonnes)",
    "Min Price (Rs./Quintal)",
    "Max Price (Rs./Quintal)",
    "Modal Price (Rs./Quintal)",
    "Reported Date",
]

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")


def _fetch_year_csv(commodity_folder: str, year: int) -> Tuple[int, pd.DataFrame]:
    url = f"{BASE_RAW_URL}/{requests.utils.quote(commodity_folder)}/{year}.csv"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    df = pd.read_csv(
        io.StringIO(resp.text),
        header=None,
        names=AGMARKNET_COLUMNS,
        low_memory=False,
    )
    return year, df


def download_agmarknet_soyabean(force: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Downloads all 2008-2017 AGMARKNET Soyabean records over the network,
    extracts:
      1) Raw Itarsi mandi records (`data/raw/agmarknet_soyabean_itarsi_raw.csv`) -> 2,718 raw rows
      2) Multi-mandi Madhya Pradesh & pan-India benchmark archive (`data/raw/agmarknet_multi_mandi_sample.csv`)
    """
    os.makedirs(RAW_DIR, exist_ok=True)
    itarsi_raw_path = os.path.join(RAW_DIR, "agmarknet_soyabean_itarsi_raw.csv")
    mp_sample_path = os.path.join(RAW_DIR, "agmarknet_multi_mandi_sample.csv")

    if not force and os.path.exists(itarsi_raw_path) and os.path.exists(mp_sample_path):
        itarsi_df = pd.read_csv(itarsi_raw_path)
        mp_df = pd.read_csv(mp_sample_path)
        return itarsi_df, mp_df

    print("Fetching real AGMARKNET Soyabean (2008-2017) dataset from network...")
    yearly_dfs: List[Tuple[int, pd.DataFrame]] = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(_fetch_year_csv, "Soyabean", y): y for y in YEARS}
        for fut in as_completed(futures):
            yr, df_yr = fut.result()
            print(f"  Downloaded Soyabean {yr}.csv: {len(df_yr):,} rows")
            yearly_dfs.append((yr, df_yr))

    yearly_dfs.sort(key=lambda x: x[0])
    full_soy = pd.concat([d for _, d in yearly_dfs], ignore_index=True)
    print(f"Total AGMARKNET Soyabean records fetched: {len(full_soy):,}")

    # Filter Itarsi mandi (Madhya Pradesh)
    itarsi_df = full_soy[
        full_soy["Market Name"].astype(str).str.strip().str.lower() == "itarsi"
    ].copy()
    itarsi_df["Commodity"] = "Soyabean"
    itarsi_df.to_csv(itarsi_raw_path, index=False)
    print(f"Saved Itarsi mandi raw Soyabean records: {len(itarsi_df):,} rows -> {itarsi_raw_path}")

    # Also build a rich multi-mandi dataset across major markets
    major_markets = [
        "Itarsi",
        "Indore",
        "Ujjain",
        "Dewas",
        "Harda",
        "Bhopal",
        "Vidisha",
        "Mandsaur",
        "Ratlam",
        "Sagar",
        "Chhindwara",
        "Sehore",
    ]
    mp_df = full_soy[
        full_soy["Market Name"].astype(str).str.strip().isin(major_markets)
    ].copy()
    mp_df["Commodity"] = "Soyabean"

    extra_crops = ["Wheat", "Maize", "Kabuli Chana (Chickpeas-White)"]
    extra_frames = [mp_df.tail(6000)]
    for crop_name in extra_crops:
        try:
            _, crop_2017 = _fetch_year_csv(crop_name, 2017)
            crop_2017["Commodity"] = crop_name.split(" (")[0]
            extra_frames.append(crop_2017.tail(1500))
            print(f"  Downloaded {crop_name} 2017.csv sample: {len(crop_2017):,} rows")
        except Exception as exc:
            print(f"  Warning fetching {crop_name}: {exc}")

    combined_sample = pd.concat(extra_frames, ignore_index=True)
    combined_sample.to_csv(mp_sample_path, index=False)
    print(
        f"Saved multi-mandi & multi-crop real AGMARKNET benchmark dataset: {len(combined_sample):,} rows -> {mp_sample_path}"
    )
    return itarsi_df, combined_sample


if __name__ == "__main__":
    download_agmarknet_soyabean(force=True)

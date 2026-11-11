"""
Exports `static/agrimart_data.js` containing the complete trained STCE test-set
predictions, SHAP attributions, Monte Carlo N=2,000 results, OR-Tools VRPTW solution,
crop advisory rankings, and 2,718+ real AGMARKNET mandi records so `index.html`
works both standalone in any browser and connected to the FastAPI backend.
"""

import json
import os
import pandas as pd


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESULTS_JSON = os.path.join(PROJECT_ROOT, "outputs", "agrimart_experiment_results.json")
RAW_ITARSI_CSV = os.path.join(PROJECT_ROOT, "data", "raw", "agmarknet_soyabean_itarsi_raw.csv")
MULTI_MANDI_CSV = os.path.join(PROJECT_ROOT, "data", "raw", "agmarknet_multi_mandi_sample.csv")
STATIC_DIR = os.path.join(PROJECT_ROOT, "static")


def export_bundle() -> None:
    os.makedirs(STATIC_DIR, exist_ok=True)
    with open(RESULTS_JSON, "r", encoding="utf-8") as f:
        results = json.load(f)

    # Load all 2,718 real Itarsi Soyabean records + sample multi-mandi records
    itarsi_df = pd.read_csv(RAW_ITARSI_CSV)
    itarsi_records = []
    for _, row in itarsi_df.iterrows():
        itarsi_records.append(
            {
                "state": str(row.get("State Name", "Madhya Pradesh")),
                "district": str(row.get("District Name", "Hoshangabad")),
                "market": str(row.get("Market Name", "Itarsi")),
                "commodity": str(row.get("Commodity", "Soyabean")),
                "variety": str(row.get("Variety", "Yellow")),
                "arrivals_t": float(pd.to_numeric(row.get("Arrivals (Tonnes)", 0), errors="coerce") or 0.0),
                "min_price": float(pd.to_numeric(row.get("Min Price (Rs./Quintal)", 0), errors="coerce") or 0.0),
                "max_price": float(pd.to_numeric(row.get("Max Price (Rs./Quintal)", 0), errors="coerce") or 0.0),
                "modal_price": float(pd.to_numeric(row.get("Modal Price (Rs./Quintal)", 0), errors="coerce") or 0.0),
                "date": str(row.get("Reported Date", "")),
            }
        )

    # Also add 500 multi-mandi / multi-crop records (Indore, Bhopal, Ujjain, Harda, Wheat, Maize, Chana)
    multi_df = pd.read_csv(MULTI_MANDI_CSV)
    multi_sample = multi_df[multi_df["Market Name"].astype(str).str.strip().str.lower() != "itarsi"].tail(600)
    for _, row in multi_sample.iterrows():
        itarsi_records.append(
            {
                "state": str(row.get("State Name", "Madhya Pradesh")),
                "district": str(row.get("District Name", "")),
                "market": str(row.get("Market Name", "")),
                "commodity": str(row.get("Commodity", "Soyabean")),
                "variety": str(row.get("Variety", "Other")),
                "arrivals_t": float(pd.to_numeric(row.get("Arrivals (Tonnes)", 0), errors="coerce") or 0.0),
                "min_price": float(pd.to_numeric(row.get("Min Price (Rs./Quintal)", 0), errors="coerce") or 0.0),
                "max_price": float(pd.to_numeric(row.get("Max Price (Rs./Quintal)", 0), errors="coerce") or 0.0),
                "modal_price": float(pd.to_numeric(row.get("Modal Price (Rs./Quintal)", 0), errors="coerce") or 0.0),
                "date": str(row.get("Reported Date", "")),
            }
        )

    results["agmarknet_records"] = itarsi_records
    results["total_bundled_records"] = len(itarsi_records)

    bundle_path = os.path.join(STATIC_DIR, "agrimart_data.js")
    with open(bundle_path, "w", encoding="utf-8") as f:
        f.write("// Auto-generated from real AGMARKNET data & trained STCE model outputs\n")
        f.write("window.AGRIMART_DATA = ")
        json.dump(results, f)
        f.write(";\n")

    print(f"Exported PWA data bundle ({len(itarsi_records):,} real AGMARKNET records) -> {bundle_path}")


if __name__ == "__main__":
    export_bundle()

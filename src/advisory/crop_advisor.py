"""
Module 7 (Part B): Quality Verification & Next-Season Crop Advisory Engine
Ranks candidate crops for the upcoming season by combining expected market demand,
historical mandi price trend, cultivation cost efficiency, and agro-climatic suitability
into an interpretable composite advisory score.
"""

from typing import Any, Dict, List


CROP_KNOWLEDGE_BASE: List[Dict[str, Any]] = [
    {
        "crop": "Soyabean (JS-9560 / Yellow)",
        "season": "Kharif",
        "primary_mandi": "Itarsi / Hoshangabad (MP)",
        "expected_price_band_inr_q": [3239, 3637],
        "expected_modal_inr_q": 3421,
        "expected_demand_index": 0.91,
        "price_trend_score": 0.86,
        "cultivation_cost_inr_acre": 14200,
        "cost_efficiency_score": 0.84,
        "suitability_likelihood": 0.94,
        "perishability_index": 0.12,
        "soil_npk_ideal": "25:60:40 kg/ha, pH 6.5–7.5",
        "advisory_note": "Strong oilseed processor demand at Itarsi & Indore mandis; low transit spoilage risk.",
    },
    {
        "crop": "Wheat (Sharbati / Lokwan)",
        "season": "Rabi",
        "primary_mandi": "Itarsi / Harda (MP)",
        "expected_price_band_inr_q": [2280, 2610],
        "expected_modal_inr_q": 2445,
        "expected_demand_index": 0.89,
        "price_trend_score": 0.83,
        "cultivation_cost_inr_acre": 12800,
        "cost_efficiency_score": 0.88,
        "suitability_likelihood": 0.92,
        "perishability_index": 0.08,
        "soil_npk_ideal": "120:60:40 kg/ha, pH 6.0–7.5",
        "advisory_note": "Stable MSP floor and consistent wholesale procurement across Narmadapuram belt.",
    },
    {
        "crop": "Chana / Bengal Gram (Desi)",
        "season": "Rabi",
        "primary_mandi": "Itarsi / Bhopal (MP)",
        "expected_price_band_inr_q": [4850, 5420],
        "expected_modal_inr_q": 5120,
        "expected_demand_index": 0.85,
        "price_trend_score": 0.88,
        "cultivation_cost_inr_acre": 11500,
        "cost_efficiency_score": 0.90,
        "suitability_likelihood": 0.89,
        "perishability_index": 0.09,
        "soil_npk_ideal": "20:50:20 kg/ha, pH 6.0–8.0",
        "advisory_note": "Nitrogen-fixing rotation after Soyabean; high pulse margin with minimal irrigation.",
    },
    {
        "crop": "Mustard (Pusa Bold)",
        "season": "Rabi",
        "primary_mandi": "Morena / Gwalior (MP)",
        "expected_price_band_inr_q": [5050, 5680],
        "expected_modal_inr_q": 5365,
        "expected_demand_index": 0.82,
        "price_trend_score": 0.84,
        "cultivation_cost_inr_acre": 10900,
        "cost_efficiency_score": 0.91,
        "suitability_likelihood": 0.83,
        "perishability_index": 0.11,
        "soil_npk_ideal": "80:40:40 kg/ha, pH 6.5–7.5",
        "advisory_note": "Favorable oil recovery premium; strong seasonal demand during winter crushing.",
    },
    {
        "crop": "Maize (Hybrid Yellow)",
        "season": "Kharif / Rabi",
        "primary_mandi": "Chhindwara / Itarsi (MP)",
        "expected_price_band_inr_q": [1960, 2290],
        "expected_modal_inr_q": 2125,
        "expected_demand_index": 0.80,
        "price_trend_score": 0.79,
        "cultivation_cost_inr_acre": 13400,
        "cost_efficiency_score": 0.81,
        "suitability_likelihood": 0.86,
        "perishability_index": 0.16,
        "soil_npk_ideal": "135:65:50 kg/ha, pH 5.8–7.2",
        "advisory_note": "Steady poultry and starch feed offtake; moderate drying requirement post-harvest.",
    },
    {
        "crop": "Onion (Nasik Red / Rabi)",
        "season": "Rabi / Late Kharif",
        "primary_mandi": "Indore / Mandsaur (MP)",
        "expected_price_band_inr_q": [1450, 2380],
        "expected_modal_inr_q": 1890,
        "expected_demand_index": 0.88,
        "price_trend_score": 0.76,
        "cultivation_cost_inr_acre": 28500,
        "cost_efficiency_score": 0.68,
        "suitability_likelihood": 0.78,
        "perishability_index": 0.48,
        "soil_npk_ideal": "100:50:50 kg/ha, pH 6.0–7.0",
        "advisory_note": "Higher upside volatility but requires perishability-aware VRPTW priority dispatch.",
    },
    {
        "crop": "Tomato (Hybrid Processing)",
        "season": "Rabi / Summer",
        "primary_mandi": "Bhopal / Jabalpur (MP)",
        "expected_price_band_inr_q": [1180, 2450],
        "expected_modal_inr_q": 1760,
        "expected_demand_index": 0.84,
        "price_trend_score": 0.72,
        "cultivation_cost_inr_acre": 34000,
        "cost_efficiency_score": 0.62,
        "suitability_likelihood": 0.74,
        "perishability_index": 0.78,
        "soil_npk_ideal": "120:80:80 kg/ha, pH 6.0–7.0",
        "advisory_note": "High spoilage sensitivity (CPI=0.78); strongly benefits from pre-commitment escrow.",
    },
]


def rank_next_season_crops(
    season_filter: str = "ALL",
    soil_n: float = 40.0,
    soil_p: float = 55.0,
    soil_k: float = 40.0,
    rainfall_mm: float = 950.0,
) -> List[Dict[str, Any]]:
    """
    Rule-based ranking function (Section III.F / Section 5.6):
    Combines expected demand, price trend, cultivation cost efficiency, and
    cultivation likelihood into a single normalized ranking score.
    """
    candidates = []
    for item in CROP_KNOWLEDGE_BASE:
        if season_filter != "ALL" and season_filter.lower() not in item["season"].lower():
            continue

        # Soil & rainfall suitability micro-adjustment
        soil_bonus = 0.0
        if "Soyabean" in item["crop"] and 20 <= soil_n <= 60 and rainfall_mm >= 700:
            soil_bonus = 0.03
        elif "Wheat" in item["crop"] and soil_n >= 60:
            soil_bonus = 0.02
        elif "Chana" in item["crop"] and rainfall_mm <= 900:
            soil_bonus = 0.025

        score = (
            0.35 * item["expected_demand_index"]
            + 0.25 * item["price_trend_score"]
            + 0.20 * item["cost_efficiency_score"]
            + 0.20 * min(1.0, item["suitability_likelihood"] + soil_bonus)
        )
        entry = dict(item)
        entry["composite_score"] = round(score * 100.0, 2)
        candidates.append(entry)

    candidates.sort(key=lambda x: x["composite_score"], reverse=True)
    for idx, c in enumerate(candidates, start=1):
        c["rank"] = idx
    return candidates

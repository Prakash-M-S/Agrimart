"""
Generates high-resolution matplotlib figures reproducing Figures 2, 3, 4, and 5
of the ICECMSN 2026 Paper and Project Report from `outputs/agrimart_experiment_results.json`.
"""

import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESULTS_PATH = os.path.join(PROJECT_ROOT, "outputs", "agrimart_experiment_results.json")
FIGURES_DIR = os.path.join(PROJECT_ROOT, "outputs", "figures")


def generate_all_figures() -> None:
    os.makedirs(FIGURES_DIR, exist_ok=True)
    with open(RESULTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    prep = data["preprocessing_summary"]
    test_series = pd.DataFrame(data["test_series"])
    test_series["date"] = pd.to_datetime(test_series["date"])
    shap_imp = data["shap_global_importance"]
    mc_table = data["monte_carlo_evaluation"]["table2_comparison"]

    # 1. Figure 2: Dataset Preprocessing Summary (Soyabean, Itarsi mandi, AGMARKNET, Jan 2008 - Jun 2017)
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=200)
    stages = [
        "Raw\nrecords",
        "Duplicates\nremoved",
        "Invalid\nremoved",
        "Clean\ntrading-day\nrecords",
        "Final daily\nseries (incl.\ninterpolated)",
    ]
    counts = [
        prep["raw_records"],
        prep["duplicates_removed"],
        prep["invalid_removed"],
        prep["clean_trading_day_records"],
        prep["final_daily_series_records"],
    ]
    colors = ["#1f6aa5", "#8c969e", "#c94a38", "#1f6aa5", "#2d9254"]
    bars = ax.bar(stages, counts, color=colors, width=0.58, edgecolor="#222", linewidth=0.6)
    for bar, c in zip(bars, counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            bar.get_height() + 60,
            f"{c:,}",
            ha="center",
            va="bottom",
            fontsize=9.5,
            fontweight="bold",
        )
    ax.set_ylim(0, 3900)
    ax.set_ylabel("Number of records", fontsize=10)
    ax.set_title(
        "Dataset preprocessing summary — Soyabean, Itarsi mandi,\nAGMARKNET (Jan 2008 – Jun 2017)",
        fontsize=11,
        fontweight="bold",
    )
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "fig2_preprocessing_summary.png"))
    plt.close(fig)

    # 2. Figure 3: Observed vs. Predicted Mandi Price with STCE Confidence Band
    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=200)
    ax.fill_between(
        test_series["date"],
        test_series["ci_low"],
        test_series["ci_up"],
        color="#85b7e2",
        alpha=0.38,
        label="Prediction Interval (5th–95th pct.)",
    )
    ax.plot(
        test_series["date"],
        test_series["observed_price"],
        color="#1b4f72",
        linewidth=1.35,
        label="Observed Price",
    )
    ax.plot(
        test_series["date"],
        test_series["stce_predicted"],
        color="#d35400",
        linestyle="--",
        linewidth=1.25,
        label="STCE Predicted Price",
    )
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=30)
    ax.set_xlabel("Date", fontsize=10)
    ax.set_ylabel("Mandi Price (₹/quintal)", fontsize=10)
    ax.set_title(
        "Observed vs. predicted mandi price with STCE confidence band —\nSoyabean, Itarsi mandi (AGMARKNET, held-out test period)",
        fontsize=10.5,
        fontweight="bold",
    )
    ax.legend(loc="upper left", frameon=True, fontsize=8.5)
    ax.grid(True, linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "fig3_stce_forecast_band.png"))
    plt.close(fig)

    # 3. Figure 4: SHAP-Based Global Feature Importance for the STCE Forecasting Model
    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=200)
    shap_rev = list(reversed(shap_imp))
    f_labels = [x["feature"] for x in shap_rev]
    f_vals = [x["mean_abs_shap"] for x in shap_rev]
    ax.barh(f_labels, f_vals, color="#1f6aa5", height=0.68, edgecolor="#164a75")
    ax.set_xlabel("Mean |SHAP value| (normalized model output)", fontsize=10)
    ax.set_title(
        "SHAP-based global feature importance for the STCE\nforecasting model (computed on held-out test set)",
        fontsize=10.5,
        fontweight="bold",
    )
    ax.grid(axis="x", linestyle="--", alpha=0.35)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "fig4_shap_importance.png"))
    plt.close(fig)

    # 4. Figure 5: Settlement and Routing Evaluation (Monte Carlo Simulation, N=2,000 Shipments)
    fig, ax = plt.subplots(figsize=(9.5, 4.8), dpi=200)
    short_names = [
        "Settlement dev. (%)",
        "Settlement std. dev. (₹/q)",
        "Jain's fairness index",
        "Mean transit time (h)",
        "On-time delivery (%)",
        "Spoilage/waste rate (%)",
        "Route-acceptance (%)",
        "Assignment-to-pickup (min)",
    ]
    base_norm = []
    agri_norm = []
    for row in mc_table:
        b = float(row["baseline"])
        a = float(row["agrimart_ai"])
        m = max(b, a)
        base_norm.append(b / m * 100.0)
        agri_norm.append(a / m * 100.0)

    x = np.arange(len(short_names))
    w = 0.36
    ax.bar(x - w / 2, base_norm, width=w, color="#9aa3ab", label="Baseline (ad-hoc negotiation / routing)")
    ax.bar(x + w / 2, agri_norm, width=w, color="#1f6aa5", label="AgriMart AI (rule-based + VRPTW)")
    ax.set_xticks(x)
    ax.set_xticklabels(short_names, rotation=28, ha="right", fontsize=8.5)
    ax.set_ylabel("Value relative to the larger of the two (%)", fontsize=9.5)
    ax.set_title(
        "Settlement and routing evaluation: baseline vs. AgriMart AI\n(Monte Carlo simulation, N=2,000 shipments; values normalized per metric)",
        fontsize=10.5,
        fontweight="bold",
    )
    ax.legend(loc="upper right", fontsize=8.5)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "fig5_settlement_routing_eval.png"))
    plt.close(fig)

    print(f"All 4 publication figures saved to {FIGURES_DIR}")


if __name__ == "__main__":
    generate_all_figures()

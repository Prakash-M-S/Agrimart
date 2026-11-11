# AgriMart AI — Confidence-Aware Dynamic Pricing & Rule-Based Settlement Framework

**AgriMart AI** is an end-to-end, low-bandwidth agricultural supply-chain decision-support platform that integrates **Single-Layer Transformer Convolutional Encoder (STCE)** price forecasting with confidence bands, **SHAP** explainable AI, **Pre-Commitment Simulated Escrow**, a **Deterministic Rule-Based Settlement Engine**, **Perishability-Aware VRPTW Routing (Google OR-Tools)**, and **Next-Season Crop & NPK Advisory**.

---

## Project Structure (7 Modules from ICECMSN 2026 Paper & Report)

- **Module 1 — AGMARKNET Data Ingestion**: [`src/data/fetch_agmarknet.py`](file:///C:/Users/prasa/Desktop/Backend/AgriMart/src/data/fetch_agmarknet.py)
  - Pulls `410,698` real historical AGMARKNET Soyabean records (`2008–2017`) over the network, extracting the `2,718` raw Itarsi Mandi records (`data/raw/agmarknet_soyabean_itarsi_raw.csv`) and a `10,500`-row multi-mandi/multi-crop benchmark dataset (`data/raw/agmarknet_multi_mandi_sample.csv`).
- **Module 2 & 3 — Preprocessing & 12-Feature Engineering**: [`src/data/preprocess.py`](file:///C:/Users/prasa/Desktop/Backend/AgriMart/src/data/preprocess.py)
  - Removes `52` invalid records $\rightarrow$ aggregates `2,666` clean variety records into `2,359` arrival-weighted trading days $\rightarrow$ interpolates `1,101` non-trading days to form the `3,460`-day continuous series (`data/processed/itarsi_soyabean_continuous_3460.csv`) and constructs the 12 sequential market features with a strict chronological `70% / 15% / 15%` split.
- **Module 4 — STCE & Benchmark Forecasting**: [`src/models/stce.py`](file:///C:/Users/prasa/Desktop/Backend/AgriMart/src/models/stce.py) & [`src/evaluation/train_and_evaluate.py`](file:///C:/Users/prasa/Desktop/Backend/AgriMart/src/evaluation/train_and_evaluate.py)
  - Trains the PyTorch `STCE`, `STCE + uncertainty head`, `LSTM`, `GRU`, `LSTM-GRU Ensemble`, `ARIMA(2,1,2)`, and `Naive` baselines (`SEED=42, EPOCHS=100, BATCH_SIZE=32, LR=1e-3`). Saved model checkpoint: `models/stce_itarsi_soyabean.pt`.
- **Module 5 — SHAP Explainability & Pre-Commitment Escrow**: [`src/escrow/ledger.py`](file:///C:/Users/prasa/Desktop/Backend/AgriMart/src/escrow/ledger.py)
  - Computes gradient-based SHAP attributions (global & per-quotation) and manages the simulated escrow state machine with an append-only SHA-256 hash-chained audit trail (`data/audit_log.json`).
- **Module 6 — Rule-Based Settlement Engine**: [`src/settlement/engine.py`](file:///C:/Users/prasa/Desktop/Backend/AgriMart/src/settlement/engine.py)
  - Implements Equations (2)–(4): $P_{\text{mid}} = (P_L + P_U)/2$, $P_{\text{rule}} = P_{\text{mid}} + w_1\Delta_{\text{demand}} - w_2\Delta_{\text{delay}} - w_3 S_{\text{spoilage}} - w_4 Q_{\text{dev}}$, and $P_f = \min(P_U, \max(P_L, P_{\text{rule}}))$.
- **Module 7 — Perishability-Aware VRPTW, Monte Carlo & Advisory**: [`src/logistics/vrptw_solver.py`](file:///C:/Users/prasa/Desktop/Backend/AgriMart/src/logistics/vrptw_solver.py), [`src/evaluation/monte_carlo.py`](file:///C:/Users/prasa/Desktop/Backend/AgriMart/src/evaluation/monte_carlo.py), [`src/advisory/crop_advisor.py`](file:///C:/Users/prasa/Desktop/Backend/AgriMart/src/advisory/crop_advisor.py)
  - Solves $\min Z = C + \lambda D + \mu S$ using Google OR-Tools, ranks drivers by punctuality & dispute history, runs the $N = 2,000$ Monte Carlo simulation, and ranks next-season crops.

---

## Quick Start

### Option A: Zero-Setup Browser Mode (Instant)
Open [`index.html`](file:///C:/Users/prasa/Desktop/Backend/AgriMart/index.html) directly in any modern web browser. It loads [`static/agrimart_data.js`](file:///C:/Users/prasa/Desktop/Backend/AgriMart/static/agrimart_data.js) containing all trained STCE test predictions, SHAP attributions, Monte Carlo benchmarks, VRPTW routes, and `3,318` real AGMARKNET mandi records.

### Option B: Full-Stack FastAPI Server Mode
```bash
python app.py
```
Then open `http://127.0.0.1:8000` in your browser (or explore the interactive OpenAPI docs at `http://127.0.0.1:8000/docs`).

### Re-Running the Full Data, Training & Figure Pipeline
```bash
python src/data/fetch_agmarknet.py
python src/data/preprocess.py
python src/evaluation/train_and_evaluate.py
python src/evaluation/generate_plots.py
python src/evaluation/export_pwa_bundle.py
```

"""
Integration & End-to-End Workflow Tests for AgriMart AI FastAPI Server (`app.py`).
Tests all REST endpoints, static PWA serving, and the complete multi-actor transaction lifecycle:
  Quote -> Lock Escrow -> VRPTW Route & Driver Reassignment -> Rule-Based Settlement -> Audit Trail.
"""

from fastapi.testclient import TestClient
import pytest
from app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_pwa_static_routes_serve_cleanly(client):
    """Verifies root index.html, manifest.json, and sw.js are served with HTTP 200."""
    resp_home = client.get("/")
    assert resp_home.status_code == 200
    assert "AgriMart AI" in resp_home.text

    resp_manifest = client.get("/manifest.json")
    assert resp_manifest.status_code == 200

    resp_sw = client.get("/sw.js")
    assert resp_sw.status_code == 200


def test_experiment_summary_endpoint(client):
    """Verifies /api/experiment-summary returns trained STCE results, SHAP, and Table I/II metrics."""
    resp = client.get("/api/experiment-summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "preprocessing_summary" in data
    assert "table1_forecast_comparison" in data
    assert "shap_global_importance" in data
    assert len(data["shap_global_importance"]) == 12


def test_end_to_end_quotation_escrow_vrptw_settlement_audit_lifecycle(client):
    """
    Full Integration Test across Modules 4, 5, 6, and 7:
    1. Generate a load-specific STCE price quotation (/api/quote)
    2. Lock the pre-commitment escrow band (/api/escrow/{tx_id}/lock)
    3. Compute perishability-aware VRPTW route with driver decline (/api/vrptw)
    4. Execute quality-gated rule-based settlement (/api/settle)
    5. Verify the immutable SHA-256 hash-chained audit trail (/api/audit-trail)
    """
    # Step 1: Generate Quote
    quote_resp = client.post(
        "/api/quote",
        json={
            "commodity": "Soyabean",
            "mandi": "Itarsi",
            "load_tonnes": 2.4,
            "distance_km": 92.0,
            "perishability_index": 0.12,
        },
    )
    assert quote_resp.status_code == 200
    quote = quote_resp.json()
    tx_id = quote["tx_id"]
    assert quote["state"] == "QUOTE_GENERATED"
    assert quote["p_low"] == 3239.0
    assert quote["p_up"] == 3637.0
    assert quote["p_point"] == 3421.0

    # Step 2: Lock Escrow
    lock_resp = client.post(f"/api/escrow/{tx_id}/lock")
    assert lock_resp.status_code == 200
    locked = lock_resp.json()
    assert locked["state"] == "ESCROW_LOCKED"

    # Step 3: Solve Perishability-Aware VRPTW with driver decline
    vrptw_resp = client.post(
        "/api/vrptw",
        json={
            "load_tonnes": 2.4,
            "perishability_index": 0.12,
            "declined_driver_ids": ["DRV-MP04-101"],
        },
    )
    assert vrptw_resp.status_code == 200
    vrptw_data = vrptw_resp.json()
    assert vrptw_data["selected_driver"]["driver_id"] == "DRV-MP04-108"
    assert len(vrptw_data["route_stops"]) >= 3

    # Step 4: Settle Transaction within [P_L, P_U]
    settle_resp = client.post(
        "/api/settle",
        json={
            "tx_id": tx_id,
            "p_low": quote["p_low"],
            "p_up": quote["p_up"],
            "d_demand": 0.02,
            "d_delay": 1.5,
            "s_spoil": 0.10,
            "q_dev": 0.03,
        },
    )
    assert settle_resp.status_code == 200
    settle_data = settle_resp.json()
    assert settle_data["within_band"] is True
    assert quote["p_low"] <= settle_data["p_final"] <= quote["p_up"]

    # Step 5: Verify Audit Trail for this tx_id
    audit_resp = client.get(f"/api/audit-trail?tx_id={tx_id}")
    assert audit_resp.status_code == 200
    trail = audit_resp.json()["audit_trail"]
    event_types = [e["event_type"] for e in trail]
    assert "QUOTE_GENERATED" in event_types
    assert "ESCROW_LOCKED" in event_types
    assert "QUALITY_VERIFIED" in event_types
    assert "SETTLED_AND_ESCROW_RELEASED" in event_types


def test_advisory_and_monte_carlo_endpoints(client):
    """Verifies /api/advisory and /api/monte-carlo endpoints return valid structures."""
    adv_resp = client.get("/api/advisory?season=Rabi&n=50&p=55&k=40&rainfall=850")
    assert adv_resp.status_code == 200
    crops = adv_resp.json()["crops"]
    assert len(crops) >= 4
    assert crops[0]["rank"] == 1

    mc_resp = client.get("/api/monte-carlo?n_shipments=200&seed=99")
    assert mc_resp.status_code == 200
    mc_data = mc_resp.json()
    assert mc_data["n_shipments"] == 200
    assert mc_data["band_violations_agrimart"] == 0


def test_lock_nonexistent_escrow_returns_404(client):
    """Verifies locking an unknown transaction ID returns HTTP 404."""
    resp = client.post("/api/escrow/AGRI-NONEXISTENT/lock")
    assert resp.status_code == 404

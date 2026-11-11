"""
Unit Tests for Module 7: Perishability-Aware VRPTW Routing, Driver Pull Workflow & Crop Advisory.
"""

import pytest
from src.advisory.crop_advisor import rank_next_season_crops
from src.logistics.vrptw_solver import (
    DEFAULT_DRIVER_FLEET,
    rank_drivers_for_load,
    solve_perishability_vrptw,
)


def test_driver_ranking_and_pull_reassignment():
    """Verifies top driver offer, capacity feasibility, and automatic pull reassignment on decline."""
    initial_ranked = rank_drivers_for_load(load_tonnes=2.4, perishability_index=0.12)
    assert len(initial_ranked) == len(DEFAULT_DRIVER_FLEET)
    top_driver = initial_ranked[0]
    assert top_driver["rank"] == 1
    assert top_driver["status"] == "TOP_RANKED_OFFERED"
    assert top_driver["driver_id"] == "DRV-MP04-101"

    # Decline top driver -> second driver must become TOP_RANKED_OFFERED
    after_decline = rank_drivers_for_load(
        load_tonnes=2.4,
        perishability_index=0.12,
        declined_driver_ids=["DRV-MP04-101"],
    )
    assert after_decline[0]["driver_id"] == "DRV-MP04-108"
    assert after_decline[0]["status"] == "TOP_RANKED_OFFERED"
    declined_entry = next(d for d in after_decline if d["driver_id"] == "DRV-MP04-101")
    assert declined_entry["declined"] is True
    assert declined_entry["status"] == "DECLINED_REASSIGNED"


def test_driver_capacity_feasibility_and_cold_chain_bonus():
    """Heavy loads (>5T) must mark smaller trucks as UNDER_CAPACITY and prioritize 10T truck."""
    heavy_ranked = rank_drivers_for_load(load_tonnes=7.5, perishability_index=0.55)
    assert heavy_ranked[0]["driver_id"] == "DRV-MP04-101"
    assert heavy_ranked[0]["capacity_feasible"] is True
    for drv in heavy_ranked[1:]:
        assert drv["capacity_feasible"] is False
        assert drv["status"] == "UNDER_CAPACITY"


def test_solve_perishability_vrptw_objective_and_stops():
    """Verifies VRPTW solver returns valid route stops, time windows, and composite objective Z."""
    sol = solve_perishability_vrptw(load_tonnes=2.4, perishability_index=0.12)
    assert sol["total_distance_km"] > 0
    assert sol["estimated_transit_time_h"] > 0
    assert sol["objective_z"] >= sol["transport_cost_inr"]
    assert sol["urgency_priority"] == "STANDARD_PERISHABLE"
    assert len(sol["route_stops"]) >= 3
    assert sol["route_stops"][0]["node_id"] == 0

    high_perish_sol = solve_perishability_vrptw(load_tonnes=2.4, perishability_index=0.75)
    assert high_perish_sol["urgency_priority"] == "HIGH"
    assert high_perish_sol["expected_spoilage_rate_pct"] > sol["expected_spoilage_rate_pct"]


def test_crop_advisory_ranking_and_season_filter():
    """Verifies composite score ordering, rank assignment, and season filtering."""
    all_crops = rank_next_season_crops(season_filter="ALL", soil_n=35.0, rainfall_mm=950.0)
    assert len(all_crops) == 7
    assert all_crops[0]["rank"] == 1
    assert "Soyabean" in all_crops[0]["crop"]
    # Verify monotonic non-increasing order of composite_score
    scores = [c["composite_score"] for c in all_crops]
    assert scores == sorted(scores, reverse=True)

    rabi_only = rank_next_season_crops(season_filter="Rabi")
    assert all("rabi" in c["season"].lower() for c in rabi_only)
    assert len(rabi_only) < len(all_crops)

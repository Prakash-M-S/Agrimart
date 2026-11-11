"""
Unit Tests for Module 6: Rule-Based Settlement Engine (Equations 2-4) & Jain's Fairness Index.
"""

import numpy as np
import pytest
from src.settlement.engine import (
    DEFAULT_WEIGHTS,
    SettlementResult,
    compute_detailed_settlement,
    jains_fairness_index,
    settle,
)


def test_settle_zero_offsets_returns_exact_midpoint():
    """When demand shift, delay, spoilage, and quality deviation are zero, P_f == P_mid."""
    p_low, p_up = 3239.0, 3637.0
    pf = settle(p_low, p_up, d_demand=0.0, d_delay=0.0, s_spoil=0.0, q_dev=0.0)
    assert pf == pytest.approx(3438.0, abs=1e-6)


def test_settle_formula_interior_point():
    """Verifies exact arithmetic of P_rule = P_mid + w1*d_demand - w2*d_delay - w3*s_spoil - w4*q_dev."""
    p_low, p_up = 3239.0, 3637.0
    p_mid = 3438.0
    d_demand, d_delay, s_spoil, q_dev = 0.02, 1.8, 0.105, 0.04
    w1, w2, w3, w4 = DEFAULT_WEIGHTS

    expected_rule = p_mid + w1 * d_demand - w2 * d_delay - w3 * s_spoil - w4 * q_dev
    pf = settle(p_low, p_up, d_demand, d_delay, s_spoil, q_dev)
    assert pf == pytest.approx(expected_rule, abs=1e-5)
    assert p_low <= pf <= p_up


def test_settle_clamps_strictly_to_lower_bound():
    """Severe delay, spoilage, and quality penalties must never drop P_f below P_L."""
    p_low, p_up = 3239.0, 3637.0
    pf = settle(p_low, p_up, d_demand=-0.50, d_delay=12.0, s_spoil=0.95, q_dev=0.50)
    assert pf == pytest.approx(p_low, abs=1e-6)

    detailed = compute_detailed_settlement(
        p_low, p_up, d_demand=-0.50, d_delay=12.0, s_spoil=0.95, q_dev=0.50
    )
    assert detailed.clamped_to_lower is True
    assert detailed.clamped_to_upper is False
    assert detailed.within_band is True
    assert detailed.p_final == p_low
    assert detailed.p_rule < p_low


def test_settle_clamps_strictly_to_upper_bound():
    """Extreme positive demand surge must never push P_f above P_U."""
    p_low, p_up = 3239.0, 3637.0
    pf = settle(p_low, p_up, d_demand=1.20, d_delay=0.0, s_spoil=0.0, q_dev=0.0)
    assert pf == pytest.approx(p_up, abs=1e-6)

    detailed = compute_detailed_settlement(
        p_low, p_up, d_demand=1.20, d_delay=0.0, s_spoil=0.0, q_dev=0.0
    )
    assert detailed.clamped_to_upper is True
    assert detailed.clamped_to_lower is False
    assert detailed.within_band is True
    assert detailed.p_final == p_up
    assert detailed.p_rule > p_up


def test_compute_detailed_settlement_audit_breakdown():
    """Checks that individual factor offsets sum to total_offset and serialize cleanly."""
    res = compute_detailed_settlement(
        p_low=3000.0,
        p_up=3400.0,
        d_demand=0.05,
        d_delay=2.0,
        s_spoil=0.10,
        q_dev=0.05,
    )
    assert isinstance(res, SettlementResult)
    assert res.p_mid == 3200.0
    assert res.offset_demand == pytest.approx(320.0 * 0.05, abs=1e-2)
    assert res.offset_delay == pytest.approx(-12.5 * 2.0, abs=1e-2)
    assert res.offset_spoilage == pytest.approx(-240.0 * 0.10, abs=1e-2)
    assert res.offset_quality == pytest.approx(-280.0 * 0.05, abs=1e-2)
    assert res.total_offset == pytest.approx(
        res.offset_demand + res.offset_delay + res.offset_spoilage + res.offset_quality,
        abs=1e-2,
    )
    as_dict = res.to_dict()
    assert as_dict["within_band"] is True
    assert "midpoint_deviation_pct" in as_dict


def test_jains_fairness_index_properties():
    """Verifies Jain's Fairness Index equals 1.0 for uniform arrays and stays in (0, 1]."""
    uniform = np.ones(100) * 3438.0
    assert jains_fairness_index(uniform) == pytest.approx(1.0, abs=1e-9)

    realistic_ratios = np.array([0.98, 1.01, 0.99, 1.00, 0.97, 1.02])
    j_val = jains_fairness_index(realistic_ratios)
    assert 0.99 <= j_val <= 1.0

    assert jains_fairness_index(np.array([])) == 1.0
    assert jains_fairness_index(np.zeros(5)) == 1.0

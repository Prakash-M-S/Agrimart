"""
Unit Tests for Module 5 (Part B): Pre-Commitment Simulated Escrow & Append-Only Audit Ledger.
"""

import pytest
from src.escrow.ledger import EscrowAuditLedger
from src.settlement.engine import compute_detailed_settlement


def test_escrow_full_lifecycle_and_hash_chain(tmp_path):
    """Tests quotation creation, lock, renegotiation, dispatch, quality check, settlement, and SHA-256 chain."""
    log_file = tmp_path / "test_audit_log.json"
    ledger = EscrowAuditLedger(log_path=str(log_file))

    # 1. Create Quotation
    quote = ledger.create_quotation(
        commodity="Soyabean",
        mandi="Itarsi",
        load_tonnes=2.4,
        p_point=3421.0,
        p_low=3239.0,
        p_up=3637.0,
        coverage_pct=92.35,
        shap_reasons=[{"feature": "Recent Modal Price", "mean_abs_shap": 0.0138}],
    )
    tx_id = quote["tx_id"]
    assert quote["state"] == "QUOTE_GENERATED"
    assert quote["load_quintals"] == 24.0
    assert quote["p_mid"] == 3438.0
    assert quote["escrow_deposit_inr"] == pytest.approx(3438.0 * 24.0, abs=1e-2)

    # 2. Request Renegotiation
    reneg = ledger.request_renegotiation(
        tx_id=tx_id,
        requested_low=3280.0,
        requested_up=3660.0,
        reason="Low mandi arrivals in Hoshangabad belt",
    )
    assert reneg["state"] == "RENEGOTIATION_REQUESTED"

    # 3. Lock Escrow
    locked = ledger.lock_escrow(tx_id)
    assert locked["state"] == "ESCROW_LOCKED"

    # 4. Record VRPTW Driver Assignment & Transit
    transit = ledger.record_routing_and_transit(
        tx_id=tx_id,
        driver_id="DRV-MP04-101",
        route_summary={"total_distance_km": 226.0, "estimated_transit_time_h": 14.41},
    )
    assert transit["state"] == "IN_TRANSIT"
    assert transit["driver_id"] == "DRV-MP04-101"

    # 5. Verify Quality & Settle
    settlement = compute_detailed_settlement(
        p_low=3239.0,
        p_up=3637.0,
        d_demand=0.01,
        d_delay=1.2,
        s_spoil=0.09,
        q_dev=0.02,
    ).to_dict()
    settled = ledger.verify_quality_and_settle(tx_id, settlement)
    assert settled["state"] == "SETTLED_AND_RELEASED"
    assert settled["quality_verified"] is True
    assert settled["payout_released_inr"] == pytest.approx(settlement["p_final"] * 24.0, abs=1e-1)

    # 6. Verify Audit Trail & Persistence Reload
    trail = ledger.get_audit_trail(tx_id=tx_id)
    assert len(trail) == 6  # QUOTE, RENEG, LOCK, DISPATCH, QUALITY_VERIFIED, SETTLED
    for record in trail:
        assert len(record["record_hash"]) == 64

    # Reload from disk into a fresh instance to verify JSON persistence
    reloaded = EscrowAuditLedger(log_path=str(log_file))
    persisted_escrow = reloaded.get_escrow(tx_id)
    assert persisted_escrow is not None
    assert persisted_escrow["state"] == "SETTLED_AND_RELEASED"
    assert len(reloaded.get_all_escrows()) == 1

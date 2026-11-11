"""
Module 5 (Part B): Pre-Commitment Simulated Escrow & Append-Only Audit Ledger
Manages contractual state transitions from quotation to quality-gated payout
and records an immutable, hash-chained audit trail.
"""

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


AUDIT_LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "audit_log.json",
)


class EscrowAuditLedger:
    """
    Simulated internal escrow ledger with an append-only audit trail.
    States:
      - QUOTE_GENERATED
      - ESCROW_LOCKED
      - RENEGOTIATION_REQUESTED
      - DRIVER_ASSIGNED
      - IN_TRANSIT
      - QUALITY_INSPECTED
      - SETTLED_AND_RELEASED
    """

    def __init__(self, log_path: str = AUDIT_LOG_PATH):
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        self._records: List[Dict[str, Any]] = []
        self._escrows: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._records = data.get("audit_trail", [])
                    self._escrows = data.get("escrows", {})
            except Exception:
                self._records = []
                self._escrows = {}

    def _save(self) -> None:
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(
                {"escrows": self._escrows, "audit_trail": self._records},
                f,
                indent=2,
            )

    def _append_event(
        self,
        tx_id: str,
        event_type: str,
        actor: str,
        details: Dict[str, Any],
    ) -> Dict[str, Any]:
        prev_hash = self._records[-1]["record_hash"] if self._records else "0" * 64
        timestamp = datetime.now(timezone.utc).isoformat()
        seq_no = len(self._records) + 1

        payload_str = json.dumps(
            {
                "seq_no": seq_no,
                "tx_id": tx_id,
                "timestamp": timestamp,
                "event_type": event_type,
                "actor": actor,
                "details": details,
                "prev_hash": prev_hash,
            },
            sort_keys=True,
        )
        record_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

        entry = {
            "seq_no": seq_no,
            "tx_id": tx_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "actor": actor,
            "details": details,
            "prev_hash": prev_hash[:16] + "...",
            "record_hash": record_hash,
        }
        self._records.append(entry)
        self._save()
        return entry

    def create_quotation(
        self,
        commodity: str,
        mandi: str,
        load_tonnes: float,
        p_point: float,
        p_low: float,
        p_up: float,
        coverage_pct: float,
        shap_reasons: List[Dict[str, Any]],
        farmer_id: str = "FARMER-MP-104",
        wholesaler_id: str = "WHOLESALE-ITR-22",
    ) -> Dict[str, Any]:
        tx_id = f"AGRI-{int(time.time() * 1000) % 1000000:06d}"
        p_mid = round((p_low + p_up) / 2.0, 2)
        load_quintals = round(load_tonnes * 10.0, 2)
        escrow_deposit_inr = round(p_mid * load_quintals, 2)

        escrow_obj = {
            "tx_id": tx_id,
            "commodity": commodity,
            "mandi": mandi,
            "load_tonnes": load_tonnes,
            "load_quintals": load_quintals,
            "p_point": round(p_point, 2),
            "p_low": round(p_low, 2),
            "p_up": round(p_up, 2),
            "p_mid": p_mid,
            "coverage_pct": round(coverage_pct, 2),
            "escrow_deposit_inr": escrow_deposit_inr,
            "farmer_id": farmer_id,
            "wholesaler_id": wholesaler_id,
            "driver_id": None,
            "state": "QUOTE_GENERATED",
            "shap_reasons": shap_reasons,
            "settlement": None,
            "quality_verified": False,
            "payout_released_inr": None,
        }
        self._escrows[tx_id] = escrow_obj
        self._append_event(
            tx_id=tx_id,
            event_type="QUOTE_GENERATED",
            actor="STCE_FORECAST_ENGINE",
            details={
                "commodity": commodity,
                "mandi": mandi,
                "load_tonnes": load_tonnes,
                "price_band_inr_q": [round(p_low, 2), round(p_up, 2)],
                "point_forecast_inr_q": round(p_point, 2),
                "interval_coverage_pct": round(coverage_pct, 2),
            },
        )
        return escrow_obj

    def lock_escrow(self, tx_id: str, actor: str = "FARMER & WHOLESALER") -> Dict[str, Any]:
        escrow = self._escrows[tx_id]
        escrow["state"] = "ESCROW_LOCKED"
        self._append_event(
            tx_id=tx_id,
            event_type="ESCROW_LOCKED",
            actor=actor,
            details={
                "committed_band_inr_q": [escrow["p_low"], escrow["p_up"]],
                "simulated_escrow_locked_inr": escrow["escrow_deposit_inr"],
            },
        )
        return escrow

    def request_renegotiation(
        self, tx_id: str, requested_low: float, requested_up: float, reason: str
    ) -> Dict[str, Any]:
        escrow = self._escrows[tx_id]
        escrow["state"] = "RENEGOTIATION_REQUESTED"
        self._append_event(
            tx_id=tx_id,
            event_type="RENEGOTIATION_REQUESTED",
            actor=escrow["farmer_id"],
            details={
                "previous_band": [escrow["p_low"], escrow["p_up"]],
                "requested_band": [round(requested_low, 2), round(requested_up, 2)],
                "reason": reason,
            },
        )
        return escrow

    def record_routing_and_transit(
        self,
        tx_id: str,
        driver_id: str,
        route_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        escrow = self._escrows[tx_id]
        escrow["driver_id"] = driver_id
        escrow["state"] = "IN_TRANSIT"
        self._append_event(
            tx_id=tx_id,
            event_type="DRIVER_ASSIGNED_AND_DISPATCHED",
            actor=driver_id,
            details=route_summary,
        )
        return escrow

    def verify_quality_and_settle(
        self,
        tx_id: str,
        settlement_result: Dict[str, Any],
        quality_note: str = "Moisture & grading verified at destination mandi gate",
    ) -> Dict[str, Any]:
        escrow = self._escrows[tx_id]
        escrow["quality_verified"] = True
        escrow["settlement"] = settlement_result
        escrow["state"] = "SETTLED_AND_RELEASED"
        final_price_q = settlement_result["p_final"]
        total_payout = round(final_price_q * escrow["load_quintals"], 2)
        escrow["payout_released_inr"] = total_payout

        self._append_event(
            tx_id=tx_id,
            event_type="QUALITY_VERIFIED",
            actor=escrow["wholesaler_id"],
            details={
                "quality_deviation_penalty": settlement_result["q_dev"],
                "spoilage_index": settlement_result["s_spoil"],
                "verification_note": quality_note,
            },
        )
        self._append_event(
            tx_id=tx_id,
            event_type="SETTLED_AND_ESCROW_RELEASED",
            actor="RULE_BASED_SETTLEMENT_ENGINE",
            details={
                "p_low": settlement_result["p_low"],
                "p_up": settlement_result["p_up"],
                "p_mid": settlement_result["p_mid"],
                "p_rule": settlement_result["p_rule"],
                "p_final_inr_q": final_price_q,
                "within_committed_band": settlement_result["within_band"],
                "total_payout_released_inr": total_payout,
            },
        )
        return escrow

    def get_audit_trail(self, tx_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if tx_id:
            return [r for r in self._records if r["tx_id"] == tx_id]
        return list(reversed(self._records[-100:]))

    def get_escrow(self, tx_id: str) -> Optional[Dict[str, Any]]:
        return self._escrows.get(tx_id)

    def get_all_escrows(self) -> List[Dict[str, Any]]:
        return list(self._escrows.values())

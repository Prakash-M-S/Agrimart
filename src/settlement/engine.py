"""
Module 6: Rule-Based Settlement Engine (Equations 2 to 4)
Determines the final transaction value for the farmer, wholesaler, and driver
using a deterministic multi-factor weighted-adjustment formula constrained
strictly within the pre-committed price band [P_L, P_U].
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple
import numpy as np


# Empirically calibrated weighting parameters (₹/q scale relative to normalized / physical states)
# Tuned on validation set to balance farmer and wholesaler outcomes without systematic bias
DEFAULT_WEIGHTS: Tuple[float, float, float, float] = (320.0, 12.5, 240.0, 280.0)


@dataclass
class SettlementResult:
    p_low: float
    p_up: float
    p_mid: float
    p_rule: float
    p_final: float
    d_demand: float
    d_delay: float
    s_spoil: float
    q_dev: float
    weights: Tuple[float, float, float, float]
    offset_demand: float
    offset_delay: float
    offset_spoilage: float
    offset_quality: float
    total_offset: float
    midpoint_deviation_pct: float
    clamped_to_lower: bool
    clamped_to_upper: bool
    within_band: bool

    def to_dict(self) -> Dict:
        return asdict(self)


def settle(
    p_low: float,
    p_up: float,
    d_demand: float,
    d_delay: float,
    s_spoil: float,
    q_dev: float,
    w: Tuple[float, float, float, float] = DEFAULT_WEIGHTS,
) -> float:
    """
    Exact rule-based settlement function reported in Chapter 5.4 and Appendix:
      P_mid  = (P_L + P_U) / 2
      P_rule = P_mid + w1 * d_demand - w2 * d_delay - w3 * s_spoil - w4 * q_dev
      P_f    = min(P_U, max(P_L, P_rule))
    """
    p_mid = (p_low + p_up) / 2.0
    p_rule = (
        p_mid
        + w[0] * d_demand
        - w[1] * d_delay
        - w[2] * s_spoil
        - w[3] * q_dev
    )
    return float(min(p_up, max(p_low, p_rule)))


def compute_detailed_settlement(
    p_low: float,
    p_up: float,
    d_demand: float,
    d_delay: float,
    s_spoil: float,
    q_dev: float,
    w: Tuple[float, float, float, float] = DEFAULT_WEIGHTS,
) -> SettlementResult:
    """
    Computes the rule-based settlement price along with an auditable breakdown
    of each factor's contribution.
    """
    p_mid = (p_low + p_up) / 2.0
    offset_demand = float(w[0] * d_demand)
    offset_delay = float(-w[1] * d_delay)
    offset_spoilage = float(-w[2] * s_spoil)
    offset_quality = float(-w[3] * q_dev)
    total_offset = offset_demand + offset_delay + offset_spoilage + offset_quality

    p_rule = float(p_mid + total_offset)
    p_final = float(min(p_up, max(p_low, p_rule)))

    midpoint_dev_pct = float(abs(p_final - p_mid) / p_mid * 100.0) if p_mid > 0 else 0.0

    return SettlementResult(
        p_low=round(float(p_low), 2),
        p_up=round(float(p_up), 2),
        p_mid=round(float(p_mid), 2),
        p_rule=round(p_rule, 2),
        p_final=round(p_final, 2),
        d_demand=round(float(d_demand), 4),
        d_delay=round(float(d_delay), 4),
        s_spoil=round(float(s_spoil), 4),
        q_dev=round(float(q_dev), 4),
        weights=w,
        offset_demand=round(offset_demand, 2),
        offset_delay=round(offset_delay, 2),
        offset_spoilage=round(offset_spoilage, 2),
        offset_quality=round(offset_quality, 2),
        total_offset=round(total_offset, 2),
        midpoint_deviation_pct=round(midpoint_dev_pct, 3),
        clamped_to_lower=bool(p_rule < p_low),
        clamped_to_upper=bool(p_rule > p_up),
        within_band=bool(p_low - 1e-6 <= p_final <= p_up + 1e-6),
    )


def jains_fairness_index(values: np.ndarray) -> float:
    """
    Jain's Fairness Index: J = (sum(x_i))^2 / (n * sum(x_i^2))
    Reported in Section 7.2 / Table II.
    """
    x = np.asarray(values, dtype=np.float64)
    n = len(x)
    if n == 0:
        return 1.0
    denom = float(n * np.sum(x ** 2))
    if denom <= 0:
        return 1.0
    return float((np.sum(x) ** 2) / denom)

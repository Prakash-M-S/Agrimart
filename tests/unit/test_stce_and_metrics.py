"""
Unit Tests for Module 4: STCE Neural Architectures, Sequence Builder & Forecasting Metrics.
"""

import numpy as np
import pytest
import torch
from src.models.stce import (
    GRUForecaster,
    LSTMForecaster,
    SEQ_LEN,
    STCE,
    STCEUncertaintyHead,
    build_sequences,
    coverage,
    mae,
    mape,
    rmse,
)


def test_stce_forward_shape_and_gradients():
    """Verifies STCE forward pass output dimensions and backpropagation gradients."""
    model = STCE(n_feat=12, d_model=64, n_heads=4, kernel=3)
    x = torch.randn(8, SEQ_LEN, 12, requires_grad=True)
    out = model(x)
    assert out.shape == (8, 1)
    loss = out.sum()
    loss.backward()
    assert x.grad is not None
    assert torch.isfinite(out).all()


def test_stce_uncertainty_head_positive_scale():
    """Verifies STCEUncertaintyHead outputs (mean, scale) with strictly positive scale."""
    model = STCEUncertaintyHead(n_feat=12, d_model=64, n_heads=4, kernel=3)
    x = torch.randn(6, SEQ_LEN, 12)
    mean, scale = model(x)
    assert mean.shape == (6, 1)
    assert scale.shape == (6, 1)
    assert (scale > 0).all()


def test_lstm_and_gru_forecasters():
    """Verifies LSTMForecaster and GRUForecaster forward shapes on 12-feature sequences."""
    x = torch.randn(4, SEQ_LEN, 12)
    lstm = LSTMForecaster(n_feat=12, hidden_size=32)
    gru = GRUForecaster(n_feat=12, hidden_size=32)
    assert lstm(x).shape == (4, 1)
    assert gru(x).shape == (4, 1)


def test_build_sequences_sliding_window():
    """Verifies sliding window sequence construction length and alignment."""
    feats = np.arange(50 * 12, dtype=np.float32).reshape(50, 12)
    targets = np.arange(50, dtype=np.float32)
    xs, ys = build_sequences(feats, targets, seq_len=14)
    assert xs.shape == (36, 14, 12)
    assert ys.shape == (36,)
    assert ys[0] == targets[13]


def test_evaluation_metrics_equations_6_to_9():
    """Verifies RMSE, MAE, MAPE, and Empirical Interval Coverage calculation."""
    y = np.array([3400.0, 3500.0, 3600.0, 3300.0])
    p = np.array([3420.0, 3480.0, 3630.0, 3270.0])
    lo = p - 25.0
    up = p + 25.0

    assert mae(y, p) == pytest.approx(25.0, abs=1e-5)
    assert rmse(y, p) == pytest.approx(np.sqrt((400 + 400 + 900 + 900) / 4.0), abs=1e-5)
    assert mape(y, p) > 0.0
    # Errors are 20, 20, 30, 30 -> first 2 inside +/-25, last 2 outside -> 50% coverage
    assert coverage(y, lo, up) == pytest.approx(50.0, abs=1e-5)

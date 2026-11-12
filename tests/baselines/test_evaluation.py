from __future__ import annotations

import numpy as np

from ntnbinance.baselines.evaluation import backtest, classification_metrics
from ntnbinance.baselines.models import BaselineSample
from ntnbinance.labels.models import Label, LabelReason
from ntnbinance.splits.models import Partition


def _sample(reason: LabelReason, label: Label) -> BaselineSample:
    return BaselineSample(
        sample_id="sample",
        partition=Partition.VALIDATION,
        symbol="BTCUSDT",
        decision_time_ms=1,
        vertical_barrier_time_ms=2,
        label=label,
        reason=reason,
        reference_price=100.0,
        upper_barrier=102.0,
        lower_barrier=98.0,
        barrier_time_ms=2,
        execution_cost=0.001,
        funding_cost=0.0002,
        vertical_close=101.0,
        features=(0.0,) * 13,
    )


def test_complete_metrics_for_perfect_predictions() -> None:
    truth = ["LONG", "SHORT", "NO_TRADE"]
    probabilities = np.eye(3, dtype=np.float64)
    metrics = classification_metrics(truth, truth, probabilities)

    assert metrics.accuracy == 1.0
    assert metrics.macro_f1 == 1.0
    assert metrics.multiclass_brier == 0.0
    assert metrics.ece_10_bin == 0.0
    assert metrics.per_class["SHORT"]["recall"] == 1.0


def test_backtest_applies_direction_cost_and_adverse_ambiguity() -> None:
    samples = [
        _sample(LabelReason.UPPER_BARRIER_NET_POSITIVE, Label.LONG),
        _sample(LabelReason.AMBIGUOUS_INTRABAR, Label.NO_TRADE),
        _sample(LabelReason.VERTICAL_BARRIER, Label.NO_TRADE),
    ]
    result = backtest(samples, ["LONG", "LONG", "SHORT"])

    # +2%-fee-funding, -2%-fee, -1%-fee.
    np.testing.assert_allclose(result.net_return_sum, -0.0132, atol=1e-12)
    assert result.trades == 3
    assert result.maximum_drawdown > 0

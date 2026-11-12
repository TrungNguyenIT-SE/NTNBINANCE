"""Complete classification, calibration and cost-aware baseline evaluation."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

from ntnbinance.baselines.models import BacktestMetrics, BaselineSample, MetricSet
from ntnbinance.labels.models import Label, LabelReason


def classification_metrics(
    truth: Sequence[str], predictions: Sequence[str], probabilities: NDArray[np.float64]
) -> MetricSet:
    labels = [label.value for label in Label]
    precision, recall, f1, support = precision_recall_fscore_support(
        truth, predictions, labels=labels, zero_division=0
    )
    encoded = np.asarray([[1.0 if value == label else 0.0 for label in labels] for value in truth])
    brier = float(np.mean(np.sum((probabilities - encoded) ** 2, axis=1)))
    confidence = np.max(probabilities, axis=1)
    predicted_index = np.argmax(probabilities, axis=1)
    pairs = zip(predicted_index, truth, strict=True)
    correct = np.asarray([labels[index] == value for index, value in pairs])
    ece = 0.0
    for lower in np.linspace(0.0, 0.9, 10):
        upper = lower + 0.1
        mask = (confidence > lower) & (confidence <= upper)
        if np.any(mask):
            observed = float(np.mean(correct[mask]))
            expected = float(np.mean(confidence[mask]))
            calibration_gap = abs(observed - expected)
            ece += float(np.mean(mask)) * calibration_gap
    per_class = {
        label: {
            "precision": float(precision[index]),
            "recall": float(recall[index]),
            "f1": float(f1[index]),
            "support": int(support[index]),
        }
        for index, label in enumerate(labels)
    }
    return MetricSet(
        accuracy=float(accuracy_score(truth, predictions)),
        macro_f1=float(np.mean(f1)),
        macro_precision=float(np.mean(precision)),
        macro_recall=float(np.mean(recall)),
        per_class=per_class,
        multiclass_brier=brier,
        ece_10_bin=ece,
    )


def _trade_return(sample: BaselineSample, prediction: str) -> float:
    if prediction == Label.NO_TRADE.value:
        return 0.0
    direction = 1.0 if prediction == Label.LONG.value else -1.0
    if sample.reason is LabelReason.UPPER_BARRIER_NET_POSITIVE:
        exit_price = sample.upper_barrier
        funding = sample.funding_cost if direction > 0 else -sample.funding_cost
    elif sample.reason is LabelReason.LOWER_BARRIER_NET_POSITIVE:
        exit_price = sample.lower_barrier
        funding = sample.funding_cost if direction < 0 else -sample.funding_cost
    elif sample.reason is LabelReason.AMBIGUOUS_INTRABAR:
        exit_price = sample.lower_barrier if direction > 0 else sample.upper_barrier
        funding = 0.0
    elif sample.reason is LabelReason.VERTICAL_BARRIER:
        exit_price = sample.vertical_close
        funding = 0.0
    else:
        # Cost-removed/data-quality rows are fail-safe losses for a directional decision.
        exit_price = sample.lower_barrier if direction > 0 else sample.upper_barrier
        funding = 0.0
    gross = direction * (exit_price / sample.reference_price - 1.0)
    return gross - sample.execution_cost - funding


def backtest(samples: Sequence[BaselineSample], predictions: Sequence[str]) -> BacktestMetrics:
    returns = [
        _trade_return(sample, prediction)
        for sample, prediction in zip(samples, predictions, strict=True)
    ]
    trades = [
        value
        for value, prediction in zip(returns, predictions, strict=True)
        if prediction != Label.NO_TRADE.value
    ]
    equity = 1.0
    peak = 1.0
    maximum_drawdown = 0.0
    for value in returns:
        equity *= 1.0 + value
        peak = max(peak, equity)
        maximum_drawdown = max(maximum_drawdown, 1.0 - equity / peak)
    return BacktestMetrics(
        samples=len(samples),
        trades=len(trades),
        trade_rate=0.0 if not samples else len(trades) / len(samples),
        net_return_sum=sum(returns),
        mean_return_per_sample=0.0 if not returns else sum(returns) / len(returns),
        mean_return_per_trade=0.0 if not trades else sum(trades) / len(trades),
        win_rate=0.0 if not trades else sum(value > 0 for value in trades) / len(trades),
        maximum_drawdown=maximum_drawdown,
    )

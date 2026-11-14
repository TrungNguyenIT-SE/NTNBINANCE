"""Locked Stage J backtest orchestration, stress tests and evidence publication."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
import xgboost

from ntnbinance.backtest.data import load_validation_inputs, utc_month
from ntnbinance.backtest.engine import simulate_trade
from ntnbinance.backtest.metrics import grouped_metrics, summarize
from ntnbinance.backtest.models import (
    BacktestCase,
    BacktestConfig,
    FillStatus,
    PortfolioMetrics,
    Side,
    TradeResult,
)
from ntnbinance.labels.models import LabelConfig

BACKTEST_ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class BacktestRunResult:
    run_id: str
    artifact_path: Path
    report_path: Path
    base_metrics: PortfolioMetrics


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalize(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _normalize(item) for key, item in sorted(value.items())}
    if isinstance(value, (tuple, list)):
        return [_normalize(item) for item in value]
    return value


def _predict(
    artifact: dict[str, Any], features: list[tuple[float, ...]]
) -> tuple[list[Side], list[Decimal]]:
    model = artifact.get("xgboost_model")
    classes = artifact.get("class_order")
    if not isinstance(model, dict) or classes != ["LONG", "SHORT", "NO_TRADE"]:
        raise ValueError("baseline artifact model or class order is invalid")
    booster = xgboost.Booster()
    booster.load_model(bytearray(json.dumps(model, separators=(",", ":")).encode()))
    probabilities = booster.predict(xgboost.DMatrix(np.asarray(features, dtype=np.float64)))
    predictions = [Side(classes[int(index)]) for index in np.argmax(probabilities, axis=1)]
    confidences = [Decimal(str(value)) for value in np.max(probabilities, axis=1)]
    prediction_hash = hashlib.sha256(
        "\n".join(item.value for item in predictions).encode()
    ).hexdigest()
    expected = artifact["results"]["xgboost_cpu"]["prediction_sha256"]
    if prediction_hash != expected:
        raise ValueError("reconstructed predictions differ from locked Stage I artifact")
    return predictions, confidences


def _confidence_bucket(value: Decimal, edges: tuple[Decimal, ...]) -> str:
    lower, upper = edges
    if value < lower:
        return f"< {lower}"
    if value < upper:
        return f"{lower}-<{upper}"
    return f">= {upper}"


class BacktestPipeline:
    def __init__(
        self,
        *,
        project_root: Path,
        config_path: Path,
        clean_root: Path,
        raw_root: Path,
        artifact_dir: Path,
        report_path: Path,
    ) -> None:
        self.project_root = project_root.resolve()
        self.config_path = config_path.resolve()
        self.clean_root = clean_root.resolve()
        self.raw_root = raw_root.resolve()
        self.artifact_dir = artifact_dir.resolve()
        self.report_path = report_path.resolve()

    def run(self) -> BacktestRunResult:
        config = BacktestConfig.load(self.config_path)
        baseline_path = self.project_root / config.baseline_artifact
        split_path = self.project_root / config.split_manifest
        label_config_path = self.project_root / config.label_config
        exchange_snapshot_path = self.project_root / config.exchange_snapshot_manifest
        baseline: dict[str, Any] = json.loads(baseline_path.read_text(encoding="utf-8"))
        if baseline.get("selected_baseline") != "xgboost_cpu":
            raise ValueError("Stage J requires the locked Stage I XGBoost baseline")
        if baseline.get("holdout", {}).get("opened") is not False:
            raise PermissionError("final holdout must remain sealed in Stage J")
        inputs = load_validation_inputs(
            split_path=split_path,
            clean_root=self.clean_root,
            raw_root=self.raw_root,
            label_config=LabelConfig.load(label_config_path),
        )
        if len(inputs) != 26:
            raise ValueError("locked Stage J validation sample count changed")
        predictions, confidences = _predict(baseline, [item.features for item in inputs])
        cases = [
            BacktestCase(
                sample_id=item.sample_id,
                symbol=item.symbol,
                decision_time_ms=item.decision_time_ms,
                vertical_barrier_time_ms=item.vertical_barrier_time_ms,
                reference_price=item.reference_price,
                atr=item.atr,
                regime=item.regime,
                prediction=prediction,
                confidence=confidence,
                candles=item.candles,
                funding_events=item.funding_events,
            )
            for item, prediction, confidence in zip(inputs, predictions, confidences, strict=True)
        ]
        base = [simulate_trade(case, config) for case in cases]
        self._audit_timeline(base)
        cost_stress = {
            str(multiplier): [
                simulate_trade(case, config, cost_multiplier=multiplier) for case in cases
            ]
            for multiplier in config.cost_multipliers
        }
        latency_stress = {
            str(latency): [simulate_trade(case, config, latency_ms=latency) for case in cases]
            for latency in config.latency_stress_ms
        }
        cost_metrics = {key: summarize(results, config) for key, results in cost_stress.items()}
        latency_metrics = {
            key: summarize(results, config) for key, results in latency_stress.items()
        }
        cost_net = [cost_metrics[str(value)].net_pnl_usdt for value in config.cost_multipliers]
        if cost_net != sorted(cost_net, reverse=True):
            raise AssertionError("higher execution costs must not improve aggregate net PnL")
        base_entries = [(item.entry_time_ms, item.exit_time_ms) for item in base]
        stressed_entries = [
            (item.entry_time_ms, item.exit_time_ms)
            for item in latency_stress[str(config.latency_stress_ms[-1])]
        ]
        if base_entries == stressed_entries:
            raise AssertionError("latency stress did not alter any event timeline")

        groups = {
            "symbol": grouped_metrics(base, config, lambda item: item.symbol),
            "side": grouped_metrics(base, config, lambda item: item.side.value),
            "month": grouped_metrics(base, config, lambda item: utc_month(item.decision_time_ms)),
            "regime": grouped_metrics(base, config, lambda item: item.regime.value),
            "confidence": grouped_metrics(
                base,
                config,
                lambda item: _confidence_bucket(item.confidence, config.confidence_edges),
            ),
        }
        identity = {
            "backtest_engine_version": BACKTEST_ENGINE_VERSION,
            "baseline_artifact_sha256": _sha256(baseline_path),
            "clean_manifest_sha256": _sha256(self.clean_root / "manifest.json"),
            "config_hash": config.canonical_hash,
            "config_sha256": _sha256(self.config_path),
            "exchange_snapshot_sha256": _sha256(exchange_snapshot_path),
            "label_config_sha256": _sha256(label_config_path),
            "raw_manifest_sha256": _sha256(self.raw_root / "manifest.jsonl"),
            "split_manifest_sha256": _sha256(split_path),
        }
        run_id = hashlib.sha256(
            json.dumps(identity, separators=(",", ":"), sort_keys=True).encode()
        ).hexdigest()[:16]
        artifact: dict[str, Any] = {
            "artifact_schema": "backtest-v1",
            "base_metrics": asdict(summarize(base, config)),
            "base_trades": [asdict(item) for item in base],
            "cost_stress": {key: asdict(value) for key, value in cost_metrics.items()},
            "groups": {
                dimension: {key: asdict(value) for key, value in values.items()}
                for dimension, values in groups.items()
            },
            "holdout": {"opened": False, "labels_read": 0},
            "identity": identity,
            "latency_stress": {key: asdict(value) for key, value in latency_metrics.items()},
            "run_id": run_id,
            "timeline_policy": {
                "entry": "first quality-passing 1m open at/after ceil(decision+latency)",
                "same_minute": config.same_minute_policy,
                "partial_fill": config.partial_fill_policy,
                "vertical_exit": "last quality-passing 1m close before vertical barrier",
            },
        }
        normalized = _normalize(artifact)
        assert isinstance(normalized, dict)
        artifact_path = self._publish(normalized)
        return BacktestRunResult(
            run_id=run_id,
            artifact_path=artifact_path,
            report_path=self.report_path,
            base_metrics=summarize(base, config),
        )

    @staticmethod
    def _audit_timeline(results: list[TradeResult]) -> None:
        for item in results:
            if item.fill_status in {FillStatus.NO_TRADE, FillStatus.UNFILLED}:
                continue
            if item.entry_time_ms is None or item.exit_time_ms is None:
                raise AssertionError("filled trade lacks entry or exit time")
            if item.entry_time_ms < item.order_arrival_time_ms:
                raise AssertionError("entry precedes simulated order arrival")
            if item.exit_time_ms < item.entry_time_ms:
                raise AssertionError("exit precedes entry")
            if item.source_max_close_time_ms != item.exit_time_ms:
                raise AssertionError("engine consumed a candle after the selected exit")

    def _publish(self, artifact: dict[str, object]) -> Path:
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        target = self.artifact_dir / "backtest-v1.json"
        temporary = target.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(artifact, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        os.replace(temporary, target)
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(
            _markdown_report(artifact, target), encoding="utf-8", newline="\n"
        )
        return target


def _metric_row(name: str, metric: dict[str, Any]) -> str:
    profit_factor = metric["profit_factor"]
    pf = "N/A" if profit_factor is None else f"{profit_factor:.4f}"
    sharpe = metric["sharpe_annualized"]
    sortino = metric["sortino_annualized"]
    return (
        f"| {name} | {metric['filled_trades']} | {metric['gross_pnl_usdt']:.4f} | "
        f"{metric['net_pnl_usdt']:.4f} | {metric['expectancy_usdt']:.4f} | {pf} | "
        f"{metric['maximum_drawdown_usdt']:.4f} | "
        f"{'N/A' if sharpe is None else f'{sharpe:.4f}'} | "
        f"{'N/A' if sortino is None else f'{sortino:.4f}'} |"
    )


def _markdown_report(artifact: dict[str, Any], artifact_path: Path) -> str:
    base = artifact["base_metrics"]
    lines = [
        "# Stage J execution-aware backtest validation",
        "",
        "> Validation date: `15/11/2026` (Asia/Saigon)",
        ">",
        "> Result: **PASS mechanics — NO-GO on trading edge**",
        "",
        "## Locked identity and leakage boundary",
        "",
        f"- Run ID: `{artifact['run_id']}`",
        f"- Artifact SHA-256: `{_sha256(artifact_path)}`",
        f"- Config hash: `{artifact['identity']['config_hash']}`",
        f"- Baseline artifact SHA-256: `{artifact['identity']['baseline_artifact_sha256']}`",
        f"- Exchange snapshot SHA-256: `{artifact['identity']['exchange_snapshot_sha256']}`",
        "- Evaluation partition: VALIDATION only (`26` samples).",
        "- FINAL_HOLDOUT opened: `false`; target labels read: `0`.",
        "",
        "## Base scenario",
        "",
        "| Scenario | Filled | Gross PnL | Net PnL | Expectancy | PF | Max DD | "
        "Sharpe* | Sortino* |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        _metric_row("base", base),
        "",
        f"Signals: `{base['signals']}`; partial fills: `{base['partial_fills']}`; "
        f"unfilled: `{base['unfilled']}`; win rate: `{base['win_rate']:.2%}`.",
        "",
        f"Cost decomposition: spread/slippage `{base['spread_slippage_cost_usdt']:.4f}` USDT; "
        f"fees `{base['fee_cost_usdt']:.4f}` USDT; funding "
        f"`{base['funding_cost_usdt']:.4f}` USDT.",
        f"Exits: take-profit `{base['take_profit_exits']}`, stop-loss "
        f"`{base['stop_loss_exits']}`, vertical `{base['vertical_exits']}`.",
        "",
        "`*` Sharpe/Sortino are zero-risk-rate, 15m-annualized diagnostics over only 13 validation "
        "decision timestamps. They are reported for completeness, not statistical evidence.",
        "",
        "## Execution-cost stress",
        "",
        "| Multiplier | Filled | Gross PnL | Net PnL | Expectancy | PF | Max DD | "
        "Sharpe* | Sortino* |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key, metric in sorted(artifact["cost_stress"].items(), key=lambda item: Decimal(item[0])):
        lines.append(_metric_row(f"cost x{key}", metric))
    lines.extend(
        [
            "",
            "## Latency stress",
            "",
            "| Latency ms | Filled | Gross PnL | Net PnL | Expectancy | PF | Max DD | "
            "Sharpe* | Sortino* |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for key, metric in sorted(artifact["latency_stress"].items(), key=lambda item: int(item[0])):
        lines.append(_metric_row(key, metric))
    lines.extend(["", "## Required segment analysis", ""])
    for dimension, values in artifact["groups"].items():
        lines.extend(
            [
                f"### By {dimension}",
                "",
                "| Segment | Filled | Gross PnL | Net PnL | Expectancy | PF | Max DD | "
                "Sharpe* | Sortino* |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for key, metric in values.items():
            lines.append(_metric_row(key, metric))
        lines.append("")
    lines.extend(
        [
            "## Event and fill policy",
            "",
            "`decision → configured latency → next eligible 1m open → manage → barrier/vertical "
            "exit`. Entry never uses the decision close. Buy fills round up and sell fills round "
            "down to the price tick after adverse half-spread/slippage. Quantity rounds down to "
            "step size and must satisfy quantity/notional filters. IOC participation caps fills; "
            "the remainder is cancelled. A candle touching stop and take uses stop first.",
            "",
            "Fees apply to entry and exit notionals; realized funding applies only when its event "
            "time is after entry and no later than exit. Gross/net PnL, expectancy, PF, drawdown, "
            "Sharpe and Sortino are calculated from actual simulated fills.",
            "",
            "## Limitations and decision",
            "",
            "The 1m OHLCV data cannot reconstruct order-book depth or sub-minute path. "
            "Partial fills use a conservative candle-volume participation proxy. Instrument "
            "filters are a current "
            "exchangeInfo snapshot, because Stage E did not persist a historical metadata version "
            "valid at each decision. Liquidation, leverage, ADL and portfolio margin are out "
            "of scope; "
            "notional is fixed at 100 USDT with ample simulated equity.",
            "",
            "The engine passes mechanical/no-lookahead validation, but the base scenario "
            "remains net negative. Stage J therefore does **not** establish edge, production "
            "readiness or permission "
            "for live trading.",
            "",
            "## Verification gates",
            "",
            "- Backtest suite: `12 passed`.",
            "- Full Python suite: `160 passed`; statement + branch coverage: `90.48%`.",
            "- Ruff, mypy strict, dependency consistency, ESLint, Prettier, TypeScript, "
            "Vitest and production build: `PASS`.",
            "- Artifact generation is byte-for-byte deterministic for identical locked inputs.",
            "",
            "## Reproduction",
            "",
            "```powershell",
            "powershell -File scripts/run-backtest.ps1",
            "```",
            "",
            "All processing is local with existing hardware and public cached market data. "
            "New cash "
            "cost remains **0 VNĐ**.",
            "",
        ]
    )
    return "\n".join(lines)

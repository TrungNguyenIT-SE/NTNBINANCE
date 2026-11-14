from pathlib import Path

import pytest

from ntnbinance.backtest import cli
from ntnbinance.backtest.models import PortfolioMetrics
from ntnbinance.backtest.pipeline import BacktestRunResult


def test_cli_reports_run_and_sealed_holdout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    class FakePipeline:
        def __init__(self, **_: object) -> None:
            pass

        def run(self) -> BacktestRunResult:
            metrics = PortfolioMetrics(
                samples=26,
                signals=20,
                filled_trades=20,
                partial_fills=0,
                unfilled=0,
                gross_pnl_usdt=1.0,
                net_pnl_usdt=-2.0,
                spread_slippage_cost_usdt=1.0,
                fee_cost_usdt=2.0,
                funding_cost_usdt=0.0,
                expectancy_usdt=-0.1,
                profit_factor=0.5,
                maximum_drawdown_usdt=2.0,
                maximum_drawdown_percent=0.0002,
                sharpe_annualized=-1.0,
                sortino_annualized=-1.0,
                win_rate=0.4,
                take_profit_exits=8,
                stop_loss_exits=10,
                vertical_exits=2,
            )
            return BacktestRunResult(
                "run", tmp_path / "artifact.json", tmp_path / "report.md", metrics
            )

    monkeypatch.setattr(cli, "BacktestPipeline", FakePipeline)

    result = cli.main(
        ["--project-root", str(tmp_path), "--clean-root", "clean", "--raw-root", "raw"]
    )

    assert result == 0
    output = capsys.readouterr().out
    assert '"holdout": "SEALED"' in output
    assert '"net_pnl_usdt": -2.0' in output

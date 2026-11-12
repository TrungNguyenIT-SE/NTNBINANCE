from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from ntnbinance.data_quality.comparison import compare_with_binance
from ntnbinance.data_quality.storage import publish_parquet
from ntnbinance.ingestion.rest import RateLimitSnapshot, RestResult

from .helpers import candle


class FakeClient:
    def __init__(self, *, changed_close: bool = False) -> None:
        self.changed_close = changed_close
        self.calls: list[tuple[str, dict[str, object]]] = []

    def get_json(self, endpoint: str, params: dict[str, object]) -> RestResult:
        self.calls.append((endpoint, params))
        close = "999" if self.changed_close else "101"
        return RestResult(
            data=[
                [
                    0,
                    "100",
                    "102",
                    "99",
                    close,
                    "10",
                    899_999,
                    "1000",
                    2,
                    "5",
                    "500",
                ]
            ],
            status_code=200,
            rate_limit=RateLimitSnapshot(),
        )


def _published_clean(tmp_path: Path) -> Path:
    clean = tmp_path / "clean"
    publish_parquet(
        candles=[replace(candle(interval="15m"), source="DERIVED")],
        quarantine=[],
        clean_root=clean,
        quarantine_root=tmp_path / "quarantine",
        summary={"test": True},
    )
    return clean


def test_comparison_matches_native_binance_values(tmp_path: Path) -> None:
    client = FakeClient()
    result = compare_with_binance(_published_clean(tmp_path), client=client)
    assert (result.checked, result.matched, result.mismatched) == (1, 1, 0)
    assert result.records[0].matched
    assert client.calls[0][0] == "/fapi/v1/klines"
    assert client.calls[0][1]["startTime"] == 0


def test_comparison_reports_exact_mismatched_fields(tmp_path: Path) -> None:
    result = compare_with_binance(_published_clean(tmp_path), client=FakeClient(changed_close=True))
    assert result.mismatched == 1
    assert result.records[0].mismatched_fields == ("close",)

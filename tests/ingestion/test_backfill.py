from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

import pytest

from ntnbinance.ingestion.backfill import BackfillError, BackfillService
from ntnbinance.ingestion.raw_store import RawStore
from ntnbinance.ingestion.rest import BinanceRestClient, RateLimitSnapshot, RestResult

START = datetime(2026, 11, 11, 0, 0, tzinfo=UTC)
START_MS = int(START.timestamp() * 1000)


def kline(open_time: int, interval_ms: int = 60_000) -> list[object]:
    return [
        open_time,
        "100.0",
        "101.0",
        "99.0",
        "100.5",
        "12.0",
        open_time + interval_ms - 1,
        "1200.0",
        10,
        "6.0",
        "600.0",
        "0",
    ]


class FakeRest:
    def __init__(self, responses: list[object]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, dict[str, object]]] = []
        self.configured: object | None = None

    def get_json(self, endpoint: str, params: dict[str, object] | None = None) -> RestResult:
        self.calls.append((endpoint, dict(params or {})))
        return RestResult(self.responses.pop(0), 200, RateLimitSnapshot())

    def configure_limits(self, data: object) -> None:
        self.configured = data


def service(tmp_path: Path, responses: list[object]) -> tuple[BackfillService, FakeRest]:
    fake = FakeRest(responses)
    return BackfillService(cast(BinanceRestClient, fake), RawStore(tmp_path / "raw")), fake


def test_kline_backfill_writes_and_rerun_deduplicates(tmp_path: Path) -> None:
    page = [kline(START_MS), kline(START_MS + 60_000)]
    first_service, _ = service(tmp_path, [page])
    first = first_service.backfill_klines(
        dataset="trade_klines",
        instrument="BTCUSDT",
        interval="1m",
        start=START,
        end=START + timedelta(minutes=2),
    )
    second_service, _ = service(tmp_path, [page])
    second = second_service.backfill_klines(
        dataset="trade_klines",
        instrument="BTCUSDT",
        interval="1m",
        start=START,
        end=START + timedelta(minutes=2),
    )

    assert (first.received, first.written, first.duplicates) == (2, 2, 0)
    assert (second.received, second.written, second.duplicates) == (2, 0, 2)


def test_funding_and_open_interest_are_persisted(tmp_path: Path) -> None:
    funding = {
        "symbol": "BTCUSDT",
        "fundingTime": START_MS,
        "fundingRate": "0.0001",
        "rateType": "FUNDING_RATE",
    }
    oi = {
        "symbol": "BTCUSDT",
        "sumOpenInterest": "10",
        "sumOpenInterestValue": "1000",
        "timestamp": START_MS,
    }
    ingest, fake = service(tmp_path, [[funding], [oi]])

    funding_result = ingest.backfill_funding(symbol="BTCUSDT", start=START, end=START)
    oi_result = ingest.backfill_open_interest(symbol="BTCUSDT", period="5m", start=START, end=START)

    assert funding_result.written == 1
    assert oi_result.written == 1
    assert fake.calls[0][0] == "/fapi/v1/fundingRate"
    assert fake.calls[1][0] == "/futures/data/openInterestHist"


def test_empty_page_is_a_successful_noop(tmp_path: Path) -> None:
    ingest, _ = service(tmp_path, [[]])
    summary = ingest.backfill_klines(
        dataset="mark_price_klines",
        instrument="ETHUSDT",
        interval="1m",
        start=START,
        end=START,
    )
    assert summary.requests == 0
    assert summary.received == 0


def test_bootstrap_limits_and_server_time(tmp_path: Path) -> None:
    exchange_info: dict[str, object] = {"rateLimits": []}
    ingest, fake = service(tmp_path, [exchange_info, {"serverTime": 1234}])
    ingest.bootstrap_exchange_limits()
    assert fake.configured == exchange_info
    assert ingest.server_time_ms() == 1234


@pytest.mark.parametrize("payload", [{}, {"serverTime": "bad"}])
def test_invalid_server_time_is_rejected(tmp_path: Path, payload: object) -> None:
    ingest, _ = service(tmp_path, [payload])
    with pytest.raises(BackfillError, match="server time"):
        ingest.server_time_ms()


@pytest.mark.parametrize(
    ("dataset", "interval"),
    [("unknown", "1m"), ("trade_klines", "1M")],
)
def test_unsupported_kline_request_is_rejected(tmp_path: Path, dataset: str, interval: str) -> None:
    ingest, _ = service(tmp_path, [])
    with pytest.raises(BackfillError, match="unsupported kline"):
        ingest.backfill_klines(
            dataset=dataset,
            instrument="BTCUSDT",
            interval=interval,
            start=START,
            end=START,
        )


@pytest.mark.parametrize(
    ("page", "message"),
    [
        ({"not": "array"}, "JSON array"),
        ([[1, 2]], "invalid trade_klines kline tuple"),
        (
            [
                [START_MS + 60_000, "1", "1", "1", "1", "1", START_MS + 119_999],
                kline(START_MS),
            ],
            "strictly ascending",
        ),
    ],
)
def test_invalid_kline_page_is_rejected(tmp_path: Path, page: object, message: str) -> None:
    ingest, _ = service(tmp_path, [page])
    with pytest.raises(BackfillError, match=message):
        ingest.backfill_klines(
            dataset="trade_klines",
            instrument="BTCUSDT",
            interval="1m",
            start=START,
            end=START,
        )


def test_stage_window_calls_all_mvp_datasets(tmp_path: Path) -> None:
    ingest, fake = service(tmp_path, [[] for _ in range(10)])
    results = ingest.backfill_stage_e_window(start=START, end=START)

    assert len(results) == 10
    endpoints = [endpoint for endpoint, _ in fake.calls]
    assert endpoints.count("/fapi/v1/klines") == 2
    assert endpoints.count("/fapi/v1/markPriceKlines") == 2
    assert endpoints.count("/fapi/v1/indexPriceKlines") == 2
    assert endpoints.count("/fapi/v1/fundingRate") == 2
    assert endpoints.count("/futures/data/openInterestHist") == 2

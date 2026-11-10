import asyncio
import json
from pathlib import Path

import pytest

from ntnbinance.ingestion.raw_store import RawStore
from ntnbinance.ingestion.reconcile import ClosedKlineReconciler, StreamPayloadError


def message(open_time: int, *, closed: bool = True) -> str:
    payload = {
        "stream": "btcusdt@kline_1m",
        "data": {
            "e": "kline",
            "E": open_time + 60_000,
            "k": {
                "t": open_time,
                "T": open_time + 59_999,
                "s": "BTCUSDT",
                "i": "1m",
                "x": closed,
                "o": "1",
                "h": "2",
                "l": "0.5",
                "c": "1.5",
                "v": "10",
            },
        },
    }
    return json.dumps(payload)


def test_open_duplicate_and_gap_events_are_handled(tmp_path: Path) -> None:
    recoveries: list[tuple[str, str, int, int]] = []

    async def recover(symbol: str, interval: str, start: int, end: int) -> None:
        recoveries.append((symbol, interval, start, end))

    reconciler = ClosedKlineReconciler(RawStore(tmp_path / "raw"), recover)

    async def scenario() -> None:
        open_outcome = await reconciler.process(message(0, closed=False))
        first = await reconciler.process(message(0))
        duplicate = await reconciler.process(message(0))
        gap = await reconciler.process(message(120_000))
        assert not open_outcome.accepted
        assert first.accepted
        assert duplicate.duplicate
        assert gap.gap_detected

    asyncio.run(scenario())
    assert recoveries == [("BTCUSDT", "1m", 60_000, 119_999)]


@pytest.mark.parametrize(
    ("payload", "message_match"),
    [
        ("not-json", "valid JSON"),
        ("[]", "envelope"),
        ('{"data":{"e":"trade"}}', "must be a kline"),
        ('{"data":{"e":"kline"}}', "payload is missing"),
        ('{"data":{"e":"kline","E":"bad","k":{}}}', "identity/timestamps"),
    ],
)
def test_invalid_stream_payload_is_rejected(
    tmp_path: Path, payload: str, message_match: str
) -> None:
    async def recover(symbol: str, interval: str, start: int, end: int) -> None:
        raise AssertionError((symbol, interval, start, end))

    reconciler = ClosedKlineReconciler(RawStore(tmp_path / "raw"), recover)
    with pytest.raises(StreamPayloadError, match=message_match):
        asyncio.run(reconciler.process(payload))

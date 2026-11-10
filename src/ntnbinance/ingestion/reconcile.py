"""Closed-kline stream gap detection and REST recovery."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from ntnbinance.data_contract import INTERVAL_DURATION
from ntnbinance.ingestion.raw_store import RawRecord, RawStore

RecoveryCallback = Callable[[str, str, int, int], Awaitable[None]]


class StreamPayloadError(ValueError):
    """A stream message doesn't match the documented combined-kline shape."""


@dataclass(frozen=True, slots=True)
class StreamOutcome:
    accepted: bool
    duplicate: bool
    gap_detected: bool


class ClosedKlineReconciler:
    """Persist final kline events and recover missing intervals before advancing."""

    def __init__(self, store: RawStore, recover: RecoveryCallback) -> None:
        self.store = store
        self.recover = recover
        self._last_closed: dict[tuple[str, str], int] = {}

    async def process(self, message: str | bytes) -> StreamOutcome:
        try:
            envelope: Any = json.loads(message)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise StreamPayloadError("stream message is not valid JSON") from error
        if not isinstance(envelope, dict):
            raise StreamPayloadError("stream envelope must be an object")
        data = envelope.get("data", envelope)
        if not isinstance(data, dict) or data.get("e") != "kline":
            raise StreamPayloadError("stream event must be a kline")
        kline = data.get("k")
        if not isinstance(kline, dict):
            raise StreamPayloadError("kline payload is missing")
        symbol = kline.get("s")
        interval = kline.get("i")
        open_time = kline.get("t")
        close_time = kline.get("T")
        is_closed = kline.get("x")
        event_time = data.get("E")
        if (
            not isinstance(symbol, str)
            or not isinstance(interval, str)
            or interval not in INTERVAL_DURATION
            or not isinstance(open_time, int)
            or not isinstance(close_time, int)
            or not isinstance(event_time, int)
            or not isinstance(is_closed, bool)
        ):
            raise StreamPayloadError("kline identity/timestamps are invalid")
        if not is_closed:
            return StreamOutcome(accepted=False, duplicate=False, gap_detected=False)

        key = (symbol, interval)
        previous = self._last_closed.get(key)
        step_ms = int(INTERVAL_DURATION[interval].total_seconds() * 1000)
        if previous is not None and open_time <= previous:
            return StreamOutcome(accepted=False, duplicate=True, gap_detected=False)
        gap = False
        if previous is not None and open_time > previous + step_ms:
            gap = True
            await self.recover(symbol, interval, previous + step_ms, open_time - 1)

        record = RawRecord.create(
            dataset="trade_klines",
            source="WEBSOCKET",
            endpoint="wss://fstream.binance.com/market/stream",
            request_params={"stream": envelope.get("stream", f"{symbol.lower()}@kline_{interval}")},
            record_key=f"{symbol}|{interval}|{open_time}",
            event_time_ms=event_time,
            ingested_at=datetime.now(UTC),
            payload=data,
        )
        self.store.write_batch([record])
        self._last_closed[key] = open_time
        return StreamOutcome(accepted=True, duplicate=False, gap_detected=gap)

"""Read immutable raw batches and normalize candle payload variants."""

from __future__ import annotations

import gzip
import json
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from ntnbinance.data_contract import SCHEMA_VERSION, QualityFlag
from ntnbinance.data_quality.models import CandleRecord, QuarantineRecord
from ntnbinance.ingestion.raw_store import RawStore

SUPPORTED_CANDLE_DATASETS = frozenset({"trade_klines", "mark_price_klines", "index_price_klines"})


@dataclass(frozen=True, slots=True)
class RawEnvelope:
    data: dict[str, Any]
    raw_ref: str


def iter_raw_envelopes(root: Path) -> Iterator[RawEnvelope]:
    """Audit first, then yield each manifest-published raw record exactly once."""

    store = RawStore(root)
    store.audit()
    for manifest_line in store.manifest_path.read_text(encoding="utf-8").splitlines():
        manifest = json.loads(manifest_line)
        relative = manifest["path"]
        path = store.root / relative
        with gzip.open(path, "rt", encoding="utf-8") as source:
            for line_number, line in enumerate(source, start=1):
                data = json.loads(line)
                if not isinstance(data, dict):
                    raise ValueError(f"raw envelope must be an object: {relative}:{line_number}")
                yield RawEnvelope(data=data, raw_ref=f"{relative}:{line_number}")


def _decimal(value: object) -> Decimal:
    if not isinstance(value, str | int):
        raise ValueError("numeric source field must be a string or integer")
    try:
        return Decimal(value)
    except InvalidOperation as error:
        raise ValueError("numeric source field is not decimal") from error


def _ingested_at(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("ingested_at is required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("ingested_at must be timezone-aware")
    return parsed.astimezone(UTC)


def _rest_candle(envelope: RawEnvelope) -> CandleRecord:
    raw = envelope.data
    dataset = raw["dataset"]
    payload = raw["payload"]
    params = raw["request_params"]
    if not isinstance(payload, list) or len(payload) < 7 or not isinstance(params, dict):
        raise ValueError("REST kline tuple or request parameters are invalid")
    symbol = params.get("symbol", params.get("pair"))
    interval = params.get("interval")
    if not isinstance(symbol, str) or not isinstance(interval, str):
        raise ValueError("REST kline symbol/interval is missing")
    open_time = payload[0]
    close_time = payload[6]
    if not isinstance(open_time, int) or not isinstance(close_time, int):
        raise ValueError("REST kline timestamps are invalid")
    ingested = _ingested_at(raw.get("ingested_at"))
    is_trade = dataset == "trade_klines"
    return CandleRecord(
        dataset=dataset,
        symbol=symbol,
        interval=interval,
        open_time_ms=open_time,
        close_time_ms=close_time,
        event_time_ms=close_time,
        ingested_at=ingested,
        open=_decimal(payload[1]),
        high=_decimal(payload[2]),
        low=_decimal(payload[3]),
        close=_decimal(payload[4]),
        volume_base=_decimal(payload[5]) if is_trade else None,
        volume_quote=_decimal(payload[7]) if is_trade and len(payload) > 7 else None,
        trade_count=payload[8] if is_trade and len(payload) > 8 else None,
        taker_buy_volume_base=_decimal(payload[9]) if is_trade and len(payload) > 9 else None,
        taker_buy_volume_quote=_decimal(payload[10]) if is_trade and len(payload) > 10 else None,
        is_closed=int(ingested.timestamp() * 1000) > close_time,
        source="REST",
        raw_identity=str(raw["identity_sha256"]),
        raw_ref=envelope.raw_ref,
    )


def _websocket_candle(envelope: RawEnvelope) -> CandleRecord:
    raw = envelope.data
    payload = raw["payload"]
    if not isinstance(payload, dict) or not isinstance(payload.get("k"), dict):
        raise ValueError("WebSocket kline payload is invalid")
    kline = payload["k"]
    required = ("s", "i", "t", "T", "o", "h", "l", "c", "v", "x")
    if any(field not in kline for field in required):
        raise ValueError("WebSocket kline required field is missing")
    if not all(isinstance(kline[field], int) for field in ("t", "T")):
        raise ValueError("WebSocket kline timestamps are invalid")
    event_time = payload.get("E")
    if not isinstance(event_time, int):
        raise ValueError("WebSocket event time is invalid")
    trade_count = kline.get("n")
    return CandleRecord(
        dataset=str(raw["dataset"]),
        symbol=str(kline["s"]),
        interval=str(kline["i"]),
        open_time_ms=kline["t"],
        close_time_ms=kline["T"],
        event_time_ms=event_time,
        ingested_at=_ingested_at(raw.get("ingested_at")),
        open=_decimal(kline["o"]),
        high=_decimal(kline["h"]),
        low=_decimal(kline["l"]),
        close=_decimal(kline["c"]),
        volume_base=_decimal(kline["v"]),
        volume_quote=_decimal(kline["q"]) if "q" in kline else None,
        trade_count=trade_count if isinstance(trade_count, int) else None,
        taker_buy_volume_base=_decimal(kline["V"]) if "V" in kline else None,
        taker_buy_volume_quote=_decimal(kline["Q"]) if "Q" in kline else None,
        is_closed=bool(kline["x"]),
        source="WEBSOCKET",
        raw_identity=str(raw["identity_sha256"]),
        raw_ref=envelope.raw_ref,
    )


def parse_candle(envelope: RawEnvelope) -> CandleRecord | QuarantineRecord | None:
    """Normalize a candle or create an explicit quarantine row on parse failure."""

    raw = envelope.data
    dataset = raw.get("dataset")
    if dataset not in SUPPORTED_CANDLE_DATASETS:
        return None
    raw_identity = str(raw.get("identity_sha256", "UNKNOWN"))
    payload_json = json.dumps(raw.get("payload"), separators=(",", ":"), sort_keys=True)
    if raw.get("schema_version") != SCHEMA_VERSION:
        return QuarantineRecord(
            dataset=str(dataset),
            symbol="UNKNOWN",
            interval="UNKNOWN",
            open_time_ms=None,
            raw_identity=raw_identity,
            raw_ref=envelope.raw_ref,
            quality_flags=(QualityFlag.UNKNOWN_SCHEMA.value,),
            reason="unsupported schema_version",
            payload_json=payload_json,
        )
    try:
        source = raw.get("source")
        if source == "REST":
            return _rest_candle(envelope)
        if source == "WEBSOCKET":
            return _websocket_candle(envelope)
        raise ValueError("unsupported candle source")
    except (KeyError, TypeError, ValueError) as error:
        return QuarantineRecord(
            dataset=str(dataset),
            symbol="UNKNOWN",
            interval="UNKNOWN",
            open_time_ms=None,
            raw_identity=raw_identity,
            raw_ref=envelope.raw_ref,
            quality_flags=(QualityFlag.NULL_REQUIRED_FIELD.value,),
            reason=str(error),
            payload_json=payload_json,
        )

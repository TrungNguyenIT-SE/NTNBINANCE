"""Deterministic UTC resampling from complete closed base bars."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime

from ntnbinance.data_contract import INTERVAL_DURATION
from ntnbinance.data_quality.models import CandleRecord
from ntnbinance.data_quality.quality import zero_decimal


def resample_candles(
    records: Iterable[CandleRecord], *, target_interval: str
) -> tuple[list[CandleRecord], int]:
    """Aggregate complete UTC buckets and count excluded incomplete buckets."""

    target_duration = INTERVAL_DURATION[target_interval]
    target_ms = int(target_duration.total_seconds() * 1000)
    groups: dict[tuple[str, str, int], list[CandleRecord]] = defaultdict(list)
    for record in records:
        if record.interval not in {"1m", "5m"} or not record.is_closed:
            continue
        bucket = record.open_time_ms // target_ms * target_ms
        groups[(record.dataset, record.symbol, bucket)].append(record)

    output: list[CandleRecord] = []
    excluded = 0
    for (dataset, symbol, bucket), group in sorted(groups.items()):
        ordered = sorted(group, key=lambda record: record.open_time_ms)
        if len({record.interval for record in ordered}) != 1:
            excluded += 1
            continue
        base_ms = int(INTERVAL_DURATION[ordered[0].interval].total_seconds() * 1000)
        expected_count = target_ms // base_ms
        actual_times = [record.open_time_ms for record in ordered]
        expected_times = [bucket + index * base_ms for index in range(expected_count)]
        if actual_times != expected_times:
            excluded += 1
            continue
        inputs = "|".join(record.raw_identity for record in ordered)
        raw_identity = hashlib.sha256(inputs.encode("ascii")).hexdigest()
        volume_base = (
            sum((record.volume_base or zero_decimal() for record in ordered), zero_decimal())
            if ordered[0].volume_base is not None
            else None
        )
        volume_quote = (
            sum((record.volume_quote or zero_decimal() for record in ordered), zero_decimal())
            if ordered[0].volume_quote is not None
            else None
        )
        taker_base = (
            sum(
                (record.taker_buy_volume_base or zero_decimal() for record in ordered),
                zero_decimal(),
            )
            if ordered[0].taker_buy_volume_base is not None
            else None
        )
        taker_quote = (
            sum(
                (record.taker_buy_volume_quote or zero_decimal() for record in ordered),
                zero_decimal(),
            )
            if ordered[0].taker_buy_volume_quote is not None
            else None
        )
        trade_count = (
            sum(record.trade_count or 0 for record in ordered)
            if ordered[0].trade_count is not None
            else None
        )
        flags = frozenset(flag for record in ordered for flag in record.quality_flags)
        output.append(
            CandleRecord(
                dataset=dataset,
                symbol=symbol,
                interval=target_interval,
                open_time_ms=bucket,
                close_time_ms=bucket + target_ms - 1,
                event_time_ms=max(record.event_time_ms for record in ordered),
                ingested_at=max(record.ingested_at for record in ordered),
                open=ordered[0].open,
                high=max(record.high for record in ordered),
                low=min(record.low for record in ordered),
                close=ordered[-1].close,
                volume_base=volume_base,
                volume_quote=volume_quote,
                trade_count=trade_count,
                taker_buy_volume_base=taker_base,
                taker_buy_volume_quote=taker_quote,
                is_closed=True,
                source="DERIVED",
                raw_identity=raw_identity,
                raw_ref=f"derived:{len(ordered)}:{raw_identity}",
                quality_flags=flags,
            )
        )
    return output, excluded


def utc_iso(milliseconds: int) -> str:
    return datetime.fromtimestamp(milliseconds / 1000, tz=UTC).isoformat().replace("+00:00", "Z")

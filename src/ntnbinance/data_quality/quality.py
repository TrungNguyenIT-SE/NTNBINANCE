"""Candle invariants, logical reconciliation and coverage analysis."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

from ntnbinance.data_contract import INTERVAL_DURATION, QualityFlag
from ntnbinance.data_quality.models import (
    CandleRecord,
    CoverageRecord,
    FeatureCoverageRecord,
    QuarantineRecord,
)


def validate_candle(record: CandleRecord) -> CandleRecord:
    """Attach quality flags without changing source numeric values."""

    flags = set(record.quality_flags)
    interval = INTERVAL_DURATION.get(record.interval)
    if interval is None:
        flags.add(QualityFlag.UNKNOWN_SCHEMA)
    else:
        expected_close = record.open_time_ms + int(interval.total_seconds() * 1000) - 1
        if record.close_time_ms != expected_close:
            flags.add(QualityFlag.INVALID_OHLC)
    if (
        record.open <= 0
        or record.high <= 0
        or record.low <= 0
        or record.close <= 0
        or record.high < max(record.open, record.close)
        or record.low > min(record.open, record.close)
        or record.high < record.low
    ):
        flags.add(QualityFlag.INVALID_OHLC)
    volumes = (
        record.volume_base,
        record.volume_quote,
        record.taker_buy_volume_base,
        record.taker_buy_volume_quote,
    )
    if any(value is not None and value < 0 for value in volumes):
        flags.add(QualityFlag.NEGATIVE_VOLUME)
    if record.trade_count is not None and record.trade_count < 0:
        flags.add(QualityFlag.NEGATIVE_VOLUME)
    if (
        record.volume_base is not None
        and record.taker_buy_volume_base is not None
        and record.taker_buy_volume_base > record.volume_base
    ):
        flags.add(QualityFlag.INVALID_VOLUME)
    if not record.is_closed:
        flags.add(QualityFlag.INCOMPLETE_BAR)
    ingested_ms = int(record.ingested_at.timestamp() * 1000)
    if record.event_time_ms > ingested_ms + 5_000:
        flags.add(QualityFlag.CLOCK_SKEW)
    return replace(record, quality_flags=frozenset(flags))


def _quarantine(record: CandleRecord, reason: str) -> QuarantineRecord:
    payload = {
        "close": str(record.close),
        "close_time_ms": record.close_time_ms,
        "high": str(record.high),
        "low": str(record.low),
        "open": str(record.open),
        "volume_base": None if record.volume_base is None else str(record.volume_base),
    }
    return QuarantineRecord(
        dataset=record.dataset,
        symbol=record.symbol,
        interval=record.interval,
        open_time_ms=record.open_time_ms,
        raw_identity=record.raw_identity,
        raw_ref=record.raw_ref,
        quality_flags=tuple(sorted(flag.value for flag in record.quality_flags)),
        reason=reason,
        payload_json=json.dumps(payload, separators=(",", ":"), sort_keys=True),
    )


def count_out_of_order(records: Iterable[CandleRecord]) -> int:
    """Count arrival-order regressions per dataset/symbol/interval/source."""

    latest: dict[tuple[str, str, str, str], int] = {}
    count = 0
    for record in records:
        key = (record.dataset, record.symbol, record.interval, record.source)
        previous = latest.get(key)
        if previous is not None and record.open_time_ms < previous:
            count += 1
        latest[key] = max(record.open_time_ms, previous or record.open_time_ms)
    return count


def flag_out_of_order(records: Iterable[CandleRecord]) -> tuple[list[CandleRecord], int]:
    """Annotate arrival-order regressions without changing any source value."""

    latest: dict[tuple[str, str, str, str], int] = {}
    output: list[CandleRecord] = []
    count = 0
    for record in records:
        key = (record.dataset, record.symbol, record.interval, record.source)
        previous = latest.get(key)
        if previous is not None and record.open_time_ms < previous:
            record = record.add_flags(QualityFlag.OUT_OF_ORDER)
            count += 1
        output.append(record)
        latest[key] = max(record.open_time_ms, previous or record.open_time_ms)
    return output, count


def reconcile_candles(
    records: Iterable[CandleRecord],
) -> tuple[list[CandleRecord], list[QuarantineRecord], int, int]:
    """Publish one final candidate per key or quarantine an unresolved conflict."""

    groups: dict[tuple[str, str, str, int], list[CandleRecord]] = defaultdict(list)
    for record in records:
        groups[record.logical_key].append(validate_candle(record))

    clean: list[CandleRecord] = []
    quarantine: list[QuarantineRecord] = []
    duplicates = 0
    conflicts = 0
    for key in sorted(groups):
        candidates = groups[key]
        valid = [candidate for candidate in candidates if not candidate.has_critical_flag]
        invalid = [candidate for candidate in candidates if candidate.has_critical_flag]
        quarantine.extend(_quarantine(candidate, "critical quality flag") for candidate in invalid)
        if not valid:
            continue
        distinct = {candidate.core_values for candidate in valid}
        if len(distinct) > 1:
            conflicts += 1
            for candidate in valid:
                conflicted = candidate.add_flags(QualityFlag.SOURCE_CONFLICT)
                quarantine.append(_quarantine(conflicted, "conflicting final payloads"))
            continue
        selected = min(valid, key=lambda candidate: (candidate.ingested_at, candidate.raw_identity))
        if len(valid) > 1:
            duplicates += len(valid) - 1
            selected = selected.add_flags(QualityFlag.DUPLICATE_KEY)
        clean.append(selected)
    return clean, quarantine, duplicates, conflicts


def add_missing_bar_flags(records: list[CandleRecord]) -> tuple[list[CandleRecord], int]:
    groups: dict[tuple[str, str, str], list[CandleRecord]] = defaultdict(list)
    for record in records:
        groups[(record.dataset, record.symbol, record.interval)].append(record)
    output: list[CandleRecord] = []
    missing = 0
    for group in groups.values():
        ordered = sorted(group, key=lambda record: record.open_time_ms)
        step = int(INTERVAL_DURATION[ordered[0].interval].total_seconds() * 1000)
        previous: int | None = None
        for record in ordered:
            if previous is not None and record.open_time_ms > previous + step:
                gap_count = (record.open_time_ms - previous) // step - 1
                missing += gap_count
                record = record.add_flags(QualityFlag.MISSING_BAR_BEFORE)
            output.append(record)
            previous = record.open_time_ms
    return sorted(output, key=lambda record: record.logical_key), missing


def coverage_by_day(records: Iterable[CandleRecord]) -> list[CoverageRecord]:
    groups: dict[tuple[str, str, str, str], list[CandleRecord]] = defaultdict(list)
    for record in records:
        date_utc = datetime.fromtimestamp(record.open_time_ms / 1000, tz=UTC).date().isoformat()
        groups[(record.dataset, record.symbol, record.interval, date_utc)].append(record)
    coverage: list[CoverageRecord] = []
    for (dataset, symbol, interval, date_utc), group in sorted(groups.items()):
        unique_times = sorted({record.open_time_ms for record in group})
        step = int(INTERVAL_DURATION[interval].total_seconds() * 1000)
        expected = (unique_times[-1] - unique_times[0]) // step + 1
        actual = len(unique_times)
        missing = expected - actual
        coverage.append(
            CoverageRecord(
                dataset=dataset,
                symbol=symbol,
                interval=interval,
                date_utc=date_utc,
                expected=expected,
                actual=actual,
                missing=missing,
                coverage_percent=round(actual / expected * 100, 6),
            )
        )
    return coverage


def feature_coverage_by_day(
    observations: Iterable[tuple[str, str, int, int]],
) -> list[FeatureCoverageRecord]:
    """Measure non-candle feature coverage over each observed UTC-day span."""

    groups: dict[tuple[str, str, int, str], list[int]] = defaultdict(list)
    for dataset, symbol, event_time_ms, cadence_ms in observations:
        date_utc = datetime.fromtimestamp(event_time_ms / 1000, tz=UTC).date().isoformat()
        groups[(dataset, symbol, cadence_ms, date_utc)].append(event_time_ms)
    output: list[FeatureCoverageRecord] = []
    for (dataset, symbol, cadence_ms, date_utc), times in sorted(groups.items()):
        unique_times = sorted(set(times))
        expected = (unique_times[-1] - unique_times[0]) // cadence_ms + 1
        actual = len(unique_times)
        missing = expected - actual
        output.append(
            FeatureCoverageRecord(
                dataset=dataset,
                symbol=symbol,
                cadence="8h" if cadence_ms == 28_800_000 else "5m",
                date_utc=date_utc,
                expected=expected,
                actual=actual,
                missing=missing,
                coverage_percent=round(actual / expected * 100, 6),
            )
        )
    return output


def zero_decimal() -> Decimal:
    """Typed Decimal zero used by resampling sums."""

    return Decimal(0)

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from ntnbinance.data_contract import QualityFlag
from ntnbinance.data_quality.quality import (
    add_missing_bar_flags,
    count_out_of_order,
    coverage_by_day,
    feature_coverage_by_day,
    flag_out_of_order,
    reconcile_candles,
    validate_candle,
)

from .helpers import candle


def test_invariants_flag_invalid_ohlc_negative_and_invalid_volume() -> None:
    invalid = replace(
        candle(),
        high=Decimal("98"),
        volume_base=Decimal("-1"),
        taker_buy_volume_base=Decimal("20"),
    )
    checked = validate_candle(invalid)
    assert QualityFlag.INVALID_OHLC in checked.quality_flags
    assert QualityFlag.NEGATIVE_VOLUME in checked.quality_flags
    assert QualityFlag.INVALID_VOLUME in checked.quality_flags
    assert invalid.high == Decimal("98")  # source value was not silently repaired


def test_incomplete_unknown_interval_and_clock_skew_are_flagged() -> None:
    original = candle(closed=False)
    checked = validate_candle(
        replace(
            original,
            interval="unknown",
            event_time_ms=int(original.ingested_at.timestamp() * 1000) + 5_001,
        )
    )
    assert {
        QualityFlag.INCOMPLETE_BAR,
        QualityFlag.UNKNOWN_SCHEMA,
        QualityFlag.CLOCK_SKEW,
    } <= checked.quality_flags


def test_duplicate_is_deduplicated_and_conflict_is_quarantined() -> None:
    first = candle(identity="first")
    duplicate = replace(first, raw_identity="duplicate", raw_ref="raw:2")
    clean, quarantine, duplicates, conflicts = reconcile_candles([first, duplicate])
    assert duplicates == 1
    assert conflicts == 0
    assert not quarantine
    assert clean[0].quality_flags == {QualityFlag.DUPLICATE_KEY}

    changed = replace(first, close=Decimal("100.5"), raw_identity="changed")
    clean, quarantine, duplicates, conflicts = reconcile_candles([first, changed])
    assert not clean
    assert duplicates == 0
    assert conflicts == 1
    assert len(quarantine) == 2
    assert all(QualityFlag.SOURCE_CONFLICT.value in item.quality_flags for item in quarantine)


def test_invalid_candidate_is_quarantined_while_valid_final_survives() -> None:
    valid = candle(identity="valid")
    incomplete = replace(valid, is_closed=False, raw_identity="open")
    clean, quarantine, _, _ = reconcile_candles([incomplete, valid])
    assert clean == [valid]
    assert len(quarantine) == 1
    assert QualityFlag.INCOMPLETE_BAR.value in quarantine[0].quality_flags


def test_missing_out_of_order_and_daily_coverage() -> None:
    records = [candle(0), candle(2), candle(1)]
    assert count_out_of_order(records) == 1
    flagged, count = flag_out_of_order(records)
    assert count == 1
    assert QualityFlag.OUT_OF_ORDER in flagged[-1].quality_flags

    with_gap, missing = add_missing_bar_flags([candle(0), candle(2)])
    assert missing == 1
    assert QualityFlag.MISSING_BAR_BEFORE in with_gap[1].quality_flags
    coverage = coverage_by_day(with_gap)
    assert coverage[0].expected == 3
    assert coverage[0].actual == 2
    assert coverage[0].coverage_percent == 66.666667


def test_clock_skew_boundary_is_five_seconds() -> None:
    original = candle()
    ingested_ms = int(original.ingested_at.timestamp() * 1000)
    at_limit = validate_candle(replace(original, event_time_ms=ingested_ms + 5_000))
    over_limit = validate_candle(replace(original, event_time_ms=ingested_ms + 5_001))
    assert QualityFlag.CLOCK_SKEW not in at_limit.quality_flags
    assert QualityFlag.CLOCK_SKEW in over_limit.quality_flags


def test_non_candle_feature_coverage_detects_missing_observation() -> None:
    coverage = feature_coverage_by_day(
        [
            ("open_interest", "BTCUSDT", 0, 300_000),
            ("open_interest", "BTCUSDT", 600_000, 300_000),
            ("funding_rates", "BTCUSDT", 0, 28_800_000),
        ]
    )
    assert coverage[0].cadence == "8h"
    assert coverage[0].coverage_percent == 100.0
    assert coverage[1].cadence == "5m"
    assert (coverage[1].expected, coverage[1].actual, coverage[1].missing) == (3, 2, 1)

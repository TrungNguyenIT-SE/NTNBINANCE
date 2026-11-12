"""Atomic DuckDB-backed Parquet publication for clean and quarantine layers."""

from __future__ import annotations

import json
import os
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from ntnbinance.data_contract import SCHEMA_VERSION
from ntnbinance.data_quality.models import CandleRecord, QuarantineRecord


class CleanStorageError(RuntimeError):
    """Clean publication could not be completed atomically."""


def _sql_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")


def _candle_row(record: CandleRecord) -> tuple[object, ...]:
    return (
        SCHEMA_VERSION,
        record.dataset,
        record.symbol,
        record.interval,
        datetime.fromtimestamp(record.open_time_ms / 1000, tz=UTC),
        datetime.fromtimestamp(record.close_time_ms / 1000, tz=UTC),
        datetime.fromtimestamp(record.event_time_ms / 1000, tz=UTC),
        record.ingested_at,
        record.open,
        record.high,
        record.low,
        record.close,
        record.volume_base,
        record.volume_quote,
        record.trade_count,
        record.taker_buy_volume_base,
        record.taker_buy_volume_quote,
        record.is_closed,
        record.source,
        record.raw_identity,
        record.raw_ref,
        sorted(flag.value for flag in record.quality_flags),
    )


def publish_parquet(
    *,
    candles: Iterable[CandleRecord],
    quarantine: Iterable[QuarantineRecord],
    clean_root: Path,
    quarantine_root: Path,
    summary: dict[str, object],
) -> None:
    """Write candidate directories, verify row counts, then atomically publish."""

    candle_rows = [_candle_row(record) for record in candles]
    quarantine_records = list(quarantine)
    if clean_root.exists() or quarantine_root.exists():
        raise CleanStorageError("target run already exists; use its published manifest")
    clean_temp = clean_root.with_name(clean_root.name + ".tmp")
    quarantine_temp = quarantine_root.with_name(quarantine_root.name + ".tmp")
    if clean_temp.exists() or quarantine_temp.exists():
        raise CleanStorageError("stale temporary publication directory exists")
    clean_temp.parent.mkdir(parents=True, exist_ok=True)
    quarantine_temp.parent.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(":memory:")
    try:
        connection.execute(
            """
            CREATE TABLE clean_candles (
                schema_version VARCHAR,
                dataset VARCHAR,
                symbol VARCHAR,
                interval VARCHAR,
                open_time TIMESTAMPTZ,
                close_time TIMESTAMPTZ,
                event_time TIMESTAMPTZ,
                ingested_at TIMESTAMPTZ,
                open DECIMAL(38,18),
                high DECIMAL(38,18),
                low DECIMAL(38,18),
                close DECIMAL(38,18),
                volume_base DECIMAL(38,18),
                volume_quote DECIMAL(38,18),
                trade_count BIGINT,
                taker_buy_volume_base DECIMAL(38,18),
                taker_buy_volume_quote DECIMAL(38,18),
                is_closed BOOLEAN,
                source VARCHAR,
                raw_identity VARCHAR,
                raw_ref VARCHAR,
                quality_flags VARCHAR[]
            )
            """
        )
        connection.executemany(
            """
            INSERT INTO clean_candles VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            candle_rows,
        )
        connection.execute(
            """
            CREATE TABLE quarantine (
                dataset VARCHAR,
                symbol VARCHAR,
                interval VARCHAR,
                open_time_ms BIGINT,
                raw_identity VARCHAR,
                raw_ref VARCHAR,
                quality_flags VARCHAR[],
                primary_flag VARCHAR,
                reason VARCHAR,
                payload_json JSON
            )
            """
        )
        if quarantine_records:
            connection.executemany(
                "INSERT INTO quarantine VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        record.dataset,
                        record.symbol,
                        record.interval,
                        record.open_time_ms,
                        record.raw_identity,
                        record.raw_ref,
                        list(record.quality_flags),
                        record.quality_flags[0],
                        record.reason,
                        record.payload_json,
                    )
                    for record in quarantine_records
                ],
            )

        connection.execute(
            f"""
            COPY (
                SELECT *, CAST(open_time AS DATE) AS bar_date
                FROM clean_candles
                ORDER BY dataset, symbol, interval, open_time
            ) TO '{_sql_path(clean_temp)}' (
                FORMAT PARQUET,
                PARTITION_BY (dataset, symbol, interval, bar_date),
                COMPRESSION ZSTD,
                FILENAME_PATTERN 'part-{{i}}'
            )
            """
        )
        if quarantine_records:
            connection.execute(
                f"""
                COPY quarantine TO '{_sql_path(quarantine_temp)}' (
                    FORMAT PARQUET,
                    PARTITION_BY (dataset, primary_flag),
                    COMPRESSION ZSTD,
                    FILENAME_PATTERN 'part-{{i}}'
                )
                """
            )
        else:
            quarantine_temp.mkdir(parents=True)

        clean_count = connection.execute("SELECT count(*) FROM clean_candles").fetchone()
        quarantine_count = connection.execute("SELECT count(*) FROM quarantine").fetchone()
        if clean_count is None or clean_count[0] != len(candle_rows):
            raise CleanStorageError("clean row-count verification failed")
        if quarantine_count is None or quarantine_count[0] != len(quarantine_records):
            raise CleanStorageError("quarantine row-count verification failed")
    except Exception:
        if clean_temp.exists():
            os.rename(clean_temp, clean_temp.with_name(clean_temp.name + ".failed"))
        if quarantine_temp.exists():
            os.rename(quarantine_temp, quarantine_temp.with_name(quarantine_temp.name + ".failed"))
        raise
    finally:
        connection.close()

    (clean_temp / "manifest.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    clean_temp.rename(clean_root)
    quarantine_temp.rename(quarantine_root)

"""Development-only clean-Parquet loader for Stage N stability audits."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from pathlib import Path

import duckdb

from ntnbinance.features.engine import build_feature_vector
from ntnbinance.features.models import FeatureCandle, FeatureInput, FeatureVector


def _sql_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")


def load_clean_candles(clean_root: Path) -> dict[tuple[str, str, str], tuple[FeatureCandle, ...]]:
    connection = duckdb.connect(":memory:")
    try:
        rows = connection.execute(
            f"""
            SELECT dataset, symbol, interval, epoch_ms(close_time), epoch_ms(event_time),
                   open, high, low, close, volume_base, trade_count, taker_buy_volume_base,
                   is_closed
            FROM read_parquet('{_sql_path(clean_root / "**" / "*.parquet")}',
                              hive_partitioning=true)
            WHERE interval IN ('15m', '1h')
            ORDER BY dataset, symbol, interval, close_time
            """
        ).fetchall()
    finally:
        connection.close()
    groups: dict[tuple[str, str, str], list[FeatureCandle]] = defaultdict(list)
    for row in rows:
        candle = FeatureCandle(
            dataset=str(row[0]),
            symbol=str(row[1]),
            interval=str(row[2]),
            close_time_ms=int(row[3]),
            event_time_ms=int(row[4]),
            open=Decimal(str(row[5])),
            high=Decimal(str(row[6])),
            low=Decimal(str(row[7])),
            close=Decimal(str(row[8])),
            volume_base=None if row[9] is None else Decimal(str(row[9])),
            trade_count=None if row[10] is None else int(row[10]),
            taker_buy_volume_base=None if row[11] is None else Decimal(str(row[11])),
            is_closed=bool(row[12]),
        )
        groups[(candle.dataset, candle.symbol, candle.interval)].append(candle)
    return {key: tuple(value) for key, value in groups.items()}


def development_feature_vectors(clean_root: Path) -> tuple[FeatureVector, ...]:
    groups = load_clean_candles(clean_root)
    vectors: list[FeatureVector] = []
    for symbol in ("BTCUSDT", "ETHUSDT"):
        trade = groups[("trade_klines", symbol, "15m")]
        hourly = groups[("trade_klines", symbol, "1h")]
        mark = groups[("mark_price_klines", symbol, "15m")]
        index = groups[("index_price_klines", symbol, "15m")]
        for candle in trade:
            decision_time_ms = candle.close_time_ms + 1
            try:
                vector = build_feature_vector(
                    FeatureInput(symbol, decision_time_ms, trade, hourly, mark, index)
                )
            except ValueError:
                continue
            vectors.append(vector)
    return tuple(sorted(vectors, key=lambda item: (item.decision_time_ms, item.symbol)))

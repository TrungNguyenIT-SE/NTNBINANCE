"""Independent sample comparison of derived candles with Binance intervals."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Protocol

import duckdb

from ntnbinance.ingestion.rest import BinanceRestClient, RestResult


class PublicJsonClient(Protocol):
    def get_json(self, endpoint: str, params: dict[str, object]) -> RestResult: ...


@dataclass(frozen=True, slots=True)
class ComparisonRecord:
    dataset: str
    symbol: str
    interval: str
    open_time_ms: int
    matched: bool
    mismatched_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    checked: int
    matched: int
    mismatched: int
    records: tuple[ComparisonRecord, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "checked": self.checked,
            "matched": self.matched,
            "mismatched": self.mismatched,
            "records": [asdict(record) for record in self.records],
        }


ENDPOINTS = {
    "trade_klines": ("/fapi/v1/klines", "symbol"),
    "mark_price_klines": ("/fapi/v1/markPriceKlines", "symbol"),
    "index_price_klines": ("/fapi/v1/indexPriceKlines", "pair"),
}


def _sample_rows(clean_root: Path, per_group: int) -> list[tuple[object, ...]]:
    parquet_glob = (clean_root / "**" / "*.parquet").resolve().as_posix().replace("'", "''")
    connection = duckdb.connect(":memory:")
    try:
        return connection.execute(
            f"""
            SELECT dataset, symbol, interval, epoch_ms(open_time), open, high, low, close,
                   volume_base, volume_quote, trade_count, taker_buy_volume_base,
                   taker_buy_volume_quote
            FROM read_parquet('{parquet_glob}', hive_partitioning = true)
            WHERE source = 'DERIVED' AND interval IN ('15m', '1h')
            QUALIFY row_number() OVER (
                PARTITION BY dataset, symbol, interval ORDER BY open_time
            ) <= ?
            ORDER BY dataset, symbol, interval, open_time
            """,
            [per_group],
        ).fetchall()
    finally:
        connection.close()


def compare_with_binance(
    clean_root: Path,
    *,
    per_group: int = 1,
    client: PublicJsonClient | None = None,
) -> ComparisonResult:
    """Compare deterministic samples against Binance's native 15m/1h candles."""

    if per_group < 1:
        raise ValueError("per_group must be positive")
    rows = _sample_rows(clean_root, per_group)
    owned_client = client is None
    active_client = client or BinanceRestClient()
    comparisons: list[ComparisonRecord] = []
    try:
        for row in rows:
            dataset, symbol, interval, open_time_ms = row[:4]
            if not isinstance(dataset, str) or not isinstance(symbol, str):
                raise ValueError("clean candle identifiers are invalid")
            if not isinstance(interval, str) or not isinstance(open_time_ms, int):
                raise ValueError("clean candle interval/time is invalid")
            endpoint, instrument_key = ENDPOINTS[dataset]
            result = active_client.get_json(
                endpoint,
                {
                    instrument_key: symbol,
                    "interval": interval,
                    "startTime": open_time_ms,
                    "endTime": open_time_ms,
                    "limit": 1,
                },
            )
            payload = result.data
            if (
                not isinstance(payload, list)
                or len(payload) != 1
                or not isinstance(payload[0], list)
            ):
                raise ValueError("Binance comparison response is not one kline")
            native = payload[0]
            fields = ("open", "high", "low", "close")
            expected = tuple(Decimal(str(value)) for value in row[4:8])
            actual = tuple(Decimal(str(native[index])) for index in range(1, 5))
            mismatched = [
                name
                for name, left, right in zip(fields, expected, actual, strict=True)
                if left != right
            ]
            if dataset == "trade_klines":
                trade_fields = (
                    ("volume_base", row[8], native[5]),
                    ("volume_quote", row[9], native[7]),
                    ("trade_count", row[10], native[8]),
                    ("taker_buy_volume_base", row[11], native[9]),
                    ("taker_buy_volume_quote", row[12], native[10]),
                )
                for name, left, right in trade_fields:
                    if Decimal(str(left)) != Decimal(str(right)):
                        mismatched.append(name)
            comparisons.append(
                ComparisonRecord(
                    dataset=dataset,
                    symbol=symbol,
                    interval=interval,
                    open_time_ms=open_time_ms,
                    matched=not mismatched,
                    mismatched_fields=tuple(mismatched),
                )
            )
    finally:
        if owned_client and isinstance(active_client, BinanceRestClient):
            active_client.close()
    matched = sum(record.matched for record in comparisons)
    return ComparisonResult(
        checked=len(comparisons),
        matched=matched,
        mismatched=len(comparisons) - matched,
        records=tuple(comparisons),
    )

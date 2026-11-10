"""Paginated USDⓈ-M backfills into the append-only raw store."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final, cast

from ntnbinance.data_contract import INTERVAL_DURATION, require_utc
from ntnbinance.ingestion.raw_store import RawRecord, RawStore, WriteResult
from ntnbinance.ingestion.rest import BinanceRestClient


class BackfillError(RuntimeError):
    """A Binance page violated ordering or payload expectations."""


@dataclass(frozen=True, slots=True)
class DatasetSpec:
    name: str
    endpoint: str
    instrument_param: str
    time_index: int
    limit: int


KLINE_DATASETS: Final[dict[str, DatasetSpec]] = {
    "trade_klines": DatasetSpec("trade_klines", "/fapi/v1/klines", "symbol", 0, 1000),
    "mark_price_klines": DatasetSpec(
        "mark_price_klines", "/fapi/v1/markPriceKlines", "symbol", 0, 1000
    ),
    "index_price_klines": DatasetSpec(
        "index_price_klines", "/fapi/v1/indexPriceKlines", "pair", 0, 1000
    ),
}


@dataclass(slots=True)
class BackfillSummary:
    requests: int = 0
    received: int = 0
    written: int = 0
    duplicates: int = 0

    def add(self, result: WriteResult, received: int) -> None:
        self.requests += 1
        self.received += received
        self.written += result.written_count
        self.duplicates += result.duplicate_count


def _milliseconds(value: datetime) -> int:
    return int(require_utc(value, "timestamp").timestamp() * 1000)


def _page_as_sequence(value: object, dataset: str) -> list[object]:
    if not isinstance(value, list):
        raise BackfillError(f"{dataset} response must be a JSON array")
    return value


class BackfillService:
    """Fetch closed-history candidates while retaining exact raw payloads."""

    def __init__(self, client: BinanceRestClient, store: RawStore) -> None:
        self.client = client
        self.store = store

    def bootstrap_exchange_limits(self) -> None:
        response = self.client.get_json("/fapi/v1/exchangeInfo")
        self.client.configure_limits(response.data)

    def server_time_ms(self) -> int:
        response = self.client.get_json("/fapi/v1/time")
        if not isinstance(response.data, dict) or not isinstance(
            response.data.get("serverTime"), int
        ):
            raise BackfillError("server time response is invalid")
        return cast(int, response.data["serverTime"])

    def backfill_klines(
        self,
        *,
        dataset: str,
        instrument: str,
        interval: str,
        start: datetime,
        end: datetime,
    ) -> BackfillSummary:
        try:
            spec = KLINE_DATASETS[dataset]
            step_ms = int(INTERVAL_DURATION[interval].total_seconds() * 1000)
        except KeyError as error:
            raise BackfillError(
                f"unsupported kline dataset/interval: {dataset}/{interval}"
            ) from error
        cursor = _milliseconds(start)
        end_ms = _milliseconds(end)
        summary = BackfillSummary()
        while cursor <= end_ms:
            params: dict[str, object] = {
                spec.instrument_param: instrument,
                "interval": interval,
                "startTime": cursor,
                "endTime": end_ms,
                "limit": spec.limit,
            }
            page = _page_as_sequence(self.client.get_json(spec.endpoint, params).data, dataset)
            if not page:
                break
            records = self._kline_records(spec, instrument, interval, params, page)
            result = self.store.write_batch(records)
            summary.add(result, len(page))
            last_open = records[-1].event_time_ms - step_ms + 1
            next_cursor = last_open + step_ms
            if next_cursor <= cursor:
                raise BackfillError(f"{dataset} pagination did not advance")
            cursor = next_cursor
            if len(page) < spec.limit:
                break
        return summary

    @staticmethod
    def _kline_records(
        spec: DatasetSpec,
        instrument: str,
        interval: str,
        params: Mapping[str, object],
        page: Sequence[object],
    ) -> list[RawRecord]:
        ingested_at = datetime.now(UTC)
        records: list[RawRecord] = []
        previous_open = -1
        for payload in page:
            if not isinstance(payload, list) or len(payload) < 7:
                raise BackfillError(f"invalid {spec.name} kline tuple")
            open_time = payload[spec.time_index]
            close_time = payload[6]
            if not isinstance(open_time, int) or not isinstance(close_time, int):
                raise BackfillError(f"invalid {spec.name} kline timestamps")
            if open_time <= previous_open:
                raise BackfillError(f"{spec.name} page is not strictly ascending")
            previous_open = open_time
            records.append(
                RawRecord.create(
                    dataset=spec.name,
                    source="REST",
                    endpoint=spec.endpoint,
                    request_params=params,
                    record_key=f"{instrument}|{interval}|{open_time}",
                    event_time_ms=close_time,
                    ingested_at=ingested_at,
                    payload=payload,
                )
            )
        return records

    def backfill_funding(self, *, symbol: str, start: datetime, end: datetime) -> BackfillSummary:
        return self._backfill_objects(
            dataset="funding_rates",
            endpoint="/fapi/v1/fundingRate",
            identity={"symbol": symbol},
            time_field="fundingTime",
            key_fields=("symbol", "fundingTime", "rateType"),
            start=start,
            end=end,
            limit=1000,
        )

    def backfill_open_interest(
        self, *, symbol: str, period: str, start: datetime, end: datetime
    ) -> BackfillSummary:
        return self._backfill_objects(
            dataset="open_interest",
            endpoint="/futures/data/openInterestHist",
            identity={"symbol": symbol, "period": period},
            time_field="timestamp",
            key_fields=("symbol", "timestamp"),
            start=start,
            end=end,
            limit=500,
        )

    def _backfill_objects(
        self,
        *,
        dataset: str,
        endpoint: str,
        identity: Mapping[str, object],
        time_field: str,
        key_fields: tuple[str, ...],
        start: datetime,
        end: datetime,
        limit: int,
    ) -> BackfillSummary:
        cursor = _milliseconds(start)
        end_ms = _milliseconds(end)
        summary = BackfillSummary()
        while cursor <= end_ms:
            params = {**identity, "startTime": cursor, "endTime": end_ms, "limit": limit}
            page = _page_as_sequence(self.client.get_json(endpoint, params).data, dataset)
            if not page:
                break
            ingested_at = datetime.now(UTC)
            records: list[RawRecord] = []
            previous_time = -1
            for payload in page:
                if not isinstance(payload, dict) or not isinstance(payload.get(time_field), int):
                    raise BackfillError(f"invalid {dataset} object")
                event_time = payload[time_field]
                if event_time < previous_time:
                    raise BackfillError(f"{dataset} page is not ascending")
                previous_time = event_time
                key = "|".join(str(payload.get(field, "STANDARD")) for field in key_fields)
                records.append(
                    RawRecord.create(
                        dataset=dataset,
                        source="REST",
                        endpoint=endpoint,
                        request_params=params,
                        record_key=key,
                        event_time_ms=event_time,
                        ingested_at=ingested_at,
                        payload=payload,
                    )
                )
            result = self.store.write_batch(records)
            summary.add(result, len(page))
            next_cursor = records[-1].event_time_ms + 1
            if next_cursor <= cursor:
                raise BackfillError(f"{dataset} pagination did not advance")
            cursor = next_cursor
            if len(page) < limit:
                break
        return summary

    def backfill_stage_e_window(
        self,
        *,
        start: datetime,
        end: datetime,
        symbols: tuple[str, ...] = ("BTCUSDT", "ETHUSDT"),
        base_interval: str = "1m",
    ) -> dict[str, BackfillSummary]:
        """Collect the MVP trade, reference-price and derivative context window."""

        results: dict[str, BackfillSummary] = {}
        for symbol in symbols:
            for dataset in KLINE_DATASETS:
                key = f"{dataset}:{symbol}:{base_interval}"
                results[key] = self.backfill_klines(
                    dataset=dataset,
                    instrument=symbol,
                    interval=base_interval,
                    start=start,
                    end=end,
                )
            results[f"funding_rates:{symbol}"] = self.backfill_funding(
                symbol=symbol, start=start, end=end
            )
            results[f"open_interest:{symbol}:5m"] = self.backfill_open_interest(
                symbol=symbol, period="5m", start=start, end=end
            )
        return results

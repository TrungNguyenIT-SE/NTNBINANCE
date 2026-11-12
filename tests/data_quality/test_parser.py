from __future__ import annotations

from ntnbinance.data_contract import SCHEMA_VERSION, QualityFlag
from ntnbinance.data_quality.models import CandleRecord, QuarantineRecord
from ntnbinance.data_quality.parser import RawEnvelope, parse_candle


def _raw(*, source: str = "REST", schema: str = SCHEMA_VERSION) -> dict[str, object]:
    return {
        "dataset": "trade_klines",
        "source": source,
        "schema_version": schema,
        "identity_sha256": "abc",
        "ingested_at": "1970-01-01T00:01:00Z",
        "request_params": {"symbol": "BTCUSDT", "interval": "1m"},
        "payload": [0, "100", "102", "99", "101", "10", 59_999, "1000", 2, "5", "500"],
    }


def test_parse_rest_and_websocket_candles() -> None:
    parsed = parse_candle(RawEnvelope(_raw(), "raw:1"))
    assert isinstance(parsed, CandleRecord)
    assert parsed.is_closed
    assert parsed.symbol == "BTCUSDT"

    raw = _raw(source="WEBSOCKET")
    raw["payload"] = {
        "E": 59_999,
        "k": {
            "s": "BTCUSDT",
            "i": "1m",
            "t": 0,
            "T": 59_999,
            "o": "100",
            "h": "102",
            "l": "99",
            "c": "101",
            "v": "10",
            "q": "1000",
            "n": 2,
            "V": "5",
            "Q": "500",
            "x": True,
        },
    }
    parsed = parse_candle(RawEnvelope(raw, "raw:2"))
    assert isinstance(parsed, CandleRecord)
    assert parsed.source == "WEBSOCKET"


def test_parser_quarantines_schema_and_required_field_errors() -> None:
    wrong_schema = parse_candle(RawEnvelope(_raw(schema="0"), "raw:1"))
    assert isinstance(wrong_schema, QuarantineRecord)
    assert wrong_schema.quality_flags == (QualityFlag.UNKNOWN_SCHEMA.value,)

    invalid = _raw()
    invalid["payload"] = []
    parsed = parse_candle(RawEnvelope(invalid, "raw:2"))
    assert isinstance(parsed, QuarantineRecord)
    assert parsed.quality_flags == (QualityFlag.NULL_REQUIRED_FIELD.value,)


def test_parser_ignores_non_candle_features() -> None:
    raw = _raw()
    raw["dataset"] = "funding_rate"
    assert parse_candle(RawEnvelope(raw, "raw:1")) is None

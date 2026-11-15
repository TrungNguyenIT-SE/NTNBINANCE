"""Generate the reproducible Stage M theme/resolution/source benchmark."""

from __future__ import annotations

import json
import platform
import statistics
import time
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from ntnbinance.image_pipeline.models import Candle
from ntnbinance.image_pipeline.ocr import read_chart_text
from ntnbinance.image_pipeline.quality import crop_chart, measure_quality
from ntnbinance.image_pipeline.renderer import render_chart

ROOT = Path(__file__).resolve().parents[1]
DECISION_TIME_MS = 1_794_787_200_000


def _candles() -> tuple[Candle, ...]:
    return tuple(
        Candle(
            open_time_ms=DECISION_TIME_MS - (96 - index) * 900_000,
            close_time_ms=DECISION_TIME_MS - (95 - index) * 900_000,
            open=Decimal(1800 + index % 13),
            high=Decimal(1812 + index % 13),
            low=Decimal(1792 + index % 13),
            close=Decimal(1800 + index % 13 + (5 if index % 3 else -4)),
            volume=Decimal(1000 + index * 7),
        )
        for index in range(96)
    )


def main() -> None:
    rows: list[dict[str, object]] = []
    candles = _candles()
    for theme in ("DARK", "LIGHT", "ALT"):
        for width, height in ((960, 640), (1280, 720), (1920, 1080)):
            for source in ("SYNTHETIC", "BINANCE_LIKE", "TRADINGVIEW_LIKE"):
                image = render_chart(
                    candles,
                    symbol="ETHUSDT",
                    timeframe="15m",
                    decision_time_ms=DECISION_TIME_MS,
                    theme=theme,
                    size=(width, height),
                    source_layout=source,
                )
                started = time.perf_counter()
                quality = measure_quality(image, timeframe="15m")
                ocr = read_chart_text(crop_chart(image, quality.roi))
                elapsed_ms = (time.perf_counter() - started) * 1000
                fields_correct = (
                    ocr.symbol == "ETHUSDT"
                    and ocr.timeframe == "15m"
                    and ocr.timestamp_ms == DECISION_TIME_MS
                    and ocr.last_price == candles[-1].close
                )
                rows.append(
                    {
                        "theme": theme,
                        "resolution": f"{width}x{height}",
                        "source": source,
                        "quality_decision": quality.decision.value,
                        "ocr_fields_correct": fields_correct,
                        "ocr_confidence": round(ocr.mean_confidence, 4),
                        "latency_ms": round(elapsed_ms, 2),
                    }
                )
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "matrix_cases": len(rows),
        "accepted": sum(row["quality_decision"] == "ACCEPT" for row in rows),
        "ocr_correct": sum(bool(row["ocr_fields_correct"]) for row in rows),
        "latency_ms": {
            "median": round(statistics.median(float(row["latency_ms"]) for row in rows), 2),
            "p95": round(
                sorted(float(row["latency_ms"]) for row in rows)[int(len(rows) * 0.95) - 1],
                2,
            ),
            "max": max(float(row["latency_ms"]) for row in rows),
        },
        "cases": rows,
    }
    output = ROOT / "reports" / "image-pipeline-benchmark.json"
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in payload.items() if key != "cases"}, indent=2))


if __name__ == "__main__":
    main()

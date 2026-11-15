"""Point-in-time-safe synthetic candlestick renderer for research fixtures."""

from __future__ import annotations

import hashlib
import io
from datetime import UTC, datetime
from decimal import Decimal

from PIL import Image, ImageDraw, ImageFont

from ntnbinance.image_pipeline.models import Candle

THEMES = {
    "DARK": {
        "background": "#0d1421",
        "foreground": "#dce4f0",
        "grid": "#2b384b",
        "up": "#26c891",
        "down": "#f05252",
    },
    "LIGHT": {
        "background": "#f7f9fc",
        "foreground": "#202836",
        "grid": "#d7dce5",
        "up": "#12977e",
        "down": "#da4242",
    },
    "ALT": {
        "background": "#13121f",
        "foreground": "#eae6fa",
        "grid": "#343046",
        "up": "#40b1ee",
        "down": "#ffae42",
    },
}


def _float(value: Decimal) -> float:
    return float(value)


def render_chart(
    candles: tuple[Candle, ...],
    *,
    symbol: str,
    timeframe: str,
    decision_time_ms: int,
    theme: str = "DARK",
    size: tuple[int, int] = (1280, 720),
    source_layout: str = "SYNTHETIC",
) -> Image.Image:
    if not candles:
        raise ValueError("at least one closed candle is required")
    if tuple(sorted(candles, key=lambda item: item.open_time_ms)) != candles:
        raise ValueError("candles must be ordered by open time")
    if any(item.close_time_ms > decision_time_ms for item in candles):
        raise ValueError("renderer cannot consume candles after decision_time")
    if timeframe not in {"1h", "15m"} or symbol not in {"BTCUSDT", "ETHUSDT"}:
        raise ValueError("unsupported symbol or timeframe")
    colors = THEMES.get(theme)
    if colors is None:
        raise ValueError("unsupported render theme")
    width, height = size
    if width < 800 or height < 600:
        raise ValueError("render size is below the image contract")

    image = Image.new("RGB", size, colors["background"])
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.load_default(size=max(20, width // 55))
    label_font = ImageFont.load_default(size=max(14, width // 80))
    margin_left = int(width * 0.055)
    margin_right = int(width * (0.13 if source_layout == "BINANCE_LIKE" else 0.10))
    plot_top = int(height * (0.16 if source_layout == "TRADINGVIEW_LIKE" else 0.14))
    plot_bottom = int(height * 0.84)
    plot_right = width - margin_right
    plot_width = plot_right - margin_left
    plot_height = plot_bottom - plot_top

    captured = datetime.fromtimestamp(decision_time_ms / 1000, tz=UTC).strftime("%Y-%m-%d %H:%M")
    draw.text(
        (margin_left, int(height * 0.035)),
        f"{symbol}  {timeframe}",
        font=title_font,
        fill=colors["foreground"],
    )
    draw.text(
        (int(width * 0.48), int(height * 0.045)),
        f"UTC {captured}",
        font=label_font,
        fill=colors["foreground"],
    )
    draw.text(
        (int(width * 0.78), int(height * 0.035)),
        f"LAST {_float(candles[-1].close):.2f}",
        font=title_font,
        fill=colors["up"] if candles[-1].close >= candles[-1].open else colors["down"],
    )
    for index in range(7):
        y = plot_top + index * plot_height // 6
        draw.line((margin_left, y, plot_right, y), fill=colors["grid"], width=1)
    for index in range(9):
        x = margin_left + index * plot_width // 8
        draw.line((x, plot_top, x, plot_bottom), fill=colors["grid"], width=1)

    visible = candles[-min(len(candles), 120) :]
    minimum = min(_float(item.low) for item in visible)
    maximum = max(_float(item.high) for item in visible)
    price_span = maximum - minimum or 1.0
    step = plot_width / len(visible)
    body_width = max(3, int(step * 0.62))

    def price_y(value: Decimal) -> int:
        normalized = (_float(value) - minimum) / price_span
        return plot_bottom - int(normalized * plot_height)

    for index, candle in enumerate(visible):
        center = int(margin_left + (index + 0.5) * step)
        color = colors["up"] if candle.close >= candle.open else colors["down"]
        draw.line((center, price_y(candle.high), center, price_y(candle.low)), fill=color, width=1)
        top = min(price_y(candle.open), price_y(candle.close))
        bottom = max(price_y(candle.open), price_y(candle.close))
        draw.rectangle(
            (center - body_width // 2, top, center + body_width // 2, max(top + 2, bottom)),
            fill=color,
        )

    draw.rectangle(
        (margin_left, plot_top, plot_right, plot_bottom), outline=colors["foreground"], width=1
    )
    for index in range(3):
        price = maximum - index * price_span / 2
        y = plot_top + index * plot_height // 2
        draw.text(
            (plot_right + 8, y - 8),
            f"{price:.2f}",
            font=label_font,
            fill=colors["foreground"],
        )
    for index in range(3):
        candle = visible[index * (len(visible) - 1) // 2]
        timestamp = datetime.fromtimestamp(candle.close_time_ms / 1000, tz=UTC).strftime(
            "%m-%d %H:%M"
        )
        x = margin_left + index * plot_width // 2
        draw.text((x, plot_bottom + 10), timestamp, font=label_font, fill=colors["foreground"])
    return image


def png_bytes(image: Image.Image) -> bytes:
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True, exif=b"", icc_profile=None)
    return output.getvalue()


def image_sha256(image: Image.Image) -> str:
    return hashlib.sha256(png_bytes(image)).hexdigest()

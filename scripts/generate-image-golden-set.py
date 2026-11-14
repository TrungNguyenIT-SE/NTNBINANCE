"""Generate deterministic, dependency-free Stage K PNG chart fixtures and manifest."""

from __future__ import annotations

import hashlib
import json
import math
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path

WIDTH = 960
HEIGHT = 640
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "tests" / "fixtures" / "images"

FONT = {
    " ": ("000",) * 5,
    "-": ("000", "000", "111", "000", "000"),
    ".": ("000", "000", "000", "000", "010"),
    ":": ("000", "010", "000", "010", "000"),
    "0": ("111", "101", "101", "101", "111"),
    "1": ("010", "110", "010", "010", "111"),
    "2": ("111", "001", "111", "100", "111"),
    "3": ("111", "001", "111", "001", "111"),
    "4": ("101", "101", "111", "001", "001"),
    "5": ("111", "100", "111", "001", "111"),
    "6": ("111", "100", "111", "101", "111"),
    "7": ("111", "001", "010", "010", "010"),
    "8": ("111", "101", "111", "101", "111"),
    "9": ("111", "101", "111", "001", "111"),
    "A": ("010", "101", "111", "101", "101"),
    "B": ("110", "101", "110", "101", "110"),
    "C": ("111", "100", "100", "100", "111"),
    "D": ("110", "101", "101", "101", "110"),
    "E": ("111", "100", "110", "100", "111"),
    "F": ("111", "100", "110", "100", "100"),
    "G": ("111", "100", "101", "101", "111"),
    "H": ("101", "101", "111", "101", "101"),
    "I": ("111", "010", "010", "010", "111"),
    "J": ("001", "001", "001", "101", "111"),
    "K": ("101", "101", "110", "101", "101"),
    "L": ("100", "100", "100", "100", "111"),
    "M": ("101", "111", "111", "101", "101"),
    "N": ("101", "111", "111", "111", "101"),
    "O": ("111", "101", "101", "101", "111"),
    "P": ("111", "101", "111", "100", "100"),
    "Q": ("111", "101", "101", "111", "001"),
    "R": ("110", "101", "110", "101", "101"),
    "S": ("111", "100", "111", "001", "111"),
    "T": ("111", "010", "010", "010", "010"),
    "U": ("101", "101", "101", "101", "111"),
    "V": ("101", "101", "101", "101", "010"),
    "W": ("101", "101", "111", "111", "101"),
    "X": ("101", "101", "010", "101", "101"),
    "Y": ("101", "101", "010", "010", "010"),
    "Z": ("111", "001", "010", "100", "111"),
}


@dataclass(frozen=True)
class Style:
    background: tuple[int, int, int]
    foreground: tuple[int, int, int]
    grid: tuple[int, int, int]
    up: tuple[int, int, int]
    down: tuple[int, int, int]


DARK = Style((13, 20, 33), (220, 228, 240), (43, 56, 75), (38, 200, 145), (240, 82, 82))
LIGHT = Style((247, 249, 252), (32, 40, 54), (215, 220, 229), (18, 151, 126), (218, 66, 66))
ALT = Style((19, 18, 31), (234, 230, 250), (52, 48, 70), (64, 177, 238), (255, 174, 66))
LOW_CONTRAST = Style(
    (109, 109, 109), (126, 126, 126), (116, 116, 116), (129, 129, 129), (122, 122, 122)
)


class Canvas:
    def __init__(self, style: Style) -> None:
        self.style = style
        self.pixels = bytearray(style.background * (WIDTH * HEIGHT))

    def pixel(self, x: int, y: int, color: tuple[int, int, int]) -> None:
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            offset = (y * WIDTH + x) * 3
            self.pixels[offset : offset + 3] = bytes(color)

    def rect(self, x: int, y: int, width: int, height: int, color: tuple[int, int, int]) -> None:
        for row in range(max(0, y), min(HEIGHT, y + height)):
            start = (row * WIDTH + max(0, x)) * 3
            end = (row * WIDTH + min(WIDTH, x + width)) * 3
            self.pixels[start:end] = bytes(color) * ((end - start) // 3)

    def line(self, x1: int, y1: int, x2: int, y2: int, color: tuple[int, int, int]) -> None:
        steps = max(abs(x2 - x1), abs(y2 - y1), 1)
        for step in range(steps + 1):
            self.pixel(x1 + (x2 - x1) * step // steps, y1 + (y2 - y1) * step // steps, color)

    def text(self, x: int, y: int, value: str, color: tuple[int, int, int], scale: int = 3) -> None:
        cursor = x
        for character in value.upper():
            glyph = FONT.get(character, FONT[" "])
            for row, pattern in enumerate(glyph):
                for column, enabled in enumerate(pattern):
                    if enabled == "1":
                        self.rect(cursor + column * scale, y + row * scale, scale, scale, color)
            cursor += 4 * scale

    def png(self) -> bytes:
        rows = bytearray()
        stride = WIDTH * 3
        for y in range(HEIGHT):
            rows.append(0)
            rows.extend(self.pixels[y * stride : (y + 1) * stride])

        def chunk(name: bytes, data: bytes) -> bytes:
            return (
                struct.pack(">I", len(data))
                + name
                + data
                + struct.pack(">I", zlib.crc32(name + data))
            )

        return (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(rows), 9))
            + chunk(b"IEND", b"")
        )


def render(symbol: str, timeframe: str, style: Style, defect: str | None) -> bytes:
    canvas = Canvas(style)
    plot_left = 52 if defect != "crop" else 0
    plot_top, plot_right, plot_bottom = 78, 855, 585
    for x in range(plot_left, plot_right + 1, 100):
        canvas.line(x, plot_top, x, plot_bottom, style.grid)
    for y in range(plot_top, plot_bottom + 1, 84):
        canvas.line(plot_left, y, plot_right, y, style.grid)
    canvas.text(55, 24, f"{symbol}  {timeframe}", style.foreground, 4)
    canvas.text(570, 30, "UTC 2026-11-15 01:30", style.foreground, 2)
    count = 88 if timeframe == "1H" else 96
    spacing = max(7, (plot_right - plot_left - 18) // count)
    for index in range(count):
        center = plot_left + 12 + index * spacing
        middle = 330 + int(92 * math.sin(index / 7.1) + 26 * math.sin(index / 2.9))
        body = 8 + index % 17
        rising = index % 3 != 0
        color = style.up if rising else style.down
        high = middle - body - 9 - index % 5
        low = middle + body + 9 + index % 6
        canvas.line(center, high, center, low, color)
        canvas.rect(center - 2, middle - body if rising else middle, 5, body, color)
    if defect != "crop":
        canvas.line(plot_right, plot_top, plot_right, plot_bottom, style.foreground)
        canvas.line(plot_left, plot_bottom, plot_right, plot_bottom, style.foreground)
        canvas.text(868, 100, "72000.0", style.foreground, 2)
        canvas.text(868, 320, "70000.0", style.foreground, 2)
        canvas.text(868, 548, "68000.0", style.foreground, 2)
    if defect == "blur":
        canvas.rect(0, 0, WIDTH, HEIGHT, (86, 91, 99))
        canvas.text(300, 300, "BLURRED CHART", (101, 106, 114), 5)
    elif defect == "occluded":
        canvas.rect(270, 185, 430, 250, (34, 34, 38))
        canvas.text(360, 285, "ORDER PANEL", (230, 230, 235), 4)
    return canvas.png()


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    pairs = [
        ("K01", "BTCUSDT", "DARK", DARK, None, "ACCEPT", "VALID_DARK"),
        ("K02", "ETHUSDT", "LIGHT", LIGHT, None, "ACCEPT", "VALID_LIGHT"),
        ("K03", "ETHUSDT", "ALT", ALT, None, "ACCEPT", "VALID_ALT_COLORS"),
        ("K04", "BTCUSDT", "LIGHT", LIGHT, None, "ACCEPT", "VALID_LIGHT"),
        ("K05", "BTCUSDT", "DARK", DARK, "blur", "REJECTED_INPUT", "BLUR"),
        ("K06", "ETHUSDT", "LIGHT", LIGHT, "crop", "REJECTED_INPUT", "CROP_AXES"),
        ("K07", "BTCUSDT", "DARK", DARK, "occluded", "REJECTED_INPUT", "OCCLUSION"),
        ("K08", "ETHUSDT", "LOW_CONTRAST", LOW_CONTRAST, None, "REJECTED_INPUT", "THEME_CONTRAST"),
        ("K09", "BTCUSDT", "DARK", DARK, None, "REJECTED_INPUT", "PAIR_SYMBOL_MISMATCH"),
        ("K10", "BTCUSDT", "LIGHT", LIGHT, None, "REJECTED_INPUT", "PAIR_TIMEFRAME_MISMATCH"),
        ("K11", "ETHUSDT", "DARK", DARK, None, "NO_TRADE", "STALE_IMAGE"),
        ("K12", "BTCUSDT", "LIGHT", LIGHT, None, "NO_TRADE", "LAST_PRICE_MISMATCH"),
    ]
    manifest: dict[str, object] = {
        "schema_version": "1.0.0",
        "generator": "scripts/generate-image-golden-set.py",
        "width_px": WIDTH,
        "height_px": HEIGHT,
        "pairs": [],
    }
    entries: list[dict[str, object]] = []
    for pair_id, symbol, theme, style, defect, verdict, reason in pairs:
        timeframes = ("1H", "15M")
        symbols = (symbol, "ETHUSDT") if pair_id == "K09" else (symbol, symbol)
        if pair_id == "K10":
            timeframes = ("1H", "1H")
        files: list[dict[str, str]] = []
        for slot, image_symbol, timeframe in zip(("1h", "15m"), symbols, timeframes, strict=True):
            filename = f"{pair_id.lower()}_{slot}.png"
            payload = render(image_symbol, timeframe, style, defect)
            (OUTPUT / filename).write_bytes(payload)
            files.append(
                {"slot": slot, "path": filename, "sha256": hashlib.sha256(payload).hexdigest()}
            )
        entries.append(
            {
                "pair_id": pair_id,
                "declared_symbol": symbol,
                "theme": theme,
                "defect": defect,
                "expected_decision": verdict,
                "primary_reason": reason,
                "images": files,
            }
        )
    manifest["pairs"] = entries
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    main()

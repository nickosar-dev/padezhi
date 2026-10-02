#!/usr/bin/env python3
"""Рисует icon-192.png и icon-512.png: тёмный фон и шесть столбиков цветов падежей.
Столбики держатся в центральной «безопасной зоне», поэтому иконка годится и как maskable."""
import struct
import zlib
from pathlib import Path

BG = (0x18, 0x20, 0x2D)
BARS = [  # gen acc dat instr loc voc — цвета из тёмной темы приложения
    ((0x9A, 0xA4, 0xFF), 0.62),
    ((0x4F, 0xD0, 0xBC), 0.86),
    ((0xE6, 0xB2, 0x4E), 0.48),
    ((0xF2, 0x8B, 0xB8), 1.00),
    ((0xA5, 0xD2, 0x6A), 0.70),
    ((0xC7, 0xA3, 0xF2), 0.40),
]


def png(w, h, rows):
    raw = b"".join(b"\x00" + bytes(r) for r in rows)

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def icon(size):
    px = [[BG for _ in range(size)] for _ in range(size)]
    left, right = 0.27 * size, 0.73 * size
    top, bottom = 0.31 * size, 0.69 * size
    slot = (right - left) / len(BARS)
    bar_w = slot * 0.72
    for i, (color, height) in enumerate(BARS):
        x0 = int(round(left + i * slot + (slot - bar_w) / 2))
        x1 = int(round(left + i * slot + (slot + bar_w) / 2))
        y0 = int(round(bottom - (bottom - top) * height))
        for y in range(y0, int(round(bottom))):
            for x in range(x0, x1):
                px[y][x] = color
    rows = [[c for p in row for c in p] for row in px]
    return png(size, size, rows)


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    for s in (192, 512):
        (here / f"icon-{s}.png").write_bytes(icon(s))
        print(f"icon-{s}.png")

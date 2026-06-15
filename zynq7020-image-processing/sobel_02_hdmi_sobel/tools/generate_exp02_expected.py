#!/usr/bin/env python3
"""Generate the Experiment 2 Sobel golden data and threshold images."""

from __future__ import annotations

import argparse
import re
import struct
import zlib
from pathlib import Path

WIDTH = 128
HEIGHT = 72
PIXELS = WIDTH * HEIGHT
ROM_PATTERN = re.compile(r"image_mem\[\s*(\d+)\s*\]\s*=\s*24'h([0-9a-fA-F]{6})")


def read_rom(path: Path) -> list[tuple[int, int, int]]:
    values: list[tuple[int, int, int] | None] = [None] * PIXELS
    for address_text, rgb_text in ROM_PATTERN.findall(path.read_text(encoding="ascii")):
        address = int(address_text)
        if not 0 <= address < PIXELS:
            raise SystemExit(f"{path}: ROM address {address} is out of range")
        value = int(rgb_text, 16)
        values[address] = ((value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF)

    missing = [index for index, value in enumerate(values) if value is None]
    if missing:
        raise SystemExit(f"{path}: missing {len(missing)} ROM entries; first is {missing[0]}")
    return [value for value in values if value is not None]


def rgb_to_gray(rgb: list[tuple[int, int, int]]) -> list[int]:
    return [((r * 77) + (g * 150) + (b * 29)) >> 8 for r, g, b in rgb]


def sobel(gray: list[int]) -> list[int]:
    edge = [0] * PIXELS
    for y in range(1, HEIGHT - 1):
        for x in range(1, WIDTH - 1):
            top = (y - 1) * WIDTH
            middle = y * WIDTH
            bottom = (y + 1) * WIDTH
            gx = (
                -gray[top + x - 1]
                + gray[top + x + 1]
                - 2 * gray[middle + x - 1]
                + 2 * gray[middle + x + 1]
                - gray[bottom + x - 1]
                + gray[bottom + x + 1]
            )
            gy = (
                -gray[top + x - 1]
                - 2 * gray[top + x]
                - gray[top + x + 1]
                + gray[bottom + x - 1]
                + 2 * gray[bottom + x]
                + gray[bottom + x + 1]
            )
            edge[middle + x] = min(abs(gx) + abs(gy), 255)
    return edge


def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(chunk_type)
    crc = zlib.crc32(data, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def write_gray_png(path: Path, width: int, height: int, pixels: bytes) -> None:
    rows = []
    for y in range(height):
        start = y * width
        rows.append(b"\x00" + pixels[start : start + width])
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(b"".join(rows), level=9))
        + png_chunk(b"IEND", b"")
    )


def scale_10x(pixels: list[int]) -> bytes:
    output = bytearray()
    for y in range(HEIGHT):
        row = bytes(pixels[y * WIDTH : (y + 1) * WIDTH])
        expanded = b"".join(bytes([value]) * 10 for value in row)
        for _ in range(10):
            output.extend(expanded)
    return bytes(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--hex-output", type=Path, required=True)
    args = parser.parse_args()

    rgb = read_rom(args.rom)
    gray = rgb_to_gray(rgb)
    edge = sobel(gray)

    args.hex_output.parent.mkdir(parents=True, exist_ok=True)
    args.hex_output.write_text(
        "".join(f"{value:02x}\n" for value in edge), encoding="ascii"
    )

    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    write_gray_png(
        args.evidence_dir / "exp02_edge_strength.png",
        1280,
        720,
        scale_10x(edge),
    )

    thresholds = (40, 80, 120)
    counts: list[tuple[int, int]] = []
    for threshold in thresholds:
        binary = [255 if value >= threshold else 0 for value in edge]
        count = sum(value == 255 for value in binary)
        counts.append((threshold, count))
        write_gray_png(
            args.evidence_dir / f"exp02_threshold_{threshold}.png",
            1280,
            720,
            scale_10x(binary),
        )

    if not all(counts[index][1] >= counts[index + 1][1] for index in range(2)):
        raise SystemExit(f"threshold counts are not monotonic: {counts}")

    stats_path = args.evidence_dir / "exp02_threshold_stats.txt"
    stats_path.write_text(
        "\n".join(
            [
                "Experiment 2 fixed-image Sobel threshold statistics",
                "Image size: 128 x 72 (9216 source pixels)",
                "Comparison: edge_pixel >= threshold",
                "",
                *[
                    f"threshold={threshold:3d} white_pixels={count:4d}"
                    for threshold, count in counts
                ],
                "",
                "Monotonic non-increasing check: passed",
                "",
            ]
        ),
        encoding="ascii",
    )

    print(f"EXP02_GOLDEN_PIXELS={len(edge)}")
    for threshold, count in counts:
        print(f"EXP02_THRESHOLD_{threshold}_WHITE={count}")
    print("EXP02_THRESHOLD_MONOTONIC=passed")


if __name__ == "__main__":
    main()

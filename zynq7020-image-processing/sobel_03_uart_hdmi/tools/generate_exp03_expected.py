#!/usr/bin/env python3
"""Generate Experiment 3 UART -> PS -> BRAM golden data and the expected HDMI image.

The PS receiver (ps_uart_bram_app/src/main.c) parses a fixed 128x72 RGB888 frame
sent by host_camera_uart over UART and writes 0x00RRGGBB words into AXI BRAM. The
PL side (hdmi_bram_display.v) reads the framebuffer and shows it on HDMI with a
10x upscale and a single-color display border.

This script:
  * synthesises a deterministic 128x72 test image,
  * encodes it with the exact host frame format,
  * parses it back with a golden model mirroring main.c receive_frame() and
    asserts the round trip is lossless,
  * injects malformed frames and asserts the documented error codes,
  * writes the framebuffer as 32-bit hex for the RTL testbench, and
  * renders the expected 1280x720 HDMI image (10x upscale + display border).

Pure standard library only (no numpy / opencv / PIL).
"""

from __future__ import annotations

import argparse
import struct
import zlib
from pathlib import Path

WIDTH = 128
HEIGHT = 72
PIXELS = WIDTH * HEIGHT
RGB888_FORMAT = 0x18

FRAME_SYNC = (0x55, 0xAA)
LINE_SYNC = (0x33, 0xCC)

SCALE = 10
OUT_WIDTH = WIDTH * SCALE    # 1280
OUT_HEIGHT = HEIGHT * SCALE  # 720

# Must match the defaults in hdmi_bram_display.v.
BORDER_WIDTH = 20
BORDER_COLOR = (0x00, 0x66, 0xFF)


def make_test_image() -> list[tuple[int, int, int]]:
    """Deterministic 128x72 pattern that exercises all three colour channels."""
    image: list[tuple[int, int, int]] = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            r = (x * 255) // (WIDTH - 1)
            g = (y * 255) // (HEIGHT - 1)
            b = ((x + y) * 255) // (WIDTH + HEIGHT - 2)
            image.append((r, g, b))
    return image


def encode_frame(image, width=WIDTH, height=HEIGHT, fmt=RGB888_FORMAT,
                 bad_row=None, truncate=None) -> bytes:
    """Encode a frame using the exact host_camera_uart format.

    bad_row=(index, value) forces one line header to carry a wrong row number.
    truncate=N cuts the byte stream to N bytes to model a UART timeout.
    """
    out = bytearray()
    out += bytes(FRAME_SYNC)
    out += bytes((width & 0xFF, (width >> 8) & 0xFF))
    out += bytes((height & 0xFF, (height >> 8) & 0xFF))
    out.append(fmt & 0xFF)
    for y in range(height):
        out += bytes(LINE_SYNC)
        row_value = y
        if bad_row is not None and y == bad_row[0]:
            row_value = bad_row[1]
        out += bytes((row_value & 0xFF, (row_value >> 8) & 0xFF))
        for x in range(width):
            r, g, b = image[y * width + x]
            out += bytes((r & 0xFF, g & 0xFF, b & 0xFF))
    if truncate is not None:
        return bytes(out[:truncate])
    return bytes(out)


class ByteStream:
    """Minimal byte reader; recv() returns None at end of stream (a 'timeout')."""

    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def recv(self):
        if self.pos >= len(self.data):
            return None
        value = self.data[self.pos]
        self.pos += 1
        return value


def _wait_for_sync(stream, first, second):
    prev = None
    while True:
        cur = stream.recv()
        if cur is None:
            return False
        if prev == first and cur == second:
            return True
        prev = cur


def _recv_u16_le(stream):
    low = stream.recv()
    if low is None:
        return None
    high = stream.recv()
    if high is None:
        return None
    return low | (high << 8)


def parse_frame(data: bytes):
    """Golden model of main.c receive_frame(). Returns (code, framebuffer|None).

    Codes match main.c exactly: 0 ok, -1 size/format, -2 row, -3 frame-sync
    timeout, -4 header timeout, -5 line-sync timeout, -6 row timeout, -7 pixel
    timeout.
    """
    stream = ByteStream(data)
    framebuffer = [0] * PIXELS

    if not _wait_for_sync(stream, *FRAME_SYNC):
        return -3, None
    width = _recv_u16_le(stream)
    if width is None:
        return -4, None
    height = _recv_u16_le(stream)
    if height is None:
        return -4, None
    fmt = stream.recv()
    if fmt is None:
        return -4, None
    if width != WIDTH or height != HEIGHT or fmt != RGB888_FORMAT:
        return -1, None

    for row_expected in range(HEIGHT):
        if not _wait_for_sync(stream, *LINE_SYNC):
            return -5, None
        row = _recv_u16_le(stream)
        if row is None:
            return -6, None
        if row != row_expected:
            return -2, None
        for x in range(WIDTH):
            r = stream.recv()
            g = stream.recv()
            b = stream.recv()
            if r is None or g is None or b is None:
                return -7, None
            framebuffer[row_expected * WIDTH + x] = (r << 16) | (g << 8) | b
    return 0, framebuffer


def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(chunk_type)
    crc = zlib.crc32(data, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def write_rgb_png(path: Path, width: int, height: int, rgb_rows) -> None:
    """rgb_rows: iterable of bytes, each of length width*3 (truecolour, 8 bit)."""
    raw = bytearray()
    for row in rgb_rows:
        raw.append(0)  # filter type 0 (none)
        raw += row
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)  # colour type 2
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(bytes(raw), level=9))
        + png_chunk(b"IEND", b"")
    )


def render_expected_hdmi(framebuffer):
    """Render the 1280x720 expected screen: 10x upscale plus the display border."""
    rows = []
    for out_y in range(OUT_HEIGHT):
        src_y = out_y // SCALE
        row = bytearray()
        for out_x in range(OUT_WIDTH):
            in_border = (
                out_x < BORDER_WIDTH
                or out_x >= OUT_WIDTH - BORDER_WIDTH
                or out_y < BORDER_WIDTH
                or out_y >= OUT_HEIGHT - BORDER_WIDTH
            )
            if in_border:
                r, g, b = BORDER_COLOR
            else:
                src_x = out_x // SCALE
                pixel = framebuffer[src_y * WIDTH + src_x]
                r, g, b = (pixel >> 16) & 0xFF, (pixel >> 8) & 0xFF, pixel & 0xFF
            row += bytes((r, g, b))
        rows.append(bytes(row))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--hex-output", type=Path, required=True)
    args = parser.parse_args()

    image = make_test_image()

    # 1. Round-trip lossless check.
    code, framebuffer = parse_frame(encode_frame(image))
    if code != 0 or framebuffer is None:
        raise SystemExit(f"round-trip parse failed with code {code}")
    expected_fb = [(r << 16) | (g << 8) | b for (r, g, b) in image]
    if framebuffer != expected_fb:
        raise SystemExit("round-trip framebuffer mismatch")

    # 2. Error-injection checks (return codes must match main.c).
    cases = [
        ("wrong_width", encode_frame(image, width=64), -1),
        ("wrong_format", encode_frame(image, fmt=0x10), -1),
        ("wrong_row", encode_frame(image, bad_row=(10, 99)), -2),
        ("trunc_before_header", encode_frame(image, truncate=1), -3),
        ("trunc_after_header", encode_frame(image, truncate=7), -5),
        ("trunc_mid_pixels", encode_frame(image, truncate=7 + 4 + 100), -7),
    ]
    results = []
    for name, bad_stream, expected_code in cases:
        got, _ = parse_frame(bad_stream)
        results.append((name, expected_code, got))
        if got != expected_code:
            raise SystemExit(f"error case {name}: expected {expected_code}, got {got}")

    # 3. Framebuffer hex for the RTL testbench (32-bit 0x00RRGGBB words).
    args.hex_output.parent.mkdir(parents=True, exist_ok=True)
    args.hex_output.write_text(
        "".join(f"{word:08x}\n" for word in framebuffer), encoding="ascii"
    )

    # 4. Expected HDMI image (10x upscale + display border).
    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    write_rgb_png(
        args.evidence_dir / "exp03_expected_image.png",
        OUT_WIDTH,
        OUT_HEIGHT,
        render_expected_hdmi(framebuffer),
    )

    # 5. Self-check report.
    border_px = OUT_WIDTH * OUT_HEIGHT - (OUT_WIDTH - 2 * BORDER_WIDTH) * (
        OUT_HEIGHT - 2 * BORDER_WIDTH
    )
    report = [
        "实验 3 UART -> PS -> BRAM 协议离线自检",
        f"图像尺寸：{WIDTH} x {HEIGHT}（{PIXELS} 像素，RGB888，format=0x{RGB888_FORMAT:02x}）",
        f"帧头 0x{FRAME_SYNC[0]:02x}{FRAME_SYNC[1]:02x}，行头 0x{LINE_SYNC[0]:02x}{LINE_SYNC[1]:02x}",
        "",
        "往返无损检查：通过（解析重建的 framebuffer 与源图逐像素一致）",
        "",
        "错误注入检查（错误码须与 main.c 一致）：",
        *[f"  {name:20s} expected={exp:3d} got={got:3d}" for name, exp, got in results],
        "",
        f"HDMI 输出：{OUT_WIDTH} x {OUT_HEIGHT}，每源像素放大 {SCALE} x {SCALE}",
        f"显示边框：BORDER_WIDTH={BORDER_WIDTH}，"
        f"BORDER_COLOR=#{BORDER_COLOR[0]:02x}{BORDER_COLOR[1]:02x}{BORDER_COLOR[2]:02x}，"
        f"边框像素={border_px}",
        "",
    ]
    (args.evidence_dir / "exp03_protocol_selfcheck.txt").write_text(
        "\n".join(report), encoding="utf-8"
    )

    print(f"EXP03_PIXELS={PIXELS}")
    print("EXP03_ROUNDTRIP=passed")
    for name, exp, got in results:
        print(f"EXP03_ERR_{name}={got}")
    print("EXP03_SELFCHECK=passed")


if __name__ == "__main__":
    main()

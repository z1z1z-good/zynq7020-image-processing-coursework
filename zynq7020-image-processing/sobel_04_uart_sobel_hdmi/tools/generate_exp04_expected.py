#!/usr/bin/env python3
"""Generate Experiment 4 UART -> PS -> BRAM -> PL Sobel golden data and expected HDMI image.

Experiment 4 reuses the experiment 3 input chain (PC -> UART -> PS -> AXI BRAM) and
adds PL gray + Sobel + a colored-edge display.  The PS receiver
(``ps_uart_sobel_bram_app/src/main.c``) parses a fixed 128x72 RGB888 frame and
writes ``0x00RRGGBB`` words into AXI BRAM -- this is byte-for-byte identical to
experiment 3.  The PL side (``hdmi_bram_sobel_display.v``) then reads the
framebuffer, computes ``gray = (77*R + 150*G + 29*B) >> 8`` and a 3x3 Sobel
(``mag = |gx| + |gy|`` saturated to 255, with the 1-pixel image border forced to
0), stores the 8-bit edge magnitude in ``edge_mem`` and shows it on HDMI with a
10x upscale.  The first-week base extension marks edge pixels
(``edge_pixel >= EDGE_THRESHOLD``) in ``EDGE_COLOR`` over a black background.

This script:
  * synthesises a deterministic, edge-rich 128x72 test image,
  * encodes it with the exact host frame format and parses it back with a golden
    model mirroring ``main.c`` ``receive_frame()``, asserting the round trip is
    lossless and the documented error codes hold,
  * computes the gray + Sobel software golden matching ``rgb_to_gray.v`` /
    ``sobel_core.v``,
  * writes the framebuffer as 32-bit hex for the RTL testbench, and
  * renders the expected 1280x720 colored-edge HDMI image, a raw edge-strength
    grayscale image, and a 40/80/120 edge-pixel-count comparison.

Pure standard library only (no numpy / opencv / PIL); the PNG writer is the same
hand-rolled ``struct`` + ``zlib`` approach used by ``generate_exp03_expected.py``.
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

# Must match the defaults in hdmi_bram_sobel_display.v.
EDGE_THRESHOLD = 80
EDGE_COLOR = (0x00, 0xFF, 0x00)  # green
THRESHOLDS = (40, 80, 120)


def make_test_image() -> list[tuple[int, int, int]]:
    """Deterministic 128x72 pattern with both weak (gradient) and strong edges.

    A smooth RGB gradient exercises all three colour channels and produces weak
    Sobel responses, while a few solid blocks, a hollow rectangle and a diagonal
    line produce strong responses so the 40/80/120 threshold comparison is
    meaningful.
    """
    image: list[tuple[int, int, int]] = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            r = (x * 255) // (WIDTH - 1)
            g = (y * 255) // (HEIGHT - 1)
            b = ((x + y) * 255) // (WIDTH + HEIGHT - 2)

            if 12 <= x < 40 and 12 <= y < 32:
                r, g, b = 240, 240, 240           # bright solid block
            elif 60 <= x < 100 and 20 <= y < 52 and not (70 <= x < 90 and 30 <= y < 42):
                r, g, b = 16, 16, 16              # hollow dark frame
            elif 100 <= x < 120 and 48 <= y < 66:
                r, g, b = 250, 32, 32             # red block

            if abs(x - 2 * y) < 2:
                r, g, b = 255, 255, 0             # diagonal yellow line

            image.append((r & 0xFF, g & 0xFF, b & 0xFF))
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


def rgb_to_gray(rgb: list[tuple[int, int, int]]) -> list[int]:
    """8-bit luma matching rgb_to_gray.v: (77*R + 150*G + 29*B) >> 8."""
    return [((r * 77) + (g * 150) + (b * 29)) >> 8 for r, g, b in rgb]


def sobel(gray: list[int]) -> list[int]:
    """3x3 Sobel matching sobel_core.v: mag = |gx| + |gy| (sat 255), border = 0."""
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


def colored_edge(edge: list[int], threshold: int = EDGE_THRESHOLD,
                 color: tuple[int, int, int] = EDGE_COLOR) -> list[tuple[int, int, int]]:
    """edge_pixel >= threshold -> color, else black. Mirrors the RTL display map."""
    return [color if value >= threshold else (0, 0, 0) for value in edge]


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


def write_gray_png(path: Path, width: int, height: int, pixels: bytes) -> None:
    """pixels: bytes of length width*height (greyscale, 8 bit)."""
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        rows += pixels[y * width:(y + 1) * width]
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)  # colour type 0
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(bytes(rows), level=9))
        + png_chunk(b"IEND", b"")
    )


def scale_gray_10x(pixels: list[int]) -> bytes:
    """Upscale a 128x72 greyscale list to 1280x720 bytes (10x10 nearest)."""
    output = bytearray()
    for y in range(HEIGHT):
        row = bytes(pixels[y * WIDTH:(y + 1) * WIDTH])
        expanded = b"".join(bytes([value]) * SCALE for value in row)
        for _ in range(SCALE):
            output.extend(expanded)
    return bytes(output)


def render_colored_rows(color: list[tuple[int, int, int]]):
    """Upscale a 128x72 list of (r,g,b) to 1280x720 truecolour rows (10x10)."""
    rows = []
    for out_y in range(OUT_HEIGHT):
        src_y = out_y // SCALE
        row = bytearray()
        for out_x in range(OUT_WIDTH):
            r, g, b = color[src_y * WIDTH + out_x // SCALE]
            row += bytes((r, g, b))
        rows.append(bytes(row))
    return rows


def render_expected_hdmi(framebuffer, threshold: int = EDGE_THRESHOLD,
                         color: tuple[int, int, int] = EDGE_COLOR):
    """framebuffer: list of 0x00RRGGBB ints -> expected 1280x720 colored-edge rows.

    Reproduces the whole PL chain: gray -> Sobel -> threshold colour -> 10x upscale.
    """
    rgb = [((p >> 16) & 0xFF, (p >> 8) & 0xFF, p & 0xFF) for p in framebuffer]
    edge = sobel(rgb_to_gray(rgb))
    return render_colored_rows(colored_edge(edge, threshold, color))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--hex-output", type=Path, required=True)
    args = parser.parse_args()

    image = make_test_image()

    # 1. Round-trip lossless check (real host format -> golden receive_frame).
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

    # 3. Software golden gray + Sobel (matches rgb_to_gray.v / sobel_core.v).
    gray = rgb_to_gray(image)
    edge = sobel(gray)

    # 4. Framebuffer hex for the RTL testbench (32-bit 0x00RRGGBB words, original RGB;
    #    the PL itself recomputes gray + Sobel).
    args.hex_output.parent.mkdir(parents=True, exist_ok=True)
    args.hex_output.write_text(
        "".join(f"{word:08x}\n" for word in expected_fb), encoding="ascii"
    )

    # 5. Expected HDMI image (colored edges, default threshold 80) + raw edge strength.
    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    write_rgb_png(
        args.evidence_dir / "exp04_expected_image.png",
        OUT_WIDTH, OUT_HEIGHT,
        render_colored_rows(colored_edge(edge)),
    )
    write_gray_png(
        args.evidence_dir / "exp04_edge_strength.png",
        OUT_WIDTH, OUT_HEIGHT,
        scale_gray_10x(edge),
    )

    # 6. 40/80/120 edge-pixel-count comparison + colored threshold images.
    counts: list[tuple[int, int]] = []
    for threshold in THRESHOLDS:
        count = sum(value >= threshold for value in edge)
        counts.append((threshold, count))
        write_rgb_png(
            args.evidence_dir / f"exp04_edge_threshold_{threshold}.png",
            OUT_WIDTH, OUT_HEIGHT,
            render_colored_rows(colored_edge(edge, threshold)),
        )
    if not all(counts[i][1] >= counts[i + 1][1] for i in range(len(counts) - 1)):
        raise SystemExit(f"edge-pixel counts are not monotonic: {counts}")

    stats = [
        "实验 4 PL Sobel 彩色边缘标记阈值统计",
        f"图像尺寸：{WIDTH} x {HEIGHT}（{PIXELS} 个源像素）",
        f"边缘颜色：EDGE_COLOR=#{EDGE_COLOR[0]:02x}{EDGE_COLOR[1]:02x}{EDGE_COLOR[2]:02x}",
        "比较规则：edge_pixel >= threshold 标记为彩色，否则黑色",
        "",
        *[f"threshold={t:3d} edge_pixels={c:4d}" for t, c in counts],
        "",
        "边缘像素数随阈值升高单调不增加检查：通过",
        "",
    ]
    (args.evidence_dir / "exp04_threshold_stats.txt").write_text(
        "\n".join(stats), encoding="utf-8"
    )

    report = [
        "实验 4 UART -> PS -> BRAM -> PL Sobel 协议与算法离线自检",
        f"图像尺寸：{WIDTH} x {HEIGHT}（{PIXELS} 像素，RGB888，format=0x{RGB888_FORMAT:02x}）",
        f"帧头 0x{FRAME_SYNC[0]:02x}{FRAME_SYNC[1]:02x}，行头 0x{LINE_SYNC[0]:02x}{LINE_SYNC[1]:02x}",
        "",
        "往返无损检查：通过（解析重建的 framebuffer 与源图逐像素一致）",
        "",
        "错误注入检查（错误码须与 main.c 一致）：",
        *[f"  {name:20s} expected={exp:3d} got={got:3d}" for name, exp, got in results],
        "",
        f"灰度公式：gray = (77*R + 150*G + 29*B) >> 8（与 rgb_to_gray.v 一致）",
        f"Sobel：mag = |gx| + |gy| 饱和到 255，四周 1 像素边界置 0（与 sobel_core.v 一致）",
        f"HDMI 输出：{OUT_WIDTH} x {OUT_HEIGHT}，每源像素放大 {SCALE} x {SCALE}",
        f"默认显示阈值：EDGE_THRESHOLD={EDGE_THRESHOLD}",
        "",
    ]
    (args.evidence_dir / "exp04_protocol_selfcheck.txt").write_text(
        "\n".join(report), encoding="utf-8"
    )

    print(f"EXP04_PIXELS={PIXELS}")
    print("EXP04_ROUNDTRIP=passed")
    for name, exp, got in results:
        print(f"EXP04_ERR_{name}={got}")
    for t, c in counts:
        print(f"EXP04_EDGE_PIXELS_{t}={c}")
    print("EXP04_THRESHOLD_MONOTONIC=passed")
    print("EXP04_SELFCHECK=passed")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate Experiment 5 (sobel_05_pc_control_display) golden data and expected images.

Experiment 5 builds on experiment 4: the PC host sends, over the SAME UART, both
image frames (``55 AA`` + size + ``18`` + per-line ``33 CC`` + RGB888) and binary
control frames (``A5 5A cmd value``).  The PS receiver
(``ps_uart_control_bram_app/src/main.c``) dispatches by 2-byte sync via
``wait_for_packet_start`` -> ``receive_frame_body`` (writes ``0x00RRGGBB`` words to
the BRAM image area ``0x0000..0x8FFC``) or ``handle_control_packet`` (writes three
control words ``0x9000`` mode / ``0x9004`` threshold / ``0x9008`` overlay).  The PL
(``hdmi_bram_sobel_display.v``) reads the three control words at every frame start,
then scans the image, computes ``gray=(77R+150G+29B)>>8`` and a 3x3 Sobel
(``mag=|gx|+|gy|`` saturated to 255, 1-pixel border = 0), and selects the HDMI
output per ``display_mode``: original / gray / Sobel-binary / original+colored-edge,
with ``edge_on = edge_pixel >= threshold`` and a fixed red overlay ``0xff2020``.

This module is BOTH the importable golden library (used by ``tools/cosim/exp05_cosim.py``)
and a standalone evidence generator.  Pure standard library only (no numpy / cv2 / PIL);
the PNG writer is the hand-rolled ``struct`` + ``zlib`` approach reused from
``generate_exp04_expected.py``.  It does not open a real UART / camera / board.
"""

from __future__ import annotations

import argparse
import struct
import zlib
from pathlib import Path

# ---- image / protocol constants (must match main.c and hdmi_bram_sobel_display.v) ----
WIDTH = 128
HEIGHT = 72
PIXELS = WIDTH * HEIGHT          # 9216
RGB888_FORMAT = 0x18

FRAME_SYNC = (0x55, 0xAA)
LINE_SYNC = (0x33, 0xCC)
CONTROL_SYNC = (0xA5, 0x5A)

CTRL_CMD_MODE = 0x01
CTRL_CMD_THRESHOLD = 0x02
CTRL_CMD_OVERLAY = 0x03

SCALE = 10
OUT_WIDTH = WIDTH * SCALE        # 1280
OUT_HEIGHT = HEIGHT * SCALE      # 720

# Display modes (display_mode field, 2 bit).
MODE_ORIGINAL = 0
MODE_GRAY = 1
MODE_EDGE = 2
MODE_OVERLAY = 3

# Reset / power-on defaults (PL reset block and PS control_write_defaults()).
DEFAULT_MODE = 2
DEFAULT_THRESHOLD = 80
DEFAULT_OVERLAY = 0

OVERLAY_COLOR = (0xFF, 0x20, 0x20)   # fixed red edge overlay, matches RTL 24'hff2020
THRESHOLDS = (40, 80, 120)

# Control-word byte addresses and 32-bit word indices in the framebuffer dump.
CTRL_MODE_ADDR = 0x9000
CTRL_THRESHOLD_ADDR = 0x9004
CTRL_OVERLAY_ADDR = 0x9008
CTRL_MODE_WORD = CTRL_MODE_ADDR >> 2          # 9216
CTRL_THRESHOLD_WORD = CTRL_THRESHOLD_ADDR >> 2  # 9217
CTRL_OVERLAY_WORD = CTRL_OVERLAY_ADDR >> 2      # 9218
FB_WORDS = CTRL_OVERLAY_WORD + 1                # 9219 (covers image area + 3 control words)

MODE_NAMES = {MODE_ORIGINAL: "original", MODE_GRAY: "gray",
              MODE_EDGE: "edge", MODE_OVERLAY: "overlay"}
MODE_FROM_NAME = {v: k for k, v in MODE_NAMES.items()}


# --------------------------- test image ---------------------------
def make_test_image() -> list[tuple[int, int, int]]:
    """Deterministic 128x72 pattern with both weak (gradient) and strong edges.

    Identical construction to experiment 4 so the gray + Sobel golden is directly
    comparable: a smooth RGB gradient (weak edges across all channels) plus solid
    blocks, a hollow frame and a diagonal line (strong edges), giving a meaningful
    40/80/120 threshold spread.
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


# --------------------------- host frame / control encoders ---------------------------
def encode_frame(image, width=WIDTH, height=HEIGHT, fmt=RGB888_FORMAT,
                 bad_row=None, truncate=None) -> bytes:
    """Encode an image frame using the exact host_camera_uart format.

    bad_row=(index, value) forces one line header to carry a wrong row number.
    truncate=N cuts the stream to N bytes to model a UART timeout mid-frame.
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


def encode_control_frame(cmd: int, value: int) -> bytes:
    """Encode one control frame: A5 5A cmd value (matches send_control_command)."""
    return bytes((CONTROL_SYNC[0], CONTROL_SYNC[1], cmd & 0xFF, value & 0xFF))


def encode_controls(mode=None, threshold=None, overlay=None) -> bytes:
    """Mirror camera_uart_sender.send_requested_controls ordering: mode, threshold, overlay."""
    out = bytearray()
    if mode is not None:
        out += encode_control_frame(CTRL_CMD_MODE, mode)
    if threshold is not None:
        out += encode_control_frame(CTRL_CMD_THRESHOLD, threshold)
    if overlay is not None:
        out += encode_control_frame(CTRL_CMD_OVERLAY, 1 if overlay else 0)
    return bytes(out)


# --------------------------- PS dispatch golden (mirrors main.c) ---------------------------
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


def _wait_for_packet_start(stream):
    """Mirror wait_for_packet_start: 1 on 55 AA, 2 on A5 5A, 0 on stream end."""
    prev = 0
    while True:
        cur = stream.recv()
        if cur is None:
            return 0
        if prev == FRAME_SYNC[0] and cur == FRAME_SYNC[1]:
            return 1
        if prev == CONTROL_SYNC[0] and cur == CONTROL_SYNC[1]:
            return 2
        prev = cur


def _recv_u16_le(stream):
    low = stream.recv()
    if low is None:
        return None
    high = stream.recv()
    if high is None:
        return None
    return low | (high << 8)


def _wait_for_line_sync(stream):
    prev = None
    while True:
        cur = stream.recv()
        if cur is None:
            return False
        if prev == LINE_SYNC[0] and cur == LINE_SYNC[1]:
            return True
        prev = cur


def _receive_frame_body(stream, fb):
    """Mirror receive_frame_body(): codes 0 / -1 / -2 / -4 / -5 / -6 / -7."""
    width = _recv_u16_le(stream)
    if width is None:
        return -4
    height = _recv_u16_le(stream)
    if height is None:
        return -4
    fmt = stream.recv()
    if fmt is None:
        return -4
    if width != WIDTH or height != HEIGHT or fmt != RGB888_FORMAT:
        return -1
    for row_expected in range(HEIGHT):
        if not _wait_for_line_sync(stream):
            return -5
        row = _recv_u16_le(stream)
        if row is None:
            return -6
        if row != row_expected:
            return -2
        for x in range(WIDTH):
            r = stream.recv()
            g = stream.recv()
            b = stream.recv()
            if r is None or g is None or b is None:
                return -7
            fb[row_expected * WIDTH + x] = (r << 16) | (g << 8) | b
    return 0


def _handle_control_packet(stream, fb):
    """Mirror handle_control_packet(): cmd 1/2/3 -> write control word, ret 1; else -12.

    Header/value timeout returns -10 / -11 (matches main.c)."""
    cmd = stream.recv()
    if cmd is None:
        return -10
    value = stream.recv()
    if value is None:
        return -11
    if cmd == CTRL_CMD_MODE:
        fb[CTRL_MODE_WORD] = value & 0x03
    elif cmd == CTRL_CMD_THRESHOLD:
        fb[CTRL_THRESHOLD_WORD] = value & 0xFF
    elif cmd == CTRL_CMD_OVERLAY:
        fb[CTRL_OVERLAY_WORD] = 1 if value else 0
    else:
        return -12
    return 1


def dispatch_stream(data: bytes):
    """Golden model of main.c's dispatch loop. Returns (fb_words, events).

    fb_words has FB_WORDS entries (image area 0..9215 + control words 9216/17/18),
    pre-loaded with the power-on defaults (control_write_defaults).  events is a list
    of ("frame"|"ctrl", code) in processing order, until the stream is exhausted.
    """
    fb = [0] * FB_WORDS
    fb[CTRL_MODE_WORD] = DEFAULT_MODE
    fb[CTRL_THRESHOLD_WORD] = DEFAULT_THRESHOLD
    fb[CTRL_OVERLAY_WORD] = DEFAULT_OVERLAY
    stream = ByteStream(data)
    events = []
    while True:
        kind = _wait_for_packet_start(stream)
        if kind == 0:
            break
        if kind == 1:
            events.append(("frame", _receive_frame_body(stream, fb)))
        else:
            events.append(("ctrl", _handle_control_packet(stream, fb)))
    return fb, events


# --------------------------- gray + Sobel + display mux ---------------------------
def rgb_to_gray(rgb: list[tuple[int, int, int]]) -> list[int]:
    """8-bit luma matching rgb_to_gray.v: (77*R + 150*G + 29*B) >> 8."""
    return [((r * 77) + (g * 150) + (b * 29)) >> 8 for r, g, b in rgb]


def sobel(gray: list[int]) -> list[int]:
    """3x3 Sobel matching sobel_core.v: mag = |gx| + |gy| (sat 255), 1px border = 0."""
    edge = [0] * PIXELS
    for y in range(1, HEIGHT - 1):
        for x in range(1, WIDTH - 1):
            top = (y - 1) * WIDTH
            middle = y * WIDTH
            bottom = (y + 1) * WIDTH
            gx = (
                -gray[top + x - 1] + gray[top + x + 1]
                - 2 * gray[middle + x - 1] + 2 * gray[middle + x + 1]
                - gray[bottom + x - 1] + gray[bottom + x + 1]
            )
            gy = (
                -gray[top + x - 1] - 2 * gray[top + x] - gray[top + x + 1]
                + gray[bottom + x - 1] + 2 * gray[bottom + x] + gray[bottom + x + 1]
            )
            edge[middle + x] = min(abs(gx) + abs(gy), 255)
    return edge


def display_mux(rgb, edge, mode, threshold, overlay):
    """Per-source-pixel HDMI colour, matching the hdmi_bram_sobel_display.v display mux.

    rgb: list[(r,g,b)]; edge: list[int] (Sobel magnitude); returns list[(r,g,b)].
    """
    out = []
    overlay_active = bool(overlay) or (mode == MODE_OVERLAY)
    for i, (r, g, b) in enumerate(rgb):
        gray = ((r * 77) + (g * 150) + (b * 29)) >> 8
        edge_on = edge[i] >= threshold
        if mode == MODE_GRAY:
            base = (gray, gray, gray)
        elif mode == MODE_EDGE:
            base = (255, 255, 255) if edge_on else (0, 0, 0)
        else:                       # MODE_ORIGINAL or MODE_OVERLAY -> original
            base = (r, g, b)
        if mode != MODE_EDGE and overlay_active and edge_on:
            out.append(OVERLAY_COLOR)
        else:
            out.append(base)
    return out


def words_to_rgb(framebuffer_words) -> list[tuple[int, int, int]]:
    return [((p >> 16) & 0xFF, (p >> 8) & 0xFF, p & 0xFF) for p in framebuffer_words[:PIXELS]]


def render_rows(color_pixels):
    """Upscale a 128x72 list of (r,g,b) to 1280x720 truecolour rows (10x10 nearest)."""
    rows = []
    for out_y in range(OUT_HEIGHT):
        src_y = out_y // SCALE
        row = bytearray()
        base = src_y * WIDTH
        for out_x in range(OUT_WIDTH):
            r, g, b = color_pixels[base + out_x // SCALE]
            row += bytes((r, g, b))
        rows.append(bytes(row))
    return rows


def render_expected_display(framebuffer_words, mode, threshold, overlay):
    """Full PL chain for one control config -> expected 1280x720 rows."""
    rgb = words_to_rgb(framebuffer_words)
    edge = sobel(rgb_to_gray(rgb))
    return render_rows(display_mux(rgb, edge, mode, threshold, overlay))


# --------------------------- PNG writers (struct + zlib, std lib only) ---------------------------
def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(chunk_type)
    crc = zlib.crc32(data, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def write_rgb_png(path: Path, width: int, height: int, rgb_rows) -> None:
    raw = bytearray()
    for row in rgb_rows:
        raw.append(0)             # filter type 0 (none)
        raw += row
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)  # colour type 2
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(bytes(raw), level=9))
        + _png_chunk(b"IEND", b"")
    )


def write_gray_png(path: Path, width: int, height: int, pixels: bytes) -> None:
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        rows += pixels[y * width:(y + 1) * width]
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)  # colour type 0
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(bytes(rows), level=9))
        + _png_chunk(b"IEND", b"")
    )


def scale_gray_10x(pixels: list[int]) -> bytes:
    output = bytearray()
    for y in range(HEIGHT):
        row = bytes(pixels[y * WIDTH:(y + 1) * WIDTH])
        expanded = b"".join(bytes([value]) * SCALE for value in row)
        for _ in range(SCALE):
            output.extend(expanded)
    return bytes(output)


# --------------------------- framebuffer hex helpers ---------------------------
def image_to_words(image) -> list[int]:
    return [(r << 16) | (g << 8) | b for (r, g, b) in image]


def build_fb_words(image, mode, threshold, overlay) -> list[int]:
    """Image area words + the three control words at 9216/9217/9218 -> FB_WORDS list."""
    words = image_to_words(image) + [0] * (FB_WORDS - PIXELS)
    words[CTRL_MODE_WORD] = mode & 0x03
    words[CTRL_THRESHOLD_WORD] = threshold & 0xFF
    words[CTRL_OVERLAY_WORD] = 1 if overlay else 0
    return words


def write_fb_hex(path: Path, words) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{w:08x}\n" for w in words), encoding="ascii")


# --------------------------- standalone evidence generator ---------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="exp5 golden + expected-image generator")
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--hex-output", type=Path, required=True,
                        help="framebuffer hex (image + default control words) for the RTL tb")
    args = parser.parse_args()

    image = make_test_image()

    # 1. Round-trip: real host frame + all three control frames -> golden dispatch.
    stream = encode_frame(image) + encode_controls(mode=MODE_OVERLAY, threshold=40, overlay=True)
    fb, events = dispatch_stream(stream)
    if events != [("frame", 0), ("ctrl", 1), ("ctrl", 1), ("ctrl", 1)]:
        raise SystemExit(f"round-trip dispatch events unexpected: {events}")
    if fb[:PIXELS] != image_to_words(image):
        raise SystemExit("round-trip image-area mismatch")
    if (fb[CTRL_MODE_WORD], fb[CTRL_THRESHOLD_WORD], fb[CTRL_OVERLAY_WORD]) != (MODE_OVERLAY, 40, 1):
        raise SystemExit("round-trip control words mismatch")

    # 2. Control-byte encoding matches the documented A5 5A cmd value frames.
    assert encode_control_frame(CTRL_CMD_MODE, MODE_EDGE) == bytes((0xA5, 0x5A, 0x01, 0x02))
    assert encode_control_frame(CTRL_CMD_THRESHOLD, 120) == bytes((0xA5, 0x5A, 0x02, 0x78))
    assert encode_control_frame(CTRL_CMD_OVERLAY, 1) == bytes((0xA5, 0x5A, 0x03, 0x01))

    # 3. Error injection: codes must match receive_frame_body / handle_control_packet.
    cases = [
        ("wrong_width", encode_frame(image, width=64), ("frame", -1)),
        ("wrong_format", encode_frame(image, fmt=0x10), ("frame", -1)),
        ("wrong_row", encode_frame(image, bad_row=(10, 99)), ("frame", -2)),
        ("trunc_after_header", encode_frame(image, truncate=7), ("frame", -5)),
        ("trunc_mid_pixels", encode_frame(image, truncate=7 + 4 + 100), ("frame", -7)),
        ("unknown_cmd", encode_control_frame(0x09, 0x00), ("ctrl", -12)),
    ]
    err_results = []
    for name, bad_stream, expected_first in cases:
        _, ev = dispatch_stream(bad_stream)
        # 只校验首个被分发的数据包返回码；畸形图像帧的尾部字节会被分发循环继续扫描出零散
        # 伪包（与真实 PS 行为一致），不影响首包判定（与 cosim run 脚本的“首个 PKT”一致）。
        got = ev[0] if ev else ("none", 0)
        err_results.append((name, expected_first, got))
        if got != expected_first:
            raise SystemExit(f"error case {name}: expected {expected_first}, got {got}")

    # 4. Software golden gray + Sobel (matches rgb_to_gray.v / sobel_core.v).
    gray = rgb_to_gray(image)
    edge = sobel(gray)

    # 5. Framebuffer hex (image area + default control words mode=2/thr=80/overlay=0).
    write_fb_hex(args.hex_output, build_fb_words(image, DEFAULT_MODE, DEFAULT_THRESHOLD, DEFAULT_OVERLAY))

    # 6. Expected display images for each mode / threshold / overlay (1280x720).
    fb_words = image_to_words(image)
    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    write_rgb_png(args.evidence_dir / "exp05_mode_original.png", OUT_WIDTH, OUT_HEIGHT,
                  render_expected_display(fb_words, MODE_ORIGINAL, DEFAULT_THRESHOLD, 0))
    write_rgb_png(args.evidence_dir / "exp05_mode_gray.png", OUT_WIDTH, OUT_HEIGHT,
                  render_expected_display(fb_words, MODE_GRAY, DEFAULT_THRESHOLD, 0))
    write_rgb_png(args.evidence_dir / "exp05_mode_edge.png", OUT_WIDTH, OUT_HEIGHT,
                  render_expected_display(fb_words, MODE_EDGE, DEFAULT_THRESHOLD, 0))
    write_rgb_png(args.evidence_dir / "exp05_mode_overlay.png", OUT_WIDTH, OUT_HEIGHT,
                  render_expected_display(fb_words, MODE_OVERLAY, DEFAULT_THRESHOLD, 0))
    write_gray_png(args.evidence_dir / "exp05_edge_strength.png", OUT_WIDTH, OUT_HEIGHT,
                   scale_gray_10x(edge))

    # 7. 40/80/120 edge threshold images (edge mode) + monotonic edge-pixel-count stats.
    counts = []
    for threshold in THRESHOLDS:
        count = sum(value >= threshold for value in edge)
        counts.append((threshold, count))
        write_rgb_png(args.evidence_dir / f"exp05_edge_threshold_{threshold}.png",
                      OUT_WIDTH, OUT_HEIGHT,
                      render_expected_display(fb_words, MODE_EDGE, threshold, 0))
    if not all(counts[i][1] >= counts[i + 1][1] for i in range(len(counts) - 1)):
        raise SystemExit(f"edge-pixel counts are not monotonic: {counts}")

    # 8. Overlay-on vs overlay-off pixel deltas (overlay paints red over non-edge modes).
    overlay_red = sum(1 for px in display_mux(words_to_rgb(fb_words), edge, MODE_ORIGINAL, DEFAULT_THRESHOLD, 1)
                      if px == OVERLAY_COLOR)

    stats = [
        "实验 5 显示控制阈值与边缘像素统计",
        f"图像尺寸：{WIDTH} x {HEIGHT}（{PIXELS} 源像素）",
        f"灰度：gray = (77*R + 150*G + 29*B) >> 8",
        f"Sobel：mag = |gx| + |gy| 饱和 255，1 像素边界置 0",
        f"边缘叠加颜色：OVERLAY_COLOR = #{OVERLAY_COLOR[0]:02x}{OVERLAY_COLOR[1]:02x}{OVERLAY_COLOR[2]:02x}",
        "比较规则：edge_pixel >= threshold 视为边缘",
        "",
        *[f"threshold={t:3d} edge_pixels={c:4d}" for t, c in counts],
        "",
        f"overlay=on(原图模式)红色叠加像素数 (threshold={DEFAULT_THRESHOLD})：{overlay_red}",
        "边缘像素数随阈值升高单调不增加检查：通过",
        "",
    ]
    (args.evidence_dir / "exp05_threshold_stats.txt").write_text("\n".join(stats), encoding="utf-8")

    report = [
        "实验 5 上位机控制显示 协议与算法离线自检",
        f"图像：{WIDTH} x {HEIGHT}（RGB888, format=0x{RGB888_FORMAT:02x}）",
        f"图像帧头 0x{FRAME_SYNC[0]:02x}{FRAME_SYNC[1]:02x}，行头 0x{LINE_SYNC[0]:02x}{LINE_SYNC[1]:02x}，"
        f"控制帧头 0x{CONTROL_SYNC[0]:02x}{CONTROL_SYNC[1]:02x}",
        f"控制字地址：mode=0x{CTRL_MODE_ADDR:04x} threshold=0x{CTRL_THRESHOLD_ADDR:04x} "
        f"overlay=0x{CTRL_OVERLAY_ADDR:04x}（字索引 {CTRL_MODE_WORD}/{CTRL_THRESHOLD_WORD}/{CTRL_OVERLAY_WORD}）",
        f"图像区最后一像素字节地址 0x{(PIXELS - 1) * 4:04x}，与控制区不重叠",
        "",
        "往返无损：真实图像帧 + 三个控制帧 -> dispatch -> 图像区与控制字逐项一致：通过",
        f"控制帧字节：a5 5a 01 mode / a5 5a 02 threshold / a5 5a 03 overlay：通过",
        "",
        "错误注入（返回码须与 main.c 一致）：",
        *[f"  {name:20s} expected={exp} got={got}" for name, exp, got in err_results],
        "",
        "显示模式映射（display_mux 与 hdmi_bram_sobel_display.v 一致）：",
        "  mode=0 原图 / mode=1 灰度 / mode=2 Sobel 二值 / mode=3 原图+红色边缘",
        "  非边缘模式下 overlay_enable=1 或 mode=3 时，edge_pixel>=threshold 处叠加 0xff2020",
        "",
    ]
    (args.evidence_dir / "exp05_protocol_selfcheck.txt").write_text("\n".join(report), encoding="utf-8")

    print(f"EXP05_PIXELS={PIXELS}")
    print("EXP05_ROUNDTRIP=passed")
    print("EXP05_CONTROL_BYTES=passed")
    for name, exp, got in err_results:
        print(f"EXP05_ERR_{name}={got[1]}")
    for t, c in counts:
        print(f"EXP05_EDGE_PIXELS_{t}={c}")
    print(f"EXP05_OVERLAY_RED_PIXELS={overlay_red}")
    print("EXP05_THRESHOLD_MONOTONIC=passed")
    print("EXP05_SELFCHECK=passed")


if __name__ == "__main__":
    main()

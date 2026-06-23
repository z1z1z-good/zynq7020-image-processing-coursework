#!/usr/bin/env python3
"""Offline tests for prepare_frame and the fixed-frame protocol invariants.

These run the real numpy + OpenCV (Plan A scaling has to execute for real), so
use the interpreter that has them, for example:

    set PYTHONUTF8=1
    python tests/test_prepare_frame.py        # standalone, prints PASS/FAIL
    pytest tests/test_prepare_frame.py         # or via pytest

No serial port, camera or board is touched.
"""
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import camera_uart_sender as host

WIDTH, HEIGHT = 128, 72
# Required original sizes: 4:3, 16:9 and a 9:16 portrait.
SIZES = ((640, 480), (1920, 1080), (1080, 1920))
CONTENT_SIZES = tuple(
    host.parse_proc_size(proc_size, WIDTH, HEIGHT) for proc_size in host.PROC_SIZES
)
FRAME_HEADER = bytes((0x55, 0xAA, 0x80, 0x00, 0x48, 0x00, 0x18))


def _gradient_bgr(width: int, height: int) -> np.ndarray:
    """Deterministic non-uniform BGR image (no pure-black pixels) so cropping
    and coarsening effects are detectable."""
    xs = np.linspace(10, 250, width, dtype=np.uint8)
    ys = np.linspace(10, 250, height, dtype=np.uint8)
    blue = np.tile(xs, (height, 1))
    green = np.tile(ys.reshape(-1, 1), (1, width))
    red = np.full((height, width), 128, dtype=np.uint8)
    return np.dstack([blue, green, red]).astype(np.uint8)


def test_shapes_all_modes_all_sizes():
    for w, h in SIZES:
        src = _gradient_bgr(w, h)
        for mode in host.FIT_MODES:
            for content in CONTENT_SIZES:
                out = host.prepare_frame(src, WIDTH, HEIGHT, mode, content)
                assert out.shape == (HEIGHT, WIDTH, 3), (w, h, mode, content, out.shape)
                assert out.dtype == np.uint8, (w, h, mode, content, out.dtype)


def test_stretch_matches_legacy_resize():
    """stretch stays byte-identical to the previous inline downscale path."""
    for w, h in SIZES:
        src = _gradient_bgr(w, h)
        legacy = cv2.cvtColor(
            cv2.resize(src, (WIDTH, HEIGHT), interpolation=cv2.INTER_AREA),
            cv2.COLOR_BGR2RGB,
        )
        out = host.prepare_frame(src, WIDTH, HEIGHT, "stretch")
        assert np.array_equal(out, legacy), (w, h)


def test_letterbox_aspect_and_fill():
    fill_bgr = (0, 0, 255)            # red, in BGR order
    fill_rgb = fill_bgr[::-1]         # reads back as (255, 0, 0) after BGR->RGB
    white = (255, 255, 255)
    for w, h in SIZES:
        src = np.full((h, w, 3), 255, dtype=np.uint8)  # solid white subject
        out = host.prepare_frame(src, WIDTH, HEIGHT, "letterbox", None, fill_bgr)

        white_mask = np.all(out == white, axis=2)
        assert white_mask.any(), (w, h)
        rows = np.where(white_mask.any(axis=1))[0]
        cols = np.where(white_mask.any(axis=0))[0]
        box_h = int(rows[-1] - rows[0] + 1)
        box_w = int(cols[-1] - cols[0] + 1)

        scale = min(WIDTH / w, HEIGHT / h)
        exp_w = max(1, min(WIDTH, round(w * scale)))
        exp_h = max(1, min(HEIGHT, round(h * scale)))
        assert (box_w, box_h) == (exp_w, exp_h), (w, h, box_w, box_h, exp_w, exp_h)

        # subject aspect ratio preserved (within rounding tolerance)
        rel_err = abs((box_w / box_h) - (w / h)) / (w / h)
        assert rel_err < 0.05, (w, h, box_w, box_h, rel_err)

        # padding equals the requested fill colour, and every pixel is either
        # subject or fill (placement is a hard copy, so no blended edge colour)
        fill_mask = np.all(out == fill_rgb, axis=2)
        if box_w < WIDTH or box_h < HEIGHT:
            assert fill_mask.any(), (w, h)
        assert np.all(white_mask | fill_mask), (w, h)


def test_center_crop_no_black_border():
    for w, h in SIZES:
        src = np.full((h, w, 3), 200, dtype=np.uint8)  # solid grey, no black
        out = host.prepare_frame(src, WIDTH, HEIGHT, "center-crop")
        assert out.min() == 200 and out.max() == 200, (w, h, out.min(), out.max())


def test_center_crop_is_centered():
    """A top/bottom split keeps its boundary near the output centre row."""
    w, h = 640, 480  # 4:3 -> scaled by width, cropped vertically
    src = np.zeros((h, w, 3), dtype=np.uint8)
    src[: h // 2] = 60
    src[h // 2:] = 220
    out = host.prepare_frame(src, WIDTH, HEIGHT, "center-crop")
    column = out[:, WIDTH // 2, 0].astype(int)
    boundary = int(np.argmax(np.abs(np.diff(column))))
    assert abs(boundary - HEIGHT // 2) <= 3, (boundary, HEIGHT // 2)


def test_content_size_is_coarser_and_valid():
    src = _gradient_bgr(640, 480)
    out = host.prepare_frame(src, WIDTH, HEIGHT, "stretch", (64, 36))
    assert out.shape == (HEIGHT, WIDTH, 3) and out.dtype == np.uint8

    # 64x36 -> 128x72 is an exact 2x nearest upscale: every 2x2 block is uniform
    assert np.array_equal(out[0::2, 0::2], out[1::2, 0::2])
    assert np.array_equal(out[0::2, 0::2], out[0::2, 1::2])
    assert np.array_equal(out[0::2, 0::2], out[1::2, 1::2])

    # genuinely coarser than the full-resolution stretch
    full = host.prepare_frame(src, WIDTH, HEIGHT, "stretch", None)
    assert not np.array_equal(out, full)

    # the coarse frame is still a legal 128x72 packet
    pkt = host.build_frame_packet(out)
    assert len(pkt) == 27943, len(pkt)
    assert pkt[:7] == FRAME_HEADER, pkt[:7].hex(" ")


def test_proc_size_choices_cover_c_grade_reference_sizes():
    required = {"128x72", "160x90", "144x108"}
    assert required.issubset(set(host.PROC_SIZES))
    assert host.parse_proc_size("128x72", WIDTH, HEIGHT) is None
    assert host.parse_proc_size("160x90", WIDTH, HEIGHT) == (160, 90)
    assert host.parse_proc_size("144x108", WIDTH, HEIGHT) == (144, 108)


def test_packet_invariants_all_modes_sizes():
    for w, h in SIZES:
        src = _gradient_bgr(w, h)
        for mode in host.FIT_MODES:
            for content in CONTENT_SIZES:
                out = host.prepare_frame(src, WIDTH, HEIGHT, mode, content)
                pkt = host.build_frame_packet(out)
                assert len(pkt) == 27943, (w, h, mode, content, len(pkt))
                assert pkt[:7] == FRAME_HEADER, (w, h, mode, content, pkt[:7].hex(" "))


def _run_all() -> int:
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"FAIL {test.__name__}: {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())

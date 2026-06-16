#!/usr/bin/env python3
"""实验 4 无板卡软硬件协同仿真的 Python 环节。

子命令：
  gen            用真实 camera_uart_sender.build_frame_packet 生成 UART 字节流，
                 与本地编码器逐字节比对（证明上位机打包一致），写出 frame_stream.bin
                 和 golden_fb.hex（期望的原始 RGB framebuffer）。
  check-fb       比对 PS 主机模型产出的 framebuffer 与 golden（逐像素，原始 RGB）。
  render-compare 读 RTL 仿真捕获的 1280x720 HDMI 像素，重建 PNG，并与“由 golden
                 framebuffer 计算 gray+Sobel+彩色边缘映射”的期望画面逐像素比对。

PS 接收路径与实验 3 完全一致（receive_frame 把原始 RGB 写入 BRAM），新增的只是 PL 侧
gray + Sobel + 彩色边缘显示，因此期望画面在本脚本里用软件 golden 计算（与 sobel_core.v /
rgb_to_gray.v / hdmi_bram_sobel_display.v 的映射一致）。复用 ../generate_exp04_expected.py
的纯标准库实现；真实上位机脚本依赖 numpy，cv2/serial 在导入时用空桩绕过（本环节不打开
真实串口/摄像头）。
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import types
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TOOLS_DIR = SCRIPT_DIR.parent
SOBEL4_DIR = TOOLS_DIR.parent
ZYNQ_DIR = SOBEL4_DIR.parent
HOST_DIR = ZYNQ_DIR / "host_camera_uart"


def _load_generate():
    spec = importlib.util.spec_from_file_location(
        "generate_exp04_expected", TOOLS_DIR / "generate_exp04_expected.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_host_sender():
    # 本协同环节不打开真实串口/摄像头，用空桩满足模块级 import 与类型注解。
    cv2 = types.ModuleType("cv2")
    sys.modules["cv2"] = cv2
    serial = types.ModuleType("serial")
    serial.Serial = type("Serial", (), {})
    sys.modules["serial"] = serial
    if str(HOST_DIR) not in sys.path:
        sys.path.insert(0, str(HOST_DIR))
    import camera_uart_sender  # noqa: E402

    return camera_uart_sender


def cmd_gen(args: argparse.Namespace) -> None:
    import numpy as np

    g = _load_generate()
    host = _load_host_sender()

    image = g.make_test_image()  # list[(r,g,b)]，行主序
    my_stream = g.encode_frame(image)

    arr = np.array(image, dtype=np.uint8).reshape(g.HEIGHT, g.WIDTH, 3)
    real_stream = bytes(host.build_frame_packet(arr))

    if real_stream != bytes(my_stream):
        raise SystemExit("host packing mismatch: real camera_uart_sender != local encoder")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "frame_stream.bin").write_bytes(real_stream)

    golden_fb = [(r << 16) | (gg << 8) | b for (r, gg, b) in image]
    (out_dir / "golden_fb.hex").write_text(
        "".join(f"{w:08x}\n" for w in golden_fb), encoding="ascii"
    )

    # 错误注入字节流：交给真实 PS C 解析器验证返回码。
    error_cases = [
        ("wrong_width", g.encode_frame(image, width=64), -1),
        ("wrong_format", g.encode_frame(image, fmt=0x10), -1),
        ("wrong_row", g.encode_frame(image, bad_row=(10, 99)), -2),
        ("trunc_before_header", g.encode_frame(image, truncate=1), -3),
        ("trunc_after_header", g.encode_frame(image, truncate=7), -5),
        ("trunc_mid_pixels", g.encode_frame(image, truncate=7 + 4 + 100), -7),
    ]
    err_dir = out_dir / "errors"
    err_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name, stream, code in error_cases:
        (err_dir / f"{name}.bin").write_bytes(bytes(stream))
        manifest.append(f"{name} {code}")
    (out_dir / "error_cases.txt").write_text(
        "\n".join(manifest) + "\n", encoding="ascii", newline="\n"
    )

    print(f"EXP04_COSIM_HOST_PACK=match bytes={len(real_stream)}")
    print(f"EXP04_COSIM_GOLDEN_FB_WORDS={len(golden_fb)}")
    print(f"EXP04_COSIM_ERROR_CASES={len(error_cases)}")


def _read_hex_words(path: Path) -> list[int]:
    return [int(line, 16) for line in path.read_text(encoding="ascii").split() if line]


def cmd_check_fb(args: argparse.Namespace) -> None:
    golden = _read_hex_words(Path(args.golden))
    actual = _read_hex_words(Path(args.actual))
    if len(golden) != len(actual):
        raise SystemExit(f"length mismatch: golden {len(golden)} vs actual {len(actual)}")
    mismatches = [i for i, (a, b) in enumerate(zip(golden, actual)) if a != b]
    if mismatches:
        first = mismatches[0]
        raise SystemExit(
            f"framebuffer mismatch at {len(mismatches)} words; "
            f"first @ {first}: golden {golden[first]:06x} actual {actual[first] & 0xffffff:06x}"
        )
    print(f"EXP04_COSIM_FB=match words={len(golden)}")


def cmd_render_compare(args: argparse.Namespace) -> None:
    g = _load_generate()
    golden_fb = _read_hex_words(Path(args.golden_fb))

    out_w, out_h = g.OUT_WIDTH, g.OUT_HEIGHT
    golden_rows = g.render_expected_hdmi(golden_fb)  # list[bytes]，每行 out_w*3，gray+Sobel+彩色

    # RTL 捕获：每个有效像素一行 RRGGBB（6 个十六进制），光栅顺序。
    capture = [
        line.strip()
        for line in Path(args.capture).read_text(encoding="ascii").split()
        if line.strip()
    ]
    expected_px = out_w * out_h
    if len(capture) != expected_px:
        raise SystemExit(f"capture pixel count {len(capture)} != expected {expected_px}")

    cap_rows = []
    mismatches = 0
    first_bad = None
    for y in range(out_h):
        row = bytearray()
        base = y * out_w
        golden_row = golden_rows[y]
        for x in range(out_w):
            v = capture[base + x]
            r = int(v[0:2], 16)
            gg = int(v[2:4], 16)
            b = int(v[4:6], 16)
            row += bytes((r, gg, b))
            if (r != golden_row[x * 3] or gg != golden_row[x * 3 + 1]
                    or b != golden_row[x * 3 + 2]):
                mismatches += 1
                if first_bad is None:
                    first_bad = (x, y)
        cap_rows.append(bytes(row))

    g.write_rgb_png(Path(args.png_out), out_w, out_h, cap_rows)

    if mismatches:
        raise SystemExit(
            f"rendered HDMI mismatch: {mismatches} px differ, first @ {first_bad}"
        )
    print(f"EXP04_COSIM_PNG=match pixels={expected_px}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_gen = sub.add_parser("gen")
    p_gen.add_argument("--out-dir", required=True)
    p_gen.set_defaults(func=cmd_gen)

    p_fb = sub.add_parser("check-fb")
    p_fb.add_argument("--golden", required=True)
    p_fb.add_argument("--actual", required=True)
    p_fb.set_defaults(func=cmd_check_fb)

    p_rc = sub.add_parser("render-compare")
    p_rc.add_argument("--golden-fb", required=True)
    p_rc.add_argument("--capture", required=True)
    p_rc.add_argument("--png-out", required=True)
    p_rc.set_defaults(func=cmd_render_compare)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

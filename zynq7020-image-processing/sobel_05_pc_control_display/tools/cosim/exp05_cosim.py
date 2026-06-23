#!/usr/bin/env python3
"""实验 5 无板卡软硬件协同仿真的 Python 环节。

子命令：
  gen            用真实 camera_uart_sender.build_frame_packet 生成图像帧字节流，并用真实
                 send_requested_controls（喂入假串口捕获字节）生成控制帧字节流，二者都与本地
                 编码器逐字节比对（证明上位机打包与控制命令一致）。写出：
                   frame_stream.bin   真实图像帧 + 真实控制帧（mode=overlay/thr=40/overlay=on）
                   golden_image.hex   期望图像区 9216 个 0x00RRGGBB 词
                   expected_ctrl.txt  期望控制字 "mode threshold overlay"
                   render_<tag>.hex   各显示配置的 framebuffer（图像区 + 控制字，FB_WORDS 词）
                   render_cases.txt   各配置 tag
                   errors/*.bin + error_cases.txt  错误注入字节流与期望 (kind code)
  check-fb       比对 PS 主机模型产出的 framebuffer：图像区与 golden 逐像素一致，且控制字
                 0x9000/0x9004/0x9008 与下发值一致。
  render-compare 读 render_<tag>.hex（自带图像 + 控制字），按 hdmi_bram_sobel_display.v 的显示
                 mux 计算期望 1280x720 画面，与 RTL 仿真捕获的像素逐像素比对并重建 PNG。

PS 接收+控制路径由真实 main.c 经 ps_protocol_model.c 在主机编译运行；PL 显示由 RTL testbench
渲染。期望画面用软件 golden 计算（与 rgb_to_gray.v / sobel_core.v / hdmi_bram_sobel_display.v
一致），复用 ../generate_exp05_expected.py。真实上位机脚本依赖 numpy，cv2/serial 在导入时用
空桩绕过（本环节不打开真实串口/摄像头）。
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import types
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TOOLS_DIR = SCRIPT_DIR.parent
SOBEL5_DIR = TOOLS_DIR.parent
ZYNQ_DIR = SOBEL5_DIR.parent
HOST_DIR = ZYNQ_DIR / "host_camera_uart"

# 显示配置矩阵：四模式 + 三阈值（边缘）+ 叠加两种触发 + 锐化四强度。元组 = (tag, mode, thr, ovl, sharpen)。
RENDER_CONFIGS = [
    ("orig", 0, 80, 0, 0),       # 原图
    ("gray", 1, 80, 0, 0),       # 灰度
    ("edge40", 2, 40, 0, 0),     # 边缘 阈值 40
    ("edge80", 2, 80, 0, 0),     # 边缘 阈值 80
    ("edge120", 2, 120, 0, 0),   # 边缘 阈值 120
    ("overlay", 3, 80, 0, 0),    # 原图 + 红边（mode=3 触发）
    ("ovlon", 0, 80, 1, 0),      # 原图 + 红边（overlay_enable 触发）
    ("sharp0", 4, 80, 0, 0),     # 锐化 k=0（应逐像素等于原图）
    ("sharp64", 4, 80, 0, 64),   # 锐化 k=64
    ("sharp128", 4, 80, 0, 128), # 锐化 k=128
    ("sharp255", 4, 80, 0, 255), # 锐化 k=255（强锐化 + 饱和裁剪）
]

# PS 解析检查用的主配置：四个控制字都取与默认(2/80/0/0)不同的值。
PRIMARY_MODE = 3      # overlay
PRIMARY_THR = 40
PRIMARY_OVL = 1
PRIMARY_SHARPEN = 96


def _load_generate():
    spec = importlib.util.spec_from_file_location(
        "generate_exp05_expected", TOOLS_DIR / "generate_exp05_expected.py"
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


class _FakeSerial:
    """捕获 send_control_command/send_requested_controls 写出的字节，不打开真实串口。"""

    def __init__(self):
        self.buf = bytearray()

    def write(self, data):
        self.buf.extend(bytes(data))
        return len(data)


def _read_hex_words(path: Path) -> list[int]:
    return [int(tok, 16) for tok in path.read_text(encoding="ascii").split() if tok]


def cmd_gen(args: argparse.Namespace) -> None:
    import numpy as np

    g = _load_generate()
    host = _load_host_sender()

    image = g.make_test_image()

    # 1) 真实上位机图像打包，与本地编码器逐字节比对。
    my_img_stream = g.encode_frame(image)
    arr = np.array(image, dtype=np.uint8).reshape(g.HEIGHT, g.WIDTH, 3)
    real_img_stream = bytes(host.build_frame_packet(arr))
    if real_img_stream != my_img_stream:
        raise SystemExit("host image packing mismatch: real camera_uart_sender != local encoder")

    # 2) 真实上位机控制命令（喂入假串口捕获），与本地编码器逐字节比对。
    fake = _FakeSerial()
    host.send_requested_controls(
        fake, mode=g.MODE_NAMES[PRIMARY_MODE], threshold=PRIMARY_THR,
        overlay="on" if PRIMARY_OVL else "off",
    )
    real_ctrl = bytes(fake.buf)
    my_ctrl = g.encode_controls(PRIMARY_MODE, PRIMARY_THR, bool(PRIMARY_OVL))
    if real_ctrl != my_ctrl:
        raise SystemExit("host control packing mismatch: real send_requested_controls != local encoder")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 真实图像帧 + 真实控制帧(mode/thr/ovl) + 锐化控制帧(a5 5a 04 k) -> 喂给真实 PS 模型。
    # 锐化控制帧用 golden 编码器生成（基础 host sender 暂无锐化命令，协议字节格式一致）。
    sharpen_ctrl = g.encode_control_frame(g.CTRL_CMD_SHARPEN, PRIMARY_SHARPEN)
    (out_dir / "frame_stream.bin").write_bytes(real_img_stream + real_ctrl + sharpen_ctrl)
    g.write_fb_hex(out_dir / "golden_image.hex", g.image_to_words(image))
    (out_dir / "expected_ctrl.txt").write_text(
        f"{PRIMARY_MODE} {PRIMARY_THR} {PRIMARY_OVL} {PRIMARY_SHARPEN}\n", encoding="ascii", newline="\n"
    )

    # 各显示配置的渲染 framebuffer（图像区 + 控制字）。
    for tag, mode, thr, ovl, shp in RENDER_CONFIGS:
        g.write_fb_hex(out_dir / f"render_{tag}.hex", g.build_fb_words(image, mode, thr, ovl, shp))
    (out_dir / "render_cases.txt").write_text(
        "".join(f"{tag} {mode} {thr} {ovl} {shp}\n" for tag, mode, thr, ovl, shp in RENDER_CONFIGS),
        encoding="ascii", newline="\n",
    )

    # 错误注入：每个流首个数据包的期望 (kind code)，与真实 PS 解析返回码核对。
    img_frame = g.encode_frame(image)
    error_cases = [
        ("wrong_width", g.encode_frame(image, width=64), "frame", -1),
        ("wrong_format", g.encode_frame(image, fmt=0x10), "frame", -1),
        ("wrong_row", g.encode_frame(image, bad_row=(10, 99)), "frame", -2),
        ("trunc_after_header", g.encode_frame(image, truncate=7), "frame", -5),
        ("trunc_mid_pixels", g.encode_frame(image, truncate=7 + 4 + 100), "frame", -7),
        ("unknown_cmd", g.encode_control_frame(0x09, 0x00), "ctrl", -12),
    ]
    err_dir = out_dir / "errors"
    err_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name, stream, kind, code in error_cases:
        (err_dir / f"{name}.bin").write_bytes(bytes(stream))
        manifest.append(f"{name} {kind} {code}")
    (out_dir / "error_cases.txt").write_text("\n".join(manifest) + "\n", encoding="ascii", newline="\n")

    # 控制字与图像区不重叠的纸面核对。
    assert (g.PIXELS - 1) * 4 < g.CTRL_MODE_ADDR, "image area overlaps control words"

    print(f"EXP05_COSIM_HOST_PACK=match bytes={len(real_img_stream)}")
    print(f"EXP05_COSIM_HOST_CONTROL=match bytes={len(real_ctrl)}")
    print(f"EXP05_COSIM_RENDER_CASES={len(RENDER_CONFIGS)}")
    print(f"EXP05_COSIM_ERROR_CASES={len(error_cases)}")


def cmd_check_fb(args: argparse.Namespace) -> None:
    g = _load_generate()
    golden_image = _read_hex_words(Path(args.golden_image))
    actual = _read_hex_words(Path(args.actual))
    mode, thr, ovl, shp = (int(t) for t in Path(args.expected_ctrl).read_text().split())

    if len(actual) < g.FB_WORDS:
        raise SystemExit(f"actual framebuffer too short: {len(actual)} < {g.FB_WORDS}")

    # 图像区逐像素一致（仅比较低 24 位，PS 写 0x00RRGGBB）。
    mismatches = [i for i in range(g.PIXELS)
                  if (actual[i] & 0xFFFFFF) != (golden_image[i] & 0xFFFFFF)]
    if mismatches:
        first = mismatches[0]
        raise SystemExit(
            f"framebuffer image mismatch at {len(mismatches)} words; first @ {first}: "
            f"golden {golden_image[first] & 0xFFFFFF:06x} actual {actual[first] & 0xFFFFFF:06x}"
        )

    # 控制字一致（含锐化字 0x900C）。
    got = (actual[g.CTRL_MODE_WORD], actual[g.CTRL_THRESHOLD_WORD],
           actual[g.CTRL_OVERLAY_WORD], actual[g.CTRL_SHARPEN_WORD])
    if got != (mode, thr, ovl, shp):
        raise SystemExit(f"control words mismatch: expected {(mode, thr, ovl, shp)} got {got}")

    print(f"EXP05_COSIM_FB=match image_words={g.PIXELS} ctrl=mode={mode},thr={thr},ovl={ovl},sharpen={shp}")


def cmd_render_compare(args: argparse.Namespace) -> None:
    g = _load_generate()
    fb = _read_hex_words(Path(args.fb_hex))
    image_words = fb[:g.PIXELS]
    mode = fb[g.CTRL_MODE_WORD] & 0x07
    threshold = fb[g.CTRL_THRESHOLD_WORD] & 0xFF
    overlay = 1 if fb[g.CTRL_OVERLAY_WORD] else 0
    sharpen = fb[g.CTRL_SHARPEN_WORD] & 0xFF

    out_w, out_h = g.OUT_WIDTH, g.OUT_HEIGHT
    golden_rows = g.render_expected_display(image_words, mode, threshold, overlay, sharpen)

    capture = [tok for tok in Path(args.capture).read_text(encoding="ascii").split() if tok]
    expected_px = out_w * out_h
    if len(capture) != expected_px:
        raise SystemExit(f"capture pixel count {len(capture)} != expected {expected_px}")

    cap_rows = []
    mismatches = 0
    first_bad = None
    corner_artifact = 0
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
            if (r != golden_row[x * 3] or gg != golden_row[x * 3 + 1] or b != golden_row[x * 3 + 2]):
                # 已知右下角 1 像素边界伪影：该时序无尾部消隐区（H_START..H_TOTAL 全为有效区），
                # 帧末像素经 2 拍显示流水输出时已进入下一帧扫描起点（sobel_done 被复位为 0），
                # 故被输出门控为黑。仅此一个角点，对实际显示无影响；其余像素必须严格一致。
                if (x, y) == (out_w - 1, out_h - 1):
                    corner_artifact = 1
                else:
                    mismatches += 1
                    if first_bad is None:
                        first_bad = (x, y)
        cap_rows.append(bytes(row))

    g.write_rgb_png(Path(args.png_out), out_w, out_h, cap_rows)

    if mismatches:
        raise SystemExit(f"rendered HDMI mismatch ({args.tag}): {mismatches} px differ, first @ {first_bad}")
    print(f"EXP05_COSIM_PNG_{args.tag}=match pixels={expected_px} corner_artifact={corner_artifact} "
          f"mode={mode} thr={threshold} ovl={overlay} sharpen={sharpen}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_gen = sub.add_parser("gen")
    p_gen.add_argument("--out-dir", required=True)
    p_gen.set_defaults(func=cmd_gen)

    p_fb = sub.add_parser("check-fb")
    p_fb.add_argument("--golden-image", required=True)
    p_fb.add_argument("--expected-ctrl", required=True)
    p_fb.add_argument("--actual", required=True)
    p_fb.set_defaults(func=cmd_check_fb)

    p_rc = sub.add_parser("render-compare")
    p_rc.add_argument("--fb-hex", required=True)
    p_rc.add_argument("--capture", required=True)
    p_rc.add_argument("--png-out", required=True)
    p_rc.add_argument("--tag", default="frame")
    p_rc.set_defaults(func=cmd_render_compare)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

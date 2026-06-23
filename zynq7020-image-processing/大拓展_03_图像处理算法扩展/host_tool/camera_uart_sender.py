#!/usr/bin/env python3
"""大拓展 03（图像处理算法扩展，任务3 B档）上位机发送器。

在实验 5 既有 UART 协议（图像帧 `55 AA` + 行 `33 CC` + 控制帧 `A5 5A cmd value`）之上，
新增**锐化**算法的显示模式与控制命令，并**并入大拓展 01（输入规格扩展）的主机缩放能力**，
使两个扩展在同一工具里共存：

    显示模式 :  original / gray / edge / overlay / sharpen   (mode 控制命令 0x01, value=4 即锐化)
    锐化强度 :  控制命令 0x04 value=k(0..255) -> PL 控制字 0x900C，每帧实时生效
    输入缩放 :  --fit-mode stretch/letterbox/center-crop + --proc-size 128x72/160x90/144x108/64x36
                （大拓展 01：纯主机缩放，硬件始终收 128x72；与锐化正交，可叠加演示）

锐化与 PL/PS 完全一致；软件参考实现见 sharpen_algo.py。本脚本既是命令行工具，也被
camera_uart_gui.py 复用（打包、缩放、发送、控制命令）。

示例：
    # 发送一张图片并切到锐化模式、强度 64
    python camera_uart_sender.py --port COM7 --image pic.jpg --once --mode sharpen --sharpen 64
    # 大拓展01 缩放 + 大拓展03 锐化叠加：按 64x36 处理后送、并开锐化
    python camera_uart_sender.py --port COM7 --image pic.jpg --once --proc-size 64x36 --mode sharpen --sharpen 64
    # 仅实时调锐化强度（不发图）
    python camera_uart_sender.py --port COM7 --control-only --sharpen 200
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import cv2
import numpy as np
import serial

import sharpen_algo

FRAME_SYNC = bytes((0x55, 0xAA))
LINE_SYNC = bytes((0x33, 0xCC))
CONTROL_SYNC = bytes((0xA5, 0x5A))
RGB888_FORMAT = 0x18

CONTROL_MODE = 0x01
CONTROL_THRESHOLD = 0x02
CONTROL_OVERLAY = 0x03
CONTROL_SHARPEN = 0x04

# 显示模式名 -> 控制值（与 hdmi_bram_sobel_display.v 的 MODE_* 一致；sharpen=4）。
MODE_VALUES = {
    "original": 0,
    "gray": 1,
    "edge": 2,
    "overlay": 3,
    "sharpen": 4,
}
MODE_NAMES = tuple(MODE_VALUES.keys())

# 大拓展 01（输入规格扩展）的主机缩放选项，与锐化共存：fit 模式 + 处理分辨率。
FIT_MODES = ("stretch", "letterbox", "center-crop")
PROC_SIZES = ("128x72", "160x90", "144x108", "64x36")

DEFAULT_WIDTH = 128
DEFAULT_HEIGHT = 72


# --------------------------- 中文路径安全的图像读写 ---------------------------
def imread_unicode(path: str, flags: int = cv2.IMREAD_COLOR) -> "np.ndarray | None":
    """cv2.imread 在 Windows 上读不了非 ASCII（中文）路径，用 np.fromfile + imdecode 兜底。"""
    try:
        data = np.fromfile(path, dtype=np.uint8)
    except OSError:
        return None
    if data.size == 0:
        return None
    return cv2.imdecode(data, flags)


def imwrite_unicode(path: str, bgr: np.ndarray) -> bool:
    """cv2.imwrite 的非 ASCII 路径安全版（imencode + ndarray.tofile）。"""
    ext = Path(path).suffix or ".png"
    ok, buf = cv2.imencode(ext, bgr)
    if not ok:
        return False
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    buf.tofile(path)
    return True


def load_source_bgr(path: str, flip: bool = False) -> np.ndarray:
    """读入整幅原图 BGR（保留原始分辨率，交给 prepare_frame 缩放）。支持中文路径。"""
    bgr = imread_unicode(path, cv2.IMREAD_COLOR)
    if bgr is None:
        raise RuntimeError(f"failed to open image {path}")
    if flip:
        bgr = cv2.flip(bgr, 1)
    return bgr


# --------------------------- 大拓展 01 缩放（fit 模式 + 处理分辨率） ---------------------------
def _interpolation(dst_w: int, dst_h: int, src_w: int, src_h: int) -> int:
    return cv2.INTER_AREA if dst_w * dst_h <= src_w * src_h else cv2.INTER_LINEAR


def _fit_bgr(frame_bgr: np.ndarray, width: int, height: int, fit_mode: str,
             fill: tuple[int, int, int]) -> np.ndarray:
    src_h, src_w = frame_bgr.shape[:2]
    if fit_mode == "stretch":
        return cv2.resize(frame_bgr, (width, height), interpolation=_interpolation(width, height, src_w, src_h))
    if fit_mode == "letterbox":
        scale = min(width / src_w, height / src_h)
        new_w = max(1, min(width, round(src_w * scale)))
        new_h = max(1, min(height, round(src_h * scale)))
        resized = cv2.resize(frame_bgr, (new_w, new_h), interpolation=_interpolation(new_w, new_h, src_w, src_h))
        canvas = np.empty((height, width, 3), dtype=np.uint8)
        canvas[:, :] = fill
        x0, y0 = (width - new_w) // 2, (height - new_h) // 2
        canvas[y0:y0 + new_h, x0:x0 + new_w] = resized
        return canvas
    if fit_mode == "center-crop":
        scale = max(width / src_w, height / src_h)
        new_w, new_h = max(width, round(src_w * scale)), max(height, round(src_h * scale))
        resized = cv2.resize(frame_bgr, (new_w, new_h), interpolation=_interpolation(new_w, new_h, src_w, src_h))
        x0, y0 = (new_w - width) // 2, (new_h - height) // 2
        return resized[y0:y0 + height, x0:x0 + width]
    raise ValueError(f"unsupported fit_mode: {fit_mode!r}")


def prepare_frame(frame_bgr: np.ndarray, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT,
                  fit_mode: str = "stretch", content_size: "tuple[int, int] | None" = None,
                  fill: tuple[int, int, int] = (0, 0, 0)) -> np.ndarray:
    """任意尺寸 BGR -> 固定 width x height 的 RGB888（大拓展 01 方案 A：缩放全在主机）。

    fit_mode：stretch 直接拉伸 / letterbox 等比加黑边 / center-crop 等比裁剪。
    content_size：先按较粗处理分辨率（如 64x36）渲染，再最近邻放回固定发送尺寸，
    使“低处理分辨率”的块状效果在 HDMI 可见。None 表示全分辨率。
    """
    if content_size is not None and tuple(content_size) != (width, height):
        proc_w, proc_h = content_size
        if proc_w <= 0 or proc_h <= 0:
            raise ValueError("content_size dimensions must be positive")
        content_bgr = _fit_bgr(frame_bgr, proc_w, proc_h, fit_mode, fill)
        fitted_bgr = cv2.resize(content_bgr, (width, height), interpolation=cv2.INTER_NEAREST)
    else:
        fitted_bgr = _fit_bgr(frame_bgr, width, height, fit_mode, fill)
    return cv2.cvtColor(fitted_bgr, cv2.COLOR_BGR2RGB)


def parse_proc_size(value: str, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT) -> "tuple[int, int] | None":
    proc_w, proc_h = (int(part) for part in value.lower().split("x"))
    if proc_w <= 0 or proc_h <= 0:
        raise ValueError("--proc-size dimensions must be positive")
    return None if (proc_w, proc_h) == (width, height) else (proc_w, proc_h)


def parse_fill_color(value: str) -> tuple[int, int, int]:
    parts = value.split(",")
    if len(parts) != 3:
        raise ValueError("--fill-color must be 'R,G,B', for example '0,0,0'")
    r, g, b = (int(part) for part in parts)
    for channel in (r, g, b):
        if not 0 <= channel <= 255:
            raise ValueError("--fill-color channels must be in range 0..255")
    return (b, g, r)


def load_image_rgb(path: str, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT,
                   flip: bool = False, fit_mode: str = "stretch",
                   content_size: "tuple[int, int] | None" = None) -> np.ndarray:
    """读入图片 -> 缩放到 width x height 的 RGB888(uint8)。支持中文路径与 fit/proc 缩放。"""
    return prepare_frame(load_source_bgr(path, flip), width, height, fit_mode, content_size)


# --------------------------- 帧 / 控制打包发送 ---------------------------
def build_frame_packet(rgb_image: np.ndarray) -> bytes:
    """把 RGB888(uint8, HxWx3) 打包成一帧 UART 字节流（与实验 5 协议一致）。"""
    height, width, channels = rgb_image.shape
    if channels != 3:
        raise ValueError("RGB image must have 3 channels")
    if rgb_image.dtype != np.uint8:
        raise ValueError("RGB image must be uint8")

    packet = bytearray()
    packet.extend(FRAME_SYNC)
    packet.extend((width & 0xFF, (width >> 8) & 0xFF))
    packet.extend((height & 0xFF, (height >> 8) & 0xFF))
    packet.append(RGB888_FORMAT)

    contiguous = np.ascontiguousarray(rgb_image)
    for row in range(height):
        packet.extend(LINE_SYNC)
        packet.extend((row & 0xFF, (row >> 8) & 0xFF))
        packet.extend(contiguous[row].tobytes())
    return bytes(packet)


def send_frame_by_line(ser: serial.Serial, rgb_image: np.ndarray, line_delay: float = 0.0) -> None:
    height, width, _ = rgb_image.shape
    ser.write(FRAME_SYNC)
    ser.write(bytes((width & 0xFF, (width >> 8) & 0xFF)))
    ser.write(bytes((height & 0xFF, (height >> 8) & 0xFF)))
    ser.write(bytes((RGB888_FORMAT,)))

    contiguous = np.ascontiguousarray(rgb_image)
    for row in range(height):
        ser.write(LINE_SYNC)
        ser.write(bytes((row & 0xFF, (row >> 8) & 0xFF)))
        ser.write(contiguous[row].tobytes())
        if line_delay > 0.0:
            time.sleep(line_delay)


def send_control_command(ser: serial.Serial, command: int, value: int) -> None:
    """下发一条控制帧：A5 5A cmd value。"""
    if not 0 <= value <= 255:
        raise ValueError("control command value must be in range 0..255")
    ser.write(CONTROL_SYNC)
    ser.write(bytes((command & 0xFF, value & 0xFF)))


def send_mode(ser: serial.Serial, mode: str) -> None:
    if mode not in MODE_VALUES:
        raise ValueError(f"unknown mode {mode!r}; choose from {MODE_NAMES}")
    send_control_command(ser, CONTROL_MODE, MODE_VALUES[mode])


def send_sharpen(ser: serial.Serial, strength: int) -> None:
    """实时设置锐化强度（控制字 0x900C）。这是 GUI 滑块拖动时调用的核心函数。"""
    send_control_command(ser, CONTROL_SHARPEN, int(strength) & 0xFF)


def send_requested_controls(ser: serial.Serial, mode: "str | None" = None,
                            threshold: "int | None" = None, overlay: "str | None" = None,
                            sharpen: "int | None" = None) -> None:
    """按 mode -> threshold -> overlay -> sharpen 的顺序下发存在的控制命令。"""
    if mode is not None:
        send_mode(ser, mode)
    if threshold is not None:
        if not 0 <= threshold <= 255:
            raise ValueError("--threshold must be in range 0..255")
        send_control_command(ser, CONTROL_THRESHOLD, threshold)
    if overlay is not None:
        send_control_command(ser, CONTROL_OVERLAY, 1 if overlay == "on" else 0)
    if sharpen is not None:
        send_sharpen(ser, sharpen)


# --------------------------- 命令行 ---------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="大拓展03 锐化 + 大拓展01 缩放：发送图像并实时控制 PL 算法（任务3 B档）。"
    )
    parser.add_argument("--port", help="串口，例如 COM7 或 /dev/ttyUSB0（--no-send 时可省略）")
    parser.add_argument("--baud", type=int, default=115_200, help="UART 波特率")
    parser.add_argument("--image", help="要发送/处理的图片文件")
    parser.add_argument("--camera", type=int, help="改用摄像头索引（与 --image 二选一）")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH, help="输出宽")
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT, help="输出高")
    parser.add_argument("--fit-mode", choices=FIT_MODES, default="stretch", help="大拓展01 缩放方式")
    parser.add_argument("--proc-size", choices=PROC_SIZES, default="128x72", help="大拓展01 处理分辨率")
    parser.add_argument("--fill-color", help="letterbox 黑边填充色 'R,G,B'，默认黑")
    parser.add_argument("--flip", action="store_true", help="水平翻转输入")
    parser.add_argument("--once", action="store_true", help="只发送一帧后退出")
    parser.add_argument("--fps", type=float, default=2.0, help="摄像头发送帧率")
    parser.add_argument("--line-delay", type=float, default=0.0, help="每行后延时（秒）")
    parser.add_argument("--mode", choices=MODE_NAMES, help="显示模式控制命令（含 sharpen）")
    parser.add_argument("--threshold", type=int, help="边缘阈值控制命令 0..255")
    parser.add_argument("--overlay", choices=("off", "on"), help="红色边缘叠加控制命令")
    parser.add_argument("--sharpen", type=int, help="锐化强度控制命令 0..255（控制字 0x900C）")
    parser.add_argument("--control-only", action="store_true", help="只发控制命令，不发图像")
    parser.add_argument("--no-send", action="store_true", help="不打开串口（仅本地处理，配合 --software-out）")
    parser.add_argument("--software-out", help="把软件锐化参考结果保存为图片（与 HDMI 硬件输出对照）")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.sharpen is not None and not 0 <= args.sharpen <= 255:
        raise ValueError("--sharpen must be in range 0..255")
    content_size = parse_proc_size(args.proc_size, args.width, args.height)
    fill = parse_fill_color(args.fill_color) if args.fill_color else (0, 0, 0)

    # 本地软件锐化参考（不需要串口）。
    if args.software_out is not None:
        if not args.image:
            raise ValueError("--software-out 需要 --image")
        rgb = prepare_frame(load_source_bgr(args.image, args.flip), args.width, args.height,
                            args.fit_mode, content_size, fill)
        result = sharpen_algo.sharpen(rgb, args.sharpen if args.sharpen is not None else 0)
        if not imwrite_unicode(args.software_out, cv2.cvtColor(result, cv2.COLOR_RGB2BGR)):
            raise RuntimeError(f"failed to write {args.software_out}")
        print(f"software sharpen (k={args.sharpen or 0}) written to {args.software_out}")

    if args.no_send:
        return 0
    if not args.port:
        raise ValueError("--port is required unless --no-send is given")

    has_control = any(v is not None for v in (args.mode, args.threshold, args.overlay, args.sharpen))
    if args.control_only and not has_control:
        raise ValueError("--control-only needs at least one of --mode/--threshold/--overlay/--sharpen")

    with serial.Serial(args.port, args.baud, timeout=0, write_timeout=2) as ser:
        time.sleep(0.2)
        send_requested_controls(ser, args.mode, args.threshold, args.overlay, args.sharpen)
        if has_control:
            print("sent control command(s):",
                  f"mode={args.mode} threshold={args.threshold} overlay={args.overlay} sharpen={args.sharpen}")
        if args.control_only:
            return 0

        if args.camera is not None:
            cap = cv2.VideoCapture(args.camera)
            if not cap.isOpened():
                raise RuntimeError(f"failed to open camera {args.camera}")
            print(f"streaming camera {args.camera} -> {args.port}; Ctrl+C to stop")
            interval = 1.0 / args.fps if args.fps > 0 else 0.0
            try:
                while True:
                    ok, bgr = cap.read()
                    if not ok:
                        break
                    if args.flip:
                        bgr = cv2.flip(bgr, 1)
                    frame_rgb = prepare_frame(bgr, args.width, args.height, args.fit_mode, content_size, fill)
                    send_frame_by_line(ser, frame_rgb, args.line_delay)
                    if args.once:
                        break
                    time.sleep(interval)
            except KeyboardInterrupt:
                print("\nstopped")
            finally:
                cap.release()
        elif args.image:
            rgb = prepare_frame(load_source_bgr(args.image, args.flip), args.width, args.height,
                               args.fit_mode, content_size, fill)
            send_frame_by_line(ser, rgb, args.line_delay)
            print(f"sent {args.width}x{args.height} RGB888 image {args.image} "
                  f"({args.fit_mode}, proc {args.proc_size}) to {args.port}")
        else:
            print("no --image/--camera given; only control commands were sent")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

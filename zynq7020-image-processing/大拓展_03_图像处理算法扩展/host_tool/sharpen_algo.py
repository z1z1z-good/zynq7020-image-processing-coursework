#!/usr/bin/env python3
"""大拓展 03（图像处理算法扩展，任务3 B档）锐化算法的软件参考实现。

本模块是锐化算法的**软件 golden**，与 PL 端 RTL 逐位一致，用于两处：
  1. GUI 实时预览（拖动强度滑块即时看到“原图 -> 锐化”的可见改善）；
  2. B 档要求的“软件参考对比”——与 HDMI 硬件输出逐像素对照。

与 RTL（sobel_core.v / hdmi_bram_sobel_display.v）完全一致的定点运算：

    gray  = (77*R + 150*G + 29*B) >> 8                 # 与 rgb_to_gray.v 一致
    lap   = 4*center - up - down - left - right         # 4 邻域拉普拉斯，1 像素边界=0
    delta = floor(strength * lap / 256)                 # 与 RTL 算术右移 >>>8 一致（向下取整）
    out_c = clamp(c + delta, 0, 255)   for c in R,G,B   # 逐通道，保留彩色

strength（0..255）即 GUI 滑块取值，也是控制字 0x900C / 控制命令 `a5 5a 04 k` 的 value。
strength=0 时输出与原图逐像素相同（对应 RTL 的 sharp0 == 原图）。

只依赖 numpy；不打开串口/摄像头，便于离线对照与单元自检。
"""
from __future__ import annotations

import numpy as np

# 灰度权重（与 rgb_to_gray.v / generate_exp05_expected.py 一致）。
GRAY_R = 77
GRAY_G = 150
GRAY_B = 29


def to_gray(rgb: np.ndarray) -> np.ndarray:
    """RGB(uint8, HxWx3) -> 灰度(int32, HxW)：(77R + 150G + 29B) >> 8。"""
    rgb = np.ascontiguousarray(rgb)
    r = rgb[:, :, 0].astype(np.int32)
    g = rgb[:, :, 1].astype(np.int32)
    b = rgb[:, :, 2].astype(np.int32)
    return (r * GRAY_R + g * GRAY_G + b * GRAY_B) >> 8


def laplacian(gray: np.ndarray) -> np.ndarray:
    """4 邻域拉普拉斯，匹配 sobel_core.v：lap = 4*center - up - down - left - right。

    1 像素边界保持 0（与 RTL 在边界/flush 阶段输出 lap=0 一致）。返回 int32，可正可负。
    """
    gray = gray.astype(np.int32)
    h, w = gray.shape
    lap = np.zeros((h, w), dtype=np.int32)
    if h >= 3 and w >= 3:
        center = gray[1:-1, 1:-1]
        up = gray[0:-2, 1:-1]
        down = gray[2:, 1:-1]
        left = gray[1:-1, 0:-2]
        right = gray[1:-1, 2:]
        lap[1:-1, 1:-1] = 4 * center - up - down - left - right
    return lap


def sharpen(rgb: np.ndarray, strength: int) -> np.ndarray:
    """对 RGB(uint8) 图像做锐化，返回 RGB(uint8)。

    strength<=0 时返回原图副本。整数运算与 RTL 逐位一致：
    delta = floor(strength * lap / 256)，再逐通道 clamp(c + delta, 0, 255)。
    """
    rgb = np.ascontiguousarray(rgb, dtype=np.uint8)
    strength = int(strength)
    if strength <= 0:
        return rgb.copy()

    lap = laplacian(to_gray(rgb))
    # int64 防溢出；floor_divide 显式向下取整，等价于 RTL 的算术右移 >>>8、以及软件 golden 的 >>8。
    delta = np.floor_divide(strength * lap.astype(np.int64), 256)
    out = rgb.astype(np.int64) + delta[:, :, None]
    return np.clip(out, 0, 255).astype(np.uint8)


def sharpen_delta_map(rgb: np.ndarray, strength: int) -> np.ndarray:
    """返回每像素锐化增量 delta（int32, HxW），便于可视化“锐化作用在哪里”。"""
    lap = laplacian(to_gray(rgb))
    return np.floor_divide(int(strength) * lap.astype(np.int64), 256).astype(np.int32)


if __name__ == "__main__":
    # 简易自检：strength=0 等于原图；强度越大改变越多；输出始终在 [0,255]。
    rng = np.random.default_rng(0)
    img = rng.integers(0, 256, size=(72, 128, 3), dtype=np.uint8)
    assert np.array_equal(sharpen(img, 0), img), "strength=0 必须等于原图"
    changed = [int(np.count_nonzero(np.any(sharpen(img, k) != img, axis=2))) for k in (16, 64, 128, 255)]
    assert changed == sorted(changed), f"改变像素数应随强度单调不减: {changed}"
    for k in (0, 1, 64, 200, 255):
        out = sharpen(img, k)
        assert out.min() >= 0 and out.max() <= 255 and out.dtype == np.uint8
    print("sharpen_algo self-check passed; changed pixels @16/64/128/255 =", changed)

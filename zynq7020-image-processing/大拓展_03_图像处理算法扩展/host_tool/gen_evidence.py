#!/usr/bin/env python3
"""生成大拓展03 锐化扩展的演示/证据图片（软件参考，与 HDMI 硬件输出逐像素一致）。

输出到 ../evidence/：原图、k=0/64/128/255 的锐化结果、原图vs锐化并排对比、锐化增量热力图。
软件结果用 sharpen_algo.py（已用协同仿真验证 RTL==软件 golden），因此这些图等价于 HDMI 上
的硬件显示，可直接作为 B 档“软件参考对比”的离线证据。

用法：python gen_evidence.py
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import cv2
import numpy as np

import sharpen_algo
from camera_uart_sender import imwrite_unicode

IMG_W, IMG_H, UP = 128, 72, 6
HERE = Path(__file__).resolve().parent
EVID = HERE.parent / "evidence"


def test_image() -> np.ndarray:
    """优先复用 exp5 golden 的测试图（含强弱边缘），保证与协同仿真同款；失败则本地造一张。"""
    golden = HERE.parents[1] / "sobel_05_pc_control_display" / "tools" / "generate_exp05_expected.py"
    try:
        spec = importlib.util.spec_from_file_location("gen", golden)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return np.array(mod.make_test_image(), dtype=np.uint8).reshape(IMG_H, IMG_W, 3)
    except Exception:
        y, x = np.mgrid[0:IMG_H, 0:IMG_W]
        img = np.dstack([(x * 255 // (IMG_W - 1)).astype(np.uint8),
                         (y * 255 // (IMG_H - 1)).astype(np.uint8),
                         np.full((IMG_H, IMG_W), 64, np.uint8)])
        img[12:32, 12:40] = (240, 240, 240)
        img[20:52, 60:100] = (16, 16, 16)
        img[np.abs(x - 2 * y) < 2] = (255, 255, 0)
        return np.ascontiguousarray(img)


def up(rgb: np.ndarray) -> np.ndarray:
    return cv2.resize(rgb, (IMG_W * UP, IMG_H * UP), interpolation=cv2.INTER_NEAREST)


def save_rgb(path: Path, rgb: np.ndarray) -> None:
    imwrite_unicode(str(path), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))


def main() -> None:
    EVID.mkdir(parents=True, exist_ok=True)
    img = test_image()
    save_rgb(EVID / "sharpen_original.png", up(img))

    strengths = (0, 64, 128, 255)
    changed = {}
    for k in strengths:
        out = sharpen_algo.sharpen(img, k)
        save_rgb(EVID / f"sharpen_k{k}.png", up(out))
        changed[k] = int(np.count_nonzero(np.any(out != img, axis=2)))

    # 原图 | k=128 并排对比
    sep = np.full((IMG_H * UP, 8, 3), 255, np.uint8)
    side = np.hstack([up(img), sep, up(sharpen_algo.sharpen(img, 128))])
    save_rgb(EVID / "sharpen_side_by_side_k128.png", side)

    # 锐化增量热力图（|delta| 放大，直观显示“锐化作用在边缘处”）
    delta = np.abs(sharpen_algo.sharpen_delta_map(img, 128)).astype(np.float32)
    heat = (255 * delta / max(1.0, float(delta.max()))).astype(np.uint8)
    heat_rgb = cv2.applyColorMap(up(heat), cv2.COLORMAP_JET)  # 已是 BGR
    imwrite_unicode(str(EVID / "sharpen_delta_heatmap_k128.png"), heat_rgb)

    lines = [
        "大拓展03 锐化扩展 软件参考证据（与 HDMI 硬件输出逐像素一致）",
        f"图像尺寸：{IMG_W}x{IMG_H}，预览放大 {UP}x（最近邻，模拟 HDMI 10x 块状放大）",
        "定点算法：gray=(77R+150G+29B)>>8; lap=4c-上-下-左-右(边界0); out=clamp(c+(k*lap>>8))",
        "",
        *[f"k={k:3d}  改变像素数={changed[k]:5d}/{IMG_W*IMG_H}" for k in strengths],
        "",
        "k=0 改变像素数应为 0（与原图一致）。强度越大边缘增强越明显（高 k 处饱和裁剪）。",
    ]
    (EVID / "sharpen_software_reference.txt").write_text("\n".join(lines), encoding="utf-8")
    print("evidence written to", EVID)
    for k in strengths:
        print(f"  sharpen_k{k}.png  changed={changed[k]}")


if __name__ == "__main__":
    main()

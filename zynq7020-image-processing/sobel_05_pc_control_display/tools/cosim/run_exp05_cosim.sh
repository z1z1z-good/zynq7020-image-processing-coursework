#!/usr/bin/env bash
# 一键跑通实验 5 无板卡软硬件协同仿真链（Git-Bash）：
#
#   真实 camera_uart_sender 图像打包 + 真实 send_requested_controls 控制帧
#     -> 与本地编码器逐字节比对（证明上位机打包与控制命令一致）
#     -> 合成 UART 字节流(文件)
#     -> 真实 main.c 分发循环(wait_for_packet_start)主机编译运行
#        -> 图像区 framebuffer + 控制字 0x9000/0x9004/0x9008
#        -> 与 golden 图像逐像素 + 控制字逐项比对
#        -> 错误注入(图像帧/未知控制命令)返回码核对
#     -> hdmi_bram_sobel_display 自检(xsim, 缩小时序) 校验时序/sobel_done/显示映射自洽
#     -> hdmi_bram_sobel_display 全分辨率渲染(xsim) 逐配置(原图/灰度/边缘×3阈值/叠加×2)
#        捕获 HDMI 帧 -> 重建 PNG 与软件 golden 逐像素自动比对
#
# 工具路径可用环境变量覆盖：EXP05_PYTHON / EXP05_HOSTCC / EXP05_VIVADO_BIN。
# 设 EXP05_COSIM_QUICK=1 只跑步骤 1-7（跳过较慢的全分辨率渲染循环）。
# 中间产物写入可删除重建的 build/cosim/，不提交 Git。
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"          # tools/cosim
S5="$(cd "$HERE/../.." && pwd)"                 # sobel_05_pc_control_display
OUT="$S5/build/cosim"
PY="${EXP05_PYTHON:-D:/Miniconda3/python.exe}"
GCC="${EXP05_HOSTCC:-gcc}"
VIV_BIN="${EXP05_VIVADO_BIN:-D:/Vivado/Vivado/2023.2/bin}"
STUBS="$S5/tools/ps_syntax_check/include"
SRC="$S5/ps_uart_control_bram_app/src"
RTL_DIR="$S5/sobel_05_pc_control_display.srcs/sources_1/new"
RTL_DISPLAY="$RTL_DIR/hdmi_bram_sobel_display.v"
RTL_GRAY="$RTL_DIR/rgb_to_gray.v"
RTL_SOBEL="$RTL_DIR/sobel_core.v"
TB_SELF="$S5/sim/hdmi_bram_sobel_display_tb.v"
TB_COSIM="$S5/sim/hdmi_bram_sobel_display_cosim_tb.v"

mkdir -p "$OUT"

echo "[1/8] gen real UART image+control byte streams + golden + per-config render fb (assert host packing)"
PYTHONUTF8=1 "$PY" "$HERE/exp05_cosim.py" gen --out-dir "$OUT"

echo "[2/8] build real-main.c PS host model (wait_for_packet_start dispatch loop)"
"$GCC" -Wall -Dmain=ps_app_main_unused -I "$STUBS" -I "$SRC" \
    "$HERE/ps_protocol_model.c" -o "$OUT/ps_protocol_model.exe"

echo "[3/8] run real PS parser+control on the real byte stream -> framebuffer + control words"
"$OUT/ps_protocol_model.exe" "$OUT/frame_stream.bin" "$OUT/fb_from_ps.hex"

echo "[4/8] check PS framebuffer image area == golden AND control words == sent values"
PYTHONUTF8=1 "$PY" "$HERE/exp05_cosim.py" check-fb \
    --golden-image "$OUT/golden_image.hex" --expected-ctrl "$OUT/expected_ctrl.txt" \
    --actual "$OUT/fb_from_ps.hex"

echo "[5/8] error-injection return codes vs real parser (first dispatched packet)"
while read -r name kind code; do
    [ -z "$name" ] && continue
    "$OUT/ps_protocol_model.exe" "$OUT/errors/$name.bin" "$OUT/errors/$name.fb.hex" \
        > "$OUT/errors/$name.out" 2>&1 || true
    got="$(grep -m1 '^PKT ' "$OUT/errors/$name.out" | sed -E 's/^PKT ([a-z]+) code=(-?[0-9]+).*/\1 \2/' | tr -d '\r')"
    if [ "$got" != "$kind $code" ]; then
        echo "  error case $name: expected [$kind $code] got [$got]" >&2
        exit 1
    fi
    echo "  $name -> $got"
done < <(tr -d '\r' < "$OUT/error_cases.txt")
echo "EXP05_COSIM_ERRORS=match"

cd "$OUT"

echo "[6/8] compile RTL + testbenches (xvlog)"
"$VIV_BIN/xvlog.bat" "$RTL_DISPLAY" "$RTL_GRAY" "$RTL_SOBEL" "$TB_SELF" "$TB_COSIM" > xvlog.log 2>&1

echo "[7/8] RTL self-check (timing / sobel_done / display-mux self-consistency, overlay config)"
cp -f render_overlay.hex fb_in.hex
"$VIV_BIN/xelab.bat" hdmi_bram_sobel_display_tb -s selfcheck_tb -timescale 1ns/1ps > xelab_self.log 2>&1
"$VIV_BIN/xsim.bat" selfcheck_tb -runall > xsim_self.log 2>&1
grep -q "EXP05_SELFCHECK_TB=passed" xsim_self.log \
    || { echo "RTL self-check failed; see $OUT/xsim_self.log" >&2; tail -n 30 xsim_self.log >&2; exit 1; }
grep -o "EXP05_SELFCHECK_TB=passed active=[0-9]* red=[0-9]*" xsim_self.log

if [ "${EXP05_COSIM_QUICK:-0}" = "1" ]; then
    echo "EXP05_COSIM_QUICK=1 -> skip full-resolution render loop"
    echo "EXP05_COSIM_CHAIN=quick-ok"
    exit 0
fi

echo "[8/8] full-resolution render + PNG reconstruct + per-config golden compare"
"$VIV_BIN/xelab.bat" hdmi_bram_sobel_display_cosim_tb -s cosim_tb -timescale 1ns/1ps > xelab_cosim.log 2>&1
while read -r tag mode thr ovl; do
    [ -z "$tag" ] && continue
    cp -f "render_${tag}.hex" fb_in.hex
    "$VIV_BIN/xsim.bat" cosim_tb -runall > "xsim_cosim_${tag}.log" 2>&1
    grep -q "EXP05_COSIM_CAPTURE=ok" "xsim_cosim_${tag}.log" \
        || { echo "RTL capture failed ($tag); see $OUT/xsim_cosim_${tag}.log" >&2; tail -n 30 "xsim_cosim_${tag}.log" >&2; exit 1; }
    PYTHONUTF8=1 "$PY" "$HERE/exp05_cosim.py" render-compare \
        --fb-hex "$OUT/render_${tag}.hex" --capture "$OUT/hdmi_capture.hex" \
        --png-out "$OUT/exp05_cosim_${tag}.png" --tag "$tag"
done < <(tr -d '\r' < render_cases.txt)

echo "EXP05_COSIM_CHAIN=passed"

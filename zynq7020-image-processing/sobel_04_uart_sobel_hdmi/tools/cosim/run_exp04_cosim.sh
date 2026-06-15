#!/usr/bin/env bash
# 一键跑通实验 4 无板卡软硬件协同仿真链（Git-Bash）：
#
#   真实 camera_uart_sender 打包 -> UART 字节流(文件)
#     -> 真实 main.c receive_frame(主机编译) -> 原始 RGB framebuffer
#     -> 与 golden 逐像素比对 + 错误注入码核对
#     -> hdmi_bram_sobel_display 自检(xsim) 校验显示映射/时序/sobel_done
#     -> hdmi_bram_sobel_display 全分辨率 RTL 渲染(xsim) -> 捕获 HDMI 边缘帧
#     -> 重建 PNG 与软件 golden(gray+Sobel+彩色边缘) 逐像素自动比对
#
# 工具路径可用环境变量覆盖：EXP04_PYTHON / EXP04_HOSTCC / EXP04_VIVADO_BIN。
# 中间产物写入可删除重建的 build/cosim/，不提交 Git。
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"          # tools/cosim
S4="$(cd "$HERE/../.." && pwd)"                 # sobel_04_uart_sobel_hdmi
OUT="$S4/build/cosim"
PY="${EXP04_PYTHON:-D:/Miniconda3/python.exe}"
GCC="${EXP04_HOSTCC:-gcc}"
VIV_BIN="${EXP04_VIVADO_BIN:-D:/Vivado/Vivado/2023.2/bin}"
STUBS="$S4/tools/ps_syntax_check/include"
SRC="$S4/ps_uart_sobel_bram_app/src"
RTL_DIR="$S4/sobel_04_uart_sobel_hdmi.srcs/sources_1/new"
RTL_DISPLAY="$RTL_DIR/hdmi_bram_sobel_display.v"
RTL_GRAY="$RTL_DIR/rgb_to_gray.v"
RTL_SOBEL="$RTL_DIR/sobel_core.v"
TB_SELF="$S4/sim/hdmi_bram_sobel_display_tb.v"
TB_COSIM="$S4/sim/hdmi_bram_sobel_display_cosim_tb.v"

mkdir -p "$OUT"

echo "[1/8] gen real UART byte stream + golden framebuffer (assert host packing)"
PYTHONUTF8=1 "$PY" "$HERE/exp04_cosim.py" gen --out-dir "$OUT"

echo "[2/8] build real-main.c PS host model"
"$GCC" -Wall -Dmain=ps_app_main_unused -I "$STUBS" -I "$SRC" \
    "$HERE/ps_protocol_model.c" -o "$OUT/ps_protocol_model.exe"

echo "[3/8] run real PS parser on the real byte stream -> framebuffer"
"$OUT/ps_protocol_model.exe" "$OUT/frame_stream.bin" "$OUT/fb_from_ps.hex"

echo "[4/8] check PS-parsed framebuffer == golden (original RGB)"
PYTHONUTF8=1 "$PY" "$HERE/exp04_cosim.py" check-fb \
    --golden "$OUT/golden_fb.hex" --actual "$OUT/fb_from_ps.hex"

echo "[5/8] error-injection return codes vs real parser"
while read -r name code; do
    "$OUT/ps_protocol_model.exe" "$OUT/errors/$name.bin" "$OUT/errors/$name.fb.hex" \
        > "$OUT/errors/$name.out"
    got="$(grep -o 'PS_MODEL_CODE=-\?[0-9]*' "$OUT/errors/$name.out" | cut -d= -f2 | tr -d '\r')"
    if [ "$got" != "$code" ]; then
        echo "  error case $name: expected $code got $got" >&2
        exit 1
    fi
    echo "  $name -> $got"
done < <(tr -d '\r' < "$OUT/error_cases.txt")
echo "EXP04_COSIM_ERRORS=match"

cd "$OUT"

echo "[6/8] compile RTL + testbenches (xvlog)"
"$VIV_BIN/xvlog.bat" "$RTL_DISPLAY" "$RTL_GRAY" "$RTL_SOBEL" "$TB_SELF" "$TB_COSIM" \
    > xvlog.log 2>&1

echo "[7/8] RTL self-check (display mapping / timing / sobel_done)"
"$VIV_BIN/xelab.bat" hdmi_bram_sobel_display_tb -s selfcheck_tb -timescale 1ns/1ps \
    > xelab_self.log 2>&1
"$VIV_BIN/xsim.bat" selfcheck_tb -runall > xsim_self.log 2>&1
grep -q "EXP04_SELFCHECK_TB=passed" xsim_self.log \
    || { echo "RTL self-check failed; see $OUT/xsim_self.log" >&2; exit 1; }
grep -o "EXP04_SELFCHECK_TB=passed active=[0-9]* green=[0-9]*" xsim_self.log

echo "[8/8] RTL full-resolution render + reconstruct PNG + pixel compare vs golden"
"$VIV_BIN/xelab.bat" hdmi_bram_sobel_display_cosim_tb -s cosim_tb -timescale 1ns/1ps \
    > xelab_cosim.log 2>&1
"$VIV_BIN/xsim.bat" cosim_tb -runall > xsim_cosim.log 2>&1
grep -q "EXP04_COSIM_CAPTURE=ok" xsim_cosim.log \
    || { echo "RTL capture failed; see $OUT/xsim_cosim.log" >&2; exit 1; }
grep -o "EXP04_COSIM_CAPTURE=ok pixels=[0-9]*" xsim_cosim.log

PYTHONUTF8=1 "$PY" "$HERE/exp04_cosim.py" render-compare \
    --golden-fb "$OUT/golden_fb.hex" --capture "$OUT/hdmi_capture.hex" \
    --png-out "$OUT/exp04_cosim_rendered.png"

echo "EXP04_COSIM_CHAIN=passed"

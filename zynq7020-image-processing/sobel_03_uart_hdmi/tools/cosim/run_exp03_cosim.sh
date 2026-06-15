#!/usr/bin/env bash
# 一键跑通实验 3 无板卡软硬件协同仿真链（Git-Bash）：
#
#   真实 camera_uart_sender 打包 -> UART 字节流(文件)
#     -> 真实 main.c receive_frame(主机编译) -> framebuffer
#     -> 与 golden 逐像素比对 + 错误注入码核对
#     -> hdmi_bram_display 全分辨率 RTL 渲染(xsim) -> 捕获 HDMI 帧
#     -> 重建 PNG 与 golden 逐像素自动比对
#
# 工具路径可用环境变量覆盖：EXP03_PYTHON / EXP03_HOSTCC / EXP03_VIVADO_BIN。
# 中间产物写入可删除重建的 build/cosim/，不提交 Git。
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"          # tools/cosim
S3="$(cd "$HERE/../.." && pwd)"                 # sobel_03_uart_hdmi
OUT="$S3/build/cosim"
PY="${EXP03_PYTHON:-D:/Miniconda3/python.exe}"
GCC="${EXP03_HOSTCC:-gcc}"
VIV_BIN="${EXP03_VIVADO_BIN:-D:/Vivado/Vivado/2023.2/bin}"
STUBS="$S3/tools/ps_syntax_check/include"
SRC="$S3/ps_uart_bram_app/src"
RTL="$S3/sobel_03_uart_hdmi.srcs/sources_1/new/hdmi_bram_display.v"
TB="$S3/sim/hdmi_bram_display_cosim_tb.v"

mkdir -p "$OUT"

echo "[1/7] gen real UART byte stream + golden framebuffer (assert host packing)"
PYTHONUTF8=1 "$PY" "$HERE/exp03_cosim.py" gen --out-dir "$OUT"

echo "[2/7] build real-main.c PS host model"
"$GCC" -Wall -Dmain=ps_app_main_unused -I "$STUBS" -I "$SRC" \
    "$HERE/ps_protocol_model.c" -o "$OUT/ps_protocol_model.exe"

echo "[3/7] run real PS parser on the real byte stream -> framebuffer"
"$OUT/ps_protocol_model.exe" "$OUT/frame_stream.bin" "$OUT/fb_from_ps.hex"

echo "[4/7] check PS-parsed framebuffer == golden"
PYTHONUTF8=1 "$PY" "$HERE/exp03_cosim.py" check-fb \
    --golden "$OUT/golden_fb.hex" --actual "$OUT/fb_from_ps.hex"

echo "[5/7] error-injection return codes vs real parser"
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
echo "EXP03_COSIM_ERRORS=match"

echo "[6/7] RTL full-resolution render (xvlog/xelab/xsim)"
cd "$OUT"
"$VIV_BIN/xvlog.bat" "$RTL" "$TB" > xvlog.log 2>&1
"$VIV_BIN/xelab.bat" hdmi_bram_display_cosim_tb -s cosim_tb -timescale 1ns/1ps > xelab.log 2>&1
"$VIV_BIN/xsim.bat" cosim_tb -runall > xsim.log 2>&1
grep -q "EXP03_COSIM_CAPTURE=ok" xsim.log || { echo "RTL capture failed; see $OUT/xsim.log" >&2; exit 1; }
grep -o "EXP03_COSIM_CAPTURE=ok pixels=[0-9]*" xsim.log

echo "[7/7] reconstruct PNG from RTL capture + pixel compare vs golden"
PYTHONUTF8=1 "$PY" "$HERE/exp03_cosim.py" render-compare \
    --golden-fb "$OUT/golden_fb.hex" --capture "$OUT/hdmi_capture.hex" \
    --png-out "$OUT/exp03_cosim_rendered.png"

echo "EXP03_COSIM_CHAIN=passed"

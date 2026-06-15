# 实验 4 UART -> PS -> BRAM -> PL Sobel -> HDMI 远程开发证据

## 运行信息

- 日期：2026-06-16
- 分支：`exp/04-uart-sobel`
- 工具：Vivado/XSim 2023.2、Vitis 2023.2、arm-none-eabi-gcc 12.2.0、host gcc 8.1.0、Python 3.11
- 器件：`xc7z020clg400-2`
- 基础扩展：彩色边缘标记，默认 `EDGE_THRESHOLD=8'd80`、`EDGE_COLOR=24'h00ff00`（绿色）
- 状态：远程协同仿真与构建、XSim 自检、PS 源码检查通过；真实 JTAG / UART / HDMI 与完整 Vitis ELF 待现场

## 证据文件

| 文件 | 内容 |
| --- | --- |
| `exp04_expected_image.png` | 合成 `128x72` 测试图经 gray+Sobel+彩色边缘映射、10x 放大后的预期 `1280x720` HDMI 画面（默认绿色边缘、黑色背景） |
| `exp04_edge_strength.png` | 原始 8 bit Sobel 边缘强度灰度图（10x 放大） |
| `exp04_edge_threshold_40.png` / `_80.png` / `_120.png` | 阈值 40 / 80 / 120 下的彩色边缘图 |
| `exp04_threshold_stats.txt` | 三个阈值的边缘像素数统计与单调不增加自检 |
| `exp04_protocol_selfcheck.txt` | 协议黄金模型编码与 PS 解析往返无损 + 错误码注入自检 |
| `exp04_cosim.txt` | 无板卡软硬件协同仿真链：真实上位机打包 → 真实 main.c 解析 → RTL 渲染 → PNG 逐像素比对 |
| `exp04_simulation.txt` | XSim 自检（显示映射 / 时序 / sobel_done）与全分辨率渲染捕获摘要 |
| `exp04_remote_build.txt` | 综合 / 实现 / bitstream 精简结果（含 BD 隔离重建说明、资源、时序、DRC） |
| `exp04_utilization.txt` | Vivado utilization 报告 |
| `exp04_timing_summary.txt` | Vivado timing summary（WNS/TNS/WHS/THS） |
| `exp04_drc.txt` | Vivado DRC 报告 |
| `exp04_ps_build.txt` | PS 程序编译验证（arm-none-eabi-gcc 源码检查 + 完整 Vitis 脚本说明） |

生成的 `top.bit` / `.xsa` / `.dcp` 保存在已忽略的本地 `build/` 目录，未提交 Git。

## 关键结果

- 协同仿真链（`EXP04_COSIM_CHAIN=passed`）：真实 `camera_uart_sender.build_frame_packet` 与本地编码器逐字节一致（27943 byte）；真实 `main.c` 解析产出的原始 RGB framebuffer 与 golden 逐像素一致（9216 word）；错误码 `-1/-2/-3/-5/-7` 与 `main.c` 一致；RTL 渲染 `1280x720`（921600 像素）与软件 golden（gray + Sobel + 彩色边缘映射）逐像素一致。仅导入打包函数，未打开真实串口/摄像头。
- XSim 自检：`EXP04_SELFCHECK_TB=passed active=36864 green=4436`；全分辨率捕获 `EXP04_COSIM_CAPTURE=ok pixels=921600`。
- 阈值边缘像素数：`40 -> 1139`、`80 -> 1109`、`120 -> 1093`（随阈值升高单调不增加）。
- 构建：`EXP04_BUILD=passed`；WNS `+13.453 ns`、TNS `0`、WHS `+0.058 ns`、THS `0`；`4446` LUT、`3662` FF、`18` BRAM36、`0` DSP、`1` MMCM；DRC `0` errors（`20` 个 REQP-1839 + `1` 个 CHECK-3 warning，已说明，不阻塞）。
- PS：`arm-none-eabi-gcc 12.2.0` 源码级编译 `main.c` 0 error、0 warning；完整 Vitis BSP/ELF 待正常 Vitis 环境（XSCT 无头超时）。

诚实边界：以上仅覆盖协议 / 格式 / 算法 / 显示映射与远程构建；"协同仿真通过"不等于"上板通过"。

## 待现场回传的证据

- 实际测试的分支和完整提交号。
- 板卡型号、Vivado/Vitis 版本、COM 口、显示设备型号和测试日期。
- Hardware Manager 识别目标、Program Device 和 PS 串口启动日志（含 `received frame`）。
- HDMI 显示彩色 Sobel 边缘（默认绿色、黑底）的照片与分辨率信息。
- 能确认板卡、JTAG、HDMI 和 USB 串口接线的照片。
- 若做阈值或边缘颜色对比：各参数下的 HDMI 照片。
- 现场 utilization、timing summary 和 DRC 摘要。

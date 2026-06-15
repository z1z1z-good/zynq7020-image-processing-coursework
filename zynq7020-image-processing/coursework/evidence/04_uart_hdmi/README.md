# 实验 3 UART -> PS -> BRAM -> HDMI 远程开发证据

## 运行信息

- 日期：2026-06-15
- 分支：`exp/03-uart-hdmi`
- 工具：Vivado/XSim 2023.2、Vitis 2023.2、arm-none-eabi-gcc 12.2.0
- 器件：`xc7z020clg400-2`
- 默认边框：`BORDER_WIDTH=20`、`BORDER_COLOR=24'h0066ff`
- 状态：远程 PL 仿真与构建、协议黄金模型和 PS 源码静态检查通过；正式 Vitis/BSP/ELF 构建及真实 JTAG / UART / HDMI 待完成

## 证据文件

| 文件 | 内容 |
| --- | --- |
| `exp03_expected_image.png` | 合成 `128x72` 测试图 10x 放大 + 蓝色边框的预期 `1280x720` HDMI 画面 |
| `exp03_protocol_selfcheck.txt` | 协议黄金模型编码与 PS 解析往返无损 + 错误码注入自检；未直接调用上位机发送脚本 |
| `exp03_simulation.txt` | 精简 XSim 结果（时序 / 缩放 / 边框 / 读延迟流水线） |
| `exp03_remote_build.txt` | 精简实现与 bitstream 结果（含 BD 隔离重建说明） |
| `exp03_utilization.txt` | Vivado utilization 报告 |
| `exp03_timing_summary.txt` | Vivado timing summary（WNS/TNS/WHS/THS） |
| `exp03_drc.txt` | Vivado DRC 报告 |
| `exp03_ps_build.txt` | PS 程序编译验证（完整 Vitis 脚本 + arm-gcc 源码检查） |

生成的 `top.bit` / `.xsa` / `.dcp` 保存在已忽略的本地 `build/` 目录，未提交 Git。

## 关键结果

- 协议黄金模型：`9216` 像素往返无损；错误码 `-1/-2/-3/-5/-7` 与 `main.c` 一致；未直接回归上位机发送脚本。
- 仿真：`HDMI BRAM display simulation passed`，0 errors。
- 构建：WNS `8.173 ns`、TNS `0`；`1775` LUT、`1504` FF、`16` BRAM、`0` DSP；DRC `0` violations。
- PS：`arm-none-eabi-gcc 12.2.0` 静态编译 `main.c`，0 error、0 warning；正式 Vitis/BSP/ELF 构建待完成。

## 待现场回传的证据

- 实际测试的分支和完整提交号。
- 板卡型号、Vivado/Vitis 版本、COM 口、显示设备型号和测试日期。
- Hardware Manager 识别目标、Program Device 和 PS 串口启动日志。
- HDMI 显示原图（含蓝色边框）的照片与分辨率信息。
- 能确认板卡、JTAG、HDMI 和 USB 串口接线的照片。

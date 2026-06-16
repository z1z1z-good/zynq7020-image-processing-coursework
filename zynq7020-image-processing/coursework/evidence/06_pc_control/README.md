# 实验 5 上位机控制 HDMI 显示模式 远程开发证据

## 运行信息

- 日期：2026-06-16
- 分支：`exp/05-pc-control`
- 工具：Vivado/XSim 2023.2、Vitis 2023.2、arm-none-eabi-gcc 12.2.0、host gcc、Python 3.11
- 器件：`xc7z020clg400-2`
- 控制协议：控制帧 `A5 5A cmd value`（cmd=1 mode / cmd=2 threshold / cmd=3 overlay）；控制字 `0x9000`/`0x9004`/`0x9008`
- 显示模式：0 原图 / 1 灰度 / 2 Sobel 二值边缘 / 3 原图+红色边缘叠加（`0xff2020`）；复位默认 mode=2 / thr=80 / overlay=0
- 状态：远程协同仿真与构建、XSim 自检、PS 源码检查通过；真实 JTAG / UART / HDMI 与完整 Vitis ELF 待现场

## 证据文件

| 文件 | 内容 |
| --- | --- |
| `exp05_display_control_model.txt` | 既有轻量显示控制模型仿真（6 用例：四模式 + 阈值 + 叠加） |
| `exp05_mode_original.png` / `_gray.png` / `_edge.png` / `_overlay.png` | 四种显示模式预期 `1280x720` HDMI 画面（默认阈值 80） |
| `exp05_edge_threshold_40.png` / `_80.png` / `_120.png` | 边缘模式三档阈值预期画面 |
| `exp05_edge_strength.png` | 原始 8 bit Sobel 边缘强度灰度图（10x 放大） |
| `exp05_threshold_stats.txt` | 三阈值边缘像素数统计与单调不增加自检 |
| `exp05_protocol_selfcheck.txt` | 协议黄金模型：往返无损 + 控制帧字节 + 错误码注入自检 |
| `exp05_cosim.txt` | 无板卡协同仿真链：真实上位机打包+控制帧 → 真实 main.c 分发 → 图像区+控制字 → RTL 逐配置渲染比对 |
| `exp05_simulation.txt` | XSim 自检（时序 / sobel_done / 显示映射自洽）与全分辨率渲染摘要 |
| `exp05_remote_build.txt` | 综合 / 实现 / bitstream 精简结果（BD 隔离重建、资源、时序、DRC） |
| `exp05_utilization.txt` | Vivado utilization 报告 |
| `exp05_timing_summary.txt` | Vivado timing summary（WNS/TNS/WHS/THS） |
| `exp05_drc.txt` | Vivado DRC 报告 |
| `exp05_ps_build.txt` | PS 程序编译验证（arm-none-eabi-gcc 源码检查 + 完整 Vitis 脚本说明） |

生成的 `top.bit` / `.xsa` / `.dcp` 保存在已忽略的本地 build 目录，未提交 Git。

## 关键结果

- 协同仿真链 `EXP05_COSIM_CHAIN=passed`：真实 `build_frame_packet`(27943B) 与 `send_requested_controls`(12B) 逐字节一致；真实 `main.c` 分发产出图像区 9216 word 与 golden 一致、控制字 `0x9000/4/8 = mode=3/thr=40/overlay=1` 与下发一致；6 个错误注入码（`-1/-2/-5/-7` 与未知控制命令 `-12`）与 `main.c` 一致；mode=0/1/2/3 + 阈值 40/80/120 + overlay=0/1 共 7 组全分辨率(`921600` 像素)渲染与软件 golden 逐像素一致。仅导入打包/控制函数，未开真实串口/摄像头。
- XSim 自检：`EXP05_SELFCHECK_TB=passed active=36864 red=3844`。
- 阈值边缘像素数：`40 -> 1139`、`80 -> 1109`、`120 -> 1093`（随阈值升高单调不增加）。
- 构建：`EXP05_BUILD=passed`；WNS `+0.325 ns`、TNS `0`、WHS `+0.043 ns`、THS `0`；`10795` LUT、`4113` FF、`20` BRAM Tile、`0` DSP、`1` MMCM；DRC `0` violations（Fully Routed）。
- PS：`arm-none-eabi-gcc 12.2.0` 源码级编译 `main.c` 0 error / 0 warning；完整 Vitis BSP/ELF 待正常 Vitis 环境（XSCT 无头超时）。
- 已知右下角单像素边界伪影（该时序无尾部消隐 + 2 拍显示流水，帧末像素落在 sobel_done 复位后被门控为黑），肉眼不可见，详见 `exp05_cosim.txt`。

诚实边界：以上仅覆盖协议 / 格式 / 算法 / 显示映射与远程构建；“协同仿真通过”不等于“上板通过”。

## 待现场回传的证据

- 实际测试的分支和完整提交号；板卡型号、Vivado/Vitis 版本、COM 口、显示设备型号和测试日期。
- Hardware Manager 识别目标、Program Device 与 PS 串口启动日志（`PS UART PL Control HDMI display` 横幅 + `control:` 回显 + `received frame`）。
- 四种显示模式（原图 / 灰度 / 边缘 / 叠加）各一张 HDMI 照片。
- 阈值 40 / 80 / 120 的边缘对比照片；overlay 开 / 关对比照片。
- 串口控制命令回显完整文本；上位机命令与日志。
- 现场 utilization / timing summary / DRC 摘要。
- 能确认板卡、JTAG、HDMI 和 USB 串口接线的照片。

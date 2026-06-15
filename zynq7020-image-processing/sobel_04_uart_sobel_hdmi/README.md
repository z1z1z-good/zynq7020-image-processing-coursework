# sobel_04_uart_sobel_hdmi 实验说明

本实验在 `sobel_03_uart_hdmi` 的基础上继续完成 Sobel 边缘检测显示。

数据仍然由 PC 端通过串口发送到 ZYNQ7020，PS 端负责接收 `128 x 72` RGB888 图像并写入 AXI BRAM，PL 端从 BRAM 读取原始图像，完成灰度转换和 Sobel 运算，最后把边缘检测结果通过 HDMI 显示到显示器上。

## 实验步骤总览

建议在已经完成 `sobel_03_uart_hdmi` 的基础上再做本实验：

1. 打开 `sobel_04_uart_sobel_hdmi.xpr`，确认顶层、Block Design、HDMI 约束和 Sobel 相关源码存在。
2. 检查 `hdmi_pl_top.v` 是否例化 `hdmi_bram_sobel_display`。
3. 在 Vivado 中运行 Synthesis、Implementation，并生成 `top.bit`。
4. 下载 bitstream 到开发板。
5. 打开 SDK 工作区，重新生成 BSP，编译并运行 `ps_uart_bram_app`。
6. 用串口调试助手确认启动信息为 `PS UART PL Sobel HDMI display`。
7. 关闭串口调试助手，使用 `host_camera_uart` 中的 GUI 或命令行脚本发送图片。
8. 观察 HDMI 是否显示输入图像的 Sobel 边缘结果。
9. 保存 HDMI 照片、串口输出截图、资源利用率和时序结果。

## 1. 实验目标

```text
PC 摄像头 / 图片
    -> UART 115200
    -> ZYNQ PS UART
    -> PS 写入 AXI BRAM 原始 RGB 图像
    -> PL 读取 BRAM 原图
    -> PL rgb_to_gray
    -> PL sobel_core
    -> PL edge_mem
    -> HDMI 显示 Sobel 边缘图
```

和 `sobel_03_uart_hdmi` 的区别：

```text
sobel_03: HDMI 显示串口收到的原始 RGB 图像
sobel_04: HDMI 显示 PL Sobel 运算后的灰度边缘图
```

当前保持已经调通的稳定串口配置：

```text
baud   = 115200
format = 8N1
image  = 128 x 72 RGB888
fps    = 0.2
```

## 2. 主要文件

```text
sobel_04_uart_sobel_hdmi.xpr
    Vivado 工程

create_ps_uart_sobel_hdmi_bd.tcl
    重新生成 PS UART + AXI BRAM Block Design 的 Tcl 脚本

sobel_04_uart_sobel_hdmi.srcs/sources_1/new/top.v
    工程顶层，连接 ZYNQ PS BD 和 HDMI PL 顶层

sobel_04_uart_sobel_hdmi.srcs/sources_1/new/hdmi_pl_top.v
    HDMI PL 顶层，连接 video_clock、rgb2dvi 和 Sobel 显示模块

sobel_04_uart_sobel_hdmi.srcs/sources_1/new/hdmi_bram_sobel_display.v
    从 BRAM 读取原图，在 PL 中执行 Sobel，并输出 HDMI 显示数据

sobel_04_uart_sobel_hdmi.srcs/sources_1/new/rgb_to_gray.v
    RGB888 转灰度

sobel_04_uart_sobel_hdmi.srcs/sources_1/new/sobel_core.v
    Sobel 卷积核心

sobel_04_uart_sobel_hdmi.srcs/constrs_1/new/hdmi_out_test.xdc
    HDMI 管脚约束

sobel_04_uart_sobel_hdmi.sdk/ps_uart_bram_app/src/main.c
    SDK 工作区中实际编译运行的 PS 端程序

ps_uart_sobel_bram_app/src/main.c
    PS 端程序源码备份，内容与 SDK 中 main.c 保持一致

../host_camera_uart/camera_uart_sender.py
    PC 端串口发送脚本
```

## 3. 硬件结构

Block Design 仍然复用第 3 步的硬件链路：

```text
processing_system7_0 M_AXI_GP0
    -> SmartConnect
    -> AXI BRAM Controller
    -> Block Memory Generator Port A

Block Memory Generator Port B
    -> PL Sobel HDMI display
```

BRAM 地址：

```text
base  = 0x40000000
range = 64 KB
```

PS 写入 BRAM 的原始图像格式：

```text
address = 0x40000000 + ((y * 128 + x) << 2)
data    = 0x00RRGGBB
```

PL 端 `hdmi_bram_sobel_display.v` 每个 HDMI 帧开始时扫描一遍 BRAM 中的 `128 x 72` 原图，然后完成：

```text
BRAM RGB888 -> rgb_to_gray -> sobel_core -> edge_mem
```

HDMI 显示时从 `edge_mem` 读取 8 bit 灰度边缘值，并复制到 RGB 三个通道：

```text
R = edge
G = edge
B = edge
```

最终显示为黑白边缘图。

## 4. Vivado 使用流程

打开工程：

```text
D:\Github\FPGA-course\zynq7020-image-processing\sobel_04_uart_sobel_hdmi\sobel_04_uart_sobel_hdmi.xpr
```

如果需要重新生成 Block Design，在 Vivado Tcl Console 中执行：

```tcl
cd D:/Github/FPGA-course/zynq7020-image-processing/sobel_04_uart_sobel_hdmi
source create_ps_uart_sobel_hdmi_bd.tcl
```

然后依次执行：

```text
Run Synthesis
Run Implementation
Generate Bitstream
```

生成 bitstream 后，下载 FPGA：

```text
Xilinx -> Program FPGA
```

bitstream 通常位于：

```text
sobel_04_uart_sobel_hdmi.runs/impl_1/top.bit
```

如果工程还没有生成 `.runs` 目录，说明还没有在 Vivado 中重新综合和实现。

## 5. SDK 使用流程

SDK 工作区：

```text
D:\Github\FPGA-course\zynq7020-image-processing\sobel_04_uart_sobel_hdmi\sobel_04_uart_sobel_hdmi.sdk
```

由于本工程从 `sobel_03` 复制而来，SDK Project Explorer 中可能仍然显示：

```text
top_hw_platform_0
ps_uart_bram_app_bsp
ps_uart_bram_app
```

这里直接编译运行 `ps_uart_bram_app` 即可。它的 `main.c` 已经改成 `sobel_04` 版本，启动时会打印：

```text
PS UART PL Sobel HDMI display
BRAM base: 0x40000000, baud: 115200, image: 128x72
```

SDK 中执行：

```text
右键 ps_uart_bram_app_bsp -> Re-generate BSP Sources
右键 ps_uart_bram_app     -> Clean Project
右键 ps_uart_bram_app     -> Build Project
右键 ps_uart_bram_app     -> Run As -> Launch on Hardware (System Debugger)
```

PS 程序功能：

```text
1. 初始化 PS UART，波特率 115200
2. 先向 BRAM 写入一张 128x72 彩色测试图
3. 循环等待 PC 端发送 RGB888 图像
4. 接收后把原始 RGB 图像写入 BRAM
5. Sobel 运算由 PL 自动读取 BRAM 并完成
```

## 6. 串口配置

串口调试助手配置：

```text
端口号:  例如 COM7
波特率:  115200
数据位:  8
校验位:  None
停止位:  1
流控:    None
```

运行 PS 程序后，串口应看到：

```text
PS UART PL Sobel HDMI display
BRAM base: 0x40000000, baud: 115200, image: 128x72
waiting for frame header
```

`waiting for frame header` 表示板子正在等待 PC 端发送图像帧，是正常现象。

## 7. PC 端发送视频

PC 端继续使用：

```text
D:\Github\FPGA-course\zynq7020-image-processing\host_camera_uart
```

先进入 Anaconda 环境：

```bash
conda activate fpga
cd D:\Github\FPGA-course\zynq7020-image-processing\host_camera_uart
```

发送摄像头视频：

```bash
python camera_uart_sender.py --port COM7 --baud 115200 --camera 0 --fps 0.2 --preview
```

发送单张图片：

```bash
python camera_uart_sender.py --port COM7 --baud 115200 --image test.jpg --once --preview
```

如果出现串口错误或画面不稳定，可以增加行间延时：

```bash
python camera_uart_sender.py --port COM7 --baud 115200 --camera 0 --fps 0.2 --line-delay 0.001 --preview
```

注意：运行 Python 脚本前必须关闭串口调试助手，因为同一个 COM 口不能被两个程序同时打开。

## 8. 预期现象

只下载 bitstream 并运行 PS 程序后：

```text
串口显示 sobel_04 启动信息
HDMI 显示测试图经过 PL Sobel 后的边缘图
```

运行 PC 摄像头发送脚本后：

```text
串口打印 received frame 1、received frame 2 ...
HDMI 显示摄像头画面的 Sobel 边缘检测结果
```

画面是黑白边缘图，不再是彩色原图。

## 9. 帧率说明

当前 `115200` baud 下，一帧 `128 x 72 RGB888` 数据大约为：

```text
128 * 72 * 3 = 27648 byte
```

UART 8N1 的有效吞吐约为：

```text
115200 / 10 = 11520 byte/s
```

所以输入视频帧率仍然很低，推荐：

```text
--fps 0.2
```

PL 端 Sobel 运算本身很快，瓶颈主要是串口输入带宽。

## 10. 常见问题

### 10.1 串口没有 sobel_04 启动信息

检查：

```text
是否运行了 sobel_04 SDK 工作区里的 ps_uart_bram_app
是否重新 Build 了最新 main.c
是否下载了 sobel_04 的 bitstream
串口是否为 115200 8N1
COM 口是否正确
```

如果串口仍显示：

```text
PS UART BRAM HDMI display
```

说明你运行的还是 `sobel_03` 的旧 ELF。

### 10.2 HDMI 显示原图而不是边缘图

检查：

```text
Vivado 是否打开 sobel_04_uart_sobel_hdmi.xpr
hdmi_pl_top.v 中是否例化 hdmi_bram_sobel_display
工程 Sources 中是否包含 rgb_to_gray.v、sobel_core.v、hdmi_bram_sobel_display.v
是否重新 Generate Bitstream 并 Program FPGA
```

### 10.3 HDMI 黑屏

检查：

```text
显示器是否能识别 1280x720 HDMI 输入
video_clock 和 rgb2dvi_0 是否仍然存在
hdmi_out_test.xdc 是否启用
是否有 Vivado 综合/实现错误
```

如果串口正常、HDMI 黑屏，先回到 `sobel_03_uart_hdmi` 验证 HDMI 基线是否仍然正常。

### 10.4 画面边缘不明显

Sobel 输出取决于输入画面的亮度变化。如果画面过暗、过亮或背景太平，边缘会比较少。

可以测试：

```text
把摄像头对准有明显轮廓的物体
使用黑白反差明显的图片
打开 PC 端 --preview 确认输入图像正常
```

### 10.5 frame error

常见错误：

```text
frame error -1
    宽度、高度或格式不匹配

frame error -2
    行号不匹配，通常是串口数据丢失

frame error -5/-6/-7
    中途等待行头、行号或像素数据超时
```

处理方法：

```text
确认 --baud 115200
降低 --fps
增加 --line-delay 0.001
检查 USB 线和 COM 口
```

## 11. 第一周基础扩展

本实验的基础扩展围绕 PL Sobel 输出显示，控制在 1 个 Verilog 文件或 1 个参数对比实验内完成。学生至少完成 1 项，并把修改说明和 HDMI 现象写入初步实验报告。

| 选题 | 修改范围 | 验收标准 |
| --- | --- | --- |
| 固定阈值二值化边缘显示 | `hdmi_bram_sobel_display.v` 的 Sobel 输出到 RGB 映射 | HDMI 显示黑白二值边缘图，报告给出阈值 |
| 边缘反色显示 | `hdmi_bram_sobel_display.v` 的 RGB 输出映射 | 原黑底白边变成白底黑边，摄像头输入后仍能显示边缘 |
| 彩色边缘标记 | `hdmi_bram_sobel_display.v` 的 RGB 输出映射 | 边缘用红色、绿色或蓝色突出显示 |
| Sobel 阈值参数对比 | `hdmi_bram_sobel_display.v` 或 `sobel_core.v` 中的固定阈值常量 | 至少对比 3 个阈值下的 HDMI 效果，并记录资源利用率 |

本分支已实现 **彩色边缘标记** 扩展：`hdmi_bram_sobel_display.v` 新增参数
`EDGE_THRESHOLD`（默认 `8'd80`）与 `EDGE_COLOR`（默认 `24'h00ff00`，绿色）。
`edge_pixel >= EDGE_THRESHOLD` 的像素以 `EDGE_COLOR` 突出显示，其余为黑色；只改
`edge_pixel -> RGB` 显示映射，`edge_mem` 仍保存原始 8 bit Sobel 强度，不影响 BRAM 扫描、
`rgb_to_gray` 和 `sobel_core` 数据通路。换 `EDGE_COLOR` 为 `24'hff0000` / `24'h0000ff`
即可改红 / 蓝。离线另对比阈值 `40`、`80`、`120` 的边缘像素数（见
`coursework/evidence/05_uart_sobel/exp04_threshold_stats.txt`）。详见下文第 13 节。

## 12. 后续实验入口

`sobel_04` 是后续上位机控制实验的基础工程。完成本实验后，进入 `sobel_05_pc_control_display`，在本工程基础上继续完成：

1. 上位机控制 Sobel 二值化阈值。
2. 上位机控制边缘彩色叠加。
3. 上位机控制灰度图、边缘图和叠加图显示模式切换。

这些内容不再作为 `sobel_04` 的普通选做项，而是在 `sobel_05_pc_control_display` 中作为基础实验要求完成。

## 13. 远程开发结果与现场上板流程

### 13.1 当前状态

- 分支：`exp/04-uart-sobel`（从与 `origin/main` 一致的 `main` 创建）
- 工具：Vivado/XSim 2023.2、Vitis 2023.2、arm-none-eabi-gcc 12.2.0、host gcc 8.1.0、Python 3.11
- 器件：`xc7z020clg400-2`
- 基础扩展：彩色边缘标记，默认 `EDGE_THRESHOLD = 8'd80`、`EDGE_COLOR = 24'h00ff00`（绿色）
- 状态：远程协同仿真与构建通过，待现场上板验证

获取现场实际测试的提交号：

```powershell
git switch exp/04-uart-sobel
git pull --ff-only origin exp/04-uart-sobel
git rev-parse HEAD
```

### 13.2 远程已验证（不等于上板通过）

证据位于 `coursework/evidence/05_uart_sobel/`：

- 无板卡软硬件协同仿真链（`exp04_cosim.txt`）：真实 `camera_uart_sender.build_frame_packet`
  打包与本地编码器逐字节一致（27943 byte）；真实 `main.c receive_frame` 解析产出的原始
  RGB framebuffer 与 golden 逐像素一致（9216 word）；错误码 `-1/-2/-3/-5/-7` 与 `main.c` 一致；
  RTL 渲染 `1280x720` 帧（921600 像素）与软件 golden（gray + Sobel + 彩色边缘映射）逐像素一致。
- XSim 自检（`exp04_simulation.txt`）：显示映射、HDMI 时序、`sobel_done`、彩色边缘像素均通过。
- 综合 / 实现 / 时序 / DRC / bitstream（`exp04_remote_build.txt` 等）：`EXP04_BUILD=passed`，
  WNS `+13.453 ns`、TNS `0`、WHS `+0.058 ns`、THS `0`；`4446` LUT、`3662` FF、`18` BRAM36、
  `0` DSP、`1` MMCM；DRC `0` errors（`20` 个 REQP-1839 + `1` 个 CHECK-3 warning，已说明，不阻塞）。
- PS 源码检查（`exp04_ps_build.txt`）：`arm-none-eabi-gcc 12.2.0` 源码级编译 `main.c` 0 error、
  0 warning；完整 Vitis BSP/ELF 待正常 Vitis 环境（XSCT 无头超时）。

诚实边界：以上仅覆盖协议 / 格式 / 算法 / 显示映射与远程构建；真实 JTAG、UART、HDMI 物理输出、
DDR 与完整 Vitis ELF 必须现场验证，未收到真实照片与日志前不标记为"上板通过"。

### 13.3 所需硬件与接线

- 目标为 `xc7z020clg400-2` 的 ZYNQ7020 开发板、配套电源与 JTAG 下载线。
- USB 串口线（PS UART1，MIO48/49，`115200 8N1`）。
- HDMI 线和支持 `1280 x 720` 的显示器或采集设备。
- 拍摄 HDMI 画面与板卡接线的相机。

断电连接 JTAG、HDMI、USB 串口和电源；HDMI 接显示器输入并选对输入源；上电后确认
Hardware Manager 能识别目标器件，确认设备管理器中开发板的 COM 口。

### 13.4 用户侧构建

命令行（本目录，全局综合，可删除重建）：

```powershell
& D:\Vivado\Vivado\2023.2\bin\vivado.bat -mode batch -nojournal -nolog -source run_exp04_bitstream.tcl
```

生成（不提交 Git）：`build\vivado_2023_2\top.bit` 与 `build\vivado_2023_2\ps_uart_bram_hdmi.xsa`。

Vivado GUI 查看：`File -> Open Project` 打开 `build\vivado_2023_2\exp04_build.xpr`，在
`Open Implemented Design` 中查看 Report Timing Summary / Utilization / DRC。原始 2017.4 XPR
只作基线，不要直接升级或覆盖。

PS 程序（正常 Vitis 2023.2 环境）：

```powershell
& D:\Vivado\Vitis\2023.2\bin\xsct.bat build_exp04_ps_app.tcl
```

或在 Vitis GUI 中用 `ps_uart_bram_hdmi.xsa` 新建 platform / standalone domain / BSP，新建空应用并
复制 `ps_uart_sobel_bram_app/src/main.c` 后编译。

### 13.5 下载与运行

1. 打开 Hardware Manager → Open Target → Auto Connect，确认识别到 Zynq-7020。
2. Program Device，bitstream 指向 `build\vivado_2023_2\top.bit`。
3. 运行 `ps_uart_bram_app`，串口（`115200 8N1`）应打印：

```text
PS UART PL Sobel HDMI display
BRAM base: 0x40000000, baud: 115200, image: 128x72
waiting for frame header
```

4. 关闭串口调试助手（同一 COM 口不能被两个程序占用），用上位机发送图片：

```powershell
conda activate fpga
cd ..\host_camera_uart
python camera_uart_sender.py --port COM7 --baud 115200 --image test.jpg --once --preview
python camera_uart_sender.py --port COM7 --baud 115200 --camera 0 --fps 0.2 --preview
```

不稳定时增加 `--line-delay 0.001`。

### 13.6 预期现象

- 只下载 bitstream + 运行 PS：HDMI 显示内置测试图经 PL Sobel 后的彩色边缘（默认绿色边缘、黑色背景）。
- 发送图片后：串口打印 `received frame 1/2/...`，HDMI 显示输入图像的绿色 Sobel 边缘（背景黑）。

### 13.7 阈值与边缘颜色调整

- `EDGE_THRESHOLD`（默认 `80`）控制判定为边缘的强度门限，越高边缘越少。
- `EDGE_COLOR`（默认 `24'h00ff00`）控制边缘颜色，可改 `24'hff0000`（红）/`24'h0000ff`（蓝）。
- 离线阈值对比图与统计：`coursework/evidence/05_uart_sobel/exp04_edge_threshold_{40,80,120}.png`
  与 `exp04_threshold_stats.txt`（边缘像素数随阈值升高单调不增加）。
- 现场如需对比阈值，修改参数后重新生成 bitstream，分别拍照记录。

### 13.8 通过标准

1. 显示器稳定识别 `1280 x 720`，连续保持至少 30 秒。
2. 画面为黑色背景上的彩色（默认绿色）Sobel 边缘，对准有明显轮廓的物体边缘清晰。
3. 串口能持续打印 `received frame N`，画面随输入更新（低帧率属设计限制，UART 带宽约 11520 byte/s）。
4. Program Device、板卡型号、Vivado/Vitis 版本与实际提交号均有记录。

收到真实 HDMI 照片与现场日志前，本实验不标记为"上板通过"。

### 13.9 失败排查顺序

1. 串口无 `PS UART PL Sobel HDMI display`：确认运行的是 sobel_04 的 ELF、COM 口与 `115200 8N1`、
   bitstream 为 sobel_04；若打印 `PS UART BRAM HDMI display` 说明跑的是 sobel_03 旧 ELF。
2. HDMI 黑屏：先回归 `sobel_03_uart_hdmi` 验证 HDMI 基线；检查显示器是否支持 720p、`video_clock`
   与 `rgb2dvi_0`、`hdmi_out_test.xdc`、`video_locked` 与 `sobel_done`。
3. 显示原图而非边缘：确认 `hdmi_pl_top.v` 例化 `hdmi_bram_sobel_display`、工程含 `rgb_to_gray.v`/
   `sobel_core.v`、已重新 Generate Bitstream 并 Program。
4. 边缘不明显：对准黑白反差明显的物体，必要时调低 `EDGE_THRESHOLD`。
5. `frame error -1/-2/-5/-6/-7`：核对 `--baud 115200`、宽高 `128x72`、降低 `--fps`、加 `--line-delay`。
6. Program Device 失败：保存 Hardware Manager 完整错误，不要只记录最后一行。

### 13.10 现场必须回传

- 实际分支和完整提交号、测试日期、板卡型号、Vivado/Vitis 版本、COM 口、显示设备型号。
- Hardware Manager 识别目标与 Program Device 成功截图或完整日志。
- PS 串口启动信息与 `received frame` 完整文本。
- HDMI 显示彩色 Sobel 边缘的照片（含分辨率信息），以及一张能确认板卡 / JTAG / HDMI / USB 串口接线的照片。
- 若做了阈值或边缘颜色对比：各参数下的 HDMI 照片。
- 现场 utilization、timing summary 与 DRC 摘要。
- 若失败：失败步骤、完整错误文本和最后一个正常现象。


# sobel_05_pc_control_display 实验说明

本实验在 `sobel_04_uart_sobel_hdmi` 的基础上，增加“上位机控制显示”的能力。PC 端通过串口发送控制命令，PS 端解析命令并写入控制字，PL 端根据控制字改变 HDMI 显示效果。

本实验不是普通可选扩展，而是第二周综合扩展的基础平台。学生需要先完成以下上位机控制显示能力，再在主目录 README 中选择 1 个综合扩展任务继续完成：

1. Sobel 二值化阈值控制。
2. 边缘彩色叠加显示控制。
3. 灰度图 / 边缘图 / 叠加图显示模式切换。

本实验不要求学生修改 PC 端 GUI。`host_camera_uart` 中的统一上位机已经兼容本实验：前面实验仍然使用图像发送功能，本实验额外使用显示控制功能。

## 1. 实验目标

完成本实验后，学生应能说明：

1. 图像数据和控制命令如何区分。
2. PS 端如何把上位机命令转换为控制字。
3. PL 端如何根据控制字选择 HDMI 显示模式。
4. PL 端如何根据阈值控制 Sobel 二值化边缘。
5. PL 端如何把边缘用彩色叠加到原图上。
6. 为什么控制功能要先仿真，再上板验证。

## 2. 数据流

```text
PC 图片 / 摄像头
    -> UART 图像帧
    -> PS 写入 AXI BRAM 图像区
    -> PL 读取图像并完成灰度转换和 Sobel
    -> HDMI 显示

PC 控制命令
    -> UART 命令
    -> PS 解析命令
    -> PS 写入 AXI BRAM 控制字
    -> PL 读取控制字
    -> 切换显示模式、阈值和彩色叠加开关
```

建议把 BRAM 分成两个区域：

```text
0x40000000 + 0x0000
    图像 framebuffer，128 x 72，每像素 32 bit，格式 0x00RRGGBB

0x40000000 + 0x9000
    控制字区域，例如 display_mode、threshold、overlay_enable
```

控制字地址只是建议。实际工程中必须确认 BRAM 空间足够，并且控制字地址不与图像区冲突。

## 3. 控制命令

本实验使用固定二进制控制帧，避免和图像二进制数据混淆：

```text
control frame: a5 5a cmd value
```

命令定义：

```text
cmd = 01
    value = 0: 原图
    value = 1: 灰度图
    value = 2: Sobel 二值化边缘图
    value = 3: 原图 + 彩色边缘叠加

cmd = 02
    value = 0..255: Sobel 二值化阈值

cmd = 03
    value = 0: 关闭彩色边缘叠加
    value = 1: 打开彩色边缘叠加
```

命令行上位机示例：

```bash
python camera_uart_sender.py --port COM7 --baud 115200 --control-only --mode edge --threshold 80 --overlay off
python camera_uart_sender.py --port COM7 --baud 115200 --control-only --mode overlay --threshold 40 --overlay on
```

GUI 上位机中使用 `Display control for sobel_05` 区域设置 `Mode`、`Threshold` 和 `Overlay`，点击 `Send Control` 即可发送控制帧。

## 4. 控制字设计

本实验至少需要 3 个控制字：

```text
display_mode
    0: 原图
    1: 灰度图
    2: Sobel 二值化边缘图
    3: 原图 + 彩色边缘叠加

threshold
    Sobel 二值化阈值，建议初始值 80

overlay_enable
    0: 关闭彩色边缘叠加
    1: 打开彩色边缘叠加
```

PS 端负责写控制字，PL 端负责读取控制字并改变 HDMI 输出。

## 5. 主要修改范围

本实验从 `sobel_04_uart_sobel_hdmi` 派生工程，主要修改：

```text
PS 端 main.c
    增加控制命令解析
    增加 display_mode、threshold、overlay_enable 写入
    增加命令回显，打印当前控制状态

hdmi_bram_sobel_display.v
    增加控制字读取
    增加灰度图、边缘图、彩色叠加图输出选择
    增加 Sobel 阈值判断

仿真 testbench
    构造不同控制字
    验证不同模式、阈值和叠加开关下的 RGB 输出
```

不建议第一版同时修改 PC GUI、提高波特率或引入网络传输。

## 6. SDK 工程

本实验需要 PS 端 SDK 程序。当前目录已经包含完整 SDK 工作区：

```text
sobel_05_pc_control_display.sdk/
    top_hw_platform_0/
    ps_uart_control_bram_app_bsp/
    ps_uart_control_bram_app/
```

SDK 中真正要运行的应用工程是：

```text
sobel_05_pc_control_display.sdk/ps_uart_control_bram_app
```

应用源码位置：

```text
sobel_05_pc_control_display.sdk/ps_uart_control_bram_app/src/main.c
```

已经编译生成的 ELF 位置：

```text
sobel_05_pc_control_display.sdk/ps_uart_control_bram_app/Debug/ps_uart_control_bram_app.elf
```

外层目录：

```text
ps_uart_control_bram_app/src/main.c
```

是源码备份和重建 SDK 工程时的导入来源，不是 SDK GUI 中直接打开的工程。

如果 SDK 工程丢失，或 SDK 中只剩下 `top_hw_platform_0` 而没有应用工程，可以在本目录运行：

```bash
xsct rebuild_sdk_workspace.tcl
```

Windows 下如果 `xsct` 没有加入 PATH，可以运行：

```powershell
& 'C:\Xilinx\SDK\2017.4\bin\xsct.bat' rebuild_sdk_workspace.tcl
```

不要删除：

```text
sobel_05_pc_control_display.sdk/top_hw_platform_0
sobel_05_pc_control_display.sdk/ps_uart_control_bram_app_bsp
sobel_05_pc_control_display.sdk/ps_uart_control_bram_app
sobel_05_pc_control_display.sdk/top.hdf
ps_uart_control_bram_app
rebuild_sdk_workspace.tcl
```

其中 `top_hw_platform_0` 是硬件平台，`ps_uart_control_bram_app_bsp` 是 BSP，`ps_uart_control_bram_app` 是要下载运行的 PS 程序。SDK 自动生成 `top_hw_platform_1` 通常是重复导入硬件平台导致的；正常使用本目录已有的 `top_hw_platform_0` 即可。

## 7. 实验步骤

### 7.1 先复现 sobel_04

先完成 `sobel_04_uart_sobel_hdmi`，确认：

```text
PS 程序能接收 PC 图像
PL Sobel 能显示边缘图
HDMI 输出稳定
```

如果 `sobel_04` 没有跑通，不建议直接做本实验。

### 7.2 完成控制逻辑仿真

仿真必须先于上板完成。至少验证：

1. `display_mode = 1` 时输出灰度图。
2. `display_mode = 2` 时输出 Sobel 二值化边缘图。
3. `display_mode = 3` 或 `overlay_enable = 1` 时输出原图叠加彩色边缘。
4. 改变 `threshold` 后，边缘输出数量或边缘强度发生变化。

仿真可以使用固定像素输入，不要求完整模拟 UART 图像发送。报告中必须给出模式切换、阈值变化和叠加开关的波形或输出截图。

本目录提供了一个轻量级显示控制仿真：

```text
sim/display_control_model.v
sim/display_control_model_tb.v
```

命令行运行：

```bash
iverilog -g2012 -o sim/display_control_model_tb.vvp sim/display_control_model.v sim/display_control_model_tb.v
vvp sim/display_control_model_tb.vvp
```

该仿真只验证显示模式、阈值和叠加输出选择，不替代完整 Vivado 上板验证。

### 7.3 修改 PS 程序

在 PS 端 `main.c` 中增加命令解析，至少支持：

```text
a5 5a 01 mode
a5 5a 02 threshold
a5 5a 03 overlay_enable
```

PS 收到命令后，将控制值写入 BRAM 控制字区域，并通过串口回显当前状态。

### 7.4 修改 PL 显示逻辑

在 `hdmi_bram_sobel_display.v` 中增加显示模式选择：

```text
mode = 0
    输出原始 RGB

mode = 1
    输出灰度图

mode = 2
    输出 Sobel 二值化边缘图

mode = 3
    输出原图 + 彩色边缘叠加
```

阈值判断建议先做成简单逻辑：

```text
edge_bin = (edge_data >= threshold) ? 8'hff : 8'h00
```

彩色叠加建议先使用固定颜色，例如红色边缘：

```text
if (edge_bin)
    RGB = red
else
    RGB = original_rgb
```

### 7.5 上板验证

上板时建议流程：

1. 下载 bitstream。
2. 运行 PS 程序。
3. 用 PC 端工具发送图像。
4. 在 GUI 的 `Display control for sobel_05` 区域选择 `gray`，点击 `Send Control`，观察灰度图。
5. 选择 `edge`，观察 Sobel 二值化边缘图。
6. 选择 `overlay` 或勾选 `Overlay`，观察彩色边缘叠加图。
7. 分别设置阈值 `40`、`80`、`120`，比较阈值变化效果。

注意：同一个 COM 口不能同时被两个不同程序占用。GUI 连续发送图像时，可以直接在同一个 GUI 中修改 `Mode`、`Threshold`、`Overlay` 并点击 `Send Control`；控制帧会通过当前发送线程排队发出。

## 8. 验收标准

基础验收必须完成：

1. PC 命令能切换灰度图、Sobel 二值化边缘图、彩色边缘叠加图。
2. PC 命令能设置 Sobel 阈值，并能观察边缘效果变化。
3. PC 命令能打开或关闭彩色边缘叠加。
4. PS 串口能回显当前模式、阈值和叠加状态。
5. 提交控制逻辑仿真截图或波形截图。
6. 提交 HDMI 模式切换照片或视频截图。
7. 提交 Vivado 资源利用率和时序结果。

## 9. 报告要求

报告中至少说明：

1. 上位机命令格式。
2. PS 端命令解析流程。
3. 控制字地址和含义。
4. PL 端模式选择、阈值判断和彩色叠加逻辑。
5. 仿真结果。
6. 上板结果。
7. 与 `sobel_04` 基础边缘图的效果对比。

## 10. 后续扩展建议

完成本实验后，如果还需要进一步提高，可以选择：

| 选题 | 仿真要求 | 上板验收 |
| --- | --- | --- |
| 命令协议增强 | 验证错误命令不会破坏图像接收 | 错误命令能被忽略，合法命令稳定控制显示 |
| 更多显示模式 | 验证新增模式的 RGB 输出 | PC 命令可切换更多显示效果 |
| 阈值状态统计 | 仿真或软件测试边缘像素统计 | 串口能输出当前阈值和边缘像素数量 |

不建议把网络摄像头、DMA、Ethernet 或 PC GUI 修改作为本实验的基础要求。

## 11. 常见问题

### 11.1 命令和图像发送冲突

同一个串口不能同时被两个 PC 程序打开。使用 GUI 时，图像发送和控制命令已经集成在同一个程序中；不要再同时打开串口调试助手。

### 11.2 HDMI 模式没有变化

检查：

```text
PS 是否正确收到命令
PS 是否把控制字写入正确 BRAM 地址
PL 是否读取了控制字
显示模式选择逻辑是否接入 RGB 输出
bitstream 是否重新生成并下载
```

### 11.3 阈值命令没有效果

检查 Sobel 输出是否经过阈值判断。如果只是把 `edge_data` 直接复制到 RGB，阈值控制不会改变显示结果。

## 12. 远程开发结果与现场上板流程

> 本节由无板卡远程开发阶段补充，记录已在远程通过的检查与待现场完成的验证。
> 严格区分“协同仿真 / 构建通过”与“上板通过”。

### 12.1 远程开发结果（`exp/05-pc-control` 分支）

- 工具：Vivado/XSim 2023.2、Vitis 2023.2、arm-none-eabi-gcc 12.2.0、host gcc、Python 3.11；器件 `xc7z020clg400-2`。
- 既有实现核对（未重写）：PC（`camera_uart_sender.send_control_command` / `send_requested_controls` 发 `A5 5A cmd value`）、PS（`main.c` 用 `wait_for_packet_start` 分发图像帧/控制帧、`handle_control_packet` 写控制字）、PL（`hdmi_bram_sobel_display.v` 每帧先读 3 个控制字再扫描、四模式显示 mux）均完整正确。
- 无板卡协同仿真链 `EXP05_COSIM_CHAIN=passed`：真实上位机图像打包(27943B)+控制帧(12B)与本地编码器逐字节一致；真实 `main.c` 分发产出图像区(9216 word)与 golden 一致、控制字 `0x9000/4/8` 与下发(mode=3/thr=40/overlay=1)一致；6 个错误注入返回码与 `main.c` 一致；XSim 自检 `EXP05_SELFCHECK_TB=passed`；全分辨率渲染对 mode=0/1/2/3、阈值 40/80/120、overlay=0/1 共 7 组逐像素比对一致（右下角单像素边界伪影已说明）。
- 全局构建 `EXP05_BUILD=passed`：综合/实现/bitstream 通过；WNS=0.325 ns、TNS=0、WHS=0.043 ns、THS=0；DRC 0 violations；10795 LUT / 4113 FF / 20 BRAM / 0 DSP / 1 MMCM；导出 `ps_uart_bram_hdmi.xsa`。
- PS 源码检查：`arm-none-eabi-gcc -c -Wall -Wextra` 0 error / 0 warning。
- 证据目录：`coursework/evidence/06_pc_control/`。复现命令见 12.4。

### 12.2 控制字地图（数据流契约，勿改语义）

```text
PC 图像/控制 --UART--> PS(main.c) --AXI--> BRAM --PortB--> PL(hdmi_bram_sobel_display) --> HDMI
  图像帧 55 AA w_l w_h h_l h_h 18 + 每行(33 CC row_l row_h + 128x RGB)  -> 图像区
  控制帧 A5 5A cmd value (cmd=1 mode / 2 threshold / 3 overlay)         -> 控制字
```

| BRAM 字节地址 | 字索引 | 名称 | 含义 | 位宽 |
| --- | --- | --- | --- | --- |
| `0x0000`..`0x8FFC` | 0..9215 | 图像区 framebuffer | 128x72，每像素 `0x00RRGGBB` | 24 (存于 32) |
| `0x9000` | 9216 | `display_mode` | 0 原图 / 1 灰度 / 2 边缘 / 3 叠加 | 2 bit |
| `0x9004` | 9217 | `threshold` | Sobel 二值化阈值 0..255 | 8 bit |
| `0x9008` | 9218 | `overlay_enable` | 0 关 / 1 开 彩色边缘叠加 | 1 bit |

图像区最后一像素地址 `0x8FFC`，与控制区不重叠，均在 64KB BRAM 内。复位 / 上电默认 mode=2(边缘) / thr=80 / overlay=0。彩色叠加固定红色 `0xff2020`：非边缘模式下 `overlay_enable=1` 或 `mode=3` 时，`edge_pixel>=threshold` 处涂红。

### 12.3 现场上板流程

硬件：黑金 ZYNQ7020 开发板、HDMI 显示器、USB 串口线、JTAG。

1. 分支与提交号：`exp/05-pc-control`；提交号以现场 `git log -1` 为准。
2. 接线：JTAG-USB、HDMI 接显示器、USB 串口（PS UART1，MIO48/49，115200 8N1）。
3. 用户侧构建（正常 Vivado/Vitis 2023.2 环境）：
   - bitstream：`vivado -mode batch -source run_exp05_bitstream.tcl`（路径过深时设 `EXP05_BUILD_DIR` 为短路径）。
   - PS ELF：`xsct build_exp05_ps_app.tcl`（依赖上一步导出的 XSA）；或用现有 `.sdk` 工作区（见 §6）。
4. 下载 bitstream：Hardware Manager → Open Target → Program Device（`top.bit`）。
5. 运行 PS：下载并运行 `ps_uart_control_bram_app.elf`；串口应打印横幅 `PS UART PL Control HDMI display` 与初始 `control: mode=2 threshold=80 overlay=0`。
6. 上位机发图：`python camera_uart_sender.py --port COMx --baud 115200 --image <图片> --once`。
7. 上位机控制（CLI 任选，或 GUI 的 `Display control for sobel_05`）：
   - `... --control-only --mode gray` / `--mode edge --threshold 80`（可换 40/120）/ `--mode overlay`
   - `... --control-only --overlay on`（在当前模式叠加红边）/ `--overlay off`
8. 预期现象：
   - 串口：每条控制命令回显 `control: mode=.. threshold=.. overlay=..`；收图回显 `received frame N`。
   - HDMI：mode=0 原图；mode=1 灰度；mode=2 黑白边缘（阈值越大白边越少）；mode=3 或 overlay 开 在原图上叠加红色边缘。
9. 通过标准：四模式切换正确、阈值改变边缘数量、红边叠加可开关、串口回显与设置一致、图像与控制命令不冲突。
10. 失败时保存：完整串口文本、各模式 HDMI 照片、Vivado 资源/时序/DRC、上位机日志、最后一个正常现象。
11. 回传清单：见 `coursework/evidence/06_pc_control/README.md` 的“待现场回传”。

### 12.4 远程复现命令

```bash
# 协同仿真链（含全分辨率逐配置渲染比对）
bash tools/cosim/run_exp05_cosim.sh
# 仅逻辑层（跳过较慢的全分辨率渲染）
EXP05_COSIM_QUICK=1 bash tools/cosim/run_exp05_cosim.sh
# 预期画面与协议自检
python tools/generate_exp05_expected.py --evidence-dir <evid_dir> --hex-output <hex>
# 全局综合/实现/bitstream（路径过深时设短 build dir）
EXP05_BUILD_DIR=D:/codex_prj/x5b vivado -mode batch -source run_exp05_bitstream.tcl
# PS 源码检查
arm-none-eabi-gcc -c -Wall -Wextra -mcpu=cortex-a9 -I tools/ps_syntax_check/include \
    ps_uart_control_bram_app/src/main.c -o main.o
```

### 12.5 第二周综合大拓展扩展点（当前不开工，待方向确认）

本工程是第二周综合大拓展的基础平台，已留干净扩展点；扩展时保持 12.2 的图像区 / 控制字地址语义不变：

- **选项 1（推荐主线）上位机输入与缩放策略**：仅改 `host_camera_uart`（把 `cv2.resize` 抽成可复用 `prepare_frame()`，加 `--fit-mode` stretch/letterbox/center-crop），FPGA 端 128x72 链路完全不动。
- **选项 2 网络传输（lwIP）**：在 PS 侧新增网络接收并写同一 BRAM 图像区，PL / HDMI / 控制字链路保持不变。
- **选项 3 新增 PL 算法（Prewitt/Laplacian/滤波）**：`display_mode` 现为 2 bit（4 模式已满）、`cmd=1` 的 `value&0x03` 也限 2 bit。新增算法/模式需在两处扩展：(a) `hdmi_bram_sobel_display.v` 显示 mux 组合块（`case (display_mode)` 处新增分支并并联新算法核），(b) 控制协议（把 `display_mode` 扩宽到 3 bit，或新增 `cmd=4` 选择算法）。

# sobel_02_hdmi_sobel 实验说明

本实验在 `sobel_01_hdmi_pattern` 的 HDMI 固定图片显示基础上，加入灰度转换和 Sobel 边缘检测。输入仍然来自 `128 x 72` 固定图片 ROM，PL 端完成图像处理后把边缘结果放大显示到 `1280 x 720` HDMI 画面。

## 1. 实验目标

完成本实验后，学生应能说明：

1. RGB888 图像如何转换为 8 bit 灰度。
2. Sobel 卷积如何输出边缘强度。
3. `edge_mem` 为什么用于保存一帧边缘结果。
4. 固定图片 Sobel 结果如何通过 HDMI 输出。

## 2. 数据流

```text
image_rom_128x72
    -> rgb_to_gray
    -> sobel_core
    -> edge_mem
    -> hdmi_sobel_display
    -> rgb2dvi_0
    -> HDMI 显示器
```

显示关系：

```text
输入图片: 128 x 72 RGB888
Sobel 输出: 128 x 72 8 bit edge
HDMI 输出: 1280 x 720
缩放倍数: 10 x 10
```

## 3. 主要文件

```text
sobel_02_hdmi_sobel.xpr
    Vivado 工程

add_sobel_sources.tcl
    向工程加入 Sobel 相关源码的 Tcl 脚本

sobel_02_hdmi_sobel.srcs/sources_1/new/top.v
    工程顶层

sobel_02_hdmi_sobel.srcs/sources_1/new/hdmi_sobel_display.v
    读取固定图片，驱动灰度转换、Sobel 和 HDMI 显示

sobel_02_hdmi_sobel.srcs/sources_1/new/rgb_to_gray.v
    RGB888 转灰度模块

sobel_02_hdmi_sobel.srcs/sources_1/new/sobel_core.v
    Sobel 卷积核心

sobel_02_hdmi_sobel.srcs/sources_1/new/image_rom_128x72.v
    固定图片 ROM

sobel_02_hdmi_sobel.srcs/constrs_1/new/hdmi_out_test.xdc
    HDMI 管脚约束
```

上一级目录中的 `../hdmi_common` 是 Sobel 系列工程共用的 HDMI 基础依赖目录，不能删除。

## 4. 实验步骤

### 4.1 打开 Vivado 工程

打开工程：

```text
D:\Github\FPGA-course\zynq7020-image-processing\sobel_02_hdmi_sobel\sobel_02_hdmi_sobel.xpr
```

确认 Sources 中包含：

```text
top.v
hdmi_sobel_display.v
rgb_to_gray.v
sobel_core.v
image_rom_128x72.v
video_clock
rgb2dvi_0
hdmi_out_test.xdc
```

如果 Sobel 相关源码没有加入工程，可在 Vivado Tcl Console 中执行：

```tcl
cd D:/Github/FPGA-course/zynq7020-image-processing/sobel_02_hdmi_sobel
source add_sobel_sources.tcl
```

### 4.2 检查顶层模块

确认 Vivado 顶层为：

```text
top
```

如果顶层不正确，在 Sources 中右键 `top.v`，选择 `Set as Top`。

### 4.3 观察关键代码

打开 `hdmi_sobel_display.v`，重点观察：

```text
ST_IDLE
ST_RUN
ST_WAIT
ST_DISPLAY
```

这几个状态完成固定图片扫描、灰度转换、Sobel 处理和 HDMI 显示。

继续观察：

```text
rgb_to_gray u_rgb_to_gray
sobel_core u_sobel_core
edge_mem
```

报告中应说明 `edge_valid` 有效时如何把 `edge_data` 写入 `edge_mem`。

### 4.4 综合、实现和生成 bitstream

在 Vivado 中依次执行：

```text
Run Synthesis
Run Implementation
Generate Bitstream
```

生成 bitstream 后，查看资源利用率和时序结果。

### 4.5 下载到开发板

连接开发板、HDMI 显示器和 JTAG，执行：

```text
Open Hardware Manager
Open Target
Program Device
```

选择本工程生成的 `top.bit`。

### 4.6 记录实验现象

预期现象：

```text
HDMI 显示器输出固定图片的 Sobel 边缘检测结果
画面为黑白灰度边缘图
```

需要保存：

1. HDMI Sobel 显示照片。
2. Vivado 资源利用率截图。
3. Vivado 时序结果截图。
4. `hdmi_sobel_display.v` 中关键数据流说明。

## 5. 验收标准

基础实验验收时应能说明：

1. `rgb_to_gray` 的输入输出信号。
2. `sobel_core` 的输入输出信号。
3. `edge_mem` 的写入和读取时机。
4. Sobel 输出如何映射为 HDMI 的 `R/G/B` 三个通道。

## 6. 常见问题

### 6.1 HDMI 显示全黑

检查：

```text
sobel_done 是否最终置 1
edge_mem 是否有写入
rgb_to_gray.v 和 sobel_core.v 是否已加入工程
是否重新 Generate Bitstream
```

### 6.2 显示器无信号

先回到 `sobel_01_hdmi_pattern` 验证 HDMI 基础链路。如果 `sobel_01` 正常，再检查本工程的顶层和约束。

### 6.3 边缘效果不明显

Sobel 输出取决于输入图片内容。可以对比 `sobel_00_rtl_sim` 的输出图，判断是算法效果问题还是 HDMI 显示问题。

## 7. 可选扩展

本实验的扩展应控制在 1 个 Verilog 文件或 1 个参数实验内，属于第一周基础扩展。学生至少完成 1 项，并把修改说明和 HDMI 现象写入初步实验报告。

| 选题 | 修改范围 | 验收标准 |
| --- | --- | --- |
| 固定阈值二值化边缘显示 | `hdmi_sobel_display.v` 中 Sobel 输出到 RGB 的映射 | HDMI 显示黑白二值边缘图，报告给出所用阈值 |
| 边缘反色显示 | `hdmi_sobel_display.v` 的 RGB 输出映射 | 原黑底白边变成白底黑边，报告说明映射关系 |
| 彩色边缘标记 | `hdmi_sobel_display.v` 的 RGB 输出映射 | 边缘使用红色、绿色或蓝色突出显示 |
| Sobel 阈值参数对比 | `hdmi_sobel_display.v` 或 `sobel_core.v` 中的固定阈值常量 | 至少对比 3 个阈值下的 HDMI 显示效果 |

不建议在本实验中加入 UART、PS 软件、网络传输或 GUI 修改。本实验重点是固定图片条件下的 PL 图像处理链路。

## 8. 远程开发结果与现场上板流程

### 8.1 当前状态

- 分支：`exp/02-hdmi-sobel`
- 基线：从与 `origin/main` 一致的 `main` 创建
- 工具：Vivado/XSim 2023.2
- 器件：`xc7z020clg400-2`
- 状态：远程仿真、综合、实现、时序、DRC 和 bitstream 生成通过；真实 HDMI 上板待现场验证
- 默认显示阈值：`EDGE_THRESHOLD = 8'd80`

获取现场实际测试的提交号：

```powershell
git switch exp/02-hdmi-sobel
git pull --ff-only origin exp/02-hdmi-sobel
git rev-parse HEAD
```

### 8.2 已验证的数据链

```text
128 x 72 RGB888 ROM
  -> rgb_to_gray
  -> sobel_core
  -> 8 bit edge_mem
  -> edge_pixel >= 80 ? white : black
  -> 10 x 10 scaling
  -> 1280 x 720 HDMI
```

阈值只影响 HDMI 显示映射，`edge_mem` 始终保存原始 8 bit Sobel 强度。

XSim 自检覆盖：

1. 全部 `9216` 个 RGB 转灰度结果。
2. 全部 `9216` 个 Sobel 坐标、数值和 `edge_mem` 写入次数。
3. 边界像素处理和唯一一次 `edge_frame_done`。
4. HDMI 有效像素数、HS/VS 脉宽和缩放地址。
5. 阈值 80 时 RGB 只能为 `24'h000000` 或 `24'hffffff`。

### 8.3 命令行复现

在本目录执行：

```powershell
& D:\Vivado\Vivado\2023.2\bin\vivado.bat -mode batch -nojournal -nolog -source run_exp02_sim.tcl
& D:\Vivado\Vivado\2023.2\bin\vivado.bat -mode batch -nojournal -nolog -source run_exp02_bitstream.tcl
```

第二条命令生成但不提交：

```text
build/vivado_2023_2/top.bit
```

若独立 Python 不在 `D:\Miniconda3\python.exe`，运行仿真前设置：

```powershell
$env:EXP02_PYTHON = "C:\path\to\python.exe"
```

Vivado GUI 查看方法：

1. 打开 Vivado 2023.2。
2. `File -> Open Project`，选择 `build/vivado_2023_2/exp02_build.xpr`。
3. 在 `Open Implemented Design` 中查看 `Report Timing Summary`、`Report Utilization` 和 `Report DRC`。
4. 原始 2017.4 XPR 只作为基线，不要直接升级或覆盖。

### 8.4 硬件与接线

需要：

- 目标为 `xc7z020clg400-2` 的 ZYNQ7020 开发板。
- 与板卡匹配的电源和 JTAG 下载线。
- HDMI 线和支持 `1280 x 720` 的显示器或采集设备。
- 用于拍摄显示器和板卡连接状态的相机。

接线顺序：

1. 断电连接 JTAG、HDMI 和板卡电源。
2. HDMI 连接开发板输出端与显示器输入端。
3. 选择正确的 HDMI 输入源，再给开发板上电。
4. 确认 JTAG 能在 Hardware Manager 中识别目标器件。

本实验没有 PS 程序、串口或上位机步骤。

### 8.5 Program Device

1. 完成上面的 bitstream 构建。
2. 打开 `Hardware Manager`。
3. 选择 `Open Target -> Auto Connect`。
4. 确认识别到正确的 Zynq-7020 器件。
5. 选择 `Program Device`。
6. Bitstream 指向 `build/vivado_2023_2/top.bit`。
7. 点击 `Program`，保存成功日志或截图。

### 8.6 预期画面与通过标准

预期画面为黑底白边的固定图片 Sobel 二值图，默认阈值为 80。现场画面应与
`coursework/evidence/03_hdmi_sobel/exp02_threshold_80.png` 的结构一致。

通过标准：

1. 显示器稳定识别 `1280 x 720`，连续保持至少 30 秒。
2. 画面无滚动、周期性闪烁、撕裂或明显错行。
3. 输出只有黑色背景和白色边缘。
4. 边缘位置与阈值 80 预期图一致。
5. Program Device、板卡型号、Vivado 版本和实际提交号均有记录。

在收到真实 HDMI 照片前，不得把本实验标记为“上板通过”。

### 8.7 失败排查顺序

1. 无信号：先回归 `sobel_01_hdmi_pattern`，确认 HDMI 时钟、TMDS 和显示器输入源。
2. 全黑：检查 `video_locked`、`sobel_done`、`edge_frame_done` 和 `edge_mem` 写入。
3. 图像错位：检查显示器是否为 720p，并核对 `de`、HS/VS 和 BRAM 读延迟。
4. 边缘不一致：核对实际提交号、默认阈值 80，并重新运行 XSim。
5. Program Device 失败：保存 Hardware Manager 完整错误，不要只记录最后一行。

### 8.8 现场必须回传

- 实际分支和完整提交号。
- 测试日期、板卡型号、Vivado 版本和显示器/采集设备型号。
- Hardware Manager 识别目标和 Program Device 成功截图或完整日志。
- 同时包含有效画面、分辨率信息的 HDMI 照片。
- 一张能确认板卡、JTAG 和 HDMI 接线的照片。
- 现场 utilization、timing summary 和 DRC 摘要。
- 若失败：失败步骤、完整错误文本和最后一个正常现象。

# sobel_01_hdmi_pattern 实验说明

本实验验证 ZYNQ7020 开发板的 HDMI 输出链路。工程把一张 `128 x 72` RGB 图片存放在 Verilog ROM 中，并放大 10 倍显示到 `1280 x 720` HDMI 画面。

## 1. 实验目标

完成本实验后，学生应能说明：

1. HDMI 720p 显示时序的基本参数。
2. `video_clock` 和 `rgb2dvi_0` IP 的作用。
3. `128 x 72` 图片如何映射到 `1280 x 720` 显示区域。
4. Verilog ROM 中 `24'hRRGGBB` 像素数据的含义。

## 2. 数据流

```text
image_rom_128x72
    -> hdmi_image_display
    -> rgb2dvi_0
    -> HDMI 显示器
```

显示关系：

```text
输入图片: 128 x 72
HDMI 输出: 1280 x 720
缩放倍数: 10 x 10
```

## 3. 主要文件

```text
sobel_01_hdmi_pattern.xpr
    Vivado 工程

sobel_01_hdmi_pattern.srcs/sources_1/new/top.v
    工程顶层，连接 video_clock、显示逻辑和 rgb2dvi_0

sobel_01_hdmi_pattern.srcs/sources_1/new/hdmi_image_display.v
    产生 1280x720 时序，读取 128x72 ROM 图片并放大显示

sobel_01_hdmi_pattern.srcs/constrs_1/new/hdmi_out_test.xdc
    HDMI 管脚约束
```

上一级目录中的 `../hdmi_common` 是 Sobel 系列工程共用的 HDMI 基础依赖目录，不能删除。删除后重新打开工程或重新生成 IP 时可能出现 `video_clock`、`rgb2dvi_0` 或 HDMI 约束路径缺失。

## 4. 实验步骤

### 4.1 打开 Vivado 工程

打开工程：

```text
zynq7020-image-processing\sobel_01_hdmi_pattern\sobel_01_hdmi_pattern.xpr
```

确认 Sources 中包含：

```text
top.v
hdmi_image_display.v
video_clock
rgb2dvi_0
hdmi_out_test.xdc
```

### 4.2 检查顶层模块

确认 Vivado 顶层为：

```text
top
```

如果顶层不正确，在 Sources 中右键 `top.v`，选择 `Set as Top`。

### 4.3 观察显示参数

打开 `hdmi_image_display.v`，重点查看：

```text
H_ACTIVE = 1280
V_ACTIVE = 720
IMG_WIDTH = 128
IMG_HEIGHT = 72
SCALE_X = H_ACTIVE / IMG_WIDTH
SCALE_Y = V_ACTIVE / IMG_HEIGHT
```

报告中应能说明 `SCALE_X = 10`、`SCALE_Y = 10` 的含义。

### 4.4 综合、实现和生成 bitstream

在 Vivado 中依次执行：

```text
Run Synthesis
Run Implementation
Generate Bitstream
```

生成 bitstream 后，查看是否有关键 DRC 错误。如果只有普通 warning，可以先记录后继续上板。

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
HDMI 显示器识别到 1280x720 输入
屏幕显示 128x72 图片放大后的画面
```

需要保存：

1. HDMI 显示照片。
2. Vivado 综合或实现完成截图。
3. 资源利用率截图。
4. 时序结果截图。

## 5. 验收标准

基础实验验收时应能说明：

1. HDMI 显示链路正常工作。
2. `hdmi_image_display.v` 中行列计数器如何产生有效显示区域。
3. ROM 地址如何由 `image_x` 和 `image_y` 计算。
4. 图片为什么能从 `128 x 72` 放大到 `1280 x 720`。

## 6. 常见问题

### 6.1 HDMI 黑屏

检查：

```text
显示器是否切到正确 HDMI 输入
HDMI 线是否正常
是否已经 Program Device
top.v 是否为顶层
hdmi_out_test.xdc 是否启用
video_clock 和 rgb2dvi_0 是否存在
```

### 6.2 Vivado 提示 IP 缺失

不要删除 `../hdmi_common`。如果工程路径被移动，先确认工程仍能找到 `video_clock` 和 `rgb2dvi_0`。

### 6.3 显示器不识别信号

优先检查时钟 IP、HDMI 管脚约束和开发板 HDMI 接口。确认显示器支持 `1280 x 720` 输入。

## 7. 可选扩展

本实验的扩展只围绕 HDMI 显示位置、背景和固定图片数据，属于第一周基础扩展。学生至少完成 1 项，并把 HDMI 现象写入初步实验报告。

| 选题 | 修改范围 | 验收标准 |
| --- | --- | --- |
| 调整图片显示位置 | `hdmi_image_display.v` 中的坐标映射 | 图片能显示在左上、居中或指定区域，报告说明坐标计算方法 |
| 修改背景颜色 | `hdmi_image_display.v` 的非图片区域 RGB 输出 | HDMI 背景颜色发生变化，图片区域仍正常显示 |
| 更换固定图片 | `hdmi_image_display.v` 中的 `image_rom_128x72` 数据 | HDMI 显示新图片，报告说明 ROM 像素格式为 `24'hRRGGBB` |
| 增加简单边框 | `hdmi_image_display.v` 的有效显示区域判断 | 图片周围出现单色边框，且不影响图片内容 |

不建议在本实验中加入串口、PS 软件或 Sobel 运算。本实验重点是把 HDMI 时序、ROM 读地址和图像缩放关系讲清楚。

## 8. 远程开发结果与现场上板流程

### 8.1 分支、提交和远程结论

- 分支：`exp/01-hdmi-pattern`
- 远程构建基线提交：`fab4bce33a8382f8620659d42599c479fa3fadb6`
- 现场测试前执行 `git rev-parse HEAD`，记录实际测试的最终提交号
- Vivado/XSim 2023.2：仿真、综合、实现和 bitstream 生成通过
- 时序：WNS `7.969 ns`、TNS `0 ns`
- DRC：0 error、1 warning；`ZPS7-1` 是纯 PL 设计未实例化 PS7 的已知警告
- JTAG、Program Device 和 HDMI 实机现象：待现场验证

旧 XPR 来自 Vivado 2017.4，且历史 IP repository 已不在仓库中。现场优先使用
`run_exp01_bitstream.tcl` 创建隔离的 2023.2 工程；脚本直接编译已归档的 HDMI
RTL/VHDL，不会覆盖原始 XPR。

### 8.2 所需硬件与接线

1. 与约束匹配的黑金 ZYNQ7020 开发板，器件为 `xc7z020clg400-2`。
2. 匹配的板卡电源和 JTAG 下载线。
3. HDMI 线和支持 `1280 x 720` 输入的显示器或采集设备。
4. 将 JTAG 接到电脑、HDMI 接到显示器，再给开发板上电。
5. 如果板卡不是课程指定型号，先核对 `hdmi_out_test.xdc` 的 `U18` 系统时钟、
   HDMI TMDS 和 `hdmi_oen` 管脚；芯片相同不代表板级管脚相同。

本实验不使用 USB 串口、PS 软件或上位机程序。

### 8.3 拉取和构建

```powershell
git fetch origin
git switch exp/01-hdmi-pattern
git pull --ff-only origin exp/01-hdmi-pattern
git rev-parse HEAD

cd zynq7020-image-processing\sobel_01_hdmi_pattern
& D:\Vivado\Vivado\2023.2\bin\vivado.bat -mode batch -nojournal -nolog -source run_exp01_sim.tcl
& D:\Vivado\Vivado\2023.2\bin\vivado.bat -mode batch -nojournal -nolog -source run_exp01_bitstream.tcl
```

必须看到：

```text
HDMI pattern timing simulation passed
EXP01_SIM=passed
EXP01_BUILD=passed
```

生成的 bitstream 位于：

```text
zynq7020-image-processing\sobel_01_hdmi_pattern\build\vivado_2023_2\top.bit
```

GUI 查看方式：构建后用 Vivado 2023.2 打开
`build\vivado_2023_2\exp01_build.xpr`，查看 Sources、Implemented Design、
Utilization 和 Timing Summary。不要保存升级结果到原始 2017.4 XPR。

### 8.4 下载 bitstream

1. 启动 Vivado 2023.2，选择 `Open Hardware Manager`。
2. 选择 `Open Target -> Auto Connect`，确认识别到 `xc7z020`。
3. 选择 `Program Device`。
4. Bitstream 选择 `build\vivado_2023_2\top.bit`。
5. 完成后保持开发板供电，观察显示器是否锁定到 `1280 x 720`。

本实验没有 PS 程序，不需要 Vitis、FSBL、ELF 或 Run As。

### 8.5 预期现象与通过标准

- 无预期串口输出。
- HDMI 应显示全屏固定渐变图：中央红色竖条、白色横带和两条黑色对角线。
- 现场画面应与
  [`coursework/evidence/02_hdmi_pattern/exp01_expected_pattern.png`](../coursework/evidence/02_hdmi_pattern/exp01_expected_pattern.png)
  一致，不应黑屏、滚动、周期闪烁、明显错色或裁切。
- 显示器应稳定识别 `1280 x 720`，持续观察至少 30 秒。
- Program Device 成功，现场实现报告无 timing violation，才判定实验 1 通过。
- 在真实照片和日志回传前，仓库状态保持“远程构建通过、待现场验证”。

### 8.6 失败时保存的完整材料

1. `git rev-parse HEAD`、板卡型号、Vivado 版本和测试日期。
2. Vivado Tcl Console、Program Device 和 Hardware Manager 的完整错误文本。
3. `vivado.log`、综合/实现/bitstream 日志，不能只截最后一行。
4. `report_utilization` 和 `report_timing_summary`，至少包含 WNS/TNS。
5. 显示器提示“无信号”、黑屏、错色或异常画面的照片/视频截图。
6. JTAG 设备列表截图，以及失败发生的准确步骤。
7. 若修改过 XDC，回传修改后的完整文件和板卡原理图对应页。

### 8.7 必须回传的文件

- HDMI 固定图照片，最好同时拍到显示器和开发板
- Program Device 成功截图或完整失败日志
- utilization 摘要
- timing summary，至少包含 WNS/TNS
- 实际测试提交号和板卡/Vivado/JTAG 信息
- 任何为复现问题而临时修改的文件

# sobel_03_uart_hdmi 实验说明

本实验实现 PC 端通过串口发送图像，ZYNQ PS 端接收图像并写入 AXI BRAM，PL 端从 BRAM 读取图像并通过 HDMI 输出到显示器。

当前版本用于验证 **UART -> PS -> AXI BRAM -> PL HDMI** 的完整显示链路。图像分辨率固定为 `128 x 72`，像素格式为 `RGB888`，HDMI 端将图像放大 10 倍显示到 `1280 x 720` 画面中。

## 实验步骤总览

建议按下面顺序完成，不要跳过 HDMI 或 SDK 的单独验证：

1. 打开 `sobel_03_uart_hdmi.xpr`，确认顶层、Block Design、HDMI 约束和 `hdmi_bram_display.v` 存在。
2. 在 Vivado 中运行 Synthesis、Implementation，并生成 `top.bit`。
3. 下载 bitstream 到开发板，确认 HDMI 有基础输出。
4. 打开 SDK 工作区，重新生成 BSP，编译并运行 `ps_uart_bram_app`。
5. 用串口调试助手确认 PS 程序打印启动信息和 `waiting for frame header`。
6. 关闭串口调试助手，使用 `host_camera_uart` 中的 GUI 或命令行脚本发送图片。
7. 观察 HDMI 是否显示 PC 端发送的原始图像。
8. 保存 HDMI 照片、串口输出截图、资源利用率和时序结果。

## 1. 实验数据流

```text
PC 摄像头 / 图片
    -> USB 串口，115200 baud
    -> ZYNQ PS UART
    -> PS 软件解析帧数据
    -> AXI GP0
    -> AXI BRAM Controller
    -> Block RAM
    -> PL HDMI 读 BRAM
    -> RGB2DVI
    -> HDMI 显示器
```

当前实验保持串口波特率为 `115200`。这个波特率比较稳，但带宽较低，所以画面刷新速度会比较慢。

## 2. 工程文件

主要文件如下：

```text
sobel_03_uart_hdmi.xpr
    Vivado 工程

create_ps_uart_bram_hdmi_bd.tcl
    Block Design 生成脚本

sobel_03_uart_hdmi.srcs/sources_1/new/top.v
    顶层模块

sobel_03_uart_hdmi.srcs/sources_1/new/hdmi_pl_top.v
    PL 侧 HDMI 显示顶层

sobel_03_uart_hdmi.srcs/sources_1/new/hdmi_bram_display.v
    从 BRAM 读取 128x72 图像并放大显示

sobel_03_uart_hdmi.srcs/constrs_1/new/hdmi_out_test.xdc
    HDMI 管脚约束

ps_uart_bram_app/src/main.c
    PS 端 SDK 应用源码

sobel_03_uart_hdmi.sdk/ps_uart_bram_app/src/main.c
    SDK 工作区中的 PS 端应用源码

../host_camera_uart/camera_uart_sender.py
    PC 端摄像头 / 图片串口发送脚本

../host_camera_uart/README.md
    PC 端环境安装和运行说明

../host_camera_uart/requirements.txt
    PC 端 Python 依赖
```

上一级目录中的 `../hdmi_common` 是 Sobel 系列工程共用的 HDMI 基础依赖目录，不能删除。Vivado 工程文件中保留了指向该目录的相对路径，用于记录 `video_clock`、`rgb2dvi_0`、`hdmi_out_test.xdc` 和 HDMI IP repository 的来源。删除该目录后，重新打开工程或重新生成 IP 时可能出现 HDMI 相关文件缺失。

## 3. 硬件设计

### 3.1 打开 Vivado 工程

打开工程：

```text
D:\Github\FPGA-course\zynq7020-image-processing\sobel_03_uart_hdmi\sobel_03_uart_hdmi.xpr
```

如果需要重新生成 Block Design，可以在 Vivado Tcl Console 中执行：

```tcl
cd D:/Github/FPGA-course/zynq7020-image-processing/sobel_03_uart_hdmi
source create_ps_uart_bram_hdmi_bd.tcl
```

Block Design 中包含：

```text
ZYNQ7 Processing System
SmartConnect
AXI BRAM Controller
Block Memory Generator
BRAM_PORTB 外接到 PL HDMI 逻辑
```

BRAM 地址映射：

```text
BRAM base address = 0x40000000
BRAM range        = 64 KB
```

PS 写入 BRAM 的 framebuffer 格式：

```text
address = 0x40000000 + ((y * 128 + x) << 2)
data    = 0x00RRGGBB
```

每个像素占 32 bit，低 24 bit 为 RGB888。

### 3.2 HDMI 显示逻辑

PL 端显示逻辑主要由以下模块完成：

```text
top.v
    连接 Block Design 和 HDMI PL 顶层

hdmi_pl_top.v
    生成视频时钟，连接 HDMI 读 BRAM 模块和 RGB2DVI

hdmi_bram_display.v
    产生 1280x720 时序，从 BRAM 读取 128x72 图像并做 10 倍放大
```

显示关系：

```text
BRAM 图像: 128 x 72
HDMI 输出: 1280 x 720
缩放倍数: 10 x 10
```

`hdmi_bram_display.v` 中已经处理 BRAM 读延迟，HDMI 同步信号和像素数据对齐后再输出。

### 3.3 生成 bitstream

在 Vivado 中依次执行：

```text
Run Synthesis
Run Implementation
Generate Bitstream
```

生成 bitstream 后，检查没有关键 DRC 错误。当前代码已经把 BRAM 读端复位改成同步复位，用于避免 RAMB36 异步控制相关 DRC。

## 4. SDK 软件工程

SDK 工作区目录：

```text
D:\Github\FPGA-course\zynq7020-image-processing\sobel_03_uart_hdmi\sobel_03_uart_hdmi.sdk
```

Project Explorer 中通常有 3 个工程：

```text
top_hw_platform_0
    硬件平台

ps_uart_bram_app_bsp
    BSP 工程

ps_uart_bram_app
    PS 端应用工程
```

需要修改和运行的是：

```text
ps_uart_bram_app
```

### 4.1 当前 SDK 关键配置

PS 端 `main.c` 当前配置：

```c
#define IMG_WIDTH        128U
#define IMG_HEIGHT       72U
#define RGB888_FORMAT    0x18U
#define UART_BAUD_RATE   115200U
#define UART_WAIT_MS     2000U
```

串口波特率已经改为 `115200`。

### 4.2 编译 SDK 工程

在 SDK 中执行：

```text
右键 ps_uart_bram_app_bsp -> Re-generate BSP Sources
右键 ps_uart_bram_app     -> Clean Project
右键 ps_uart_bram_app     -> Build Project
```

如果只改了 `main.c`，通常重新 Build `ps_uart_bram_app` 即可。

### 4.3 下载 FPGA 和运行 PS 程序

先下载 bitstream：

```text
Xilinx -> Program FPGA
```

bitstream 通常在：

```text
sobel_03_uart_hdmi.runs/impl_1/top.bit
```

然后运行 PS 程序：

```text
右键 ps_uart_bram_app -> Run As -> Launch on Hardware (System Debugger)
```

如果 SDK 进入 Debug 界面，可以通过下面方式回到原来的 C/C++ 工程界面：

```text
右上角点击 C/C++ 图标
```

或者：

```text
Window -> Perspective -> Open Perspective -> C/C++
```

## 5. 串口配置

串口调试助手配置：

```text
端口号:  根据开发板实际端口选择，例如 COM7
波特率:  115200
数据位:  8
校验位:  None
停止位:  1
流控:    None
```

PS 程序启动后，串口调试助手应该看到：

```text
PS UART BRAM HDMI display
BRAM base: 0x40000000, baud: 115200
waiting for frame header
```

`waiting for frame header` 表示 PS 程序正在等待 PC 端发送图像帧，这是正常现象。

注意：同一个 COM 口同一时间只能被一个程序打开。运行 Python 发送脚本前，需要关闭串口调试助手。

## 6. PC 端 Python 环境

PC 端脚本位于：

```text
D:\Github\FPGA-course\zynq7020-image-processing\host_camera_uart
```

推荐使用 Anaconda 创建独立环境。

### 6.1 安装 Anaconda

1. 进入 Anaconda 官网下载 Windows 版本安装包。
2. 按默认选项安装。
3. 安装完成后，打开 Anaconda Prompt。
4. 检查 conda 是否可用：

```bash
conda --version
```

### 6.2 创建 fpga 虚拟环境

本实验指定 Python 版本为 `3.11`：

```bash
conda create -n fpga python=3.11 -y
conda activate fpga
```

进入 PC 端脚本目录：

```bash
cd D:\Github\FPGA-course\zynq7020-image-processing\host_camera_uart
```

安装依赖：

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

检查依赖是否安装成功：

```bash
python -c "import cv2, numpy, serial; print('ok')"
```

如果输出 `ok`，说明环境可以使用。

## 7. PC 端发送图像

### 7.1 摄像头发送

关闭串口调试助手后，在 Anaconda Prompt 中运行：

```bash
conda activate fpga
cd D:\Github\FPGA-course\zynq7020-image-processing\host_camera_uart
python camera_uart_sender.py --port COM7 --baud 115200 --camera 0 --fps 0.2 --preview
```

其中：

```text
--port COM7
    改成自己开发板对应的串口号

--baud 115200
    必须和 SDK 程序一致

--camera 0
    使用默认摄像头

--fps 0.2
    每 5 秒左右发送 1 帧，适合 115200 baud

--preview
    在 PC 上显示预览窗口
```

### 7.2 图片发送

也可以发送单张图片：

```bash
python camera_uart_sender.py --port COM7 --baud 115200 --image test.jpg --once --preview
```

### 7.3 串口较慢时的稳定发送

如果出现丢行、超时或画面不完整，可以增加行间延时：

```bash
python camera_uart_sender.py --port COM7 --baud 115200 --camera 0 --fps 0.2 --line-delay 0.001 --preview
```

## 8. 串口协议

PC 端每帧发送一个 frame header，然后按行发送图像数据。

### 8.1 帧头

```text
0x55 0xAA width_l width_h height_l height_h format
```

当前固定为：

```text
width  = 128
height = 72
format = 0x18
```

`0x18` 表示 RGB888。

### 8.2 行头

每一行发送前都有 line header：

```text
0x33 0xCC row_l row_h
```

`row` 从 `0` 到 `71`。

### 8.3 像素数据

每行像素数据为：

```text
128 个 RGB888 像素
每个像素 3 字节: R G B
```

PS 接收后写入 BRAM：

```text
0x00RRGGBB
```

## 9. 完整测试流程

### 9.1 只测试 FPGA 和 PS 程序

1. 打开 Vivado 工程。
2. Generate Bitstream。
3. 打开 SDK。
4. Build `ps_uart_bram_app`。
5. `Xilinx -> Program FPGA` 下载 bitstream。
6. `Run As -> Launch on Hardware (System Debugger)` 运行 PS 程序。
7. 打开串口调试助手，配置 `115200 8N1`。
8. 确认串口打印：

```text
PS UART BRAM HDMI display
BRAM base: 0x40000000, baud: 115200
waiting for frame header
```

此时显示器应有 HDMI 输出。

### 9.2 测试 PC 到 HDMI 的完整链路

1. 关闭串口调试助手。
2. 打开 Anaconda Prompt。
3. 进入 `fpga` 环境。
4. 运行 PC 端发送脚本：

```bash
conda activate fpga
cd D:\Github\FPGA-course\zynq7020-image-processing\host_camera_uart
python camera_uart_sender.py --port COM7 --baud 115200 --camera 0 --fps 0.2 --preview
```

5. 观察 HDMI 显示器。
6. 显示器应能看到 PC 摄像头图像，只是刷新比较慢。

## 10. 原始说明中的预期现象

以下为原始工程描述的预期上板现象。本分支尚未取得现场硬件证据，不能作为当前实测结论：

```text
串口能输出启动信息
串口能输出 waiting for frame header
显示器能正常输出画面
PC 发送脚本运行后，HDMI 画面能更新
```

现场复核前，上述内容仅用于说明预期行为。

## 11. 帧率说明

当前串口波特率为 `115200`，实际 UART 8N1 传输时每个字节约需要 10 bit。

理论有效字节率约为：

```text
115200 / 10 = 11520 byte/s
```

一帧 `128 x 72` 的 RGB888 图像数据大约为：

```text
128 * 72 * 3 = 27648 byte
```

再加上帧头和行头，一帧约 `27 KB`。因此在 `115200` 波特率下，理论最高帧率不到 `0.5 fps`，实际运行时建议使用：

```text
--fps 0.2
```

如果想明显提高帧率，需要后续提高串口波特率、降低图像分辨率、减少颜色字节数，或者换成 USB / Ethernet / DMA 等更高带宽的数据通道。当前实验为了稳定，保持 `115200`。

## 12. 常见问题

### 12.1 串口没有任何输出

检查：

```text
是否已经 Program FPGA
是否已经 Run PS 程序，而不是只下载 bitstream
串口号是否正确
串口是否为 115200 8N1
是否 Build 了最新的 ps_uart_bram_app
串口是否被其他软件占用
```

### 12.2 串口有输出，但是 HDMI 没有输出

检查：

```text
显示器是否切到正确 HDMI 输入
bitstream 是否是最新生成的 top.bit
Vivado 顶层是否为 top.v
hdmi_out_test.xdc 管脚约束是否启用
HDMI 线和开发板 HDMI 接口是否正常
```

### 12.3 HDMI 有输出，但是 PC 发送后画面不更新

检查：

```text
运行 Python 脚本前是否关闭了串口调试助手
Python 脚本的 --port 是否正确
Python 脚本的 --baud 是否为 115200
Python 脚本的 --fps 是否不要太高
SDK 程序是否仍在运行
```

### 12.4 串口打印 frame error

常见错误含义：

```text
frame error -1
    图像宽度、高度或格式不匹配

frame error -2
    行号不匹配，通常是串口数据丢失或发送太快

frame error -5
    等待行头超时

frame error -6
    等待行号超时

frame error -7
    等待像素数据超时
```

处理方法：

```text
降低 --fps
增加 --line-delay
检查 USB 串口连接
确认 PC 端和 SDK 端波特率一致
```

### 12.5 一直打印 waiting for frame header

这说明 PS 程序运行正常，但还没有收到 PC 端发送的图像帧。

处理方法：

```text
关闭串口调试助手
运行 camera_uart_sender.py
确认 COM 口正确
确认 baud 为 115200
```

## 13. 可选扩展

本实验的扩展围绕串口输入后的 HDMI 原图显示，属于第一周基础扩展。学生至少完成 1 项；不要求修改 PC 端 GUI，也不要求加入 Sobel。

| 选题 | 修改范围 | 验收标准 |
| --- | --- | --- |
| 修改 HDMI 背景颜色 | `hdmi_bram_display.v` 的非图像区域 RGB 输出 | 串口图像仍正常显示，背景颜色按设计变化 |
| 调整图像显示位置 | `hdmi_bram_display.v` 的坐标映射 | 128x72 图像能显示在左上、居中或指定区域 |
| 增加图像边框 | `hdmi_bram_display.v` 的显示区域判断 | HDMI 图像周围出现单色边框，图像内容不被破坏 |
| 串口帧率与稳定性记录 | 不改硬件，调整 PC 端运行参数 | 对比 2 到 3 组 `--fps` 或 `--line-delay`，记录是否出现 `frame error` |

本仓库已完成“增加图像边框”扩展：在 `hdmi_bram_display.v` 中新增可配置参数
`BORDER_WIDTH`（默认 `20`）和 `BORDER_COLOR`（默认 `24'h0066ff` 蓝色），在有效显示区
外圈叠加单色边框；仅改显示映射，不影响 BRAM 读取的图像数据，`BORDER_WIDTH=0` 可关闭。
预期 HDMI 画面见 `../coursework/evidence/04_uart_hdmi/exp03_expected_image.png`。

不建议在本实验中做 UDP、DMA、网络摄像头、双缓冲或 PC 端 GUI 修改。这些内容工作量较大，不适合作为第一周基础扩展。

## 14. 远程开发结果与现场上板流程

### 14.1 当前状态

- 分支：`exp/03-uart-hdmi`
- 基线：从与 `origin/main` 一致的 `main` 创建（含实验 0、实验 1 成果）
- 工具：Vivado / XSim 2023.2，Vitis 2023.2
- 器件：`xc7z020clg400-2`
- 状态：远程仿真、综合、实现、时序、DRC、bitstream，以及协议黄金模型自检和 PS 源码静态编译检查通过；正式 Vitis/BSP/ELF 构建及真实 JTAG / UART / HDMI 待完成
- 默认显示边框：`BORDER_WIDTH = 20`，`BORDER_COLOR = 24'h0066ff`

获取现场实际测试的提交号：

```powershell
git switch exp/03-uart-hdmi
git pull --ff-only origin exp/03-uart-hdmi
git rev-parse HEAD
```

### 14.2 已验证的数据链

```text
PC 图像 -> UART(0x55AA 帧头 + 0x33CC 行头 + 128x72 RGB888)
  -> PS receive_frame 写 AXI BRAM(0x40000000, 0x00RRGGBB)
  -> PL hdmi_bram_display 读 BRAM
  -> 10x 放大 + 外圈蓝色边框
  -> 1280x720 HDMI
```

远程阶段已确认：

1. 协议黄金模型编码与 PS `receive_frame` 解析往返无损（`9216` 像素逐像素一致），错误注入返回码
   `-1/-2/-3/-5/-7` 与 `main.c` 一致（`tools/generate_exp03_expected.py`）；该项未直接调用上位机发送脚本。
2. XSim 验证 HDMI 时序、有效像素数、HS/VS、10x 缩放地址、读延迟流水线对齐和边框映射
   （`sim/hdmi_bram_display_tb.v`）。
3. Vivado 综合/实现/时序/DRC/bitstream 通过：WNS `8.173 ns`、TNS `0`、DRC `0` violations、
   `1775` LUT / `1504` FF / `16` BRAM / `0` DSP。
4. PS 源码用 `arm-none-eabi-gcc 12.2.0` 编译检查 `0` error、`0` warning。

### 14.3 命令行复现

在本目录执行（Vivado/Vitis 自带或正常 PowerShell 环境）：

```powershell
# 仿真（生成预期数据 + XSim 自检）
& D:\Vivado\Vivado\2023.2\bin\vivado.bat -mode batch -source run_exp03_sim.tcl
# 综合/实现/bitstream + 导出 XSA
& D:\Vivado\Vivado\2023.2\bin\vivado.bat -mode batch -source run_exp03_bitstream.tcl
# PS 应用编译（生成 .elf）
& D:\Vivado\Vitis\2023.2\bin\xsct.bat build_exp03_ps_app.tcl
```

bitstream 与 XSA 生成在可删除重建的 `build/` 目录（不提交 Git）：

```text
build/vivado_2023_2/top.bit
build/vivado_2023_2/ps_uart_bram_hdmi.xsa
```

若独立 Python 不在 `D:\Miniconda3\python.exe`，仿真前设置：

```powershell
$env:EXP03_PYTHON = "C:\path\to\python.exe"
```

本次自动化环境中，XSCT 在创建 Vitis 平台时报告
“Timeout while establishing a connection with Vitis”，根因尚未确认。直接
`xvlog`/`xelab`/`xsim` 仿真和 `arm-none-eabi-gcc -c` 源码检查可提供部分证据
（见 `tools/ps_syntax_check/` 与 `../coursework/evidence/04_uart_hdmi/`），
但不能替代正式 Vitis 平台、BSP、应用和 ELF 构建。

### 14.4 硬件与接线

需要：

- 目标为 `xc7z020clg400-2` 的 ZYNQ7020 开发板、匹配电源和 JTAG 下载线。
- USB 串口线（PS UART1，`115200 8N1`），记录实际 COM 口。
- HDMI 线和支持 `1280 x 720` 的显示器或采集设备。
- 用于拍摄显示器和接线状态的相机。

接线顺序：

1. 断电连接 JTAG、HDMI、USB 串口和板卡电源。
2. HDMI 连接开发板输出端与显示器输入端，选择正确输入源。
3. 上电，确认 Hardware Manager 能识别目标器件。

### 14.5 下载、运行与发送

1. 完成上面的 bitstream 与 PS 应用构建。
2. Vitis 中 `Program FPGA`，bitstream 指向 `build/vivado_2023_2/top.bit`
   （或 Hardware Manager 手动下载 `top.bit`）。
3. `Run` / `Launch on Hardware` 运行 `ps_uart_bram_app`（`.elf`）。
4. 串口助手 `115200 8N1`，应看到：

   ```text
   PS UART BRAM HDMI display
   BRAM base: 0x40000000, baud: 115200
   waiting for frame header
   ```

5. 关闭串口助手，用 `../host_camera_uart/camera_uart_sender.py` 发送图片：

   ```bash
   python camera_uart_sender.py --port COM7 --baud 115200 --image test.jpg --once --preview
   ```

### 14.6 预期画面与通过标准

预期画面：HDMI 显示 PC 发送的 `128 x 72` 原图，10x 放大到 `1280 x 720`，四周叠加默认
`20` 像素蓝色（`24'h0066ff`）边框。结构应与
`../coursework/evidence/04_uart_hdmi/exp03_expected_image.png` 一致（该 PNG 为合成测试图，
现场图像内容取决于实际发送的图片，但缩放与边框关系应一致）。

通过标准：

1. 显示器稳定识别 `1280 x 720`，连续保持至少 30 秒。
2. 串口稳定打印启动信息；发送图像后画面更新，无明显错行或撕裂。
3. 图像四周有完整蓝色边框，图像内容不被边框破坏。
4. Program Device、PS 运行、板卡型号、Vivado/Vitis 版本、COM 口和实际提交号均有记录。

在收到真实 HDMI 照片、串口日志和 Hardware Manager 记录前，不得标记为“上板通过”。

### 14.7 失败排查顺序

1. 串口无输出：确认已 Program FPGA 且运行了 PS 程序（非仅下载 bitstream）、COM 口与
   `115200 8N1`、未被其他程序占用、已编译最新 `.elf`。
2. 串口有输出但 HDMI 无画面：确认显示器输入源、`top.bit` 为最新、顶层为 `top`、
   `hdmi_out_test.xdc` 生效、HDMI 接线。
3. HDMI 有画面但发送后不更新：关闭串口助手后再运行 Python，核对 `--port`/`--baud`/`--fps`。
4. `frame error`：降低 `--fps`、增加 `--line-delay`、确认 USB 串口与波特率一致
   （错误码含义见第 12.4 节）。
5. 边框异常：核对实际提交号与默认 `BORDER_WIDTH=20`，并重跑 XSim。

### 14.8 现场必须回传

- 实际分支和完整提交号。
- 测试日期、板卡型号、Vivado/Vitis 版本、COM 口和显示设备型号。
- Hardware Manager 识别目标、Program Device 成功、PS 程序串口启动日志。
- HDMI 显示原图（含蓝色边框）的照片，包含分辨率信息。
- 能确认板卡、JTAG、HDMI 和 USB 串口接线的照片。
- 若失败：失败步骤、完整错误文本和最后一个正常现象。

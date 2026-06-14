# ZYNQ7020 图像处理课程设计：单人 AI 辅助实施报告

> 分析依据：`zynq7020-image-processing/README.md`、实验 0 至实验 5 的 README、`host_camera_uart/README.md`  
> 面向对象：单人完成，主要借助 AI 进行代码分析、代码生成、仿真设计、故障定位和报告整理  
> 核心原则：先复现、再小改；先仿真、再综合；先单链路验证、再系统联调；每完成一步立即保存证据

## 1. 结论先行

这项课程设计不是一个单独的 Sobel 模块，而是一条逐步扩展的数据链：

```text
RTL 仿真
  -> HDMI 固定图片
  -> PL Sobel
  -> PC 经 UART 发送图像
  -> PS 写 AXI BRAM
  -> PL 读 BRAM 并显示
  -> UART 图像经 PL Sobel 后显示
  -> PC 命令控制模式、阈值和叠加
  -> 扩展多输入来源与图像缩放策略
```

单人完成的推荐策略如下：

1. 严格按实验 0 到实验 5 顺序推进，不并行修改多个 Vivado 工程。
2. 第一周的小扩展全部选择低风险、证据清楚、可复用的选项。
3. 第二周综合扩展首选“上位机与输入规格扩展”：增加 `stretch`、`letterbox`、`center-crop` 缩放策略，FPGA 处理尺寸仍保持 `128×72`。
4. 网络实时视频扩展不适合单人短周期完成，除非基础工程已全部稳定且熟悉 lwIP。
5. AI 负责绝大多数文本和代码工作，但板卡连接、Vivado/SDK GUI 操作、串口占用处理、拍照和真实性确认必须由本人完成。
6. 仓库中的实验 0 至实验 5 已有较完整源码，工作重点是环境重建、验证、最小修改和证据收集，而不是从零实现。
7. 预计净投入约 30 至 45 小时；若 Vivado/SDK 环境需从头修复，建议预留 45 至 60 小时。

### 仓库复核后的关键判断

| 项目 | 仓库实际情况 | 对计划的影响 |
| --- | --- | --- |
| 实验 0 | 有完整 RTL、自检 testbench、异常帧测试和图片转换脚本 | 先直接跑现有仿真，再做输入图扩展 |
| 实验 1–2 | 有 Vivado 2017.4 工程、HDMI IP、XDC 和 RTL | 首先做综合检查，不先改代码 |
| 实验 3–4 | PS、BRAM、PL、HDMI 源码和 BD 已存在 | 主要任务是重建 SDK 环境并上板验证 |
| 实验 5 | PC、PS、PL 三端控制逻辑已写好 | 改为验证现有实现并补系统级测试 |
| 上位机 | 已支持摄像头、单图、多图、目录、视频和控制命令 | 综合扩展应在现有基础上增加缩放策略和验证 |
| 生成物 | 没有 `.bit`、`.elf`、`.hdf/.xsa`、VCD、资源或时序报告 | 所有“成功”都必须重新生成和验证 |
| SDK | 只归档了应用工程，缺少硬件平台和 BSP | 不能假设打开 SDK 就能直接 Build |

## 2. 任务边界与评分导向

### 2.1 必须完成的交付范围

| 类别 | 必须完成 |
| --- | --- |
| 基础实验 | 实验 0 至实验 5 全部跑通 |
| 第一周扩展 | 实验 0 至实验 4 各完成 1 个小扩展 |
| 实验 5 | PC 控制显示模式、阈值和彩色叠加 |
| 第二周扩展 | 从 3 个综合方向中选择 1 个 |
| 仿真材料 | 输入图、输出图、关键波形、扩展仿真 |
| 上板材料 | HDMI 照片或视频截图、串口输出 |
| 工程材料 | 可运行工程、修改文件清单、关键代码说明 |
| Vivado 材料 | 资源利用率、时序结果、bitstream 生成结果 |
| 文档 | 仿真报告、初步实验报告、最终报告 |

### 2.2 得分优先级

课程评分中，基础复现、三份报告和扩展功能合计占绝大多数。单人策略应按下列顺序保分：

```text
基础链路稳定
  > 证据完整
  > 实验 5 控制功能
  > 综合扩展可验证
  > 额外花哨功能
```

不要为了追求高帧率、网络或复杂 GUI，牺牲基础实验和报告材料。

## 3. 开工前准备

### 3.1 硬件

- 黑金 ZYNQ7020 开发板，器件目标为 `xc7z020clg400-2`
- 可用的电源、JTAG 下载线、USB 串口线
- HDMI 线和支持 1280×720 输入的显示器
- PC 摄像头或本地测试图片
- 手机或其他拍照设备，用于记录 HDMI 画面和板卡状态

### 3.2 软件

- 优先使用 Vivado 2017.4
- Xilinx SDK 2017.4，或与工程兼容的配套环境
- Python/Conda 环境
- Icarus Verilog
- GTKWave，可用 Vivado 波形窗口替代
- 串口调试助手
- Git，用于阶段性保存修改

本次仓库复核时，当前系统 PATH 中未找到原生 `python` 和 `iverilog`；WSL 命令存在，但没有可用 Linux 发行版。因此正式执行的第 0 个任务是把 Python 和 Icarus 仿真入口真正跑通，不能直接假设 README 中的命令可用。

工程 `.xpr`、Block Design 和 SDK 元数据均显示原始版本为 Vivado/SDK 2017.4。直接使用较新版本可能触发 IP 升级、Block Design 升级或 SDK/Vitis 迁移，增加不必要风险。若只能使用新版，先复制工程，再测试升级，不能直接覆盖唯一原件。

#### 3.2.1 本机环境复核（2026 年 6 月 14 日）

| 检查项 | 本机结果 | 判断 |
| --- | --- | --- |
| CPU | Intel Core i7-13700H，20 个逻辑核心 | 足够完成综合、实现和软件开发 |
| 内存 | 约 15.6 GB | 能完成 Zynq-7020 规模工程；运行 Vivado 时应关闭大型程序 |
| 磁盘 | Vitis 安装后 `D:` 约 197 GB 可用；`C:` 约 31 GB 可用 | 空间足够，工程和工作区继续放 `D:` |
| Vivado | `D:\Vivado\Vivado\2023.2`，命令行已能输出 2023.2 版本 | PL 工程工具已安装 |
| Zynq 器件支持 | 安装目录存在 `xc7z020`、`xc7z020_clg400` 数据 | 目标芯片器件库已安装 |
| 关键 Vivado IP | 存在 `processing_system7_v5_5`、`axi_bram_ctrl`、`smartconnect`、`clk_wiz` | 具备重建硬件设计的基础 IP |
| 嵌入式工具 | 已安装 Vitis Embedded 2023.2；`vitis.bat`、XSCT、XSDB 和 ARM GCC 12.2.0 均存在 | 已具备重新建立 Zynq PS 平台和编译 C 程序的工具 |
| RTL 仿真 | ModelSim SE-64 10.5 和 ModelSim Altera 10.1d 可启动 | 有备用仿真器；仓库脚本要求的 Icarus/VVP 仍未安装 |
| Python | 已将 Miniconda 26.3.2 全用户安装到 `D:\Miniconda3`，Python 3.11.15、pip 26.0.1、Conda 和 Tkinter 均已验证 | `python`、`pip`、`conda` 和 `py` 均可作为系统命令使用 |
| JTAG/串口驱动 | 已有 Xilinx 编程线、Digilent、FTDI、CH341 和 CH343 驱动包 | 常见板载下载器和 USB 串口已有驱动基础 |
| 许可证 | Enterprise 试用已于 2023 年过期；许可证中有永久 `V_WebPACK`、`SDK` 和 `Embedded_SDK` | Zynq-7020 基础流程具备许可基础，仍需用一次 bitstream 生成实测 |
| 串口工具 | 已安装 MobaXterm；当前 `COM3` 至 `COM6` 均为蓝牙虚拟串口 | 串口终端可用，但还没有识别到开发板串口 |
| 摄像头 | 当前未检测到可用摄像头 | 不阻塞课程，可先用本地图片或视频 |
| 板卡连接 | 未检测到当前已连接的 Xilinx/Digilent JTAG 或开发板 USB 串口设备 | 还不能进行下载、串口和 HDMI 实机验证 |

本机硬件性能足够，Vivado、Vitis Embedded 和系统 Python 工具链已经具备。当前主要阻塞项缩小为仓库脚本所需的 Icarus/VVP，以及尚未取得和连接的 Zynq 开发板。现有 Vivado 2023.2 可以用于实验 1、实验 2 和实验 3 至实验 5 的硬件平台重建，但原工程生成于 Vivado 2017.4，第一次打开时必须使用工程副本，并检查 Locked IP、Upgrade IP、Block Design 和约束状态。

`D:\Vivado\Vitis\2023.2` 是当前应使用的 PS 软件开发环境；`D:\Vivado\Vitis_HLS\2023.2` 只用于把 C/C++ 算法综合成 RTL/IP，不要混用。Vitis 自带的 Python 3.8.3 是工具内部运行时，也不应替代上位机的独立 Python/Conda 环境。

#### 3.2.2 当前电脑能完成到什么程度

| 范围 | 当前状态 |
| --- | --- |
| 阅读、修改 RTL/C/Python、整理报告 | 可以 |
| 实验 0 RTL 仿真 | Python 图像工具已可用；安装 Icarus/VVP 后可以直接运行仓库脚本，也可另写 ModelSim/XSim 入口 |
| 实验 1–2 综合、实现、生成 bitstream | 工具和器件库具备；需先验证 2017.4 工程在 2023.2 中的兼容性 |
| 实验 3–5 的 PL 硬件设计 | 可以分析和综合；需处理旧 IP/BD 迁移 |
| 实验 3–5 的 PS 程序编译 | 编译工具已经具备；仍需先从 Vivado 生成 XSA，并在 Vitis 中新建 platform、domain/BSP 和应用 |
| 下载到板、串口传图、HDMI 拍照 | 当前不可以，必须连接开发板、JTAG/USB 串口和显示器 |
| 完整课程设计验收 | 当前环境尚不完整；准备 Icarus 仿真入口并取得 Zynq 板后可以完成 |

推荐优先使用当前已经配套的 Vivado/Vitis 2023.2：

1. 复制一个实验工程作为 2023.2 迁移副本。
2. 检查并升级 IP/BD，重新综合、实现并导出 XSA。
3. 在 Vitis 2023.2 中创建 platform 和 standalone domain/BSP。
4. 新建 Empty Application，复制仓库中的 `main.c` 后编译。
5. 只有新版迁移遇到无法解决的旧 IP 或 BD 问题时，再考虑并行安装 Vivado/SDK 2017.4。

剩余环境缺口按优先级排列：

1. **Python 已完成**：系统安装 Python 3.11.15，已安装 OpenCV 4.13.0、NumPy 2.4.6 和 PySerial 3.5；Tkinter、上位机模块和协议打包测试均通过。
2. **推荐安装 Icarus Verilog**：这样可以直接运行仓库的 `run_sim.ps1`；否则需要另写 ModelSim 或 XSim 仿真入口。
3. **GTKWave 可选**：用于直接查看实验 0 生成的 VCD；也可以改用 ModelSim/Vivado 波形窗口。
4. **取得 Zynq-7020 板和配件**：电源、JTAG/下载接口、USB 串口线、HDMI 线和显示器。
5. **生成缺失工程产物**：仓库目前没有 `.bit`、`.elf`、`.xsa/.hdf`、VCD、DCP、资源报告或时序报告，必须在本机重新生成。
6. **创建独立工作区**：Vitis workspace 建议使用 `D:\fpga_workspace`，避免放在带特殊字符的 Windows 用户目录中。

#### 3.2.3 是否必须使用 Zynq

若目标是**按本仓库和课程要求原样完成实验 0 至实验 5**，则必须使用 Zynq-7000，推荐与工程一致的 `xc7z020clg400-2` 开发板。原因不是 Sobel 算法只能在 Zynq 上运行，而是实验 3 至实验 5 明确依赖：

- Zynq PS7 ARM 处理系统；
- PS UART 驱动 `XUartPs`；
- PS 主端口 `M_AXI_GP0`；
- AXI BRAM Controller 和 PS/PL 共享 BRAM；
- PS 程序通过 `Xil_Out32` 写图像和控制寄存器。

因此本实施计划不考虑普通 FPGA 移植，直接以取得 Zynq-7020 上机条件为前提。

选板时按以下顺序判断：

1. **首选课程指定的黑金 ZYNQ7020 开发板**，可以最大程度沿用仓库中的 XDC、PS7 配置和 HDMI 接口。
2. 其他厂商的 `XC7Z020-CLG400` 板卡只能作为次选。芯片相同不代表板级设计相同，通常需要重新核对系统时钟、DDR、UART MIO、JTAG、HDMI 引脚和电气标准。
3. Zynq-7010、Zynq-7035、PYNQ-Z2、ZedBoard 等板卡不能直接套用现有 bitstream 或 XDC，必须做板级适配后才能使用。
4. 借板时同时取得匹配的电源、JTAG/下载接口、USB 串口线和 HDMI 线，并确认允许安装驱动。

拿到板卡后的第一轮只做环境验收，不立即修改算法：

```text
识别 JTAG
  -> 识别串口 COM
  -> 下载最小 bitstream
  -> 运行 PS Hello World
  -> HDMI 固定图
  -> 再进入实验 2 至实验 5
```

### 3.3 Python 环境

本机已采用全用户 Miniconda 安装，基础解释器和课程依赖直接作为系统 Python 使用：

```powershell
python --version
pip --version
conda --version
py --version
python -c "import cv2, numpy, serial, tkinter; print('ok')"
```

上位机脚本验证：

```powershell
python -m py_compile camera_uart_sender.py camera_uart_gui.py
python -c "import cv2, numpy, serial, tkinter; import camera_uart_sender, camera_uart_gui; print('ok')"
python -c "from camera_uart_gui import CameraUartGui; app=CameraUartGui(); app.update_idletasks(); print('gui ok'); app.destroy()"
```

2026 年 6 月 15 日的实测结果：

```text
Python：3.11.15
OpenCV：4.13.0
NumPy：2.4.6
PySerial：3.5
Tk：8.6
GUI 初始化：gui ok
数据包长度：27943
帧头：55 aa 80 00 48 00 18
```

安装及配置日志保存在工作区的 `python_system_setup.log`。

### 3.4 工程资产预检

当前课程工程已完整放入工作区：

```text
D:\codex_prj\fpga_dick\FPGA-course-main\zynq7020-image-processing
```

目录中包含 `hdmi_common`、`host_camera_uart` 和实验 0 至实验 5。正式修改前仍应保留一份只读基线或建立 Git 提交，避免 Vivado 2023.2 打开旧工程时直接升级唯一副本。

仓库静态检查得到以下结论：

- `hdmi_common` 目录只看到 README。
- 各实验目录内部已经复制了 `rgb2dvi_0.xci`、`video_clock.xci` 和 XDC，现有工程仍可能直接综合。
- `.xpr` 仍保留指向 `../hdmi_common` 的导入来源和 IP repository 路径。
- 实验 3 至实验 5 已包含有效的 Block Design 和 wrapper。
- BD 重建 Tcl 基本包含 PS7、UART1、AXI GP0、64 KB BRAM 的配置，但会删除并重建现有 BD，只能在工程副本中使用。
- 仓库没有任何 `.bit`、`.elf`、`.hdf/.xsa`、VCD、DCP 或实现报告。
- `.sdk` 目录只包含应用工程，引用的硬件平台和 BSP 不在仓库中。

第一次打开 Vivado 时必须检查：

- Sources 中 `video_clock`、`rgb2dvi_0` 是否存在
- 是否出现 Missing IP、Locked IP 或 Repository not found
- `top.v` 是否为顶层
- `hdmi_out_test.xdc` 是否启用
- 综合前是否存在红色错误标记

若工程能正常综合，不要主动重建 HDMI IP 或 Block Design。若确实缺失，优先使用各实验目录内的本地 XCI/XDC；仍无法恢复时，再补齐原始 `hdmi_common`。

实验 3 至实验 5 的 SDK 正确恢复路线：

1. 在 Vivado 中确认 BD 地址为 `0x40000000`、范围 64 KB。
2. 成功 Generate Bitstream。
3. `File -> Export -> Export Hardware`，勾选 bitstream。
4. Launch SDK，使用新的独立 workspace。
5. 建立硬件平台和 standalone BSP。
6. 新建 Empty Application，复制对应备份目录中的 `main.c`。
7. 不要直接依赖仓库中缺少 BSP 的旧 `.sdk` 工程。

### 3.5 建议的证据目录

```text
evidence/
├── 00_environment/
├── 01_rtl_sim/
├── 02_hdmi_pattern/
├── 03_hdmi_sobel/
├── 04_uart_hdmi/
├── 05_uart_sobel/
├── 06_pc_control/
├── 07_input_scaling_extension/
├── 08_resource_timing/
└── 09_final_demo/
```

每个目录至少保存：

- 一张成功现象截图或照片
- 一份关键日志
- 一段“做了什么、结果如何、问题是什么”的简短记录
- 修改前后代码差异或修改文件清单

## 4. 推荐总体路线

### 4.1 阶段依赖

| 阶段 | 进入条件 | 完成标志 |
| --- | --- | --- |
| A. 环境与原件保护 | 已取得课程工程 | 工具版本、工程副本、硬件连接清楚 |
| B. 实验 0 | Icarus/Python 可用 | 输入图、输出图、VCD、关键波形齐全 |
| C. 实验 1 | Vivado 工程可打开 | HDMI 显示固定图片 |
| D. 实验 2 | HDMI 链路稳定 | HDMI 显示固定图 Sobel 结果 |
| E. 实验 3 | SDK 和串口正常 | PC 图像经 PS/BRAM 显示原图 |
| F. 实验 4 | 实验 3 稳定 | UART 输入图像显示 Sobel 结果 |
| G. 实验 5 | 实验 4 稳定 | PC 控制模式、阈值、叠加 |
| H. 综合扩展 | 实验 5 和控制仿真稳定 | 多输入来源和三种缩放策略可验证 |
| I. 报告归档 | 所有证据已收集 | 最终报告、工程、视频、资源时序齐全 |

任何阶段未满足“完成标志”，不要继续叠加后续功能。

### 4.2 建议时间表

| 工作日 | 主要任务 | 预计净时间 |
| --- | --- | ---: |
| 第 1 天 | 环境、备份、实验 0 仿真和小扩展 | 4–6 小时 |
| 第 2 天 | 实验 1、HDMI 排错、小扩展 | 4–6 小时 |
| 第 3 天 | 实验 2、固定图 Sobel、小扩展 | 4–6 小时 |
| 第 4 天 | 实验 3 的 Vivado、SDK、串口单链路 | 5–7 小时 |
| 第 5 天 | 实验 3 完整链路、实验 4 | 5–7 小时 |
| 第 6 天 | 实验 5 控制仿真、PS/PL 控制 | 5–8 小时 |
| 第 7 天 | 实验 5 上板验证、初步报告整理 | 4–6 小时 |
| 第 8 天 | 上位机缩放策略、离线测试与 GUI/CLI 集成 | 4–6 小时 |
| 第 9 天 | 两种来源、两种原始尺寸上板验证与对比 | 4–6 小时 |
| 第 10 天 | 最终联调、资源时序、视频、最终报告 | 5–8 小时 |

每天结束时必须完成三件事：保存工程版本、整理当天证据、更新问题清单。

### 4.3 代码级验证优先级

仓库已经给出大量实现，因此每个阶段统一采用下面的顺序：

```text
静态阅读现有代码
  -> 跑仓库已有测试
  -> Vivado 综合/实现
  -> 上板复现
  -> 只改一个扩展点
  -> 重新测试并保存证据
```

不要先让 AI 重写已有模块。实验 0、2、4 共用基本相同的 `sobel_core.v`；实验 3、4 共用相同的 BRAM 原图读取结构；实验 5 已经包含控制协议和显示逻辑。

### 4.4 修改文件地图

| 任务 | 应优先修改的文件 | 注意 |
| --- | --- | --- |
| 实验 0 仿真 | `sobel_00_rtl_sim/` 下的 RTL、TB 和 tools | 这里是独立仿真基线 |
| 实验 1 扩展 | 实验 1 的 `hdmi_image_display.v` | 不要改 HDMI IP |
| 实验 2 扩展 | 实验 2 的 `hdmi_sobel_display.v` | 先解决 compile order，再改显示映射 |
| 实验 3 PS | 新 SDK 应用中的 `main.c` | 仓库 `ps_uart_bram_app/src/main.c` 作为源代码备份 |
| 实验 4 PS | 新 SDK 应用中的 `main.c` | SDK 应用名仍可能是 `ps_uart_bram_app` |
| 实验 5 PS | 新 SDK 应用中的 `main.c` | 备份源位于 `ps_uart_control_bram_app/src/main.c` |
| 实验 5 PL | 实验 5 的 `hdmi_bram_sobel_display.v` | 控制读取和显示模式都已实现 |
| 综合扩展 | `host_camera_uart/camera_uart_sender.py` 与 GUI | 提取公共缩放函数，避免重复 |

同名文件不能随意全局替换：

- 实验 0、2、4 的 `sobel_core.v` 基本一致。
- 实验 5 的 `sobel_core.v` 和 `rgb_to_gray.v` 使用同步复位，不能直接被实验 4 版本覆盖。
- 实验 3、4、5 的 `hdmi_bram_display.v` 当前逻辑一致，但实际使用的顶层模块不同。
- 仓库中的 PS 备份 `main.c` 与旧 SDK 应用副本当前一致；重建 SDK 后应确定一个主副本，并在提交前同步。

## 5. 各阶段任务拆分

## 5.1 阶段 A：环境与基线

### 目标

确保后续故障是代码问题，而不是版本、路径、串口或硬件连接问题。

### 任务

1. 复制课程工程作为工作副本。
2. 记录 Vivado、SDK、Python、Icarus 版本。
3. 确认开发板、JTAG、UART、HDMI 都能被 PC 识别。
4. 确认实际 COM 口。
5. 打开实验 1 工程，只检查 Sources 和 IP 状态，不立即升级。
6. 建立证据目录和每日实验日志。

### AI 可完成

- 生成环境检查脚本
- 分析 Vivado 报错和日志
- 检查工程中的绝对路径、缺失文件和版本信息
- 生成实验日志模板

### 必须人工完成

- 连接硬件
- 确认 COM 口、JTAG 和显示器
- 在 Vivado/SDK 中确认工程真实状态

### 验收

- 工程原件未被修改
- 工作副本可打开
- 所有工具版本有截图或文本记录
- 已知风险有记录，不带着红色工程错误进入实验 1

## 5.2 阶段 B：实验 0，RTL 仿真

### 目标

理解 UART 图像帧、RGB 转灰度、Sobel 数据流和关键握手信号。

### 基础步骤

```powershell
iverilog -V
python --version
cd <工作副本>\sobel_00_rtl_sim
.\run_sim.ps1
```

若 Windows 没有原生 Icarus：

```powershell
.\run_sim.ps1 -UseWsl
```

### 必看信号

- `frame_start`
- `rgb_valid`
- `gray_valid`
- `edge_valid`
- `edge_frame_done`

### 推荐小扩展

**更换输入图片并重新仿真。**

理由：修改范围小、容易成功，同时能得到新的输入图和输出图，适合写入仿真报告。

现有 testbench 已经自动检查错误帧头、错误格式和错误行号，这些属于基础验证，不应原样包装成个人扩展。若选择异常协议扩展，必须新增不同于现有三种场景的测试。

### AI 可完成

- 解释 `uart_rx.v`、`image_frame_rx.v`、`rgb_to_gray.v`、`sobel_core.v`
- 生成新的 `128×72 RGB888` 测试图和 HEX
- 解释 VCD 波形
- 草拟仿真报告

### 人工重点

- 确认仿真实际通过
- 选择有代表性的波形区间
- 截取输入图、输出图和波形
- 用自己的话说明 `edge_frame_done`

### 交付物

- `input_rgb.png`
- `sobel_out.png`
- VCD 文件
- 一张带信号名称的关键波形
- UART 帧格式说明
- 新旧输入图对边缘结果的对比

## 5.3 阶段 C：实验 1，HDMI 固定图片

### 目标

先单独验证 HDMI 720p 输出，避免后续把 HDMI 故障误判为 Sobel 或 BRAM 故障。

### 关键参数

```text
HDMI 输出：1280 × 720
输入图片：128 × 72
横向缩放：10
纵向缩放：10
ROM 像素：24'hRRGGBB
```

### 基础步骤

1. 打开 `sobel_01_hdmi_pattern.xpr`。
2. 确认 `top.v` 为顶层。
3. 检查 `video_clock`、`rgb2dvi_0`、XDC。
4. Run Synthesis。
5. Run Implementation。
6. Generate Bitstream。
7. Hardware Manager 中 Program Device。
8. 拍摄 HDMI 固定图。

### 推荐小扩展

**修改背景颜色。**

理由：只改非图像区域 RGB 映射，风险最低，同时能证明本人理解有效显示区域。

### 交付物

- 固定图 HDMI 照片
- 修改背景后的 HDMI 照片
- 坐标和 ROM 地址计算说明
- 资源利用率与时序截图

### 失败时的排查顺序

```text
显示器是否识别信号
  -> 时钟/IP 是否有效
  -> XDC 是否加载
  -> 顶层是否正确
  -> HDMI 差分管脚是否匹配
  -> 像素有效区是否输出非零数据
```

## 5.4 阶段 D：实验 2，固定图片 Sobel

### 目标

在不引入 PS、UART 和 BRAM 写入的条件下，单独验证 PL 图像处理链。

### 数据流

```text
image_rom
  -> rgb_to_gray
  -> sobel_core
  -> edge_mem
  -> HDMI
```

### 重点理解

- `rgb_to_gray` 输入输出及有效信号
- `sobel_core` 的行缓存和 3×3 邻域
- `edge_valid` 时写入 `edge_mem`
- HDMI 读取边缘帧的时机

### 工程检查重点

实验 2 的 `top.v` 通过 `` `include `` 引入 `image_rom_128x72.v`、`rgb_to_gray.v`、`sobel_core.v` 和 `hdmi_sobel_display.v`，而 `.xpr` 中又单独登记了部分同名 RTL。第一轮综合应重点检查是否出现 duplicate module、module not found 或 compile order 错误。

若出现重复定义，只保留一种管理方式：推荐让 `top.v` 使用 `include`，将被 include 的模块从独立编译源中移除；不要同时大改模块代码。

### 推荐小扩展

**彩色边缘标记。**

理由：只改 HDMI RGB 映射，后续可直接迁移到实验 5 的彩色叠加说明中。

### 交付物

- 原始灰度边缘图
- 彩色边缘图
- 数据流图
- `edge_mem` 写入/读取说明
- 资源与时序结果

## 5.5 阶段 E：实验 3，UART 图像到 HDMI 原图

### 目标

打通 PC、UART、PS、AXI BRAM、PL、HDMI 的完整链路。

### 数据与性能边界

```text
波特率：115200
格式：8N1
图像：128 × 72 RGB888
一帧协议包：27943 byte
理论有效速率：约 11520 byte/s
推荐发送帧率：0.2 fps
```

低帧率不是 PL 算法慢，而是 UART 带宽限制。报告中应明确这一点。

### 分层验证

1. 只下载 bitstream，确认 HDMI 基础输出。
2. 从 Vivado 导出包含 bitstream 的硬件平台。
3. 在新 SDK workspace 中创建 standalone BSP 和 Empty Application。
4. 复制 `ps_uart_bram_app/src/main.c`，编译并运行 PS 程序。
5. 串口助手确认：

```text
PS UART BRAM HDMI display
BRAM base: 0x40000000, baud: 115200
waiting for frame header
```

6. 关闭串口助手。
7. 发送单张图片：

```powershell
python camera_uart_sender.py --port COM7 --baud 115200 --image test.jpg --once --preview
```

8. 单张成功后再测试摄像头：

```powershell
python camera_uart_sender.py --port COM7 --baud 115200 --camera 0 --fps 0.2 --preview
```

9. 不稳定时增加：

```text
--line-delay 0.001
```

### 推荐小扩展

**串口帧率与稳定性记录。**

至少测试：

| 组别 | FPS | Line delay | 记录 |
| --- | ---: | ---: | --- |
| A | 0.1 | 0 | 是否完整、是否报错 |
| B | 0.2 | 0 | 是否完整、是否报错 |
| C | 0.2 | 0.001 | 是否更稳定 |

该扩展几乎不改代码，但能形成清楚的性能分析。

### 常见关键点

- 串口助手和 Python 不能同时占用 COM 口
- PC 与 PS 必须同为 115200 8N1
- `width=128`、`height=72`、格式 `0x18`
- 先等待 PS 打印 `waiting for frame header`
- 画面数秒更新一次属于正常现象

## 5.6 阶段 F：实验 4，UART 图像经 PL Sobel 显示

### 目标

在实验 3 的输入链路上加入 PL 灰度转换和 Sobel。

### 与实验 3 的唯一核心差异

```text
实验 3：BRAM 原图 -> HDMI
实验 4：BRAM 原图 -> 灰度 -> Sobel -> edge_mem -> HDMI
```

### 执行顺序

1. 确认实验 3 仍能正常接收单张图片。
2. 打开实验 4 工程。
3. 确认 `hdmi_pl_top.v` 例化 `hdmi_bram_sobel_display`。
4. 综合、实现、生成 bitstream。
5. 运行 PS 程序并检查启动文本为实验 4。
6. 先发单图，再发摄像头。
7. 确认 HDMI 显示黑白边缘而不是彩色原图。

### 推荐小扩展

**对比阈值 40、80、120 的边缘结果。**

理由：该工作会直接复用于实验 5 的动态阈值控制和最终报告的性能分析。

### 交付物

- UART 输入图像的 Sobel HDMI 照片
- 三组阈值对比
- 串口收到帧的日志
- 资源利用率和时序结果

## 5.7 阶段 G：实验 5，PC 控制显示

### 目标

在不中断图像链路的情况下，由 PC 动态控制：

- 原图
- 灰度图
- Sobel 二值边缘图
- 原图加彩色边缘
- Sobel 阈值
- 彩色叠加开关

### 控制协议

```text
A5 5A cmd value

cmd=01：显示模式
cmd=02：阈值 0..255
cmd=03：叠加开关
```

### 控制字建议

```text
BRAM 图像区：0x40000000 + 0x0000
BRAM 控制区：0x40000000 + 0x9000
```

必须确认图像区和控制区不重叠。

### 正确实施顺序

1. 先复现实验 4。
2. 确认现有 PC、PS、PL 代码已经包含控制实现，不先重写。
3. 运行仓库已有轻量控制仿真：

```powershell
iverilog -g2012 -o sim/display_control_model_tb.vvp sim/display_control_model.v sim/display_control_model_tb.v
vvp sim/display_control_model_tb.vvp
```

4. 检查 PS `main.c` 中 `cmd=01/02/03` 和控制字写入。
5. 检查 PL `hdmi_bram_sobel_display.v` 的三次 BRAM 控制字读取。
6. 检查 PC CLI/GUI 发送的四字节控制帧。
7. 补一个 BRAM 读延迟模型 testbench，验证控制字读取、扫描启动和 `sobel_done`。
8. 综合、实现、生成 bitstream。
9. 重建实验 5 的 SDK 平台/BSP，运行现有 `main.c`。
10. 上板依次验证 gray、edge、overlay。
11. 测试阈值 40、80、120。

### 已确认的地址设计

```text
图像像素数：128 × 72 = 9216 word
每像素：4 byte，格式 0x00RRGGBB
图像区字节数：9216 × 4 = 36864 = 0x9000
最后一个像素地址：0x8FFC
模式控制字：0x9000
阈值控制字：0x9004
叠加控制字：0x9008
BRAM 总范围：64 KB
```

地址没有重叠。需要验证的是 BRAM Port B 的读延迟和状态机采样时刻。

### 上位机命令

```powershell
python camera_uart_sender.py --port COM7 --baud 115200 --control-only --mode edge --threshold 80 --overlay off
python camera_uart_sender.py --port COM7 --baud 115200 --control-only --mode overlay --threshold 40 --overlay on
```

### 阶段验收门槛

- PS 能回显模式、阈值和叠加状态
- HDMI 模式确实变化
- 阈值变化能观察到边缘数量变化
- 图像发送和控制命令不冲突
- 有控制波形、串口截图和 HDMI 模式照片
- 单张图发送完成后等待画面稳定再截图；当前设计没有双缓冲，PS 写帧期间可能出现短暂撕裂

## 6. 第一周扩展选择汇总

| 实验 | 推荐扩展 | 修改量 | 风险 | 可复用价值 |
| --- | --- | ---: | ---: | --- |
| 实验 0 | 更换输入图并仿真 | 小 | 低 | 形成仿真报告对比 |
| 实验 1 | 修改 HDMI 背景色 | 很小 | 低 | 证明理解有效显示区 |
| 实验 2 | 彩色边缘标记 | 小 | 低 | 复用于实验 5 叠加 |
| 实验 3 | 帧率与稳定性记录 | 无或很小 | 低 | 形成性能分析 |
| 实验 4 | 40/80/120 阈值对比 | 小 | 低 | 复用于实验 5 控制 |

这组选择的特点是互不冲突、代码改动小、证据容易获取，而且大部分内容可以直接写进最终报告。

## 7. 第二周综合扩展建议

### 7.1 主线选择：上位机输入与缩放策略扩展

推荐选择综合扩展任务 1。仓库上位机已经支持：

- USB 摄像头
- 单张图片
- 多张图片
- 图片目录
- MP4/AVI 等视频
- 任意 CLI/GUI 宽高输入
- 实验 5 模式、阈值和叠加控制

因此不需要重写上位机，最合适的个人扩展是补齐“不同宽高比图像如何进入固定 `128×72` FPGA 处理链”的设计。

### 7.2 推荐功能

把当前直接 `cv2.resize()` 的单一拉伸方式改为可选择策略：

```text
stretch
    直接缩放到 128×72，可能改变宽高比

letterbox
    等比例缩放，空白区域补黑或指定颜色

center-crop
    等比例放大后居中裁剪，填满 128×72
```

PC 发送给 FPGA 的协议仍保持：

```text
128×72 RGB888
55 aa width_l width_h height_l height_h 18
```

这样无需修改 PS、BRAM、PL、HDMI 或 Sobel 尺寸，风险最低。

### 7.3 精确修改范围

| 文件 | 修改 |
| --- | --- |
| `camera_uart_sender.py` | 提取 `prepare_frame()`；增加 `--fit-mode`；记录原始尺寸和处理后尺寸 |
| `camera_uart_gui.py` | 增加 Fit mode 下拉框；调用同一个 `prepare_frame()`，避免 CLI/GUI 两套缩放代码 |
| 新增 Python 测试 | 测试 4:3、16:9、竖图的 stretch/letterbox/crop 输出 |
| README | 写清楚三种策略、固定 FPGA 尺寸和演示命令 |

当前 CLI 和 GUI 分别直接调用 `cv2.resize()`，存在重复逻辑。扩展时应只实现一个公共函数，两边复用。

### 7.4 离线验证

至少准备：

```text
640×480 图片：4:3
1920×1080 图片：16:9
1080×1920 图片：竖图
```

测试要求：

- 三种策略输出形状均为 `(72, 128, 3)`
- `letterbox` 不改变主体宽高比
- `center-crop` 无黑边且裁剪位置可解释
- 打包后长度为 `27943 byte`
- 帧头为 `55 aa 80 00 48 00 18`
- 原有控制命令字节不变化

### 7.5 上板演示

建议演示组合：

1. 单张 `640×480` 图片，依次发送 stretch、letterbox、center-crop。
2. 摄像头或 MP4 `1920×1080` 输入，保持 `128×72` 输出。
3. 在同一个输入下切换 original、gray、edge、overlay。
4. 记录三种策略下主体形状、边缘位置和黑边差异。

### 7.6 验收材料

- GUI 新增控件截图
- CLI 新参数帮助截图
- 三种缩放结果对比图
- Python 自动测试结果
- 两种原始尺寸、两种输入来源的上板照片或视频
- 原有实验 5 控制功能回归结果
- 一段说明：为何选择 PC 端统一为 `128×72`，而不修改硬件尺寸

### 7.7 进阶备选：Prewitt

只有在基础实验、实验 5 和主线扩展全部稳定后，才考虑增加 Prewitt。它需要新增 RTL、golden model、算法选择控制字和完整仿真，工作量显著更高。

若教师明确要求“必须修改 PL 算法”，再将 Prewitt 作为主扩展；否则不建议单人优先选择。

### 7.8 教师要求第二种硬件处理尺寸时

若“新处理尺寸”被严格解释为 FPGA 内部尺寸，建议另建工程支持 `64×36`，不要直接改坏 `128×72` 基线。需要同步修改：

- PS `IMG_WIDTH/IMG_HEIGHT`
- PC 默认发送宽高
- `scan_x/scan_y`、显示坐标和地址计算
- Sobel `WIDTH/HEIGHT`
- `rgb_mem/edge_mem` 深度
- HDMI 缩放倍数
- 仿真输入和 golden output

这是可选高风险路线，必须在主工程已完整归档后进行。

## 8. AI 与人工分工

### 8.1 适合交给 AI

- 阅读 Verilog、C、Python 和 Tcl
- 解释模块接口和数据流
- 生成小范围代码补丁
- 生成 Python golden model
- 生成 testbench 和测试向量
- 分析编译错误、时序报告和串口日志
- 比较修改前后代码
- 整理截图编号、图注和报告初稿
- 生成答辩问题及参考答案

### 8.2 不能完全交给 AI

- 判断板卡接线是否正确
- 确认 HDMI 真实显示内容
- 处理 JTAG、驱动和 COM 口占用
- 决定截图是否真实反映实验结果
- 在 Vivado GUI 中确认 IP、顶层、约束和运行状态
- 最终签字式结论和实验现象描述

### 8.3 每次让 AI 改代码时必须提供

```text
1. 当前目标
2. 相关文件完整内容或仓库路径
3. 模块接口
4. 当前错误日志
5. 期望输入输出
6. 不允许改动的部分
7. 验收命令
```

不要只说“帮我把这个 FPGA 项目做完”。一次只让 AI 完成一个可验证闭环。

### 8.4 推荐 AI 提问模板

```text
请先阅读以下 Verilog 模块和 testbench，不要立即改代码。
目标：在保持原接口和时序握手不变的前提下，实现 ______。
约束：Vivado 2017.4、Verilog-2001、图像 128x72、像素流每拍最多一个。
请输出：
1. 当前数据流和状态机分析；
2. 最小修改文件列表；
3. 可能的位宽、延迟和边界问题；
4. 修改补丁；
5. 对应 testbench；
6. 仿真通过标准。
```

## 9. 单人调试纪律

### 9.1 一次只改变一个变量

例如调试串口时，不同时修改波特率、图像尺寸和协议。调试算法时，不同时重建 HDMI IP。

### 9.2 每层先有独立成功证据

```text
PC 打包正确
PS 收帧正确
BRAM 地址正确
PL 算法正确
HDMI 时序正确
控制字正确
```

只有各层能独立证明，系统失败时才容易定位。

### 9.3 Vivado 错误分类

| 类型 | 处理 |
| --- | --- |
| Missing source/IP | 先修路径和依赖 |
| Syntax error | AI 可快速定位，先过语法 |
| Multiple drivers | 检查组合/时序块重复赋值 |
| Width mismatch | 明确每个中间量位宽和有无符号 |
| Timing failed | 找最长路径，再考虑流水线 |
| DRC error | 不忽略，确认是否阻止 bitstream |
| 普通 warning | 分类记录，确认是否影响功能 |

### 9.4 串口错误分类

| 现象 | 优先检查 |
| --- | --- |
| 无启动信息 | PS 程序是否运行、串口号、波特率 |
| 一直等帧头 | PC 是否发送、COM 是否被占用、帧头 |
| `frame error` | 宽高、格式、行号、发送节奏 |
| HDMI 不更新 | BRAM 是否写入、PL 地址和显示状态 |
| 画面不完整 | 降低 FPS、增加 line delay |

## 10. 证据收集矩阵

| 阶段 | 必拍/必存 | 报告用途 |
| --- | --- | --- |
| 环境 | 工具版本、设备管理器、工程 Sources | 环境说明 |
| 实验 0 | 输入图、输出图、关键波形 | 仿真报告 |
| 实验 1 | 固定图、背景扩展 | HDMI 原理与扩展 |
| 实验 2 | Sobel、彩色边缘 | PL 算法链 |
| 实验 3 | PS 日志、原图 HDMI、帧率记录 | PS/PL 与性能 |
| 实验 4 | Sobel HDMI、三阈值对比 | 综合基础实验 |
| 实验 5 | 模式切换、阈值、叠加、控制波形 | 控制功能 |
| 综合扩展 | 三种缩放对比、自动测试、两种输入来源 | 扩展章节 |
| Vivado | LUT/FF/BRAM/DSP、WNS/TNS | 资源时序分析 |
| 最终演示 | 连续操作视频 | 验收答辩 |

截图命名建议：

```text
exp00_wave_edge_frame_done.png
exp01_hdmi_background_blue.jpg
exp03_uart_waiting_header.png
exp05_mode_overlay_threshold40.jpg
ext_letterbox_crop_compare.png
```

## 11. 三份报告的写作路径

### 11.1 仿真报告

结构：

1. 实验目标
2. 输入图像和 UART 帧格式
3. `rgb_to_gray` 原理
4. `sobel_core` 原理
5. 关键波形
6. 输入图和输出图
7. 小扩展结果
8. 问题与解决

在实验 0 完成当天就生成初稿，不要等到最后回忆。

### 11.2 初步实验报告

结构：

1. 系统总体框图
2. 实验 0 至实验 5 完成表
3. 实验 0 至实验 4 小扩展
4. PC、PS、PL 数据流
5. 当前问题
6. 上位机输入与缩放策略扩展方案
7. 仿真计划和预计修改文件

### 11.3 最终报告

建议章节：

1. 课程设计任务
2. 系统总体架构
3. 图像与控制协议
4. 基础实验复现
5. 第一周基础扩展
6. PC 控制显示设计
7. 多输入来源与缩放策略综合扩展
8. 软件离线测试与协议回归
9. 上板结果
10. 资源、时序和性能分析
11. 问题记录与解决过程
12. 总结

每个功能章节使用同一叙述模式：

```text
目标
  -> 设计
  -> 修改文件
  -> 仿真
  -> 上板
  -> 结果
  -> 问题
```

## 12. 风险清单与止损条件

| 风险 | 概率 | 影响 | 处理 |
| --- | ---: | ---: | --- |
| Vivado 版本不兼容 | 高 | 高 | 优先 2017.4，升级前复制工程 |
| `hdmi_common` 内容不完整 | 中 | 高 | 先尝试工程内本地 XCI/XDC；不要立即重建 IP |
| SDK 平台和 BSP 缺失 | 高 | 高 | Vivado 导出硬件后，在新 workspace 重建平台/BSP |
| 仓库没有任何已验证生成物 | 高 | 高 | 不接受“源码存在”等同于“功能通过” |
| BD 重建脚本删除现有 BD | 中 | 高 | 只在工程副本中、现有 BD 确实损坏时运行 |
| 实验 2 编译源重复 | 中 | 中 | 首次综合检查 duplicate module 和 compile order |
| 串口被占用 | 高 | 中 | 串口助手与 Python 二选一 |
| UART 帧率过低被误判 | 高 | 中 | 明确 0.2 fps 是设计限制 |
| PS 写帧与 PL 扫描并发导致撕裂 | 中 | 中 | 单帧发送完成后等待稳定再取证 |
| AI RTL 能编译但功能错误 | 中高 | 高 | golden output + testbench + 波形 |
| 多个工程同时修改失去基线 | 中 | 高 | 每实验独立版本，阶段性提交 |
| 综合扩展时间失控 | 中 | 高 | 主线只改 PC 缩放；Prewitt 保留为进阶备选 |
| 最后缺截图 | 高 | 高 | 每阶段完成即保存证据 |

止损规则：

1. HDMI 基础实验未成功，不进入 UART。
2. 实验 3 未成功，不进入实验 4。
3. 实验 4 未成功，不做实验 5 上板控制。
4. 实验 5 现有功能未全部复现，不做综合扩展。
5. 上位机离线测试未通过，不连接开发板验证扩展。
6. 最终演示前 24 小时停止增加新功能，只修复和整理。

## 13. 最终验收清单

### 功能

- [ ] 实验 0 输入、输出和波形齐全
- [ ] 实验 1 HDMI 固定图成功
- [ ] 实验 2 固定图 Sobel 成功
- [ ] 实验 3 UART 原图显示成功
- [ ] 实验 4 UART Sobel 显示成功
- [ ] 实验 5 模式、阈值、叠加控制成功
- [ ] 实验 0 至实验 4 各有一个小扩展
- [ ] 多输入来源与三种缩放策略扩展完成

### 工程

- [ ] 修改文件清单完整
- [ ] PC、PS、PL 修改分别说明
- [ ] 所有仿真可重复运行
- [ ] bitstream 可重新生成
- [ ] 最终工程不是只保留生成文件

### 证据

- [ ] 关键波形
- [ ] 串口启动和收帧日志
- [ ] HDMI 各模式照片
- [ ] 阈值对比
- [ ] 三种缩放策略离线对比和自动测试
- [ ] 资源利用率
- [ ] 时序结果
- [ ] 最终演示视频

### 报告

- [ ] 仿真报告
- [ ] 初步实验报告
- [ ] 最终报告
- [ ] 图号、表号和文件名一致
- [ ] 所有实验现象都来自真实运行
- [ ] 能解释 UART 带宽瓶颈
- [ ] 能解释 PS、BRAM、PL 和 HDMI 的数据流

## 14. 推荐的第一步

正式实施时，第一轮只做以下闭环：

```text
复制工程
  -> 安装并确认 Python、Icarus、VVP 可执行
  -> 跑实验 0 默认仿真
  -> 保存输入图、输出图和 VCD
  -> 更换一张输入图再跑一次
  -> 打开实验 1 检查 Vivado 2017.4、HDMI IP 和 XDC
  -> 当天完成仿真报告初稿
```

完成这个闭环后，再进入 HDMI。实验 3 开始前另设一个明确检查点：必须能够从 Vivado 导出硬件，并在新 SDK workspace 中建立 BSP 和最小 Hello World 应用。这样可以提前暴露环境问题，不会把 SDK 缺失拖到 UART 联调阶段。

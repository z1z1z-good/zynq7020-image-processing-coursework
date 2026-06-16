# 课程设计工作区

本目录用于管理个人课程设计的实施过程、证据和报告。教师提供的实验源码与说明保持原有结构，个人修改按照 Git 分支和里程碑逐步合并。

教师仓库：<https://github.com/zhouxzh/FPGA-course/tree/main/zynq7020-image-processing>

## 当前状态

| 项目 | 状态 |
| --- | --- |
| 正式 Git 工作树 | 已建立 |
| 教师仓库远端 `upstream` | 已配置 |
| 个人私有远端 `origin` | 已配置并完成首次推送 |
| Vivado / Vitis | Vivado 2023.2 已完成实验 1、实验 3 隔离构建；实验 3 PS 源码仅完成 ARM GNU 静态编译检查，正式 Vitis/BSP/ELF 构建待完成 |
| Python 上位机环境 | Python 3.11，基础依赖已验证 |
| 实验 0 至实验 5 | 实验 0 已通过；实验 1 远程阶段完成；实验 2 在 `exp/02-hdmi-sobel` 分支已完成远程阶段；实验 3 的 PL 阶段通过，正式 Vitis 构建和现场验证待完成；实验 4 的 PL Sobel 阶段已完成远程开发（彩色边缘扩展、协同仿真、综合/实现/bitstream 与 PS 源码检查通过，待现场）；实验 5 尚未开始 |
| 开发板实机测试 | 等待板卡和连接条件 |

源码存在不等于实验已经通过。只有实际运行并保存证据后，才更新实验状态。

## 实施原则

1. 先复现，再做小范围修改。
2. 先仿真，再综合和实现，最后上板。
3. 一次只推进一个实验，不并行升级多个 Vivado 工程。
4. 每个里程碑都保存命令、日志、截图和问题记录。
5. 不提交 Vivado/Vitis 生成目录、bitstream、ELF 和临时仿真产物。

完整路线、环境复核、风险和验收要求见
[单人 AI 辅助实施报告](docs/ZYNQ7020图像处理课程设计_单人AI辅助实施报告.md)。

开发板暂不可用时，实验 1 至实验 5 的可执行范围、分批顺序、交付物和现场门禁见
[无板开发分批计划](docs/BOARDLESS_DEVELOPMENT_PLAN.md)。

「上位机 → PS → BRAM → PL → HDMI」无板卡软硬件协同仿真的可复用流程（实验 3 建立，
实验 4、实验 5 应复用）见 [无板卡协同仿真方法论](docs/BOARDLESS_COSIM_METHODOLOGY.md)。

## 实验路线

| 里程碑         | 内容                            | 当前状态                        |
| ----------- | ----------------------------- | --------------------------- |
| `exp00`     | RTL 仿真、输入输出图与关键波形             | 默认仿真通过（ModelSim SE-64 10.5） |
| `exp01`     | HDMI 固定图片                     | 蓝色边框扩展、XSim、实现和 bitstream 通过；待现场上板 |
| `exp02`     | 固定图片 Sobel                    | 全链 XSim、实现和 bitstream 通过；待现场 HDMI 验证 |
| `exp03`     | PC UART -> PS -> BRAM -> HDMI | 边框扩展、协议黄金模型自检、XSim、实现、bitstream 与 PS 源码检查通过；正式 Vitis 构建和现场上板待完成 |
| `exp04`     | UART 图像 -> PL Sobel -> HDMI   | 彩色边缘标记扩展、协同仿真链、XSim 自检、综合/实现/bitstream 与 PS 源码检查通过；完整 Vitis 构建和现场上板待完成 |
| `exp05`     | PC 控制模式、阈值和叠加                 | 远程协同仿真 + 综合/实现/DRC/bitstream + PS 源码检查通过；待现场上板 |
| `extension` | 上位机缩放策略扩展                     | 未开始                         |

默认综合扩展为 `stretch`、`letterbox`、`center-crop` 三种上位机缩放策略。Prewitt 仅作为基础路线全部稳定后的进阶备选。

## Git 工作流

- `upstream`：教师仓库，只拉取，不推送。
- `origin`：个人私有仓库，保存个人提交和标签。
- `main`：只合并已验证、可复现的里程碑。
- 工作分支：使用 `exp/00-rtl-sim`、`exp/01-hdmi-pattern` 等短期分支。
- 工具迁移：使用独立分支 `toolchain/vivado-2023.2`，不得直接覆盖唯一的 2017.4 基线。

每次提交只表达一个目的，推荐格式：

```text
docs: add experiment 0 run record
test: verify baseline Sobel simulation
feat: add letterbox frame preparation
fix: restore BRAM read latency handling
```

同步教师仓库时：

```powershell
git fetch upstream
git log --oneline --left-right main...upstream/main
```

仅在实验里程碑之间评估并合并上游更新，不在正在迁移或调试的分支中直接同步。

## 证据管理

证据统一放在 [`evidence`](evidence/README.md)，不得使用未经真实运行确认的截图或结果。

每个实验至少记录：

- 执行命令和工具版本
- 一份关键日志
- 仿真波形或实机现象
- 修改文件和提交号
- 结论、遗留问题及下一步

## 远程协作上板工作流

开发板位于用户现场，代码开发与构建检查在远程电脑完成。实验 1 至实验 5 使用以下闭环：

1. AI 从 `main` 创建当前实验的独立分支，只处理一个实验。
2. AI 阅读实验 README 和相关 RTL、Tcl、C、Python 文件，完成静态检查、仿真及可执行的
   Vivado/Vitis 命令行检查。
3. AI 不伪造 JTAG、串口或 HDMI 结果；无法连接开发板时，将状态明确写为“待现场验证”。
4. AI 更新实验 README，写明分支、提交号、构建命令、接线、下载、运行、预期现象和回传清单。
5. AI 提交并推送实验分支。默认不提交 Vivado/Vitis 大型生成目录、bitstream 和 ELF。
6. 用户在开发板旁下载或拉取该分支，按 README 完成构建、下载和现场测试。
7. 用户将原始日志、串口文本、HDMI 照片或视频截图、资源时序摘要和失败步骤回传。
8. AI 根据真实材料修复问题、整理到对应 `coursework/evidence` 目录，再次提交并推送。
9. 只有现场结果满足验收标准，才把实验标记为“上板通过”并进入下一实验。

各实验的现场分工：

| 实验 | AI 推送前完成 | 用户现场完成 | 必须回传 |
| --- | --- | --- | --- |
| 实验 0 | RTL 仿真、输入输出图、日志和波形 | 无 | 无 |
| 实验 1 | Vivado 工程检查、综合/实现脚本和上板步骤 | JTAG 下载、HDMI 固定图验证 | HDMI 照片、bitstream 结果、资源和时序摘要 |
| 实验 2 | 固定图 Sobel 工程检查、综合/实现和步骤 | JTAG 下载、HDMI Sobel 验证 | Sobel HDMI 照片、资源和时序摘要 |
| 实验 3 | Vivado/Vitis 构建检查、PS 程序和上位机离线检查 | 下载 FPGA、运行 PS、UART 传图和 HDMI 验证 | 串口日志、上位机日志、原图 HDMI 照片 |
| 实验 4 | Vivado/Vitis 构建检查、PL Sobel 和上位机检查 | 下载 FPGA、运行 PS、UART 传图和 Sobel HDMI 验证 | 串口日志、Sobel HDMI 照片、阈值对比材料 |
| 实验 5 | 控制仿真、Vivado/Vitis 构建检查和控制命令检查 | 模式、阈值、叠加的完整上板验证 | 串口回显、各模式照片、阈值对比、控制失败记录 |

注意：

- 用户侧必须记录实际使用的板卡、COM 口、Vivado/Vitis 版本和测试日期。
- 失败时不要只发“运行失败”，应回传所执行步骤、完整错误文本和最后一个正常现象。
- HDMI 照片应同时拍到有效画面；需要证明板卡连接时，再补一张包含开发板和显示器的照片。
- 可复用的启动 Prompt 和回传模板见
  [`docs/REMOTE_HARDWARE_WORKFLOW_PROMPT.md`](docs/REMOTE_HARDWARE_WORKFLOW_PROMPT.md)。

## 实验 0 实际结果

2026-06-15 在 `exp/00-rtl-sim` 分支完成仓库默认仿真：

1. `main` 与 `origin/main` 同步后创建实验分支。
2. 本机未找到 Icarus/VVP，脚本自动选择 ModelSim SE-64 10.5。
3. 未修改 RTL 和 testbench；编译结果为 0 errors、0 warnings。
4. testbench 输出 `Sobel RGB888 simulation passed`，仿真结束时间为 `275314057 ns`。
5. 默认 `128x72` 输入、Sobel 输出、精简日志和关键波形已保存到
   [`evidence/01_rtl_sim`](evidence/01_rtl_sim/README.md)。
6. 原始 VCD 约 127 MB，保留在忽略的 `build/` 目录中，不提交大型生成物。

以上里程碑只确认实验 0 默认仿真；实验 1 的独立状态见下一节。

## 实验 1 远程开发结果

2026-06-15 在 `exp/01-hdmi-pattern` 完成远程开发阶段：

1. 从已合并实验 0 的 `main` 创建分支，未修改实验 2 及后续实验。
2. 使用 Vivado 2023.2 XSim 验证 HDMI 时序、蓝色边框、`9216` 个 ROM 像素及 RGB 映射。
3. 使用隔离 Tcl 工程编译归档的 `video_clock` 和 `rgb2dvi` 源码，未覆盖 2017.4 XPR。
4. 完成可配置边框扩展，默认在有效画面四周叠加 16 像素 `24'h0066ff` 蓝色边框。
5. 综合、布局布线和 bitstream 生成通过；WNS `7.772 ns`、TNS `0 ns`。
6. DRC 为 0 error、1 warning；`ZPS7-1` 来自本实验纯 PL 设计未实例化 PS7。
7. 资源占用为 232 LUT、179 FF、12 BRAM、1 MMCM 和 8 OSERDES。
8. 远程构建基线提交为 `fab4bce33a8382f8620659d42599c479fa3fadb6`；
   扩展的最终提交号以 `exp/01-hdmi-pattern` 当前 HEAD 为准。

现场下载、HDMI 验收和回传清单见
[`sobel_01_hdmi_pattern/README.md`](../sobel_01_hdmi_pattern/README.md) 的“远程开发结果与现场上板流程”。
在收到真实 HDMI 照片和现场日志前，实验 1 不标记为“上板通过”。

## 实验 3 远程开发结果

2026-06-15 在 `exp/03-uart-hdmi` 完成 PL 远程开发阶段，PS 正式 Vitis 构建仍待闭环：

1. 从与 `origin/main` 一致的 `main`（含实验 0、实验 1 成果）创建分支，未修改实验 4、实验 5。
2. 完成“图像边框”基础扩展：`hdmi_bram_display.v` 新增 `BORDER_WIDTH`（默认 `20`）和
   `BORDER_COLOR`（默认 `24'h0066ff`），仅改显示映射，不影响 BRAM 图像数据。
3. 协议黄金模型编码与 PS `receive_frame` 解析往返无损（`9216` 像素逐像素一致），错误码
   `-1/-2/-3/-5/-7` 与 `main.c` 一致（`generate_exp03_expected.py`）；尚未直接回归上位机发送脚本。
4. XSim 验证 HDMI 时序、有效像素数、HS/VS、10x 缩放地址、读延迟流水线对齐和边框映射。
5. 使用隔离 Tcl 工程在 build 目录内重建 PS7 + AXI BRAM Block Design（全局综合，IP 版本随
   2023.2 自动解析），未覆盖 2017.4 BD；综合、实现、bitstream 与 XSA 导出通过。
6. WNS `8.173 ns`、TNS `0 ns`、WHS `0.062 ns`、THS `0 ns`；DRC 0 violations
   （本实验实例化 PS7，无 `ZPS7-1` 警告）。
7. 资源占用为 `1775` LUT、`1504` FF、`16` BRAM、`0` DSP、`1` MMCM。
8. PS 程序 `main.c` 用 `arm-none-eabi-gcc 12.2.0` 静态编译检查 0 error、0 warning；完整 Vitis
   BSP/app/ELF 构建脚本为 `build_exp03_ps_app.tcl`，本次 XSCT 连接超时，正式构建尚未完成。

仿真、协议黄金模型自检、预期 HDMI 图、资源、时序、DRC 和 PS 编译证据见
[`evidence/04_uart_hdmi`](evidence/04_uart_hdmi/README.md)。
现场下载、运行、HDMI 验收和回传清单见
[`sobel_03_uart_hdmi/README.md`](../sobel_03_uart_hdmi/README.md) 的“远程开发结果与现场上板流程”。
在收到真实 HDMI 照片、串口日志和 Hardware Manager 记录前，实验 3 不标记为“上板通过”。

## 实验 4 远程开发结果

2026-06-16 在 `exp/04-uart-sobel` 完成 PL Sobel 远程开发阶段，PS 完整 Vitis 构建仍待闭环：

1. 从与 `origin/main` 一致的 `main`（含实验 3 与协同仿真方法论）创建分支，未修改实验 3、实验 5。
2. 完成“彩色边缘标记”基础扩展：`hdmi_bram_sobel_display.v` 新增 `EDGE_THRESHOLD`（默认 `80`）和
   `EDGE_COLOR`（默认 `24'h00ff00` 绿色），`edge_pixel >= EDGE_THRESHOLD` 的像素以彩色突出、其余为黑色；
   仅改显示映射，`edge_mem` 仍保存原始 8 bit Sobel 强度，不影响 BRAM 扫描、`rgb_to_gray` 和 `sobel_core`。
3. 复用实验 3 的无板卡协同仿真方法论扩到 Sobel：新增 RGB→灰度→Sobel 软件 golden（与 `sobel_core.v`/
   `rgb_to_gray.v` 一致），真实 `camera_uart_sender` 打包与本地编码逐字节一致，真实 `main.c` 解析的
   原始 RGB framebuffer 与 golden 逐像素一致，错误码 `-1/-2/-3/-5/-7` 一致；RTL 渲染 `1280x720`
   边缘帧（921600 像素）与软件 golden 逐像素一致（`EXP04_COSIM_CHAIN=passed`）。
4. XSim 自检通过：显示映射、HDMI 时序、`sobel_done` 和彩色边缘像素（`active=36864 green=4436`）。
5. 隔离 Tcl 工程全局综合重建 PS7 + AXI BRAM Block Design（IP 版本随 2023.2 解析），未覆盖 2017.4 BD；
   综合、实现、bitstream 与 XSA 导出通过。
6. WNS `+13.453 ns`、TNS `0`、WHS `+0.058 ns`、THS `0`；`4446` LUT、`3662` FF、`18` BRAM36、`0` DSP、
   `1` MMCM；DRC `0` errors（`20` 个 REQP-1839 + `1` 个 CHECK-3 warning，源于 `sobel_core` 异步复位
   驱动 `edge_mem` 地址，已说明、不阻塞）。
7. PS 程序 `main.c`（与实验 3 接收逻辑一致）用 `arm-none-eabi-gcc 12.2.0` 源码级编译 0 error、0 warning；
   完整 Vitis BSP/app/ELF 脚本为 `build_exp04_ps_app.tcl`，本环境 XSCT 连接超时，正式构建尚未完成。

仿真、协同仿真、阈值对比、预期 HDMI 图、资源、时序、DRC 和 PS 编译证据见
[`evidence/05_uart_sobel`](evidence/05_uart_sobel/README.md)。
现场下载、运行、HDMI 验收和回传清单见
[`sobel_04_uart_sobel_hdmi/README.md`](../sobel_04_uart_sobel_hdmi/README.md) 的“远程开发结果与现场上板流程”。
在收到真实 HDMI 照片、串口日志和 Hardware Manager 记录前，实验 4 不标记为“上板通过”。

## 实验 5 远程开发结果

2026-06-16 在 `exp/05-pc-control` 完成远程开发阶段，PS 正式 Vitis 构建与上板仍待现场：

1. 从含 AGENTS.md 的 `main`（`07a0934`，与 `origin/main` 一致）创建分支与独立工作树，未改动其他实验。
2. 核对既有 PC / PS / PL 控制实现（控制帧 `A5 5A cmd value`、PS `wait_for_packet_start` 分发 + 控制字写入、PL 每帧读控制字 + 四模式显示 mux），未重写。
3. 无板卡协同仿真链 `EXP05_COSIM_CHAIN=passed`：真实上位机图像打包（27943B）+ 控制帧（12B）逐字节一致；真实 `main.c` 分发产出图像区（9216 word）与 golden 一致、控制字 `0x9000/4/8` 与下发（mode=3/thr=40/overlay=1）一致；6 个错误注入码与 `main.c` 一致；`mode=0/1/2/3` + 阈值 40/80/120 + `overlay=0/1` 共 7 组全分辨率渲染逐像素一致（右下角单像素边界伪影已说明）。
4. XSim 自检 `EXP05_SELFCHECK_TB=passed`（有效像素数 / HS/VS / sobel_done / 显示映射自洽）。
5. 隔离 Tcl 工程重建 PS7 + AXI BRAM Block Design（全局综合，IP 版本随 2023.2 解析），未覆盖 2017.4 BD；综合、实现、bitstream 与 XSA 导出通过。
6. WNS `0.325 ns`、TNS `0 ns`、WHS `0.043 ns`、THS `0 ns`；DRC `0` violations。
7. 资源占用 `10795` LUT、`4113` FF、`20` BRAM、`0` DSP、`1` MMCM。
8. PS `main.c` 用 `arm-none-eabi-gcc 12.2.0` 源码级编译 0 error、0 warning；完整 Vitis BSP/ELF 脚本为 `build_exp05_ps_app.tcl`，本环境 XSCT 连接超时，正式构建待现场。

仿真、协同仿真、预期画面、资源、时序、DRC 和 PS 编译证据见
[`evidence/06_pc_control`](evidence/06_pc_control/README.md)。
现场下载、运行、各模式 HDMI 验收和回传清单见
[`sobel_05_pc_control_display/README.md`](../sobel_05_pc_control_display/README.md) 的“远程开发结果与现场上板流程”。
在收到真实 HDMI 各模式照片、串口控制回显和 Hardware Manager 记录前，实验 5 不标记为“上板通过”。

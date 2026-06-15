# 课程设计工作区

本目录用于管理个人课程设计的实施过程、证据和报告。教师提供的实验源码与说明保持原有结构，个人修改按照 Git 分支和里程碑逐步合并。

教师仓库：<https://github.com/zhouxzh/FPGA-course/tree/main/zynq7020-image-processing>

## 当前状态

| 项目 | 状态 |
| --- | --- |
| 正式 Git 工作树 | 已建立 |
| 教师仓库远端 `upstream` | 已配置 |
| 个人私有远端 `origin` | 已配置并完成首次推送 |
| Vivado / Vitis | 2023.2，待在 Git 分支中验证旧工程迁移 |
| Python 上位机环境 | Python 3.11，基础依赖已验证 |
| 实验 0 至实验 5 | 实验 0 默认 RTL 仿真已通过；实验 1 至实验 5 尚未验证 |
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

## 实验路线

| 里程碑         | 内容                            | 当前状态                        |
| ----------- | ----------------------------- | --------------------------- |
| `exp00`     | RTL 仿真、输入输出图与关键波形             | 默认仿真通过（ModelSim SE-64 10.5） |
| `exp01`     | HDMI 固定图片                     | 未开始                         |
| `exp02`     | 固定图片 Sobel                    | 未开始                         |
| `exp03`     | PC UART -> PS -> BRAM -> HDMI | 未开始                         |
| `exp04`     | UART 图像 -> PL Sobel -> HDMI   | 未开始                         |
| `exp05`     | PC 控制模式、阈值和叠加                 | 未开始                         |
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

本里程碑只确认实验 0 默认仿真；更换输入图的小扩展和实验 1 均未开始。

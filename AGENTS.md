# ZYNQ7020 图像处理课程设计 Agent 指南

本文件供 Codex、Claude 等代码 Agent 接手本仓库时使用。所有说明和汇报优先使用中文，
Vivado、XSim、Sobel、HDMI、RTL、WNS/TNS 等技术名词保持原样。

> 本文件只放**长期稳定的规则与入口**；各实验的实时进度以
> `zynq7020-image-processing/coursework/README.md` 为准，不要在本文件里写会过期的状态快照。

## 仓库与工作范围

- Git 工作树式管理：每个实验在独立工作树 / 短期分支推进
  （`exp/00-rtl-sim`、`exp/01-hdmi-pattern`、`exp/02-hdmi-sobel`、`exp/03-uart-hdmi`、
  `exp/04-uart-sobel`、`exp/05-pc-control`）。
- 课程项目根：`zynq7020-image-processing`；总览与**实时状态**见 `coursework/README.md`。
- 远端：`origin` 个人私有仓库（可推送），`upstream` 教师仓库（只拉不推）。
- 未获用户明确要求时不要合并到 `main`（`main` 只合并已验证、可复现的里程碑）。
- 不要修改或清理与当前任务无关的用户文件；不要扰动其他实验工作树。
- 禁止使用 `git reset --hard`、`git checkout --` 等会覆盖已有工作的命令。

## 开始工作前

先执行并阅读结果：

```bash
git status --short
git branch --show-current
git log -5 --oneline
git remote -v
git fetch            # 并确认本地 main 与 origin/main 的关系
```

然后按任务范围阅读（不要跳读；文档与实际代码/运行冲突时，以代码与实际运行结果为准）：

1. `zynq7020-image-processing/README.md` 与 `coursework/README.md`
2. `coursework/docs/`：`BOARDLESS_DEVELOPMENT_PLAN.md`、`BOARDLESS_COSIM_METHODOLOGY.md`、
   `REMOTE_HARDWARE_WORKFLOW_PROMPT.md`、`ZYNQ7020图像处理课程设计_单人AI辅助实施报告.md`
3. 对应实验目录的 `README.md` 及其全部 RTL、testbench、Tcl、XDC、C、Python 与脚本
4. 对应 `coursework/evidence/<exp>` 的证据说明，以及上一实验已验证的结论
5. 检查其他工作树/分支是否有尚未并入 `main` 的相关文档或状态差异

保留工作树中已有的修改；发现陌生改动先判断是否与任务相关，不得直接撤销。

## 关键环境事实（无开发板的远程阶段）

- 工具：Vivado/XSim 2023.2、Vitis 2023.2、Python、host gcc、Vitis 自带 arm-none-eabi-gcc；
  目标器件 `xc7z020clg400-2`；原始工程来自 Vivado/SDK 2017.4。
- 本自动化环境下 Vivado/Vitis **无法派生子进程**：`launch_runs` / `launch_simulation` 报
  `Spawn failed`，XSCT 连接 Vitis 后端超时。绕过方式（详见 `BOARDLESS_COSIM_METHODOLOGY.md`）：
  - 仿真直调 `xvlog` → `xelab` → `xsim`，不用 `launch_simulation`；
  - bitstream 用非项目全局综合（`synth_design`/`opt_design`/`place_design`/`route_design`/
    `write_bitstream`，BD 设 `synth_checkpoint_mode None`，IP 版本动态解析以避免 2017.4 版本号
    在 2023.2 不被支持）；
  - PS 用 host gcc 主机模型与 arm-none-eabi-gcc 源码级 `-c` 检查；完整 Vitis BSP/ELF 须正常 Vitis 环境。
- 「上位机 → PS → BRAM → PL → HDMI」无板卡软硬件协同仿真流程见
  `BOARDLESS_COSIM_METHODOLOGY.md`（实验 3 建立、实验 4 复用，已有 exp3 / exp4 两个 worked example）。
- 本机用户名含特殊字符：给 Windows 程序（python.exe / *.bat / gcc）传参用 `D:/` 正斜杠路径，
  不要传 MSYS `/x/...` 路径；推送经代理可能间歇性 SSL 失败，循环重试 5~6 次即可。

## 实施规则

1. 先读代码和证据，再做修改；不重复已经通过的工作，除非需要回归验证。
2. 一次只推进一个实验，不提前实现后续实验功能。
3. 优先复用仓库已有 RTL、Tcl 和验证模式，避免无关重构。
4. 不得覆盖或升级唯一的原始 2017.4 XPR / Block Design；Vivado 2023.2 使用隔离、可删除重建的 Tcl 工程。
5. 不提交 `.runs`、`.cache`、`.gen`、`.bit`、XSA、ELF、VCD 等大型生成物；中间产物写入已忽略的 `build/`。
6. 不伪造 JTAG、Hardware Manager、HDMI、串口或开发板结果。
7. 没有真实硬件证据时，状态只能写为「远程仿真和构建通过，待现场验证」；
   严格区分「协同仿真通过」与「上板通过」。
8. 文档使用 UTF-8；中文描述保持正常可读，技术名词不强行翻译。

## 验证与提交

根据改动范围运行相关 testbench、Python 自检和 Vivado Tcl 流程。提交前至少：

```bash
git diff --check
git status --short
```

并确认：改动仅覆盖当前任务、生成物没有进入 Git、README/证据/实现结果一致、
用户提供的真实结果与 Agent 推断有明确区分。

提交信息使用简洁的 Conventional Commits 风格（`feat:`/`fix:`/`test:`/`build:`/`docs:`/`chore:`）。
用户要求推送时，先提交本地分支再推送对应远程分支，推送后核对 `HEAD` 与上游一致，
并汇报分支、提交号、验证结果和仍待现场完成的项目。

## 现场协作

开发板在用户现场，远程只做仿真 / 构建 / 源码检查；现场下载、串口、HDMI 由用户完成，
回传真实证据后再更新实验状态并归档到对应 `coursework/evidence/<exp>`。可复用的启动 Prompt 与
回传模板见 `coursework/docs/REMOTE_HARDWARE_WORKFLOW_PROMPT.md`。反代服务、模型地址和凭据属于
本地运行环境，不得写入仓库、日志或提交历史。

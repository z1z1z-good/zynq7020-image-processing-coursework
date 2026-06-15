# ZYNQ7020 图像处理课程设计 Agent 指南

本文件供 Codex、Claude 等代码 Agent 接手本仓库时使用。所有说明和汇报优先使用中文，
Vivado、XSim、Sobel、HDMI、RTL、WNS/TNS 等技术名词保持原样。

## 仓库与工作范围

- Git 工作树：本文件所在目录。
- 课程项目：`zynq7020-image-processing`。
- 课程总览：`zynq7020-image-processing/coursework/README.md`。
- 当前实验分支：`exp/02-hdmi-sobel`。
- 不要在未获用户明确要求时合并到 `main`。
- 不要修改或清理与当前任务无关的用户文件。
- 禁止使用 `git reset --hard`、`git checkout --` 等命令覆盖已有工作。

## 开始工作前

先执行并阅读结果：

```powershell
git status --short
git branch --show-current
git log -5 --oneline
git remote -v
```

然后按任务范围阅读：

1. `zynq7020-image-processing/coursework/README.md`
2. 对应实验目录中的 `README.md`
3. 对应 `coursework/evidence` 目录中的证据说明
4. 相关 RTL、testbench、Tcl、XDC 和生成脚本

保留工作树中的已有修改。发现陌生改动时先判断是否与任务相关，不得直接撤销。

## 当前项目状态

- 实验 0：RTL 默认仿真通过。
- 实验 1：XSim、Synthesis、Implementation 和 Bitstream 通过，待现场 HDMI 验证。
- 实验 2：全链路 XSim、Synthesis、Implementation、DRC 和 Bitstream 通过，待现场 HDMI 验证。
- 实验 3 至实验 5：尚未开始。
- 当前 Vivado 版本：2023.2。
- 目标器件：`xc7z020clg400-2`。

实验 2 默认阈值为 `80`，阈值 `40`、`80`、`120` 的白色源像素数分别为
`1307`、`1274`、`1234`。实现结果为 WNS `1.578 ns`、TNS `0.000 ns`、
WHS `0.080 ns`、THS `0.000 ns`，资源占用为 2842 LUT、2353 FF、
14 BRAM36、0 DSP。DRC 为 0 errors、1 个预期的 `ZPS7-1` warning。

实验 2 的详细证据位于：

```text
zynq7020-image-processing/coursework/evidence/03_hdmi_sobel
```

## 实施规则

1. 先读代码和证据，再做修改；不要重复已经通过的工作，除非需要回归验证。
2. 一次只推进一个实验，不提前实现后续实验功能。
3. 优先复用仓库已有 RTL、Tcl 和验证模式，避免无关重构。
4. 原工程来自 Vivado 2017.4，不得覆盖或升级唯一的原始 XPR。
5. Vivado 2023.2 使用隔离、可删除重建的 Tcl 工程。
6. 不提交 `.runs`、`.cache`、`.gen`、`.bit`、XSA、ELF、VCD 等大型生成物。
7. 不伪造 JTAG、Hardware Manager、HDMI、串口或开发板结果。
8. 没有真实硬件证据时，状态只能写为“远程仿真和构建通过，待现场验证”。
9. 文档使用 UTF-8；中文描述保持正常可读，技术名词不强行翻译。

## 验证与提交

根据改动范围运行相关 testbench、Python 自检和 Vivado Tcl 流程。至少完成：

```powershell
git diff --check
git status --short
```

提交前确认：

- 改动仅覆盖当前任务。
- 生成物没有进入 Git。
- README、证据和实现结果一致。
- 用户提供的真实结果与 Agent 推断有明确区分。

提交信息使用简洁的 Conventional Commits 风格，例如：

```text
feat: add experiment 3 uart hdmi flow
fix: correct sobel frame completion timing
test: extend hdmi output self-check
docs: record experiment 2 hardware results
```

用户要求推送时，先提交到当前本地分支，再推送对应远程分支。推送后核对
`HEAD` 与上游提交一致，并汇报分支、提交号、验证结果和仍待现场完成的项目。

## Claude 接手建议

- 先根据用户当前任务决定是否继续实验 2 现场闭环，或新建下一实验分支。
- 若用户提供 HDMI 照片、Hardware Manager 日志或构建日志，应先归档真实证据，
  再修改实验状态。
- 若用户要求开始实验 3，应从已确认的最新基线创建独立分支，先阅读实验 3 全部源码
  和课程计划，不要把实验 4、实验 5 的 Sobel 或动态控制功能提前带入。
- 反代服务、模型地址和凭据属于本地运行环境，不得写入仓库、日志或提交历史。

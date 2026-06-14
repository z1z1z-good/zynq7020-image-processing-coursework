# 课程设计工作区

本目录用于管理个人课程设计的实施过程、证据和报告。教师提供的实验源码与说明保持原有结构，个人修改按照 Git 分支和里程碑逐步合并。

教师仓库：<https://github.com/zhouxzh/FPGA-course/tree/main/zynq7020-image-processing>

## 当前状态

| 项目 | 状态 |
| --- | --- |
| 正式 Git 工作树 | 已建立 |
| 教师仓库远端 `upstream` | 已配置 |
| 个人私有远端 `origin` | 待首次推送 |
| Vivado / Vitis | 2023.2，待在 Git 分支中验证旧工程迁移 |
| Python 上位机环境 | Python 3.11，基础依赖已验证 |
| 实验 0 至实验 5 | 尚未在正式工作树中验证 |
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

| 里程碑 | 内容 | 当前状态 |
| --- | --- | --- |
| `exp00` | RTL 仿真、输入输出图与关键波形 | 未开始 |
| `exp01` | HDMI 固定图片 | 未开始 |
| `exp02` | 固定图片 Sobel | 未开始 |
| `exp03` | PC UART -> PS -> BRAM -> HDMI | 未开始 |
| `exp04` | UART 图像 -> PL Sobel -> HDMI | 未开始 |
| `exp05` | PC 控制模式、阈值和叠加 | 未开始 |
| `extension` | 上位机缩放策略扩展 | 未开始 |

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

## 下一步

当前唯一的工程里程碑是实验 0 默认仿真：

1. 从 `main` 创建 `exp/00-rtl-sim`。
2. 确认可用的 Icarus、ModelSim 或 XSim 仿真入口。
3. 不改 RTL，先运行仓库默认测试。
4. 保存输入图、输出图、波形和完整日志。
5. 通过后再选择更换输入图片的小扩展。

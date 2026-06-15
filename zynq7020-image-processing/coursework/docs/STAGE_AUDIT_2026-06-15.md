# 阶段评估与纠察（2026-06-15）

## 1. 评估口径

本次评估以 `BOARDLESS_DEVELOPMENT_PLAN.md`、各实验 README、自动化脚本、构建报告和证据目录为准。无现场板卡证据时，只确认 RTL、仿真、Vivado 构建、离线工具和软件编译等远程阶段，不将 JTAG、UART、BRAM 或 HDMI 的实际上板行为记为完成。

## 2. 阶段结论

| 实验 | 分支 / 提交 | 阶段结论 | 未完成门禁 |
| --- | --- | --- | --- |
| 实验 0：RTL 仿真 | `exp/00-rtl-sim` / `5fb3926` | 完成。ModelSim 默认流程通过，输出图和波形证据已生成。 | 无板卡门禁。 |
| 实验 1：HDMI 彩条 | `exp/01-hdmi-pattern` / `377851a` | 远程阶段完成。XSim、实现、bitstream 及报告证据可用。 | 现场下载、显示器锁定与画面核验。 |
| 实验 2：HDMI Sobel | `exp/02-hdmi-sobel` / `6e7cc90` | 远程阶段完成。全链 XSim、实现、bitstream 及报告证据可用。 | 现场 HDMI Sobel 画面核验。 |
| 实验 3：UART + HDMI | `exp/03-uart-hdmi` / `a05a3a6` | 条件完成。PL 仿真、实现、bitstream、XSA 和 PS 源码静态编译检查通过。 | 正式 Vitis 平台/BSP/应用/ELF 构建；现场 JTAG、UART、BRAM、HDMI 联调。 |
| 实验 4、实验 5、扩展算法 | 尚无完成分支 | 未开始或未形成可验收成果。 | 按开发计划依次推进。 |

## 3. 纠察发现

### P1：实验 3 文档曾把预期上板现象写成当前实测

实验 3 README 同时出现“当前实测现象”和“现场验证待完成”，口径矛盾，且证据目录没有对应板卡记录。已在实验 3 分支改为“原始说明中的预期现象”，明确当前不得视为实测成功。

### P1：实验 3 的正式 Vitis 构建尚未闭环

`BOARDLESS_DEVELOPMENT_PLAN.md` 将平台、BSP、应用和 ELF 的实际构建列为实验 3 远程门禁。本次 XSCT 到 `platform create` 时出现连接超时；根因未确认。ARM GNU 语法与类型检查只能证明源码的部分可编译性，不能替代正式 Vitis 构建。因此实验 3 只能标记为条件完成。

### P2：协议自检不是上位机实现回归

当前 `generate_exp03_expected.py` 使用独立黄金模型生成协议帧，没有直接调用 `host_camera_uart/camera_uart_sender.py`。现有证据能证明黄金模型与 PS 解析逻辑一致，不能单独证明实际发送器实现一致。实验 3 文档已收紧这一表述；后续应增加直接导入或调用发送器编码函数的回归测试。

### P2：TMDS 外部接口时序约束仍有缺口

实验 1 至实验 3 的时序报告包含 `no_output_delay (4)`，对应四路 TMDS 输出。当前内部时序为正不等于外部接口约束完整。现场阶段应结合器件、PCB 和显示器接口要求确认是否需要补充输出约束。

### P3：实验 3 XSim 存在非功能性告警

`hdmi_bram_display.v` 未声明 `timescale`，XSim 给出告警但仿真通过。该项当前不阻塞阶段结论，保留为后续清理项。

### P3：分支成果尚未形成统一集成基线

各实验采用独立分支，符合远程实验流程，但 `main` 当前仅对应实验 1，实验 0 的最终波形证据和实验 2、3 的成果未进入统一集成分支。本次不擅自合并；后续应在明确集成策略后处理。

## 4. 本次复核结果

| 检查项 | 结果 |
| --- | --- |
| 实验 0 ModelSim 默认流程 | 通过：`Sobel RGB888 simulation passed`，0 errors / 0 warnings |
| 实验 1 HDMI pattern XSim | 通过：`EXP01_SIM=passed` |
| 实验 2 HDMI Sobel 全链 XSim | 通过：`EXP02_SIM=passed`，9216 个写入样本 |
| 实验 3 HDMI BRAM 显示 XSim | 通过：`EXP03_SIM=passed` |
| 实验 3 协议黄金模型 | 通过：9216 pixels、roundtrip 与错误码检查 |
| Python 工具语法检查 | 通过 |
| 实验 3 正式 Vitis 构建 | 未通过：XSCT 创建平台时连接超时，未重试，疑点保留 |

## 5. 推送建议

实验 0、1、2 的现有阶段提交可继续作为远程基线；实验 3 应连同本次文档纠正推送，但需保留“条件完成”标识。阶段纠察报告单独置于 `audit/stage-2026-06-15`，不自动合并到 `main`。

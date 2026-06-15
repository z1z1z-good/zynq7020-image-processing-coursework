# 远程开发与现场上板工作流 Prompt

本文用于实验 1 至实验 5。每次只替换 Prompt 中的实验编号和实验名称，不跨实验提前修改。

## 启动 Prompt

```text
请在仓库
D:\codex_prj\fpga_dick\zynq7020-image-processing-coursework
中完成实验 <编号>：<实验名称> 的远程开发阶段。

协作条件：
- 你运行在远程开发电脑上，可以调用本机 Vivado 2023.2、Vitis/XSCT 2023.2、
  ModelSim/XSim 和 Python。
- 开发板、JTAG、USB 串口和 HDMI 显示器在我身边，当前不能由你直接访问。
- 你完成并推送后，我会在板卡旁下载分支并按你写的流程测试，再把真实结果回传。

开始前必须阅读：
1. coursework/README.md
2. coursework/docs/ZYNQ7020图像处理课程设计_单人AI辅助实施报告.md
3. 当前实验目录的 README.md
4. 当前实验相关 RTL、XDC、Tcl、C、Python、testbench 和已有脚本
5. 上一实验的已验证结论和证据

执行要求：
- 先检查 main 工作树、origin 和 upstream 状态。
- 从 main 创建当前实验规定的独立分支。
- 一次只处理当前实验，不提前修改后续实验。
- 先复现和检查现有工程，再做最小必要修复。
- 自动运行当前环境可执行的仿真、Vivado Tcl 检查、综合/实现、Vitis/XSCT 构建和
  Python 离线检查。
- 原始工程来自 Vivado/SDK 2017.4；使用 2023.2 时不得无记录地覆盖唯一基线。
- 不伪造未连接开发板时的 JTAG、串口、HDMI 或上板成功结果。
- 不提交 .runs、.cache、.gen、bitstream、ELF 或其他大型生成目录。
- 将精简构建日志、报告和说明保存到当前实验对应的 coursework/evidence 目录。
- 在当前实验 README 中新增“现场上板流程”，必须包括：
  1. 分支和提交号
  2. 所需硬件与接线
  3. 用户侧构建命令或 GUI 步骤
  4. bitstream 下载步骤
  5. PS 程序运行步骤（如适用）
  6. 上位机命令和参数（如适用）
  7. 预期串口输出和 HDMI 现象
  8. 通过标准
  9. 失败时需要保存的完整日志
  10. 用户需要回传的文件清单
- 完成检查后提交并推送实验分支。

最后汇报：
- 实际运行了哪些检查及结果
- 哪些结果仍标记为“待现场验证”
- 修改文件
- 分支和提交号
- 用户应执行的现场流程入口
- 用户必须回传的材料
```

## 用户现场测试模板

用户拉取分支后，按当前实验 README 执行，并记录：

```text
实验：
分支：
提交号：
测试日期：
开发板型号：
Vivado/Vitis 版本：
JTAG 状态：
串口号和参数：
HDMI 显示器或采集设备：

已执行步骤：
1.
2.
3.

实际串口输出：
<粘贴完整文本，不要只截最后一行>

实际 HDMI 现象：
<描述黑屏、无信号、固定图、原图、边缘图或控制模式>

错误发生步骤：
<没有错误则写“无”>

完整错误文本：
<粘贴原文>

回传文件：
- Vivado 综合/实现/bitstream 日志或截图
- utilization 摘要
- timing summary，至少包含 WNS/TNS
- 串口日志文本
- 上位机日志
- HDMI 照片或视频截图
- 其他能复现问题的文件
```

## 回传后的处理 Prompt

```text
这是实验 <编号> 的现场上板结果。请先核对分支和提交号，再分析我回传的日志、串口输出、
HDMI 图片和资源时序结果。

要求：
- 区分构建问题、JTAG/驱动问题、PS 软件问题、串口协议问题、BRAM/PL 问题和 HDMI 问题。
- 不覆盖或美化失败结果。
- 能从现有材料定位时直接修复并回归；信息不足时只询问阻塞定位的最少信息。
- 将真实现场材料整理到当前实验对应的 coursework/evidence 目录。
- 更新实验 README 和 coursework/README.md 的实际状态。
- 通过后提交并推送同一实验分支；未通过则保持“现场验证失败/待复测”，并给出下一轮最短复测流程。
- 不开始下一个实验。
```

## 实验对应关系

| 实验 | 分支 | 证据目录 |
| --- | --- | --- |
| 实验 1 | `exp/01-hdmi-pattern` | `coursework/evidence/02_hdmi_pattern` |
| 实验 2 | `exp/02-hdmi-sobel` | `coursework/evidence/03_hdmi_sobel` |
| 实验 3 | `exp/03-uart-hdmi` | `coursework/evidence/04_uart_hdmi` |
| 实验 4 | `exp/04-uart-sobel` | `coursework/evidence/05_uart_sobel` |
| 实验 5 | `exp/05-pc-control` | `coursework/evidence/06_pc_control` |

# 实验 2：HDMI 固定图片 Sobel 远程开发 Prompt

下面的文本可直接作为新任务提示词使用。

```text
/goal 请在仓库
D:\codex_prj\fpga_dick\zynq7020-image-processing-coursework
中完成实验 2：HDMI 固定图片 Sobel 的远程开发阶段，并完成一个简单、低风险的
基础扩展。完成后提交并推送 `exp/02-hdmi-sobel`，不要合并到 main；我负责现场上板
并回传结果。不要修改实验 3 及后续实验。

分支与基线：
- 实验 2 必须从最新 `main` 创建 `exp/02-hdmi-sobel`。
- 开始前先执行 fetch，并确认本地 main 与 origin/main 的关系。
- 当前 main 已包含实验 0、实验 1 的远程开发成果和实验 1 的 Vivado 2023.2
  隔离构建方法，应复用其可靠做法，但不要破坏实验 1。
- 实验 1 的真实 HDMI 上板结果仍可能待验证，因此不得把实验 1 或实验 2写成
  “上板通过”。
- 若分支已存在，先检查本地和远端状态，在不覆盖已有工作的前提下继续。

开始前必须阅读：
1. coursework/README.md
2. coursework/docs/REMOTE_HARDWARE_WORKFLOW_PROMPT.md
3. coursework/docs/BOARDLESS_DEVELOPMENT_PLAN.md
4. coursework/docs/ZYNQ7020图像处理课程设计_单人AI辅助实施报告.md
5. sobel_02_hdmi_sobel/README.md
6. sobel_02_hdmi_sobel 中全部相关 RTL、XDC、Tcl、IP 源文件和工程配置
7. 实验 0 的 Sobel 仿真证据，以及实验 1 的构建脚本、HDMI 证据和已知问题

基础目标：
- 输入为现有 `128 x 72` RGB888 固定图片 ROM。
- 验证 `rgb_to_gray -> sobel_core -> edge_mem -> HDMI` 完整数据链。
- HDMI 输出保持 `1280 x 720`，每个 Sobel 像素按 `10 x 10` 放大。
- 检查状态机、ROM 读取、灰度有效信号、Sobel 坐标、`edge_mem` 写入与读取、
  帧完成信号以及 HDMI 同步流水线。
- 优先修复真实功能、时序或 Vivado 2023.2 兼容问题，不做无关重构。

必须完成的小扩展：
- 实现“固定阈值二值化边缘显示”。
- 在 `hdmi_sobel_display.v` 中增加清晰的可配置参数，例如
  `EDGE_THRESHOLD`，默认值设为 `8'd80`。
- HDMI 映射规则为：
  `edge_pixel >= EDGE_THRESHOLD` 输出白色 `24'hffffff`，否则输出黑色
  `24'h000000`。
- 只改变显示映射，保留 `edge_mem` 中原始 8 bit Sobel 强度，避免影响算法数据。
- 扩展应尽量限制在 `hdmi_sobel_display.v`、testbench、脚本和证据文件中。
- 不加入 UART、PS、Vitis、网络、GUI、动态按键调阈值或其他跨实验功能。

扩展验证要求：
- 至少离线比较阈值 `40`、`80`、`120`。
- 生成三张可查看的预期二值边缘图，并统计每个阈值的白色边缘像素数量。
- 合理情况下，阈值升高时白色边缘像素数不应增加；用自检明确验证这一性质。
- 默认 bitstream 使用阈值 `80`。
- testbench 至少检查：
  1. RGB 转灰度结果或选定参考像素
  2. Sobel 输出坐标与边界处理
  3. `edge_frame_done` 最终产生
  4. `edge_mem` 完成一帧写入
  5. HDMI 有效像素数、HS/VS 脉宽和缩放地址
  6. 阈值 80 下 RGB 只输出黑或白，并与 `edge_mem` 强度一致

Vivado 与构建要求：
- 工具优先使用本机 Vivado/XSim 2023.2，目标器件为
  `xc7z020clg400-2`。
- 原工程来自 Vivado 2017.4，不得直接覆盖或升级唯一的原始 XPR。
- 参考实验 1 的方式，在 `sobel_02_hdmi_sobel` 内新增可重复执行的隔离 Tcl
  仿真和 bitstream 构建脚本。
- 如果旧 `rgb2dvi_0.xci` 或 `video_clock.xci` 被锁定，优先直接编译仓库中已归档
  的 Verilog/VHDL 源文件和约束，不依赖已丢失的旧 IP repository。
- 构建目录必须可删除重建，并尽量避免 Windows 超长路径问题。
- 实际运行 XSim、综合、实现、DRC 和 bitstream 生成。
- 保存 utilization、timing summary、DRC 摘要和精简构建结果。
- 不提交 `.runs`、`.cache`、`.gen`、bitstream、XSA 或其他大型生成物。

证据要求：
- 将精简证据保存到 `coursework/evidence/03_hdmi_sobel`。
- 至少包括：
  1. 仿真结果摘要
  2. 阈值 40、80、120 的预期输出 PNG
  3. 三个阈值对应的白色边缘像素统计
  4. 默认阈值 80 的现场对照图
  5. utilization 报告
  6. timing summary，包含 WNS、TNS、WHS、THS
  7. DRC 摘要和未消除 warning 的解释
  8. bitstream 生成成功记录，但不提交 `.bit`

文档与现场流程：
- 更新 `sobel_02_hdmi_sobel/README.md`，标记阈值二值化扩展已完成。
- 新增完整“远程开发结果与现场上板流程”，写明：
  1. 分支和最终提交号的获取方法
  2. 所需板卡、JTAG、HDMI 接线
  3. 命令行构建方法和 Vivado GUI 查看方法
  4. Hardware Manager 与 Program Device 步骤
  5. 默认阈值为 80
  6. 预期画面为黑底白边的固定图片 Sobel 二值图
  7. 现场画面应与阈值 80 的预期 PNG 一致
  8. 显示器稳定识别 1280 x 720 至少 30 秒
  9. 通过标准、失败排查顺序和完整回传清单
- 本实验没有 PS 程序、串口和上位机步骤，不要虚构这些输出。
- 没有真实开发板时，状态必须保持“远程仿真和构建通过，待现场验证”。

范围纪律：
- 允许修改：
  `sobel_02_hdmi_sobel`
  `coursework/evidence/03_hdmi_sobel`
  与实验 2 状态直接相关的少量 coursework 文档
- 不修改 `sobel_03_uart_hdmi`、`sobel_04_uart_sobel_hdmi`、
  `sobel_05_pc_control_display` 和 `host_camera_uart`。
- 不顺手开始实验 3，不把实验 2 的阈值扩展做成实验 5 的动态控制功能。
- 保留用户已有的未提交修改，不覆盖无关工作。

完成门槛：
- testbench 自检通过。
- 阈值 40、80、120 三组离线结果和统计齐全。
- 默认阈值 80 的 XSim 验证通过。
- 综合、实现、时序、DRC 和 bitstream 生成实际通过。
- `git diff --check` 通过。
- 审计确认没有实验 3 及后续文件变更。
- 提交并推送 `exp/02-hdmi-sobel`，但不要合并 main。

最后汇报：
- 修改了什么以及阈值扩展如何实现
- 实际运行的命令和结果
- 三个阈值的白色边缘像素统计
- WNS/TNS、资源占用、DRC 和 bitstream 状态
- 仍待现场验证的项目
- 分支和提交号
- README 中现场流程入口
- 我上板后必须回传的 HDMI 照片、日志和报告
```

## 推荐扩展选择

该提示词固定选择“阈值二值化”而不是彩色边缘或动态控制，原因是：

- 只修改显示映射，不改变 Sobel 核心和帧缓存数据。
- 参数化后容易仿真，阈值 `40/80/120` 可以产生清晰的报告对比。
- 默认阈值 `80` 只需生成一个 bitstream，现场步骤简单。
- 该实现可在实验 5 中继续复用，但不会提前引入实验 5 的控制逻辑。

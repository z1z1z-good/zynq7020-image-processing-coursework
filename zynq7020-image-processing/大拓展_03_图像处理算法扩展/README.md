# 大拓展 03：增加图像处理算法（任务3 B 档 · 锐化）

本目录是「综合扩展任务 3：增加图像处理算法」的独立交付目录。在实验 5
（`sobel_05_pc_control_display`）的 PS / PL / BRAM / HDMI 链路上**新增一个 PL 端图像处理
算法——图像锐化（Laplacian / unsharp 增强）**，通过上位机命令实时选择与调参，并提供
软件参考对比。对应教师评分表任务 3 的 **B 档**。

> 分支：`exp/06-pl-sharpen`（基于 `main`）。未经允许不合并入 `main`、不推送。
> 锐化是任务 3 可选算法列表中的第 4 项（教师 README「0. 图像处理算法理论介绍」明确列出）。

## 1. 教师评级口径（任务 3，来自 upstream 教师仓库 README）

| 等级 | 要求 |
| --- | --- |
| A | 新增 **3 种以上**算法 + 上板演示算法切换 + 与软件 golden 对比 + 资源利用率和时序对比分析 |
| **B** | **新增 1 种算法 + 上板演示 + 与软件参考对比** ← 本扩展目标 |
| C | 新增 1 种算法并上板演示 |
| D | 未完成 C 级要求 |

建议完成内容（教师 README）与本扩展的对应：

| 教师建议 | 本扩展落地 | 状态 |
| --- | --- | --- |
| 至少新增 1 种算法，与原 Sobel 对比 | 新增锐化（mode=4），与 Sobel(mode=2) 同工程共存、可一键切换 | ✅ |
| 增加显示模式/算法选择命令 | 复用控制帧 `A5 5A 01 mode`（mode=4 锐化）+ 新增 `A5 5A 04 k` 锐化强度 | ✅ |
| 软件参考 golden（Python/MATLAB） | `host_tool/sharpen_algo.py`（numpy），与 RTL 定点逐位一致 | ✅ |
| RTL 仿真对比硬件输出和软件参考 | 无板协同仿真 render-compare，11 配置（含 4 档锐化）逐像素一致 | ✅ |
| 上板演示算法切换 + 资源/时序 | GUI 现场演示；资源/时序已用 OOC 综合记录（见证据） | ⏳ 上板现场 / ✅ 资源时序 |

> 说明：上板演示需现场开发板完成。RTL/PS/上位机/仿真均已就绪并通过无板验证，现场只需
> 烧写 bitstream + 运行 GUI。资源利用率与时序已通过本地 OOC 综合获得（见第 6 节）。

## 2. 算法与定点定义（RTL / PS / 上位机三处逐位一致）

锐化采用基于灰度拉普拉斯的非锐化掩模（保留彩色）：

```text
gray  = (77*R + 150*G + 29*B) >> 8                   # 与 rgb_to_gray.v 一致
lap   = 4*center - up - down - left - right           # 4 邻域拉普拉斯，1 像素边界 = 0
delta = floor(strength * lap / 256)                   # RTL 算术右移 >>>8；软件 >>8 / floor_divide
out_c = clamp(c + delta, 0, 255)   for c in R,G,B     # 逐通道，保留彩色
```

- `strength` = 锐化强度 0..255，即 GUI 滑块 / 控制字 `0x900C` / 控制命令 `A5 5A 04 k` 的 value。
- `strength = 0` 时输出与原图逐像素相同；强度越大边缘/纹理越锐，过大时高频处发生饱和裁剪（halo）。
- 拉普拉斯**复用 Sobel 已验证的同一 3×3 窗口**（中心 = `mid1`），与边缘像素同地址写入新增的
  `lap_mem`，因此 Sobel 路径零改动、零回归；`strength` 在显示阶段每帧读取并应用，
  **拖动 GUI 滑块即时改变锐化程度，无需重发图像帧**。

## 3. 数据链路与改动文件

```text
上位机 GUI/sender ──UART──▶ PS main.c ──▶ AXI BRAM ──▶ PL hdmi_bram_sobel_display ──▶ HDMI 720p
   选模式/拖强度          a5 5a 04 k           控制字 0x900C        每帧读 strength，clamp(rgb+(k*lap)>>8)
```

| 层 | 文件 | 改动 |
| --- | --- | --- |
| PL | `sobel_05.../srcs/sources_1/new/sobel_core.v` | 在已验证 3×3 窗口上**附加输出** 4 邻域拉普拉斯 `lap_data`（Sobel 路径不变） |
| PL | `.../new/hdmi_bram_sobel_display.v` | 新增 `MODE_SHARPEN(4)`、`lap_mem`、控制字 `0x900C` 读取 FSM、显示端 `clamp(rgb+(k*lap)>>8)`；`display_mode` 位宽 2→3 |
| PS | `sobel_05.../ps_uart_control_bram_app/src/main.c` | 新增控制命令 `0x04`（锐化强度→`0x900C`）；mode 掩码 0x03→0x07 |
| 上位机 | `大拓展_03.../host_tool/sharpen_algo.py` | 锐化软件 golden（numpy），与 RTL 逐位一致 |
| 上位机 | `.../host_tool/camera_uart_sender.py` | 锐化感知发送器（含 `sharpen` 模式与 `0x04` 命令、中文路径安全的图像读写） |
| 上位机 | `.../host_tool/camera_uart_gui.py` | 验收 GUI：模式选择 + 实时锐化强度滑块 + 软件预览 |
| 仿真 | `sobel_05.../tools/generate_exp05_expected.py` | golden 库新增 `laplacian()` + `MODE_SHARPEN` 分支 + `0x900C` 字 |
| 仿真 | `.../tools/cosim/exp05_cosim.py`、`ps_protocol_model.c`、`run_exp05_cosim.sh` | 协同仿真新增 4 档锐化渲染对比 + 真实 PS 锐化命令端到端校验 |

> BRAM/时序/Block Design **均无需改动**（不同于任务 1 B 档），这正是「改 PL 加算法」里风险最低的一条路径。

## 4. 验收操作（现场，GUI 手操调参看可见改善）

```bash
cd zynq7020-image-processing/大拓展_03_图像处理算法扩展/host_tool
pip install -r requirements.txt        # numpy / opencv-python / pyserial
python camera_uart_gui.py
```

GUI 操作：

1. 选择串口 → **连接**（连接后界面状态会整体下发一次，HDMI 与界面一致）。
2. **载入图片** → **发送图像到 FPGA**（HDMI 显示该图）。
3. **显示模式**选 `sharpen`。
4. 拖动 **锐化强度 k 滑块（0..255）**：
   - 同窗口「原图 | 软件锐化 k」并排预览**即时刷新**（看到可见的锐化改善）；
   - HDMI 硬件画面**同步实时变锐**（控制命令 `A5 5A 04 k` 每帧生效，无需重发图像）；
   - 快捷预设按钮 `k=0/64/128/192/255` 便于现场对比（k=0 即原图）。
5. 与 Sobel 对比：模式切回 `edge` 即为原算法，体现「新增算法 vs 原 Sobel」。

> 软件预览无需连接开发板即可使用，便于上板前彩排。GUI 软件预览与 HDMI 硬件输出**逐像素一致**
> （见第 5 节），因此它同时充当 B 档要求的「软件参考对比」。

命令行等价操作（可选）：

```bash
# 发图并切到锐化、强度 128
python camera_uart_sender.py --port COM7 --image pic.jpg --once --mode sharpen --sharpen 128
# 实时调强度（不发图）
python camera_uart_sender.py --port COM7 --control-only --sharpen 200
# 离线导出软件参考图（与 HDMI 对照），不连串口
python camera_uart_sender.py --image pic.jpg --sharpen 128 --software-out sw_k128.png --no-send
```

## 5. 无板验证：RTL == 软件 golden（逐像素）

复用实验 5 的无板软硬件协同仿真链（真实上位机打包 → 真实 `main.c` PS 分发 → XSim 渲染 HDMI →
与软件 golden 逐像素对比），已扩展覆盖锐化：

```bash
cd zynq7020-image-processing/sobel_05_pc_control_display/tools/cosim
EXP05_PYTHON=/path/to/python EXP05_VIVADO_BIN=/path/to/Vivado/bin bash run_exp05_cosim.sh
```

实测结果（本地 Vivado 2023.2 XSim + Miniconda numpy + gcc）：

- 真实 `main.c` 收到 `A5 5A 04 96` → 控制字 `0x900C = 96`（`PS_MODEL_CTRL ... sharpen=96`、`EXP05_COSIM_FB=match ... sharpen=96`）。
- RTL 自检 `EXP05_SELFCHECK_TB=passed`（原 Sobel 四模式零回归）。
- 全分辨率 1280×720 逐像素对比，**11 个配置全部 `=match`**，含 `sharp0/64/128/255`
  （`sharp0` 等于原图；强度越大改变越多）。
- `EXP05_COSIM_CHAIN=passed`。
- 上位机 numpy 软件预览 == 软件 golden == RTL（`sharpen_algo` 与 golden 逐位一致，见
  `evidence/cosim_summary.txt` 与下文交叉验证）。

链路含义：**GUI 软件预览 == 软件 golden == HDMI 硬件输出**，三者逐位一致。

## 6. 资源利用率与时序（OOC 综合，xc7z020clg400-2）

对 PL 显示路径（`hdmi_bram_sobel_display + rgb_to_gray + sobel_core`）做 out-of-context 综合，
74.25 MHz 像素时钟约束：

| 指标 | 结果 | 占用 |
| --- | --- | --- |
| 时序 | **All timing constraints met**，WNS **+2.452 ns**，0 失败端点 | 13.468 ns 周期下约 18% 余量 |
| Slice LUT | 9229 | 17.35% |
| Slice Register | 2725 | 2.56% |
| Block RAM | 10.5 tile（10×RAMB36 + 1×RAMB18） | 7.5% / 140 |
| DSP | 4 | 1.82% / 220 |

锐化新增的 `lap_mem` 仅占数个 BRAM tile，强度乘法 `k*lap` 占 1 个 DSP，组合乘法路径在
74.25 MHz 下时序充裕（无需流水线）。详见 `evidence/ooc_synth_utilization.rpt`、`ooc_synth_timing.rpt`。

## 7. bitstream 构建说明

- 锐化扩展**不改 Block Design / BRAM 容量 / 时序约束**，沿用实验 5 既有构建流程即可：
  `sobel_05_pc_control_display/run_sobel_05_bitstream.tcl`（或工程内既有非工程化 Tcl 流程）。
- PS 程序重新编译 `ps_uart_control_bram_app`（已含 `0x04` 锐化命令）。
- 构建在远程 / 现场进行；注意本仓库既有的 Windows MAX_PATH 构建坑（输出目录路径不要过深）。
- 本地仅做了功能与 OOC 综合验证（无开发板）；完整 bitstream 在现场生成并烧写。

## 8. 证据目录 `evidence/`

| 文件 | 内容 |
| --- | --- |
| `sharpen_original.png` / `sharpen_k0/64/128/255.png` | 软件锐化结果（= HDMI 硬件输出的逐像素参考），k=0 即原图 |
| `sharpen_side_by_side_k128.png` | 原图 \| 锐化 并排对比 |
| `sharpen_delta_heatmap_k128.png` | 锐化增量 \|delta\| 热力图（直观显示锐化作用在边缘/纹理处） |
| `sharpen_software_reference.txt` | 各强度改变像素数统计与定点公式 |
| `cosim_summary.txt` | 无板协同仿真关键标记（11 配置逐像素 match、PS 端到端 sharpen=96） |
| `ooc_synth_utilization.rpt` / `ooc_synth_timing.rpt` | OOC 综合资源利用率与时序报告 |

证据图可用 `host_tool/gen_evidence.py` 复现。

## 9. 升到 A 档的路径（可选）

A 档需「新增 3 种以上算法」。当前基础设施已可低成本扩展：
- **Laplacian 边缘**：`lap_mem` 已有，显示端取 `|lap|` 阈值化即可，几乎零增量；
- **二值化分割**：显示端已算 `display_gray`，`gray>=threshold` 输出黑白即可；
- **均值/高斯平滑**：需再走一遍 3×3 窗口（复用 `sobel_core` 行缓存思路）。

三者都复用现有 mode 控制命令与 golden/cosim/GUI 框架，可平滑从 B 档升到 A 档。

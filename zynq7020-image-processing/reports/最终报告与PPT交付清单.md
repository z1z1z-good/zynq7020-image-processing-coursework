# 最终报告与 PPT 交付清单

资料来源：老师原仓库 `zhouxzh/FPGA-course/zynq7020-image-processing/README.md`，以及本仓库 [zynq7020-image-processing/reports/最终报告.md](./最终报告.md)、[zynq7020-image-processing/coursework/evidence/](../coursework/evidence/)、[zynq7020-image-processing/大拓展_01_上位机输入规格扩展/](../大拓展_01_上位机输入规格扩展/) 与 [zynq7020-image-processing/大拓展_03_图像处理算法扩展/](../大拓展_03_图像处理算法扩展/) 下的证据。老师原仓库地址：<https://github.com/zhouxzh/FPGA-course/tree/main/zynq7020-image-processing>

路径约定：素材索引显示为远端仓库根目录路径（以 `zynq7020-image-processing/` 开头）；图片链接按本文件所在 `reports/` 目录使用相对路径，便于 GitHub 直接跳转。

> **本清单的组织思路（与早期只讲任务 1 的版本不同）**：本组完成了**两个互补的综合扩展**，PPT 把它们当作一个整体来讲——
> **大拓展一（任务 1，C 档）在输入侧做 PC 端规格适配（不改硬件）**，**大拓展二（任务 3，B 档）在算法侧给 PL 新增锐化算法（改 PL/PS 但零回归）**。
> 一软一硬、从"输入"到"算法"两端增强同一条 `sobel_05` 链路，且**共用同一上位机工具与同一 bitstream**。
> deck 采用"分块并列"：基础页 → 综合扩展总览（融合桥页）→ 大拓展一块 → 大拓展二块 → 资源/总结（横切页同时覆盖两者）。

---

## 1. 老师要求核对

### 1.1 两个综合扩展概览（一软一硬，融合主线）

| 维度 | 大拓展一（任务 1） | 大拓展二（任务 3） |
| --- | --- | --- |
| 方向 | 输入侧：上位机与输入规格扩展 | 算法侧：新增 PL 图像处理算法 |
| 算法/功能 | 任意尺寸输入 → 固定 `128×72` 的 fit/proc 适配 | 图像锐化（Laplacian / unsharp 增强） |
| 改动层 | 仅 PC 上位机 | PL + PS（上位机做控制/预览） |
| 目标档位 | C 档（硬件不变，上位机缩放到 ≥3 种尺寸） | B 档（新增 1 种算法 + 上板 + 软件参考对比） |
| 对硬件契约 | 完全不变（复用实验 5 bitstream） | 纯附加、原 Sobel 四模式零回归；不改 BRAM/时序/BD |
| 实时控制 | 不涉及 | 控制字 `0x900C`，拖滑块 HDMI 实时变锐 |
| 主要验证 | 12/12 离线 + 36 组矩阵 | 协同仿真 11 配置逐像素 `=match` + numpy==golden==RTL + OOC 时序 |
| 共用 | 同一上位机工具（GUI 同时含 fit/proc 与锐化）、同一 UART 协议、同一 bitstream | 同上 |

> 老师要求"三选一"，本组完成两个，且二者正交、可叠加演示（先缩放后锐化），是超额完成。

### 1.2 扩展验收至少需要提交（两个扩展统一核对）

| 序号 | 老师要求 | 大拓展一 材料 | 大拓展二 材料 |
| --- | --- | --- | --- |
| 1 | 基础实验（exp0-4 扩展、exp5 控制）结果 | [最终报告.md](./最终报告.md) 第 3-4 节；现场照片 [coursework/evidence/02_hdmi_pattern/](../coursework/evidence/02_hdmi_pattern/) … [06_pc_control/](../coursework/evidence/06_pc_control/) | 同左（共用基础链路） |
| 2 | 综合扩展选择与设计方案 | 任务 1：PC 端输入规格扩展，方案 A（不改硬件），最终报告第 6 节 | 任务 3：PL 锐化，复用 Sobel 窗口、不改 BRAM/时序，最终报告第 6B 节 |
| 3 | 修改文件列表（区分 PC/PS/PL） | 仅 PC：`大拓展_01.../host_tool/*`（最终报告 5.2） | PL+PS+PC：`sobel_core.v`/`hdmi_bram_sobel_display.v`/`main.c`/`大拓展_03.../host_tool/*`（最终报告 5.3） |
| 4 | 修改前后关键代码说明 | `prepare_frame`、`--fit-mode`、`--proc-size` | 附加 `lap_data`、`MODE_SHARPEN`、`lap_mem`、`0x900C` FSM、`clamp(rgb+(k·lap)>>>8)`、`cmd 0x04` |
| 5 | 仿真/波形/软件验证 | [大拓展_01.../evidence/ext_offline_tests.txt](../大拓展_01_上位机输入规格扩展/evidence/ext_offline_tests.txt)、[ext_scaling_matrix.txt](../大拓展_01_上位机输入规格扩展/evidence/ext_scaling_matrix.txt) | [大拓展_03.../evidence/cosim_summary.txt](../大拓展_03_图像处理算法扩展/evidence/cosim_summary.txt)、[sharpen_equivalence.txt](../大拓展_03_图像处理算法扩展/evidence/sharpen_equivalence.txt) |
| 6 | 资源利用率、时序、bitstream | 复用实验 5，不增 FPGA 资源（最终报告 7.1） | PL OOC：WNS +2.452ns，[ooc_synth_utilization.rpt](../大拓展_03_图像处理算法扩展/evidence/ooc_synth_utilization.rpt)、[ooc_synth_timing.rpt](../大拓展_03_图像处理算法扩展/evidence/ooc_synth_timing.rpt) |
| 7 | 上板现象、照片/视频 | [coursework/evidence/照片证明/大拓展最终验收视频截图/](../coursework/evidence/照片证明/大拓展最终验收视频截图/) | **现场验收时补**到 [大拓展_03.../evidence/](../大拓展_03_图像处理算法扩展/evidence/)；当前可先用软件预览图占位 |
| 8 | 实验现象、问题、性能瓶颈 | UART 115200 单帧 ≈ 2.43s（最终报告第 8 节） | 同左；锐化为纯附加，时序裕量约 18% |

### 1.3 PPT 额外必须覆盖（老师要求截图）

1. 扩展题目（**两个**都要点名）。
2. 创新点（一软一硬的整体设计，而不是两个孤立功能）。
3. 实现原理（两个扩展并列讲清）。
4. 团队成员分工与贡献。

---

## 2. PPT 总体结构（16 页，两个扩展分块并列）

横切页（第 6、15、16 页）同时覆盖两个扩展；中间两块分别讲一个扩展。任务 3 的技术实现占 4 页（第 11-14），因为它是真正改了 PL 的新算法，且 PPT 优先展示技术实现。

| 页 | 标题 | 归属 | 必须度 | 核心 |
| ---: | --- | --- | --- | --- |
| 1 | 封面与成员 | 全局 | 必须 | 项目名（含两个扩展）、平台、成员 |
| 2 | 课程任务与完成范围 | 全局 | 必须 | 基础 7 项 + 两个综合扩展 |
| 3 | 系统总体结构与数据流 | 全局 | 必须 | PC/UART/PS/BRAM/PL/HDMI，标出两扩展接入点 |
| 4 | 基础实验复现 | 全局 | 必须 | exp0-5 一表 + 4 张代表图 |
| 5 | 第一周基础扩展 | 全局 | 可压缩 | 边框/阈值/彩色边缘/控制 |
| 6 | **综合扩展总览（融合桥页）** | 融合 | 必须 | 一软一硬对照表，两端增强同一链路 |
| 7 | 大拓展一：题目、方案与创新点 | 任务1 | 必须 | 输入规格扩展，PC 适配，硬件契约不变 |
| 8 | 大拓展一：实现原理与软件验证 | 任务1 | 必须 | `prepare_frame` 链路 + 12/12 + 36 矩阵 + C 档尺寸表 |
| 9 | 大拓展一：上板展示 | 任务1 | 必须 | 三种 fit、C 档三尺寸 + `64x36` 对比 |
| 10 | 大拓展二：题目与方案 | 任务3 | 必须 | PL 锐化，B 档；为什么"最低风险改 PL" |
| 11 | **大拓展二：锐化算法与定点实现** | 任务3 | 必须（技术核心） | gray/lap/clamp 定点 + 复用 Sobel 窗口 |
| 12 | **大拓展二：PL 数据通路与实时控制** | 任务3 | 必须（技术核心） | 附加 `lap_mem` 支路 + `0x900C` 每帧实时 |
| 13 | **大拓展二：无板验证与资源时序** | 任务3 | 必须（技术核心） | 11 配置逐像素 match + golden 等价 + OOC |
| 14 | 大拓展二：上板演示与验收 GUI | 任务3 | 必须 | 实时调强度 + Sobel↔锐化 切换（现场补图） |
| 15 | **资源利用率、时序与性能** | 融合 | 必须 | exp1-5 + 任务1 不增 + 任务3 OOC + UART 瓶颈 |
| 16 | 问题、总结与成员分工 | 融合 | 必须 | 两扩展瓶颈、A 档演进、分工 |

> 时间很紧时：第 5 页可删，第 7-9（任务1）可压成 2 页；但第 6 与第 10-14（融合页 + 任务3 技术页）不要删。

---

## 3. PPT 必须展示内容（融合两个扩展）

### 3.1 扩展题目（两个）

- 大拓展一：**基于 `sobel_05_pc_control_display` 的上位机与输入规格扩展**（任务 1，C 档）。一句话：不改硬件，让上位机支持不同输入尺寸、三种 fit 策略和多种处理尺寸，仍发固定 `128×72 RGB888`。
- 大拓展二：**在 `sobel_05` 的 PL 上增加图像处理算法——图像锐化**（任务 3，B 档）。一句话：在 PL 上新增锐化算法核，与原 Sobel 同工程一键切换，强度实时可调，并用与硬件逐位一致的软件 golden 对照。

### 3.2 创新点（一软一硬，合并讲，不要拆成两段孤立功能）

总纲：**两个扩展从输入侧和算法侧两端增强同一条链路，互相正交、共用上位机与 bitstream。**

1. **硬件契约不变 / 零回归扩展**：任务 1 完全不动 FPGA；任务 2 虽改 PL，但复用 Sobel 已验证的 3×3 窗口、只做"附加输出"，原四模式逐位不变（协同仿真自检零回归证明）。
2. **改动放在风险最低处**：能在 PC 端解决的（输入规格）就不改硬件（任务 1）；必须改 PL 的（新算法）就复用已验证窗口、不碰 BRAM/时序/BD（任务 2）。
3. **统一的实时控制协议**：复用实验 5 的 `A5 5A cmd value`——任务 2 只多加一个 `cmd=0x04`（锐化强度→控制字 `0x900C`），拖滑块即可让 HDMI 实时变锐，无需重发帧。
4. **软件 golden 逐位对照**：任务 1 用离线测试矩阵保证协议不变；任务 2 用与 RTL 定点逐位一致的 numpy golden，GUI 实时预览即硬件输出的可信预演。
5. **覆盖评分分档**：任务 1 的 `128x72/160x90/144x108` 正是 C 档参考尺寸；任务 2 的"新增 1 种算法 + 上板 + 软件对比"正是 B 档要件。

C 档尺寸验收对照（放任务一页显眼处）：

| 评分表参考尺寸 | 状态 | 说明 |
| --- | --- | --- |
| `128x72` | 已实现、已测试 | 原固定链路尺寸 |
| `160x90` | 已实现、已测试 | 新增 C 档参考尺寸 |
| `144x108` | 已实现、已测试 | 新增 C 档参考尺寸 |

### 3.3 实现原理（两个扩展并列）

大拓展一（输入侧，PC）：

```text
任意尺寸图片/目录/视频/摄像头
  -> prepare_frame(fit_mode, proc_size)        # stretch/letterbox/center-crop；128x72/160x90/144x108/64x36
  -> 固定 128x72 RGB888
  -> build_frame_packet: 27943B, header 55 aa 80 00 48 00 18
  -> UART -> PS 写 BRAM -> PL Sobel/显示 -> HDMI
协议不变量：128x72、27943B、55 aa 80 00 48 00 18、A5 5A cmd value
```

大拓展二（算法侧，PL+PS）：

```text
定点：gray=(77R+150G+29B)>>8; lap=4·center-up-down-left-right(边界0); out_c=clamp(c+(k·lap)>>>8)
扫描期：rgb_to_gray -> sobel_core ─┬─> edge_mem（原 Sobel 不变）
                                   └─> lap_data -> lap_mem（新增，复用同一 3x3 窗口，中心=mid1）
每帧：读控制字 0x9000/04/08/0C(mode/threshold/overlay/strength)
显示期：MODE_SHARPEN 时 clamp(rgb + (strength*lap)>>>8) -> HDMI
控制：A5 5A 04 k -> 0x900C，每帧生效，拖滑块实时变锐
```

### 3.4 团队分工与贡献（人工填真实姓名）

| 成员 | 分工 | 可写贡献点 |
| --- | --- | --- |
| skf | PL/HDMI/Sobel | HDMI 显示、Sobel 链路、肖像素材 |
| cwh | PS/UART/BRAM | exp3/4/5 串口接收、BRAM 写入、控制字协议 |
| lzj | PC 上位机与综合扩展 | 大拓展一输入规格（fit/proc、GUI/CLI、离线测试）；大拓展二上位机（锐化软件 golden、GUI 滑块与预览） |
| lcy | 资料与展示 | 照片证据、资源时序整理、报告、PPT、最终演示 |

> 任务 3 的 PL/PS 锐化实现与协同仿真验证，请按实际承担情况补写到对应成员（如 PL 同学负责 `sobel_core`/`hdmi_bram_sobel_display`、PS 同学负责 `main.c` 的 `0x04` 命令）。

---

## 4. 资源、时序、性能（含任务 3 OOC）

### 4.1 资源/时序表（PPT 第 15 页用）

| 实验/扩展 | LUT | FF | BRAM | DSP | WNS(ns) | 说明 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 实验 1 | 232 | 179 | 12 | 0 | +7.772 | HDMI 基础链路 |
| 实验 2 | 2842 | 2353 | 14 | 0 | +1.578 | 加 Sobel |
| 实验 3 | 1775 | 1504 | 16 | 0 | +8.173 | PS/BRAM/HDMI 原图 |
| 实验 4 | 4446 | 3662 | 18 | 0 | +13.453 | UART 图像 Sobel |
| 实验 5 | 10795 | 4113 | 20 | 0 | +0.325 | 多模式控制（全设计，时序裕量最小） |
| 大拓展一（任务1） | 同实验 5 | 同实验 5 | 同实验 5 | 同实验 5 | +0.325 | 只改 PC，不增 FPGA 资源 |
| 大拓展二（任务3，PL OOC） | 9229 | 2725 | 10.5 | 4 | +2.452 | 仅 PL 显示路径 OOC（含锐化 `lap_mem`+乘法）；最终 bitstream 复用实验 5，BD/BRAM/时序不变 |

> 注意区分口径：实验 1-5 是**整设计**（含 PS/BD）数字；任务 3 那行是 **PL 显示路径 OOC**（不含 PS/BD），用来证明"锐化加得起、时序过得去"。讲解时说清楚："任务 1 不增资源；任务 2 新增的 `lap_mem` 占几个 BRAM、`k·lap` 占 1 个 DSP，OOC 下 74.25MHz 时序裕量约 18%"。

### 4.2 性能瓶颈

```text
一帧协议层字节数 = 7 + 72*4 + 128*72*3 = 27943B
UART 8N1 115200 baud ≈ 27943*10/115200 ≈ 2.43 s/frame
```

结论：两个扩展都不改 UART 链路，瓶颈仍是 UART 带宽（与帧率相关，与显示稳定性/算法正确性无关）。后续提升方向：网络传输或更高带宽接口。

---

## 5. 推荐图片清单

### 5.1 大拓展一（任务1，已有现场截图）

优先 [coursework/evidence/照片证明/大拓展最终验收视频截图/](../coursework/evidence/照片证明/大拓展最终验收视频截图/)：

| 用途 | 文件 |
| --- | --- |
| 三种 fit（128x72） | [strech_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/strech_128x72.png)、[letterbos_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/letterbos_128x72.png)、[centercrop_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/centercrop_128x72.png) |
| 处理尺寸对比（64x36） | [strech_64x36.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/strech_64x36.png)、[centrecrop_64x36.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/centrecrop_64x36.png) |

基础页：[01_rtl_sim/exp00_key_waveform.png](../coursework/evidence/01_rtl_sim/exp00_key_waveform.png)、[02_hdmi_pattern/exp01_hdmi_field_20260618.jpg](../coursework/evidence/02_hdmi_pattern/exp01_hdmi_field_20260618.jpg)、[05_uart_sobel/exp04_uart_sobel_field_20260618.jpg](../coursework/evidence/05_uart_sobel/exp04_uart_sobel_field_20260618.jpg)、[06_pc_control/exp05_mode_overlay_field_20260618.jpg](../coursework/evidence/06_pc_control/exp05_mode_overlay_field_20260618.jpg)。

### 5.2 大拓展二（任务3，软件预览先占位，硬件照片现场补）

| 用途 | 文件 |
| --- | --- |
| 原图 vs 锐化 并排 | [大拓展_03.../evidence/sharpen_side_by_side_k128.png](../大拓展_03_图像处理算法扩展/evidence/sharpen_side_by_side_k128.png) |
| 不同强度 | [sharpen_k0.png](../大拓展_03_图像处理算法扩展/evidence/sharpen_k0.png)、[sharpen_k64.png](../大拓展_03_图像处理算法扩展/evidence/sharpen_k64.png)、[sharpen_k128.png](../大拓展_03_图像处理算法扩展/evidence/sharpen_k128.png)、[sharpen_k255.png](../大拓展_03_图像处理算法扩展/evidence/sharpen_k255.png) |
| 锐化作用区域热力图 | [sharpen_delta_heatmap_k128.png](../大拓展_03_图像处理算法扩展/evidence/sharpen_delta_heatmap_k128.png) |
| **上板实拍（待现场补）** | 现场拍：HDMI 锐化 k=0/64/128、Sobel↔锐化 切换、GUI 软件预览与 HDMI 对照，存入 `大拓展_03.../evidence/` |

> 提示：软件预览图在**真实照片**上更像"变清晰"；合成图硬边多会显出 Laplacian 的边缘 overshoot（振铃），那是锐化的正常表现，演示时优先用真实照片。

---

## 6. 报告与 PPT 取舍

### 6.1 最终报告必须保留

- 完整 8 节 + 6B 节（任务 3）结构。
- 每个基础实验至少一张现象图。
- 两个综合扩展各自的设计原理、验证结果、上板/待上板说明。
- 修改文件列表（任务 1 仅 PC；任务 3 含 PL/PS/PC）。
- 资源/时序表（含任务 3 OOC）。
- 问题记录与性能瓶颈。

### 6.2 PPT 必须压缩，但两扩展都要讲透

1. 系统链路是什么；2. 基础实验证明链路跑通；3. 两个综合扩展分别解决了什么（输入侧 vs 算法侧）；4. 为什么这样分工（风险最低处改）；5. 各自的验证（任务1 12/12+36矩阵；任务2 逐像素 cosim + golden 等价 + OOC）；6. 资源时序是否满足；7. 成员分工。

### 6.3 必须分清的表述

- "离线/仿真验证通过" ≠ "硬件全部验证通过"。
- 任务 2 资源那行是 **PL OOC**，不是整设计数字；最终 bitstream 复用实验 5。
- 任务 2 上板照片**现场补**；PPT/报告先用软件预览占位。

---

## 7. 逐页脚本（16 页，可直接复制到 PPT）

面向没参与技术实现的同学：每页给出标题、目的、可直接复制的正文、推荐图片、版式与讲解提示。除"成员姓名/学号/分工"需人工补充、任务 2 上板照片需现场补外，其余文字可直接用。

### 第 1 页：封面

**标题**：ZYNQ7020 图像处理课程设计 —— 基于 Sobel 的 UART 图像传输、HDMI 显示，与两个综合扩展（上位机输入规格扩展 + PL 图像锐化算法）

**正文**
- 平台：黑金 ZYNQ7020 开发板
- 主线：RTL 仿真 → HDMI 显示 → PL Sobel → UART 传图 → PS/BRAM → PC 控制
- 综合扩展（两个，互补）：① 上位机与输入规格扩展（任务 1，C 档）② PL 图像锐化算法（任务 3，B 档）
- 成员：姓名/学号/班级；日期：答辩日期

**推荐图片**：[letterbos_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/letterbos_128x72.png) 或 [sharpen_side_by_side_k128.png](../大拓展_03_图像处理算法扩展/evidence/sharpen_side_by_side_k128.png)
**讲解提示**：一句话定位——一条完整 PC→FPGA→HDMI 链路，并从输入侧和算法侧各做了一个综合扩展。

---

### 第 2 页：课程任务与完成范围

**标题**：课程设计任务与完成范围

**正文**：在 ZYNQ7020 上由浅入深完成图像处理系统。本组已完成：

1. `sobel_00_rtl_sim`：RTL 仿真（输入图、Sobel 输出、关键波形）。
2. `sobel_01_hdmi_pattern`：HDMI 固定图显示（蓝色边框扩展）。
3. `sobel_02_hdmi_sobel`：固定图 Sobel（阈值对比）。
4. `sobel_03_uart_hdmi`：PC 串口传图 → PS 写 BRAM → HDMI 原图。
5. `sobel_04_uart_sobel_hdmi`：UART 图像 PL Sobel。
6. `sobel_05_pc_control_display`：PC 控制原图/灰度/边缘/叠加/阈值。
7. 综合扩展一：上位机与输入规格扩展（任务 1，C 档）。
8. 综合扩展二：PL 图像锐化算法（任务 3，B 档）。

**版式**：一行总目标 + 完成列表（基础 6 + 扩展 2）。
**讲解提示**：建立工作范围认知，强调基础与两个综合扩展都覆盖。

---

### 第 3 页：系统总体结构与数据流

**标题**：系统总体结构与数据流

**正文**：系统由 PC 上位机、UART、ZYNQ PS、AXI BRAM、PL 图像处理、HDMI 输出组成。两个综合扩展接入点已在图中标出：**任务 1 在 PC 端做输入缩放**，**任务 2 在 PL 端新增锐化并由控制字 `0x900C` 实时驱动**。

```text
PC 上位机（缩放=任务1 / 锐化强度控制=任务2）
  -> UART 图像帧 / 控制帧(含 0x04 锐化)
  -> ZYNQ PS 协议解析
  -> AXI BRAM 图像区 + 控制字(0x9000/04/08/0C)
  -> PL 灰度 / Sobel / 锐化(任务2) / 显示选择
  -> HDMI 原图/灰度/边缘/叠加/锐化
```

**推荐图片**：PPT 形状重画流程图；高亮"任务1=PC 缩放""任务2=PL 锐化+0x900C"。
**讲解提示**：讲清数据从哪来、在哪处理、怎么显示，并指出两个扩展各加在链路哪一端。

---

### 第 4 页：基础实验复现结果

**标题**：基础实验复现结果

**正文**：从纯 RTL 仿真到上板显示与 PC 控制逐步完成。

| 实验 | 目标 | 结果 |
| --- | --- | --- |
| 0 | RTL Sobel 仿真 | 输出图/波形正常 |
| 1 | HDMI 固定图 | 稳定，带蓝色边框 |
| 2 | 固定图 Sobel | 黑白边缘正常 |
| 3 | UART 原图 | PC→PS/BRAM→HDMI |
| 4 | UART Sobel | 绿色边缘正常 |
| 5 | PC 控制 | 原图/灰度/边缘/叠加可切换 |

**推荐图片**：[exp00_key_waveform.png](../coursework/evidence/01_rtl_sim/exp00_key_waveform.png)、[exp01_hdmi_field_20260618.jpg](../coursework/evidence/02_hdmi_pattern/exp01_hdmi_field_20260618.jpg)、[exp04_uart_sobel_field_20260618.jpg](../coursework/evidence/05_uart_sobel/exp04_uart_sobel_field_20260618.jpg)、[exp05_mode_overlay_field_20260618.jpg](../coursework/evidence/06_pc_control/exp05_mode_overlay_field_20260618.jpg)
**讲解提示**：按"仿真、HDMI、UART、控制"四个词过一遍。

---

### 第 5 页：第一周基础扩展

**标题**：第一周基础扩展完成情况

**正文**：

| 实验 | 扩展 | 作用 |
| --- | --- | --- |
| 0 | 异常帧自检 | 错误帧头/格式/行号处理 |
| 1 | HDMI 蓝色边框 | 标记有效区，验证坐标映射 |
| 2 | Sobel 阈值对比 | 阈值升高边缘点减少 |
| 3 | 原图边框 | 不改 BRAM，仅 HDMI 侧叠加 |
| 4 | 绿色彩色边缘 | Sobel 结果更易观察 |
| 5 | PC 控制显示模式 | 原图/灰度/边缘/叠加/阈值 |

**讲解提示**：强调这是第一周小扩展，第二周两个大扩展从下一页开始。

---

### 第 6 页：综合扩展总览（融合桥页）★

**标题**：第二周综合扩展总览 —— 一软一硬，两端增强

**正文**：本组从**输入侧**和**算法侧**两个方向各做一个综合扩展，二者正交、共用同一上位机与同一 bitstream。

| 维度 | 大拓展一（任务1） | 大拓展二（任务3） |
| --- | --- | --- |
| 方向 | 输入侧：规格适配 | 算法侧：新增 PL 算法 |
| 内容 | 任意尺寸→固定 128×72（fit/proc） | 图像锐化（Laplacian） |
| 改动 | 仅 PC（不改硬件） | PL+PS（零回归附加） |
| 档位 | C 档 | B 档 |
| 实时控制 | — | 0x900C，拖滑块即变锐 |
| 验证 | 12/12 + 36 矩阵 | 11 配置逐像素 match + golden 等价 + OOC |

**版式**：整页就放这张对照表 + 一句话主线"输入到算法两端增强同一条链路"。
**讲解提示**：这是把两个扩展"融合"成一个故事的关键页——先讲为什么要两端都做、为什么风险都压到最低，再分别展开。

---

### 第 7 页：大拓展一 题目、方案与创新点（任务1）

**标题**：大拓展一 —— 上位机与输入规格扩展（任务1，C 档）

**正文**：让系统支持任意尺寸输入，但**不改 FPGA**：任意尺寸先在 PC 端处理成固定 `128×72 RGB888` 再发送。创新点：① 硬件契约（帧头/包长/PS/BRAM/PL/HDMI）不变；② 输入适配前移到 PC，避免多模块联动改硬件；③ 三种 fit：`stretch`/`letterbox`/`center-crop`；④ 处理尺寸 `128x72`/`160x90`/`144x108` 直接对应 C 档参考尺寸，`64x36` 作低尺寸对比。

C 档尺寸对照：`128x72`、`160x90`、`144x108` 均已实现并测试。

**推荐图片**：[strech_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/strech_128x72.png)、[letterbos_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/letterbos_128x72.png)、[centercrop_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/centercrop_128x72.png)
**讲解提示**：为什么选 PC 适配——不是不能改硬件，而是风险更低、验证更清晰。

---

### 第 8 页：大拓展一 实现原理与软件验证（任务1）

**标题**：大拓展一 实现原理与验证

**正文**：

```text
任意尺寸 BGR -> prepare_frame(fit_mode, proc_size) -> 固定 128x72 RGB888
  -> build_frame_packet（27943B，帧头 55 aa 80 00 48 00 18）-> UART -> 原 sobel_05 链路
```

离线验证：3 种原始尺寸 × 3 种 fit × 4 种处理尺寸 = 36 组矩阵；`prepare_frame` 8/8 + 协议不变量 4/4 = **12/12 通过**；所有输出 `(72,128,3)`、帧长 27943B、帧头与控制帧不变。其中 `128x72/160x90/144x108` 三种 C 档尺寸全部进入自动化矩阵。

**推荐图片**：[ext_offline_tests.txt](../大拓展_01_上位机输入规格扩展/evidence/ext_offline_tests.txt) 摘要 + 一张 fit 对比图。
**讲解提示**：强调"不是只改界面，有可复现的软件验证"，并念出三种 C 档尺寸。

---

### 第 9 页：大拓展一 上板展示（任务1）

**标题**：大拓展一 最终上板展示

**正文**：上板复用实验 5 bitstream。展示三种 fit（`stretch` 拉伸 / `letterbox` 补边 / `center-crop` 裁剪）与处理尺寸对比；页面显眼写出 C 档尺寸 `128x72/160x90/144x108`，`64x36` 作更粗对比。

**推荐图片（必放 5 张）**：[strech_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/strech_128x72.png)、[letterbos_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/letterbos_128x72.png)、[centercrop_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/centercrop_128x72.png)、[strech_64x36.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/strech_64x36.png)、[centrecrop_64x36.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/centrecrop_64x36.png)
**讲解提示**：先对齐评分尺寸，再讲三种 fit，最后 `64x36` 更粗但协议不变。

---

### 第 10 页：大拓展二 题目与方案（任务3）

**标题**：大拓展二 —— 在 PL 上新增图像锐化算法（任务3，B 档）

**正文**：在 `sobel_05` 的 PL 上新增**图像锐化（Laplacian / unsharp 增强）**，与原 Sobel 同工程一键切换。B 档要件：新增 1 种算法 + 上板演示 + 与软件参考对比，三项全做。

设计取向——**最低风险地改 PL**：
1. 复用 Sobel 已验证的 3×3 窗口（中心=`mid1`），只附加一个拉普拉斯输出，Sobel 通路逐位不变；
2. 不改 BRAM 容量 / 时序 / Block Design（区别于任务 1 的 B 档要扩 BRAM）；
3. 强度经控制字 `0x900C` 每帧读取，拖滑块 HDMI 实时变锐，无需重发帧。

**推荐图片**：[sharpen_side_by_side_k128.png](../大拓展_03_图像处理算法扩展/evidence/sharpen_side_by_side_k128.png)
**讲解提示**：点明"这是真正改了 PL 的扩展，且零回归"。

---

### 第 11 页：大拓展二 锐化算法与定点实现（技术核心）★

**标题**：锐化算法与定点实现（RTL/PS/上位机逐位一致）

**正文**：基于灰度拉普拉斯的非锐化掩模，保留彩色。

```text
gray  = (77*R + 150*G + 29*B) >> 8                 # 与 rgb_to_gray.v 一致
lap   = 4*center - up - down - left - right         # 4 邻域拉普拉斯，1px 边界 = 0
delta = floor(strength * lap / 256)                 # RTL 算术右移 >>>8
out_c = clamp(c + delta, 0, 255)   for c in R,G,B   # 逐通道
```

- 拉普拉斯**白嫖** Sobel 的 3×3 窗口：`lap = 4·mid1 − top1 − bot1 − mid0 − mid2`，中心 `mid1` 即输出像素，与边缘像素同地址写入新增 `lap_mem`。
- `strength=0` 输出 == 原图；强度越大越锐，过大时高频处饱和（overshoot/halo，是 Laplacian 锐化固有特性，真实照片上即自然"变清晰"）。
- 同一套整数运算在 PL、PS、上位机三处实现，保证软件 golden 与硬件逐位一致。

**推荐图片**：3×3 窗口示意 + 上式；[sharpen_delta_heatmap_k128.png](../大拓展_03_图像处理算法扩展/evidence/sharpen_delta_heatmap_k128.png)（锐化增量集中在边缘/纹理）。
**讲解提示**：核心两点——"复用 Sobel 窗口所以零回归""三处整数逐位一致所以软件能对硬件"。

---

### 第 12 页：大拓展二 PL 数据通路与实时控制（技术核心）★

**标题**：PL 数据通路与实时控制

**正文**：

```text
扫描期：BRAM 图像 -> rgb_to_gray -> sobel_core ─┬─> edge_mem（原 Sobel，不变）
                                                └─> lap_data -> lap_mem（新增附加输出）
每帧起始：控制 FSM 依次读 0x9000/04/08/0C(mode/threshold/overlay/strength)
显示期：MODE_SHARPEN -> clamp(rgb + (strength*lap)>>>8) -> HDMI
控制：A5 5A 04 k -> PS 写 0x900C -> PL 每帧读取 -> 拖滑块实时变锐（无需重发帧）
```

改动文件：`sobel_core.v`（+`lap_data`）、`hdmi_bram_sobel_display.v`（+`MODE_SHARPEN`/`lap_mem`/`0x900C` FSM/显示乘加，`display_mode` 2→3 bit）、`main.c`（+`cmd 0x04`）。

**推荐图片**：上面这张数据通路图（PPT 形状重画），高亮"新增 `lap_mem` 支路 + `0x900C`"。
**讲解提示**：强调"新增支路与原 Sobel 并行，显示端只多一次乘加"，以及实时控制与实验 5 的 threshold/overlay 同构。

---

### 第 13 页：大拓展二 无板验证与资源时序（技术核心）★

**标题**：无板验证（RTL == 软件 golden）与资源时序

**正文**：复用实验 5 的无板软硬件协同仿真（真实上位机打包 → 真实 `main.c` PS 分发 → XSim 渲染 HDMI → 与软件 golden 逐像素比对），扩展覆盖锐化：

| 验证项 | 结果 |
| --- | --- |
| 全分辨率 1280×720 逐像素对比 | 11 配置全部 `=match`（含 sharp0/64/128/255） |
| 真实 `main.c` 端到端 | 收 `A5 5A 04 96` → `0x900C=96` |
| 原 Sobel 四模式自检 | `EXP05_SELFCHECK_TB=passed`（零回归） |
| numpy 预览 vs golden vs RTL | 三者逐位一致 |

OOC 综合（xc7z020clg400-2，74.25 MHz）：时序达标 **WNS +2.452 ns / 0 失败端点**；LUT 9229、FF 2725、BRAM 10.5/140、DSP 4/220。

**推荐图片**：上表 + 结论"RTL == 软件 golden，逐像素一致"。证据 [cosim_summary.txt](../大拓展_03_图像处理算法扩展/evidence/cosim_summary.txt)、[sharpen_equivalence.txt](../大拓展_03_图像处理算法扩展/evidence/sharpen_equivalence.txt)、[ooc_synth_timing.rpt](../大拓展_03_图像处理算法扩展/evidence/ooc_synth_timing.rpt)
**讲解提示**：区分"无板协同仿真逐像素一致"与"最终上板演示"，后者现场补。

---

### 第 14 页：大拓展二 上板演示与验收 GUI（任务3）

**标题**：大拓展二 上板演示与验收 GUI

**正文**：验收 GUI（`大拓展_03.../host_tool/camera_uart_gui.py`）面向"手操调参看可见改善"：

1. 连接串口 → 载入图片 → 发送到 FPGA；
2. 模式选 `sharpen`，**拖锐化强度滑块**：同窗口「原图 | 软件锐化(k)」并排实时刷新，HDMI 同步变锐；
3. 切回 `edge` 即原 Sobel，现场对比"新增算法 vs 原算法"；
4. GUI 还并入任务 1 的 fit/proc 控件，可叠加演示两个扩展。

**推荐图片（现场补硬件实拍）**：HDMI 锐化 k=0/64/128、Sobel↔锐化 切换、GUI 软件预览与 HDMI 对照各一张；当前先放 [sharpen_k0.png](../大拓展_03_图像处理算法扩展/evidence/sharpen_k0.png)、[sharpen_k128.png](../大拓展_03_图像处理算法扩展/evidence/sharpen_k128.png) 占位。
**讲解提示**：先展示软件预览（保证有画面），再切 HDMI 实拍；强调"软件预览与硬件逐像素一致，是可信预演"。

---

### 第 15 页：资源利用率、时序与性能（融合）★

**标题**：资源利用率、时序与性能分析

**正文**：见第 4.1 节表（exp1-5 + 任务1 不增资源 + 任务2 PL OOC）。要点：

- 实验 5 全设计 WNS `+0.325 ns`（裕量最小）。
- 任务 1 只改 PC，不增 FPGA 资源。
- 任务 2 新增 `lap_mem`（几个 BRAM）+ `k·lap`（1 个 DSP），PL OOC 下 74.25 MHz WNS `+2.452 ns`，裕量约 18%；最终 bitstream 复用实验 5 流程。
- 瓶颈：UART 115200 单帧 ≈ 2.43s（两扩展均不改 UART）。

**版式**：左资源表，右 UART 公式 + 两条结论（任务1 不增资源、任务2 时序达标）。
**讲解提示**：说清两种口径（全设计 vs PL OOC），别把两行数字混为一谈。

---

### 第 16 页：问题、总结与成员分工（融合）

**标题**：问题记录、总结与成员贡献

**正文**：问题：① VCD 大，取关键波形截图；② UART 慢（2.43s/帧）；③ 实验 5 时序裕量小，故任务 1 选不改 PL、任务 2 选复用窗口零回归；④ 不同尺寸直接拉伸会变形 → 三种 fit；⑤ 锐化在硬边合成图上会振铃 → 演示用真实照片、强度适中。

总结：完成完整链路 + 两个互补综合扩展（输入侧 PC 适配 C 档 + 算法侧 PL 锐化 B 档），均有可复现验证（任务1 12/12+36矩阵；任务2 逐像素 cosim + golden 等价 + OOC）。后续：① UART→网络传输提帧率；② 从任务 2 的 B 档向 A 档演进——再加 Prewitt/Laplacian 边缘、二值化（`lap_mem` 与灰度已就绪，增量小），凑齐 ≥3 种算法。

成员分工：见第 3.4 节表（人工填真实姓名/学号）。

**讲解提示**：收束页，不引入新技术点；强调"完整链路 + 两端扩展 + 充分验证 + 明确演进路径"。

---

## 8. 精简版文案（16 页，时间紧可直接用）

1. **封面**：ZYNQ7020 图像处理课程设计；Sobel UART 传图/HDMI 显示 + 上位机输入规格扩展 + PL 锐化算法。
2. **课程任务**：RTL 仿真→HDMI→Sobel→UART→PS/BRAM→PC 控制 + 两个综合扩展。
3. **系统结构**：PC→UART→PS→AXI BRAM→PL→HDMI；任务1 在 PC 缩放、任务2 在 PL 锐化(0x900C)。
4. **基础实验**：exp0-5 全完成。
5. **第一周扩展**：异常帧自检、HDMI 边框、阈值对比、彩色边缘、PC 控制。
6. **综合扩展总览**：一软一硬——任务1 输入侧 PC 适配(C 档)、任务2 算法侧 PL 锐化(B 档)，正交、共用上位机与 bitstream。
7. **大拓展一题目/创新**：不改硬件，三种 fit + C 档尺寸 128x72/160x90/144x108。
8. **大拓展一原理/验证**：prepare_frame→27943B 帧；12/12 + 36 矩阵；协议不变。
9. **大拓展一上板**：stretch/letterbox/center-crop + 64x36 对比。
10. **大拓展二题目/方案**：PL 新增锐化(B 档)；复用 Sobel 窗口、不改 BRAM/时序、强度实时可调。
11. **大拓展二算法**：gray/lap/clamp 定点；lap=4·mid1−top1−bot1−mid0−mid2；三处逐位一致。
12. **大拓展二数据通路**：扫描期附加 lap_mem 支路；每帧读 0x900C；显示期 clamp(rgb+(k·lap)>>>8)。
13. **大拓展二验证**：协同仿真 11 配置逐像素 match；numpy==golden==RTL；OOC WNS+2.452ns。
14. **大拓展二上板/GUI**：实时调强度、Sobel↔锐化 切换（硬件照片现场补）。
15. **资源性能**：exp5 10795 LUT/WNS+0.325ns；任务1 不增资源；任务2 PL OOC 时序达标；UART 瓶颈。
16. **总结分工**：完整链路 + 两端扩展 + 充分验证；后续网络传输 / 凑齐≥3 种算法升 A 档；补分工表。

---

## 9. 文书同学操作顺序

1. 建 16 页空白 PPT，按第 7 节标题命名。
2. 从第 7 节复制每页"正文"到对应页。
3. 按"推荐图片"插图，不要自己重新找图；任务 2 上板图位先留空，现场拍完补入。
4. 第 3、12 页用形状工具画流程图，不要直接截图代码块。
5. 第 15 页资源表做成表格，UART 公式单独放右侧；务必标注"任务2 那行是 PL OOC"。
6. 第 16 页成员分工找技术同学确认后再填真实姓名/学号。
7. 统一术语：`ZYNQ7020`、`UART`、`AXI BRAM`、`PL Sobel`、`128x72 RGB888`、`MODE_SHARPEN`、`lap_mem`、`0x900C`、`A5 5A 04 k`。
8. 表述纪律：① "离线/仿真验证通过" ≠ "硬件验证通过"；② 任务2 资源是 PL OOC、bitstream 复用实验5；③ 任务2 上板照片现场补。

---

## 10. 待人工补充项

1. 团队成员真实姓名、学号、分工贡献（任务 2 的 PL/PS 实现请落到具体成员）。
2. PPT 封面信息：课程名、班级、姓名/学号、日期。
3. 任务 2 上板照片/录像：现场拍摄锐化强度由小到大、Sobel↔锐化 切换、GUI 软件预览与 HDMI 对照，存入 [大拓展_03.../evidence/](../大拓展_03_图像处理算法扩展/evidence/) 并补进报告 6B.5 与本清单第 14 页。
4. 正式提交前确认已纳入 Git：[最终报告.md](./最终报告.md)、本清单、[大拓展_01.../](../大拓展_01_上位机输入规格扩展/)、[大拓展_03.../](../大拓展_03_图像处理算法扩展/)、各 evidence 目录。

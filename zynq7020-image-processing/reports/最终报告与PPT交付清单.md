# 最终报告与 PPT 交付清单

资料来源：老师原仓库 `zhouxzh/FPGA-course/zynq7020-image-processing/README.md`，以及本仓库 [zynq7020-image-processing/reports/最终报告.md](./最终报告.md)、[zynq7020-image-processing/coursework/evidence/](../coursework/evidence/) 下现有证据。老师原仓库地址：<https://github.com/zhouxzh/FPGA-course/tree/main/zynq7020-image-processing>

路径约定：本清单中的素材索引显示为远端仓库根目录路径，即以 `zynq7020-image-processing/` 开头；图片和证据材料均做成可点击链接，链接目标按本文件所在的 `reports/` 目录使用相对路径，便于 GitHub 直接跳转。

## 1. 老师要求核对

### 1.2 扩展验收至少需要提交

| 序号 | 要求 | 已准备材料 |
| --- | --- | --- |
| 1 | 第一周实验 0 到实验 4 基础扩展选择和结果，实验 5 控制功能结果 | [zynq7020-image-processing/reports/最终报告.md](./最终报告.md) 第 4 节；现场照片见 [zynq7020-image-processing/coursework/evidence/02_hdmi_pattern/](../coursework/evidence/02_hdmi_pattern/)、[zynq7020-image-processing/coursework/evidence/03_hdmi_sobel/](../coursework/evidence/03_hdmi_sobel/)、[zynq7020-image-processing/coursework/evidence/04_uart_hdmi/](../coursework/evidence/04_uart_hdmi/)、[zynq7020-image-processing/coursework/evidence/05_uart_sobel/](../coursework/evidence/05_uart_sobel/)、[zynq7020-image-processing/coursework/evidence/06_pc_control/](../coursework/evidence/06_pc_control/) |
| 2 | 第二周综合扩展任务选择和设计方案 | 选择任务 1：基于 `sobel_05` 的上位机与输入规格扩展；见最终报告第 6 节 |
| 3 | 修改过的文件列表，区分 PC/PS/PL | 最终报告第 5.2 节；本扩展主要修改 PC 端，不改 PS/PL/Vivado 工程 |
| 4 | 修改前后的关键代码说明 | `prepare_frame`、`--fit-mode`、`--proc-size`、GUI Folder/Fit mode/Proc size |
| 5 | 第二周综合扩展仿真截图、波形截图或软件验证结果 | [zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/*.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/)、[zynq7020-image-processing/大拓展_01_上位机输入规格扩展/evidence/ext_offline_tests.txt](../大拓展_01_上位机输入规格扩展/evidence/ext_offline_tests.txt)、[zynq7020-image-processing/大拓展_01_上位机输入规格扩展/evidence/ext_scaling_matrix.txt](../大拓展_01_上位机输入规格扩展/evidence/ext_scaling_matrix.txt) |
| 6 | Vivado 资源利用率、时序结果和 bitstream 生成结果 | 最终报告第 7 节；第二周扩展复用实验 5 bitstream，资源/时序同实验 5 |
| 7 | 上板演示现象、照片或视频截图 | [zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/*.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/)；基础最终演示仍可参考 [zynq7020-image-processing/coursework/evidence/09_final_demo/*.jpg](../coursework/evidence/09_final_demo/) |
| 8 | 实验现象、问题和性能瓶颈分析 | 最终报告第 8 节；UART 115200 下单帧约 2.43 秒是主要瓶颈 |

### 1.3 PPT 额外必须覆盖

根据要求截图，PPT 展示内容至少包括：

1. 扩展题目。
2. 创新点。
3. 实现原理。
4. 团队成员分工与贡献。

### 1.4 综合扩展二（任务 3 锐化）材料对应

本组在任务 1（C 档）之外另完成综合扩展任务 3（B 档：新增 1 种 PL 算法 + 上板演示 + 与软件参考对比）。材料如下；**上板照片在现场验收时统一补**到 `大拓展_03_图像处理算法扩展/evidence/`。

| 任务 3 要求 | 已准备材料 |
| --- | --- |
| 新增 1 种 PL 算法并与原 Sobel 对比 | 锐化 `MODE_SHARPEN`，与 Sobel(edge) 同工程可一键切换；见最终报告第 6B 节 |
| 算法 / 显示选择命令 | 复用 `A5 5A 01 mode`(mode=4) + 新增 `A5 5A 04 k` 锐化强度（控制字 `0x900C`） |
| 软件参考 golden（Python） | `大拓展_03.../host_tool/sharpen_algo.py`，与 RTL 定点逐位一致 |
| RTL 仿真对比硬件与软件参考 | 协同仿真 11 配置（含 sharp0/64/128/255）逐像素 `=match`；证据 `大拓展_03.../evidence/cosim_summary.txt`、`sharpen_equivalence.txt` |
| 资源利用率与时序 | OOC 综合 WNS +2.452ns；证据 `大拓展_03.../evidence/ooc_synth_utilization.rpt`、`ooc_synth_timing.rpt` |
| 上板演示算法切换 | 验收 GUI 实时调强度 + Sobel↔锐化 切换；**现场照片待补** |

## 3. PPT 建议结构

建议控制在 10 到 12 页。答辩时间短时可删“基础实验细节页”，保留大拓展和资源时序。

| 页码 | 标题 | 必须程度 | 核心内容 | 推荐素材 |
| --- | --- | --- | --- | --- |
| 1 | 题目与成员 | 必须 | 项目名、平台 ZYNQ7020、成员分工 | 无或最终演示图 |
| 2 | 课程任务与实验路线 | 必须 | RTL 仿真 -> HDMI -> Sobel -> UART -> PS/BRAM -> PC 控制 | 用一张数据流图 |
| 3 | 系统总体架构 | 必须 | PC 上位机、UART、PS、AXI BRAM、PL、HDMI | [zynq7020-image-processing/reports/最终报告.md](./最终报告.md) 第 2 节 Mermaid 图可重画 |
| 4 | 基础实验复现结果 | 必须 | 实验 0 到 5 一页表格，强调都完成 | 选 4 张代表图：仿真波形、HDMI、UART Sobel、PC 控制 |
| 5 | 第一周基础扩展 | 必须 | 边框、阈值对比、彩色边缘、模式控制 | `exp01_hdmi_field`、`exp04_uart_sobel`、`exp05_mode_overlay` |
| 6 | 第二周扩展题目 | 必须 | 任务 1：上位机与输入规格扩展 | 扩展需求 5 点压缩成 3 点 |
| 7 | 创新点 | 必须 | 不改硬件，独立大拓展目录；三种 fit；醒目标出 C 档尺寸 `128x72/160x90/144x108`；保持协议不变 | [zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/strech_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/strech_128x72.png) 等最终验收截图 |
| 8 | 实现原理 | 必须 | `prepare_frame -> build_frame_packet -> UART -> sobel_05` | 简图 + 帧头 `55 aa 80 00 48 00 18` |
| 9 | 仿真/软件验证 | 必须 | 12/12 测试通过；36 组矩阵；三种 C 档参考尺寸全部进入测试矩阵；包长和帧头不变 | [zynq7020-image-processing/大拓展_01_上位机输入规格扩展/evidence/ext_offline_tests.txt](../大拓展_01_上位机输入规格扩展/evidence/ext_offline_tests.txt) 摘要、[zynq7020-image-processing/大拓展_01_上位机输入规格扩展/evidence/ext_scaling_matrix.txt](../大拓展_01_上位机输入规格扩展/evidence/ext_scaling_matrix.txt) 摘要 |
| 10 | 上板展示结果 | 必须 | 三种 fit 策略、C 档三种参考尺寸和低处理尺寸最终效果；页面上必须单独写出 `128x72/160x90/144x108` | [zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/](../coursework/evidence/照片证明/大拓展最终验收视频截图/) 选 5 张 |
| 11 | 资源、时序、性能 | 必须 | 实验 1 到 5 资源表；扩展复用实验 5；UART 瓶颈 | 最终报告第 7 节表格 |
| 12 | 问题与总结 | 必须 | UART 慢、VCD 大、时序裕量、输入尺寸策略；后续可做网络传输 | 无或简表 |

## 4. PPT 必须展示内容

### 4.1 扩展题目

题目：基于 `sobel_05_pc_control_display` 的上位机与输入规格扩展。

一句话说明：在不修改 FPGA 硬件链路的前提下，让上位机支持不同输入尺寸、不同 fit 策略和不同处理尺寸，仍输出固定 `128x72 RGB888` 图像帧给原 `sobel_05` 系统。

### 4.2 创新点

必须讲清楚这 4 点：

1. **硬件契约不变**：UART 帧头、包长、PS 解析、BRAM 地址、PL Sobel、HDMI 放大都不变。
2. **输入适配前移到 PC 端**：避免改硬件尺寸导致 BRAM、HDMI、仿真和时序联动修改。
3. **三种 fit 策略**：`stretch`、`letterbox`、`center-crop`，分别对应拉伸、补边、裁剪。
4. **处理尺寸可选，并直接对应评分分档**：`128x72`、`160x90`、`144x108` 三种尺寸覆盖 C 档参考要求，`64x36` 作为低处理尺寸对比；最终发送帧仍固定 `128x72`。

建议在 PPT 上单独放一个“C 档尺寸验收对照”小表：

| C 档参考尺寸 | 本扩展状态 | 说明 |
| --- | --- | --- |
| `128x72` | 已支持 | 旧链路兼容尺寸 |
| `160x90` | 已支持 | 新增评分参考尺寸 |
| `144x108` | 已支持 | 新增评分参考尺寸 |

讲解时把这张表放在创新点或验证页显眼位置，因为它直接对应老师给出的分档依据。

### 4.3 实现原理

建议 PPT 上用下面这条链路：

```text
任意尺寸图片/目录/视频/摄像头
  -> prepare_frame(fit_mode, proc_size)
  -> 固定 128x72 RGB888
  -> build_frame_packet: 27943B, header 55 aa 80 00 48 00 18
  -> UART
  -> PS 写 BRAM
  -> PL Sobel / display control
  -> HDMI 原图/灰度/边缘/叠加
```

### 4.4 团队分工与贡献

这里需要人工填成员姓名。建议按实际工作填，不要泛泛写“共同完成”。模板如下：

| 成员 | 分工 | 可写贡献点 |
| --- | --- | --- |
| skf | PL/HDMI/Sobel | 负责提供肖像， HDMI 显示、Sobel 链路 |
| cwh | PS/UART/BRAM | 负责实验 3/4/5 的 PS 串口接收、BRAM 写入、控制字协议 |
| lzj | PC 上位机与综合扩展 | 负责 `大拓展_01_上位机输入规格扩展/host_tool` 输入规格扩展、fit 策略、GUI/CLI、离线测试 |
| lcy | 资料与展示 | 负责照片证据、、资源时序整理、报告、PPT、最终演示材料整理 |

## 5. PPT 推荐图片清单

大拓展相关图片优先使用 [zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/](../coursework/evidence/照片证明/大拓展最终验收视频截图/) 下的最终验收截图。[zynq7020-image-processing/大拓展_01_上位机输入规格扩展/evidence/](../大拓展_01_上位机输入规格扩展/evidence/) 下的图片和日志作为软件验证辅助材料。

### 5.1 必须放

| 用途 | 文件 |
| --- | --- |
| RTL 仿真关键波形 | [zynq7020-image-processing/coursework/evidence/01_rtl_sim/exp00_key_waveform.png](../coursework/evidence/01_rtl_sim/exp00_key_waveform.png) |
| 实验 1 HDMI 固定图 | [zynq7020-image-processing/coursework/evidence/02_hdmi_pattern/exp01_hdmi_field_20260618.jpg](../coursework/evidence/02_hdmi_pattern/exp01_hdmi_field_20260618.jpg) |
| 实验 4 UART Sobel | [zynq7020-image-processing/coursework/evidence/05_uart_sobel/exp04_uart_sobel_field_20260618.jpg](../coursework/evidence/05_uart_sobel/exp04_uart_sobel_field_20260618.jpg) |
| 实验 5 叠加模式 | [zynq7020-image-processing/coursework/evidence/06_pc_control/exp05_mode_overlay_field_20260618.jpg](../coursework/evidence/06_pc_control/exp05_mode_overlay_field_20260618.jpg) |
| 大拓展横屏 fit 策略 | [zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/strech_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/strech_128x72.png)、[zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/letterbos_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/letterbos_128x72.png)、[zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/centercrop_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/centercrop_128x72.png) |
| 大拓展竖屏 fit 策略 | [zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/letterbos_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/letterbos_128x72.png) 或 [zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/centercrop_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/centercrop_128x72.png) |
| 大拓展处理尺寸对比 | [zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/strech_64x36.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/strech_64x36.png)、[zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/centrecrop_64x36.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/centrecrop_64x36.png) |
| 最终演示原图 | [zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/strech_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/strech_128x72.png) |
| 最终演示边缘 | [zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/centercrop_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/centercrop_128x72.png) |
| 最终演示叠加 | [zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/letterbos_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/letterbos_128x72.png) |

### 5.2 可选放

| 用途 | 文件 |
| --- | --- |
| 实验 2 固定图 Sobel | [zynq7020-image-processing/coursework/evidence/03_hdmi_sobel/exp02_hdmi_sobel_field_20260618.jpg](../coursework/evidence/03_hdmi_sobel/exp02_hdmi_sobel_field_20260618.jpg) |
| 实验 3 UART 原图带边框 | [zynq7020-image-processing/coursework/evidence/04_uart_hdmi/exp03_uart_hdmi_field_20260618.jpg](../coursework/evidence/04_uart_hdmi/exp03_uart_hdmi_field_20260618.jpg) |
| 实验 5 原图/灰度/边缘 | [zynq7020-image-processing/coursework/evidence/06_pc_control/exp05_mode_original_field_20260618.jpg](../coursework/evidence/06_pc_control/exp05_mode_original_field_20260618.jpg)、[zynq7020-image-processing/coursework/evidence/06_pc_control/exp05_mode_gray_field_20260618.jpg](../coursework/evidence/06_pc_control/exp05_mode_gray_field_20260618.jpg)、[zynq7020-image-processing/coursework/evidence/06_pc_control/exp05_mode_edge_threshold_sparse_field_20260618.jpg](../coursework/evidence/06_pc_control/exp05_mode_edge_threshold_sparse_field_20260618.jpg) |
| 阈值 120 最终演示 | [zynq7020-image-processing/coursework/evidence/09_final_demo/final_live_gray_threshold120_gui_20260618.jpg](../coursework/evidence/09_final_demo/final_live_gray_threshold120_gui_20260618.jpg)、[zynq7020-image-processing/coursework/evidence/09_final_demo/final_live_edge_threshold120_gui_20260618.jpg](../coursework/evidence/09_final_demo/final_live_edge_threshold120_gui_20260618.jpg)、[zynq7020-image-processing/coursework/evidence/09_final_demo/final_live_overlay_threshold120_gui_20260618.jpg](../coursework/evidence/09_final_demo/final_live_overlay_threshold120_gui_20260618.jpg) |

## 6. 资源和性能页必须写的数据

### 6.1 资源/时序表

PPT 可直接放压缩版：

| 实验 | LUT | FF | BRAM | DSP | WNS(ns) | 结论 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 实验 1 | 232 | 179 | 12 | 0 | +7.772 | HDMI 基础链路 |
| 实验 2 | 2842 | 2353 | 14 | 0 | +1.578 | 加 Sobel 后资源上升 |
| 实验 3 | 1775 | 1504 | 16 | 0 | +8.173 | PS/BRAM/HDMI 原图显示 |
| 实验 4 | 4446 | 3662 | 18 | 0 | +13.453 | UART 图像 Sobel |
| 实验 5 | 10795 | 4113 | 20 | 0 | +0.325 | 多模式控制，时序裕量最小 |
| 大拓展 | 同实验 5 | 同实验 5 | 同实验 5 | 同实验 5 | +0.325 | 只改 PC 端，不增加 FPGA 资源 |

### 6.2 性能瓶颈

必须说明 UART 带宽瓶颈：

```text
一帧协议层字节数 = 7 + 72*4 + 128*72*3 = 27943B
UART 8N1 115200 baud 理论传输时间 = 27943*10/115200 ≈ 2.43s/frame
```

结论：当前系统显示稳定性和功能验证可用，但实时帧率主要受 UART 限制。后续提升方向是网络传输或更高带宽接口。

## 7. 报告和 PPT 的取舍

### 7.1 最终报告必须保留

- 完整 8 节结构。
- 每个实验至少一张现象图。
- 第一周扩展表格。
- 第二周扩展的设计原理、验证结果、上板结果。
- 修改文件列表。
- 资源/时序表。
- 问题记录和性能瓶颈分析。

### 7.2 PPT 必须压缩

PPT 不需要逐字复述最终报告。重点是：

1. 系统链路是什么。
2. 基础实验证明链路已跑通。
3. 大拓展解决了什么问题。
4. 大拓展为什么选择 PC 端适配而不是改硬件。
5. 有哪些验证：12/12 测试、36 组矩阵、最终上板截图。
6. 资源时序是否满足，以及性能瓶颈在哪里。
7. 每个成员做了什么。

## 8. 待人工补充项

1. 团队成员真实姓名和分工贡献。
2. PPT 封面信息：课程名、班级、姓名/学号、日期。
3. 如果老师要求演示视频，需从现场过程重新录屏；报告/PPT 当前优先使用 [zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/](../coursework/evidence/照片证明/大拓展最终验收视频截图/) 下的最终截图。
4. 若需要正式提交最终报告，确认 [zynq7020-image-processing/reports/最终报告.md](./最终报告.md)、[zynq7020-image-processing/reports/最终报告与PPT交付清单.md](./最终报告与PPT交付清单.md)、[zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/*](../coursework/evidence/照片证明/大拓展最终验收视频截图/) 和 [zynq7020-image-processing/大拓展_01_上位机输入规格扩展/*](../大拓展_01_上位机输入规格扩展/) 已纳入 Git。

---

## 9. PPT 文书排版版逐页脚本

本节面向没有参与技术实现的同学。制作 PPT 时按本节逐页排版即可：每页给出标题、页面目的、正文可直接复制、推荐图片、版式建议和讲解提示。除“成员姓名/学号/分工”需要人工补充外，其余文字可以直接使用。

建议总页数：12 页。若答辩时间很短，可删第 5 页或压缩第 10 页，但第 6 到第 11 页不要删，因为这些页直接对应大拓展、验证、上板和资源性能。

### 第 1 页：封面

**页面标题**

ZYNQ7020 图像处理课程设计  
基于 Sobel 的 UART 图像传输、HDMI 显示与上位机输入规格扩展

**页面正文**

- 平台：黑金 ZYNQ7020 开发板
- 任务：完成 RTL 仿真、HDMI 显示、UART 传图、PL Sobel、上位机控制与综合扩展
- 综合扩展题目：基于 `sobel_05_pc_control_display` 的上位机与输入规格扩展
- 成员：填写姓名、学号、班级
- 日期：填写答辩日期

**推荐图片**

[zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/letterbos_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/letterbos_128x72.png)

**版式建议**

左侧放标题和成员信息，右侧放最终叠加显示照片。封面不要放过多技术细节。

**讲解提示**

本页只说明项目主题和扩展方向。重点说清楚：我们完成的是一条从 PC 输入到 FPGA 处理再到 HDMI 显示的完整链路，最终扩展集中在上位机输入规格适配。

---

### 第 2 页：课程任务与完成范围

**页面标题**

课程设计任务与完成范围

**页面正文**

本课程设计要求在 ZYNQ7020 平台上逐步完成图像处理系统：先完成 RTL 级 Sobel 仿真，再完成 HDMI 固定图显示、固定图 Sobel、PC 串口传图、PS 写入 AXI BRAM、PL 读取 BRAM 并 HDMI 显示，最后实现上位机命令控制显示模式。

本组已完成以下内容：

1. `sobel_00_rtl_sim`：RTL 仿真，生成输入图、Sobel 输出图和关键波形。
2. `sobel_01_hdmi_pattern`：HDMI 固定图显示，完成蓝色边框扩展。
3. `sobel_02_hdmi_sobel`：固定图 Sobel 显示，完成阈值对比。
4. `sobel_03_uart_hdmi`：PC 串口传图，PS 写 BRAM，HDMI 显示原图。
5. `sobel_04_uart_sobel_hdmi`：UART 输入图像经 PL Sobel 后 HDMI 显示。
6. `sobel_05_pc_control_display`：PC 控制原图、灰度、边缘、叠加和阈值。
7. 第二周综合扩展：上位机输入规格扩展，支持不同尺寸和 fit 策略。

**推荐图片**

无硬性图片。可用流程箭头图替代。

**版式建议**

用“一行总目标 + 7 个完成项”的结构。可做成左侧任务链路，右侧完成列表。

**讲解提示**

这一页不是讲代码，而是建立评委对工作范围的认识。强调基础实验和综合扩展都覆盖到了。

---

### 第 3 页：系统总体结构和数据流

**页面标题**

系统总体结构与数据流

**页面正文**

系统由 PC 上位机、UART、ZYNQ PS、AXI BRAM、PL 图像处理模块和 HDMI 输出模块组成。PC 端负责读取图片、摄像头、视频或图片目录，并将图像转换为 RGB888 帧；PS 端负责解析串口协议并写入 BRAM；PL 端从 BRAM 读取图像，完成灰度转换、Sobel 边缘检测、阈值判断和显示模式选择；最终通过 HDMI 输出原图、灰度图、边缘图或叠加图。

数据流如下：

```text
PC 上位机
  -> UART 图像帧 / 控制帧
  -> ZYNQ PS 协议解析
  -> AXI BRAM 图像区 + 控制字
  -> PL 灰度 / Sobel / 显示选择
  -> HDMI 原图 / 灰度 / 边缘 / 叠加显示
```

**推荐图片**

建议文书同学用 PPT 自带形状重画一张流程图。节点如下：

`PC 上位机` -> `UART` -> `ZYNQ PS` -> `AXI BRAM` -> `PL 图像处理` -> `HDMI 显示`

**版式建议**

流程图放中间，下方放 2 行说明：PC 负责输入与控制，FPGA 负责图像处理与 HDMI 显示。

**讲解提示**

本页只需要讲清楚“数据从哪里来、在哪里处理、最后怎么显示”。不要展开 Sobel 公式，公式放后面。

---

### 第 4 页：基础实验复现结果

**页面标题**

基础实验复现结果

**页面正文**

基础实验按由浅入深的路线完成，从纯 RTL 仿真逐步过渡到真实 HDMI 上板显示和 PC 控制显示。实验 0 验证 Sobel RTL 数据通路，实验 1 和实验 2 验证 HDMI 与固定图 Sobel，实验 3 到实验 5 逐步加入 UART、PS、BRAM、PL Sobel 和上位机控制。

| 实验 | 核心目标 | 完成结果 |
| --- | --- | --- |
| 实验 0 | RTL Sobel 仿真 | 输出图和关键波形正常 |
| 实验 1 | HDMI 固定图显示 | 显示稳定，带蓝色边框 |
| 实验 2 | 固定图 Sobel | 黑白边缘图正常 |
| 实验 3 | UART 原图显示 | PC 图像经 PS/BRAM 显示到 HDMI |
| 实验 4 | UART Sobel 显示 | 绿色边缘图正常 |
| 实验 5 | PC 控制显示 | 原图、灰度、边缘、叠加可切换 |

**推荐图片**

- [zynq7020-image-processing/coursework/evidence/01_rtl_sim/exp00_key_waveform.png](../coursework/evidence/01_rtl_sim/exp00_key_waveform.png)
- [zynq7020-image-processing/coursework/evidence/02_hdmi_pattern/exp01_hdmi_field_20260618.jpg](../coursework/evidence/02_hdmi_pattern/exp01_hdmi_field_20260618.jpg)
- [zynq7020-image-processing/coursework/evidence/05_uart_sobel/exp04_uart_sobel_field_20260618.jpg](../coursework/evidence/05_uart_sobel/exp04_uart_sobel_field_20260618.jpg)
- [zynq7020-image-processing/coursework/evidence/06_pc_control/exp05_mode_overlay_field_20260618.jpg](../coursework/evidence/06_pc_control/exp05_mode_overlay_field_20260618.jpg)

**版式建议**

上半部分放表格，下半部分放 4 张小图。不要每个实验都放大图，否则页面会拥挤。

**讲解提示**

这页证明基础链路跑通。讲解时按“仿真、HDMI、UART、控制”四个关键词过一遍即可。

---

### 第 5 页：第一周基础扩展完成情况

**页面标题**

第一周基础扩展完成情况

**页面正文**

第一周扩展围绕基础实验展开，目标是在不偏离主线的前提下增加可观察、可验证的功能点。各扩展均保留了原实验的基础功能，同时增加了显示边框、阈值对比、彩色边缘和上位机控制能力。

| 实验 | 扩展内容 | 作用 |
| --- | --- | --- |
| 实验 0 | 异常帧自检 | 验证错误帧头、错误格式、错误行号处理 |
| 实验 1 | HDMI 蓝色边框 | 标记有效显示区域，验证坐标映射 |
| 实验 2 | Sobel 阈值对比 | 验证阈值升高后边缘像素减少 |
| 实验 3 | 原图显示边框 | 不改 BRAM 数据，仅在 HDMI 侧叠加边框 |
| 实验 4 | 绿色彩色边缘 | 使 Sobel 结果更易观察 |
| 实验 5 | PC 控制显示模式 | 支持原图、灰度、边缘、叠加和阈值控制 |

**推荐图片**

- [zynq7020-image-processing/coursework/evidence/02_hdmi_pattern/exp01_hdmi_field_20260618.jpg](../coursework/evidence/02_hdmi_pattern/exp01_hdmi_field_20260618.jpg)
- [zynq7020-image-processing/coursework/evidence/03_hdmi_sobel/exp02_hdmi_sobel_field_20260618.jpg](../coursework/evidence/03_hdmi_sobel/exp02_hdmi_sobel_field_20260618.jpg)
- [zynq7020-image-processing/coursework/evidence/06_pc_control/exp05_mode_overlay_field_20260618.jpg](../coursework/evidence/06_pc_control/exp05_mode_overlay_field_20260618.jpg)

**版式建议**

表格为主，右侧放 2 到 3 张图片即可。重点不是图片数量，而是让老师看到每个实验确实有扩展点。

**讲解提示**

强调这些是第一周小扩展，不是第二周大扩展。第二周大扩展从下一页开始单独讲。

---

### 第 6 页：第二周综合扩展题目

**页面标题**

第二周综合扩展：上位机与输入规格扩展

**页面正文**

第二周选择的综合扩展任务是“基于 `sobel_05_pc_control_display` 的上位机与输入规格扩展”。该扩展的目标是让系统支持更多输入尺寸和输入来源，同时保持原有 `sobel_05` 的显示控制功能。

本扩展解决的问题是：原系统默认以固定 `128x72 RGB888` 图像帧进入 FPGA。如果直接支持任意尺寸，会牵涉 PS 接收、BRAM 地址、PL Sobel 窗口、HDMI 放大比例和仿真工程的同步修改，风险较高。因此本设计采用 PC 端统一适配方案：任意尺寸输入先在上位机端处理成固定 `128x72 RGB888`，再发送给 FPGA。

扩展目标：

1. 支持不同原始尺寸图片输入。
2. 支持 `stretch`、`letterbox`、`center-crop` 三种适配策略。
3. 支持 `128x72`、`160x90`、`144x108` 三种 C 档参考处理尺寸，并保留 `64x36` 低处理尺寸对比。
4. 保持 UART 帧格式、PS/PL/BRAM/HDMI 链路不变。
5. 保持实验 5 的原图、灰度、边缘、叠加和阈值控制可用。

**推荐图片**

[zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/strech_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/strech_128x72.png)、[zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/letterbos_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/letterbos_128x72.png)、[zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/centercrop_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/centercrop_128x72.png)

**版式建议**

左侧写“问题”，右侧写“方案”。底部放一张横屏 fit 策略对比图。

**讲解提示**

本页必须讲清楚为什么选择 PC 端适配：不是因为硬件不能改，而是因为这样风险更低、兼容性更强、验证链路更清晰。

---

### 第 7 页：创新点

**页面标题**

综合扩展创新点

**页面正文**

本扩展的创新点不是单纯增加一个输入按钮，而是把输入规格适配、协议兼容和硬件稳定性作为整体设计目标。

创新点 1：硬件契约不变  
UART 帧头、整帧包长、PS 解析逻辑、BRAM 地址映射、PL Sobel 尺寸和 HDMI 放大逻辑均保持不变。这样可以复用实验 5 已经验证通过的硬件链路。

创新点 2：输入适配前移到 PC 端  
不同尺寸、不同宽高比的输入图像先在上位机完成缩放、补边或裁剪，再统一发送固定 `128x72 RGB888` 帧，避免硬件多模块同步修改。

创新点 3：三种 fit 策略可选  
`stretch` 直接拉伸，适合保持旧工具行为；`letterbox` 等比缩放并补边，适合保持图像不变形；`center-crop` 等比放大后裁剪，适合铺满显示区域。

创新点 4：处理尺寸可选  
支持 `128x72`、`160x90`、`144x108` 和 `64x36` 四种处理尺寸。前三种不是随便列的参数，而是评分表 C 档给出的参考尺寸；`64x36` 只是额外对比尺寸。最终发送帧仍保持 `128x72`，因此不影响 FPGA 接收协议。

C 档尺寸验收对照：

| 评分表参考尺寸 | 展示/验证状态 | 评分意义 |
| --- | --- | --- |
| `128x72` | 已实现、已测试 | 原固定链路尺寸 |
| `160x90` | 已实现、已测试 | 新增 C 档参考尺寸 |
| `144x108` | 已实现、已测试 | 新增 C 档参考尺寸 |

**推荐图片**

- [zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/strech_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/strech_128x72.png)、
- [zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/letterbos_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/letterbos_128x72.png)、
- [zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/centercrop_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/centercrop_128x72.png)
- [zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/strech_64x36.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/strech_64x36.png)、[zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/centrecrop_64x36.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/centrecrop_64x36.png)

**版式建议**

四个创新点做成 2x2 卡片。右侧或底部放 fit 策略图和处理尺寸对比图，并把“C 档尺寸验收对照”做成醒目的小表。

**讲解提示**

避免说“创新点很多”这类空话。按“硬件不变、PC 适配、三种策略、三种评分参考尺寸”四点讲即可；讲到尺寸时直接念出 `128x72`、`160x90`、`144x108`。

---

### 第 8 页：实现原理

**页面标题**

综合扩展实现原理

**页面正文**

扩展的核心函数是 `prepare_frame`。任意尺寸的 BGR 输入图像先经过 `prepare_frame`，根据选择的 fit 策略和处理尺寸生成固定 `128x72 RGB888` 输出，再由 `build_frame_packet` 打包为 UART 图像帧。由于输出帧格式保持不变，PS、BRAM、PL Sobel 和 HDMI 显示逻辑无需修改。

实现链路：

```text
任意尺寸图片 / 图片目录 / 视频 / 摄像头
  -> prepare_frame(fit_mode, proc_size)
  -> 固定 128x72 RGB888
  -> build_frame_packet
  -> 27943B UART 图像帧
  -> PS 写入 AXI BRAM
  -> PL Sobel / display control
  -> HDMI 显示
```

关键协议保持不变：

```text
图像帧头：55 aa 80 00 48 00 18
整帧长度：27943B
控制帧：A5 5A cmd value
```

修改文件：

- `大拓展_01_上位机输入规格扩展/host_tool/camera_uart_sender.py`：新增 `prepare_frame`、`--fit-mode`、`--proc-size`、`--fill-color`。
- `大拓展_01_上位机输入规格扩展/host_tool/camera_uart_gui.py`：增加 GUI 中的 Fit mode、Proc size 和 Folder 入口。
- `大拓展_01_上位机输入规格扩展/host_tool/tests/*`：增加离线测试，验证输出形状、C 档参考尺寸覆盖、帧头、包长和控制帧不变。

**推荐图片**

建议重画流程图；也可放 [zynq7020-image-processing/大拓展_01_上位机输入规格扩展/evidence/ext_cli_help.txt](../大拓展_01_上位机输入规格扩展/evidence/ext_cli_help.txt) 中参数截图，但优先用流程图。

**版式建议**

中间放流程图，右侧放协议不变量：`128x72`、`27943B`、`55 aa 80 00 48 00 18`、`A5 5A cmd value`。

**讲解提示**

本页是技术核心。要突出“PC 端变化，FPGA 端不变”。

---

### 第 9 页：软件验证与仿真结果

**页面标题**

综合扩展验证结果

**页面正文**

综合扩展先完成离线验证，再进行上板演示。离线验证覆盖 3 种原始尺寸、3 种 fit 策略和 4 种处理尺寸，共 `3 x 3 x 4 = 36` 组组合。处理尺寸包含 `128x72`、`160x90`、`144x108` 三种 C 档参考尺寸，以及 `64x36` 低处理尺寸对比。也就是说，评分表里的三种 C 档尺寸都不是只写在文档里，而是全部进入了自动化测试矩阵。每组输出最终都满足固定形状 `(72,128,3)`，打包后帧长均为 `27943B`，帧头均为 `55 aa 80 00 48 00 18`。

测试结果：

```text
prepare_frame 测试：8/8 passed
protocol invariant 测试：4/4 passed
总计：12/12 offline assertions passed
```

验证结论：

1. `stretch` 与旧版 resize 行为兼容。
2. `letterbox` 能保持图像宽高比，并使用指定颜色补边。
3. `center-crop` 能铺满显示区域，不引入补边。
4. C 档尺寸验收依据：`128x72`、`160x90`、`144x108` 全部实现并通过矩阵验证；`64x36` 处理尺寸输出更粗，仅作为额外对比。
5. 控制帧仍为 `A5 5A cmd value`，实验 5 控制功能不受影响。

**推荐图片**

- [zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/letterbos_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/letterbos_128x72.png) 或 [zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/centercrop_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/centercrop_128x72.png)
- [zynq7020-image-processing/大拓展_01_上位机输入规格扩展/evidence/ext_offline_tests.txt](../大拓展_01_上位机输入规格扩展/evidence/ext_offline_tests.txt) 的测试结果可截图或手工做成表格

**版式建议**

左侧放测试表，右侧放竖屏 fit 策略对比图。中间或右上角加一个醒目的“C 档尺寸：128x72 / 160x90 / 144x108 均已验证”。不要直接贴整段日志，提炼成 12/12、36 组矩阵和三种评分尺寸即可。

**讲解提示**

这页证明扩展不是只改界面，而是有可复现的软件验证。

---

### 第 10 页：最终上板展示结果

**页面标题**

大拓展最终验收截图

**页面正文**

最终验收重点展示上位机输入规格扩展的实际效果。扩展不修改 FPGA 侧 PS/BRAM/PL/HDMI 链路，而是在 PC 端把不同尺寸输入统一适配为固定 `128x72 RGB888` 帧。页面必须显眼写出评分尺寸依据：`128x72`、`160x90`、`144x108` 三种 C 档参考尺寸已支持；`64x36` 是额外低处理尺寸对比。

展示结果：

1. `stretch 128x72`：直接拉伸到目标尺寸，画面铺满，但可能改变宽高比。
2. `letterbox 128x72`：保持原图比例，居中显示，空白区域补边。
3. `center-crop 128x72`：保持比例并铺满画面，通过裁剪边缘避免黑边。
4. C 档尺寸对照：`128x72`、`160x90`、`144x108` 均已作为 `proc-size` 实现，最后统一回到固定 `128x72` 帧。
5. `stretch/center-crop 64x36`：低处理尺寸对比，显示效果更粗，但不是 C 档评分尺寸本体。

**推荐图片**

必放 5 张：

- [zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/strech_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/strech_128x72.png)
- [zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/letterbos_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/letterbos_128x72.png)
- [zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/centercrop_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/centercrop_128x72.png)
- [zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/strech_64x36.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/strech_64x36.png)
- [zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/centrecrop_64x36.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/centrecrop_64x36.png)

**版式建议**

做成 2 行图片矩阵：第一行放三种 `128x72` fit 策略，第二行放两张 `64x36` 处理尺寸截图。图片矩阵旁边放“C 档尺寸对照：128x72、160x90、144x108 已支持”。每张图片下方写清楚模式名，不要只写“图 1/图 2”。

**讲解提示**

本页是大拓展展示核心。讲解时按“先对齐评分尺寸：128x72、160x90、144x108；再说明 stretch/letterbox/center-crop；最后补充 64x36 更粗但协议不变”的顺序说明。

---

### 第 11 页：资源利用率、时序与性能分析

**页面标题**

资源利用率、时序与性能分析

**页面正文**

实验 1 到实验 5 随着 HDMI、Sobel、BRAM 和显示控制逐步加入，资源占用逐渐上升。实验 5 功能最完整，因此 LUT 使用最多，时序裕量也最小。第二周综合扩展只修改 PC 上位机，不修改 FPGA 工程，因此 FPGA 资源和时序沿用实验 5 的结果。

| 实验 | LUT | FF | BRAM | DSP | WNS(ns) | 说明 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 实验 1 | 232 | 179 | 12 | 0 | +7.772 | HDMI 固定图 |
| 实验 2 | 2842 | 2353 | 14 | 0 | +1.578 | HDMI Sobel |
| 实验 3 | 1775 | 1504 | 16 | 0 | +8.173 | UART 原图显示 |
| 实验 4 | 4446 | 3662 | 18 | 0 | +13.453 | UART Sobel |
| 实验 5 | 10795 | 4113 | 20 | 0 | +0.325 | PC 控制多模式 |
| 大拓展 | 同实验 5 | 同实验 5 | 同实验 5 | 同实验 5 | +0.325 | 只改 PC 端 |

性能瓶颈主要是 UART 传输：

```text
一帧协议层字节数 = 7 + 72*4 + 128*72*3 = 27943B
UART 8N1 115200 baud 理论传输时间 = 27943*10/115200 ≈ 2.43s/frame
```

结论：系统功能验证和显示稳定性满足要求，但实时帧率受 UART 带宽限制。后续如果追求实时视频，应考虑网络传输或更高带宽接口。

**推荐图片**

无必须图片。建议用表格 + 小型折线/柱状图：横轴实验 1 到实验 5，纵轴 LUT 或 WNS。

**版式建议**

左侧资源表，右侧放 UART 计算公式和结论。突出“大拓展不增加 FPGA 资源”。

**讲解提示**

这一页回答老师可能问的“资源占多少、时序过没过、性能瓶颈在哪”。必须说清楚实验 5 WNS 仍为正，但裕量较小。

---

### 第 12 页：问题记录、总结与分工贡献

**页面标题**

问题记录、总结与成员贡献

**页面正文**

问题记录：

1. 仿真波形文件较大，原始 VCD 不适合提交，因此提取关键波形截图用于报告。
2. UART 传图速度较慢，`115200` baud 下单帧理论传输时间约 2.43 秒。
3. 实验 5 时序裕量较小，WNS 为 `+0.325 ns`，因此第二周扩展选择不修改 PL，避免增加时序风险。
4. 不同尺寸输入如果直接拉伸会变形，因此扩展中加入 `stretch`、`letterbox`、`center-crop` 三种策略。

总结：

本课程设计完成了从 RTL 仿真到 HDMI 上板显示、从固定图像到 PC UART 输入、从单一 Sobel 输出到上位机控制显示模式的完整链路。第二周综合扩展在不修改硬件的前提下，实现了不同输入尺寸和不同 fit 策略的上位机适配，并通过离线测试、矩阵验证和最终上板截图证明功能可用。

成员分工模板：

| 成员 | 主要分工 | 贡献说明 |
| --- | --- | --- |
| skf | PL/HDMI/Sobel/图片 | 负责提供肖像，HDMI 显示、Sobel 链路 |
| cwh | PS/UART/BRAM | 负责串口接收、BRAM 写入、控制字协议 |
| lzj | PC 上位机与大拓展 | 负责输入规格扩展、fit 策略、GUI/CLI、离线测试 |
| lcy | 文档与展示 | 负责照片证据、报告整理、资源时序整理、PPT 制作和答辩材料 |

**推荐图片**

可不放图片。若页面太空，可放最终叠加图：

[zynq7020-image-processing/coursework/evidence/照片证明/大拓展最终验收视频截图/letterbos_128x72.png](../coursework/evidence/照片证明/大拓展最终验收视频截图/letterbos_128x72.png)

**版式建议**

上半部分放问题和总结，下半部分放成员分工表。成员姓名必须由实际团队填写。

**讲解提示**

本页收束，不要再引入新技术点。重点说：完整链路完成、扩展验证充分、后续优化方向明确。

---

## 10. 可直接复制到 PPT 的精简版文案

如果时间紧，文书同学可以直接使用以下 12 页标题和正文摘要。

1. **封面**：ZYNQ7020 图像处理课程设计。基于 Sobel 的 UART 图像传输、HDMI 显示与上位机输入规格扩展。
2. **课程任务**：完成 RTL 仿真、HDMI 固定图、固定图 Sobel、UART 传图、PS/BRAM、PL Sobel、上位机控制和综合扩展。
3. **系统结构**：PC 上位机通过 UART 发送图像帧和控制帧，PS 写入 AXI BRAM，PL 完成灰度、Sobel 和显示选择，HDMI 输出结果。
4. **基础实验结果**：实验 0 到实验 5 均完成，覆盖仿真、HDMI、UART、BRAM、PL Sobel 和 PC 控制显示。
5. **第一周扩展**：完成异常帧自检、HDMI 边框、阈值对比、彩色边缘和上位机控制模式。
6. **第二周扩展题目**：基于 `sobel_05` 的上位机与输入规格扩展，目标是在不修改硬件的情况下支持不同尺寸和输入来源。
7. **创新点**：硬件契约不变，输入适配前移到 PC 端，支持 stretch/letterbox/center-crop，支持 `128x72`、`160x90`、`144x108` 三种 C 档参考尺寸和 `64x36` 对比尺寸。
8. **实现原理**：任意尺寸输入经 `prepare_frame` 变为固定 `128x72 RGB888`，再由 `build_frame_packet` 打包为 27943B UART 帧发送给原系统。
9. **验证结果**：3 种原始尺寸 × 3 种 fit × 4 种处理尺寸共 36 组矩阵验证；离线测试 12/12 通过；帧头、包长和控制帧保持不变。
10. **上板展示**：最终可展示原图、灰度、Sobel 边缘和红色边缘叠加模式，阈值变化能够影响边缘结果。
11. **资源性能**：实验 5 使用 10795 LUT、4113 FF、20 BRAM，WNS +0.325ns；大拓展只改 PC 端，不增加 FPGA 资源；UART 是主要性能瓶颈。
12. **总结分工**：项目完成完整图像处理链路和上位机输入规格扩展；后续可优化方向是网络传输和新增 PL 图像算法；补充成员分工表。

## 11. 文书同学操作顺序

1. 先建 12 页 PPT 空白页，按第 9 节每页标题命名。
2. 从第 9 节复制每页“页面正文”到对应 PPT。
3. 按每页“推荐图片”插入图片，不要自己重新找图。
4. 第 3 页和第 8 页用形状工具画流程图，不建议直接截图 Mermaid。
5. 第 11 页把资源表做成表格，UART 公式单独放到右侧。
6. 第 12 页成员分工必须找技术同学确认后再填。
7. 全文统一术语：`ZYNQ7020`、`UART`、`AXI BRAM`、`PL Sobel`、`HDMI`、`128x72 RGB888`。
8. 不要把“离线验证通过”写成“硬件全部验证通过”。大拓展的软件验证和最终上板演示要分开表述。

---

## 12. 大拓展_03（任务 3 B 档 · 锐化）PPT 补充页（优先技术实现）

本组完成了两个综合扩展。PPT 在第 6–11 页讲完任务 1（输入规格扩展）后，加入以下 5 页讲任务 3（PL 锐化算法）。按要求**优先展示技术实现**：算法定点、PL 数据通路、无板验证、资源时序四页为重点；故事性内容压到最少。上板照片在现场验收后补入第 17 页。术语统一：`MODE_SHARPEN`、`lap_mem`、控制字 `0x900C`、`A5 5A 04 k`。

> 一句话定位（可放每页脚注）：任务 3 = 在实验 5 的 PL 上**新增锐化算法**，与原 Sobel 同工程一键切换，强度实时可调，并用与硬件**逐位一致**的软件 golden 做对比。

### 第 13 页：大拓展二题目与定位（任务 3 B 档）

**页面正文**

- 题目：综合扩展任务 3——在 `sobel_05_pc_control_display` 的 PL 上新增图像处理算法，本组实现**图像锐化（Laplacian / unsharp 增强）**。
- 档位：B 档（新增 1 种算法 + 上板演示 + 与软件参考对比）。
- 与任务 1 的关系：任务 1 改 PC（输入缩放），任务 3 改 PL（新增算法），两者正交、同一上位机工具可叠加演示，合起来超出“三选一”的最低要求。
- 设计取向（一句话）：**最低风险地改 PL**——复用 Sobel 已验证的 3×3 窗口，不动 BRAM / 时序 / Block Design。

**讲解提示**：强调“这是真正改了 PL 的扩展（不是只改上位机）”，且是零回归的纯附加改动。

---

### 第 14 页：锐化算法与定点实现（技术核心）

**页面正文**

锐化采用基于灰度拉普拉斯的非锐化掩模，保留彩色。定点公式（PL / PS / 上位机三处逐位一致）：

```text
gray  = (77*R + 150*G + 29*B) >> 8                 # 与 rgb_to_gray.v 一致
lap   = 4*center - up - down - left - right         # 4 邻域拉普拉斯，1 像素边界 = 0
delta = floor(strength * lap / 256)                 # RTL 算术右移 >>>8
out_c = clamp(c + delta, 0, 255)   for c in R,G,B   # 逐通道
```

- `strength` = 锐化强度 0..255（控制字 `0x900C`）；`strength=0` 输出 == 原图。
- 拉普拉斯与 Sobel **共用同一 3×3 窗口**，中心像素 = `mid1`，故 `lap = 4·mid1 − top1 − bot1 − mid0 − mid2`，与边缘像素同地址写入新增的 `lap_mem`。

**推荐图片**：3×3 窗口示意 + 上式；可放 `大拓展_03.../evidence/sharpen_side_by_side_k128.png`（原图 | 锐化）与 `sharpen_delta_heatmap_k128.png`（锐化增量集中在边缘/纹理）。

**讲解提示**：本页是算法核心。点明“拉普拉斯白嫖了 Sobel 的窗口，所以零回归”，以及“整数运算三处逐位一致才能软件对硬件”。

---

### 第 15 页：PL 数据通路与实时控制（技术核心）

**页面正文**

```text
扫描期：BRAM 图像 -> rgb_to_gray -> sobel_core ──┬─> edge_mem（原 Sobel，不变）
                                                 └─> lap_data -> lap_mem（新增，附加输出）
每帧起始：读控制字 0x9000/04/08/0C(mode/threshold/overlay/strength)
显示期：rgb_mem + lap_mem -> clamp(rgb + (strength*lap)>>>8) -> HDMI（MODE_SHARPEN）
```

- 控制 FSM 在原 mode/threshold/overlay 三个控制字读取后，**多读一个 `0x900C`**（同构地扩了 3 个状态）。
- `strength` 每帧读取并在显示端应用：**拖上位机滑块 → HDMI 实时变锐，无需重发图像帧**（与实验 5 的 threshold/overlay 实时控制完全一致）。
- 改动文件：`sobel_core.v`（+`lap_data`）、`hdmi_bram_sobel_display.v`（+`MODE_SHARPEN`/`lap_mem`/`0x900C`/显示乘加，`display_mode` 2→3 bit）、`main.c`（+`0x04` 命令）。

**推荐图片**：上面这张数据通路图（PPT 形状重画），高亮“新增的 `lap_mem` 支路 + `0x900C`”。

**讲解提示**：强调“新增支路与原 Sobel 并行、只在显示端多一次乘加”，以及实时控制的同构性。

---

### 第 16 页：无板验证（RTL == 软件 golden）与资源时序（技术核心）

**页面正文**

复用实验 5 的无板软硬件协同仿真（真实上位机打包 → 真实 `main.c` PS 分发 → XSim 渲染 HDMI → 与软件 golden 逐像素比对），已扩展覆盖锐化：

| 验证项 | 结果 |
| --- | --- |
| 全分辨率 1280×720 逐像素对比 | **11 配置全部 `=match`**（含 sharp0/64/128/255） |
| 真实 `main.c` 端到端 | 收 `A5 5A 04 96` → 控制字 `0x900C=96` |
| 原 Sobel 四模式自检 | `EXP05_SELFCHECK_TB=passed`（零回归） |
| numpy 预览 vs golden vs RTL | 三者逐位一致 |

OOC 综合（xc7z020clg400-2，74.25 MHz）：**时序达标 WNS +2.452 ns / 0 失败端点**；LUT 9229(17%)、FF 2725、BRAM 10.5/140、DSP 4/220。`lap_mem` 占数个 BRAM，`k·lap` 占 1 个 DSP，组合乘加时序裕量约 18%。

**推荐图片**：上表 + 一行结论“RTL == 软件 golden，逐像素一致”。证据文件 `大拓展_03.../evidence/cosim_summary.txt`、`sharpen_equivalence.txt`、`ooc_synth_timing.rpt`。

**讲解提示**：这页回答“怎么证明对、占多少、过不过时序”。务必区分“无板协同仿真逐像素一致”与“最终上板演示”——后者现场补。

---

### 第 17 页：上板演示与验收 GUI（现场补照片）

**页面正文**

验收 GUI（`大拓展_03.../host_tool/camera_uart_gui.py`）面向“手操调参看可见改善”：

1. 连接串口 → 载入图片 → 发送到 FPGA；
2. 显示模式选 `sharpen`，**拖动锐化强度滑块**：同窗口「原图 | 软件锐化(k)」并排实时刷新，HDMI 同步变锐；
3. 切回 `edge` 即原 Sobel，现场对比“新增算法 vs 原算法”；
4. GUI 还并入了任务 1 的 fit / proc 缩放控件，可叠加演示两个扩展。

**推荐图片**：**现场验收时补**——锐化强度由小到大（k=0/64/128）的 HDMI 实拍、Sobel↔锐化 切换实拍、GUI 软件预览与 HDMI 对照各 1 张，放入 `大拓展_03.../evidence/` 后链接进来。当前可先放软件预览图 `大拓展_03.../evidence/sharpen_k0.png`、`sharpen_k128.png` 占位。

**讲解提示**：现场先展示软件预览（保证有画面），再切到 HDMI 实拍；强调“软件预览与硬件逐像素一致”，因此软件预览就是硬件效果的可信预演。


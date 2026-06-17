# ZYNQ7020 图像处理课程设计

本仓库是 ZYNQ7020 图像处理课程设计的个人工作仓库，核心内容集中在
[`zynq7020-image-processing`](zynq7020-image-processing)。

## 快速入口

| 入口                                                                                                                   | 用途                            |
| -------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| [`zynq7020-image-processing/README.md`](zynq7020-image-processing/README.md)                                         | 课程目标、实验路线、时间安排和评分要求           |
| [`zynq7020-image-processing/coursework/README.md`](zynq7020-image-processing/coursework/README.md)                   | 当前主线状态、证据目录、现场待办和分支边界         |
| [`zynq7020-image-processing/coursework/docs/README.md`](zynq7020-image-processing/coursework/docs/README.md)         | 详细文档索引，包括无板开发计划、协同仿真方法和历史进度日志 |
| [`zynq7020-image-processing/coursework/evidence/README.md`](zynq7020-image-processing/coursework/evidence/README.md) | 仿真、构建、资源时序和上板证据索引             |

## 主线边界

- `main` 只保留已经整理进主线的基础实验 0 到实验 5 远程开发成果。
- 第二周“大拓展”暂时保留在 `exp/05-ext-scaling`，等上机验证和证据补齐后再考虑合并。
- Vivado/Vitis 生成目录、bitstream、ELF、VCD 等大型产物不进入 Git；只提交精简日志、截图、说明和可复现脚本。

## 常用目录

| 目录 | 说明 |
| --- | --- |
| `zynq7020-image-processing/sobel_00_rtl_sim` | 实验 0：RTL 仿真 |
| `zynq7020-image-processing/sobel_01_hdmi_pattern` | 实验 1：HDMI 固定图片显示 |
| `zynq7020-image-processing/sobel_02_hdmi_sobel` | 实验 2：固定图片 Sobel |
| `zynq7020-image-processing/sobel_03_uart_hdmi` | 实验 3：UART 传图与 HDMI 原图显示 |
| `zynq7020-image-processing/sobel_04_uart_sobel_hdmi` | 实验 4：UART 输入图像的 PL Sobel 显示 |
| `zynq7020-image-processing/sobel_05_pc_control_display` | 实验 5：上位机控制模式、阈值和叠加 |
| `zynq7020-image-processing/host_camera_uart` | PC 端图像发送和控制工具 |
| `zynq7020-image-processing/coursework` | 个人实施记录、证据和报告材料 |

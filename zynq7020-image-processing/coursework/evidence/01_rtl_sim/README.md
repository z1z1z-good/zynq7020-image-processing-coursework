# 实验 0 默认 RTL 仿真证据

## 运行信息

- 日期：2026-06-15
- 分支：`exp/00-rtl-sim`
- 基线提交：`5c56b3f10bbe00019b61fd1e2ba8075a99881d20`
- Python：3.11.4
- 仿真器：ModelSim SE-64 10.5
- 参数：`128x72`、`12 MHz` 仿真时钟、`1 Mbaud`
- 命令：

```powershell
cd zynq7020-image-processing\sobel_00_rtl_sim
.\run_sim.ps1
```

`run_sim.ps1` 自动检测到本机没有 Icarus/VVP，选择了可用的 ModelSim。
备用 XSim 2023.2 入口也已单独回归通过，且生成的输入、输出 PNG 与 ModelSim 证据 SHA-256 一致。

## 实际结果

- Verilog 编译：0 errors，0 warnings。
- testbench：输出 `Sobel RGB888 simulation passed`。
- 仿真结束时间：`275314057 ns`。
- 自检覆盖：错误帧头、错误格式、错误行号和一帧有效 RGB888 图像。
- 有效帧输出像素数：`9216`，即 `128 x 72`。
- Sobel 输出：`128x72`，6980 个非零像素，最大值 255。
- RTL 和 testbench 未修改。

## 证据文件

| 文件 | 内容 |
| --- | --- |
| `exp00_default_sim.txt` | 本次自动选择、编译、自检和图片转换日志 |
| `exp00_input_rgb.png` | 默认 RGB888 输入图 |
| `exp00_sobel_out.png` | 实际仿真生成的 Sobel 输出图 |
| `exp00_key_waveform.svg` | 从实际 VCD 提取的有效帧开始和处理完成关键波形 |

原始 VCD 为约 127 MB，位于忽略的 `sobel_00_rtl_sim/build/` 中，不提交到 Git。关键波形图保留
`frame_start`、`rgb_valid`、`gray_valid`、`edge_valid` 和 `video_frame_done`。其中
`video_frame_done` 是 `edge_frame_done` 经过 `video_stream_model` 寄存后的镜像。

## 结论与范围

实验 0 仓库默认 RTL 仿真通过，输入图、输出图、日志和关键波形已归档。本次只完成默认仿真，
没有更换输入图、修改 Sobel 阈值、修改 RTL，也没有开始实验 1。

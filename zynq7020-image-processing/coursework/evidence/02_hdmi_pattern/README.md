# 实验 1 HDMI 固定图远程证据

## 运行信息

- 日期：2026-06-15
- 分支：`exp/01-hdmi-pattern`
- 远程构建基线提交：`fab4bce33a8382f8620659d42599c479fa3fadb6`
- 工具：Vivado/XSim 2023.2
- 目标器件：`xc7z020clg400-2`
- 状态：远程仿真、实现和 bitstream 通过；HDMI 实机现象待现场验证

## 实际命令

```powershell
cd zynq7020-image-processing\sobel_01_hdmi_pattern
& D:\Vivado\Vivado\2023.2\bin\vivado.bat -mode batch -nojournal -nolog -source run_exp01_sim.tcl
& D:\Vivado\Vivado\2023.2\bin\vivado.bat -mode batch -nojournal -nolog -source run_exp01_bitstream.tcl
```

## 远程结果

- XSim：`HDMI pattern timing simulation passed`，`EXP01_SIM=passed`
- 有效图像：`128 x 72 = 9216` 个 RGB888 ROM 像素，输出缩放到 `1280 x 720`
- bitstream：`EXP01_BUILD=passed`，本地生成物位于忽略的
  `sobel_01_hdmi_pattern/build/vivado_2023_2/top.bit`
- 时序：WNS `7.969 ns`，TNS `0 ns`，WHS `0.070 ns`，THS `0 ns`
- 资源：205 LUT、177 FF、12 BRAM、1 MMCM、8 OSERDES
- DRC：0 error、1 warning；`ZPS7-1` 是纯 PL 设计未使用 PS7 的已知警告

## 证据文件

| 文件 | 内容 |
| --- | --- |
| `exp01_expected_pattern.png` | 从 Verilog ROM 逐像素生成的 1280x720 现场对照图 |
| `exp01_utilization.txt` | 综合后资源利用率 |
| `exp01_timing_summary.txt` | 布局布线后时序摘要 |
| `exp01_drc.txt` | bitstream 前 DRC 结果 |

## 待现场回传

- 实际测试分支和提交号
- Vivado 版本、板卡型号、JTAG 状态和测试日期
- bitstream 生成或 Program Device 的完整日志/截图
- HDMI 固定图照片，画面应与 `exp01_expected_pattern.png` 一致
- 现场资源利用率与 timing summary
- 失败时的完整错误文本和最后一个正常步骤

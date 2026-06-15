# 实验 2 HDMI Sobel 远程开发证据

## 运行信息

- 日期：2026-06-15
- 分支：`exp/02-hdmi-sobel`
- 工具：Vivado/XSim 2023.2
- 器件：`xc7z020clg400-2`
- 默认阈值：`80`
- 状态：远程仿真和构建通过，真实 HDMI 验证待现场完成

## 执行命令

```powershell
cd zynq7020-image-processing\sobel_02_hdmi_sobel
& D:\Vivado\Vivado\2023.2\bin\vivado.bat -mode batch -nojournal -nolog -source run_exp02_sim.tcl
& D:\Vivado\Vivado\2023.2\bin\vivado.bat -mode batch -nojournal -nolog -source run_exp02_bitstream.tcl
```

## 仿真结果

XSim 输出 `HDMI Sobel full-chain simulation passed` 和
`EXP02_SIM=passed`。

- 已检查灰度样本：`9216`
- 已检查 Sobel 写入：`9216`，每个地址恰好写入一次
- `edge_frame_done`：产生一次脉冲
- HDMI 时序、有效像素数、缩放地址和阈值 80 二值 RGB：全部通过

## 阈值对比

| 阈值 | 白色源像素数 |
| ---: | ---: |
| 40 | 1307 |
| 80 | 1274 |
| 120 | 1234 |

自检确认：阈值升高时，白色像素数量单调不增加。每个源像素在
`1280 x 720` 输出中显示为一个 `10 x 10` 像素块。

## 构建结果

- Synthesis、Placement、Routing 和 Bitstream 生成：通过
- WNS：`1.578 ns`
- TNS：`0.000 ns`
- WHS：`0.080 ns`
- THS：`0.000 ns`
- LUT：`2842`
- FF：`2353`
- BRAM36：`14`
- DSP：`0`
- MMCM：`1`
- OSERDES：`8`
- DRC：`0 errors`、`1 warning`

剩余的 `ZPS7-1` warning 符合预期。本实验是纯 PL HDMI 设计，未实例化
PS7。该 warning 没有阻止 Bitstream 成功生成。

Vivado 还报告了 sandbox 本地 Tcl/WebTalk 设置 warning。它们只影响用户
设置或遥测文件，不影响 Simulation、Routing、报告和 Bitstream 生成。

## 证据文件

| 文件 | 内容 |
| --- | --- |
| `exp02_edge_strength.png` | 原始 8 bit Sobel 强度图，放大至 `1280 x 720` |
| `exp02_threshold_40.png` | 阈值 40 的预期二值 HDMI 输出 |
| `exp02_threshold_80.png` | 默认阈值的现场对照图 |
| `exp02_threshold_120.png` | 阈值 120 的预期二值 HDMI 输出 |
| `exp02_threshold_stats.txt` | 白色像素统计和单调性自检结果 |
| `exp02_simulation.txt` | 精简 XSim 结果 |
| `exp02_remote_build.txt` | 精简 Implementation 和 Bitstream 结果 |
| `exp02_utilization.txt` | Vivado utilization 报告 |
| `exp02_timing_summary.txt` | Vivado timing summary |
| `exp02_drc.txt` | Vivado DRC 报告 |

生成的 `top.bit` 保存在已忽略的本地构建目录中，没有提交到 Git。

## 待现场回传的证据

- 实际测试的分支和完整提交号
- 板卡型号、Vivado 版本、显示设备型号和测试日期
- Hardware Manager 识别目标及 Program Device 的日志或截图
- 与 `exp02_threshold_80.png` 对应的 HDMI 照片
- 能确认板卡、JTAG 和 HDMI 接线的照片
- `1280 x 720` 稳定显示至少 30 秒的确认记录

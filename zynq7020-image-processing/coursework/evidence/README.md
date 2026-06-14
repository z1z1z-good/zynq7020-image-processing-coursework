# 实验证据索引

所有证据必须来自当前工作树的真实运行。大体积的原始构建目录不纳入 Git，只提交报告需要的精简日志、截图、照片和结果摘要。

| 目录 | 内容 |
| --- | --- |
| `00_environment` | 工具版本、设备状态、工程打开检查 |
| `01_rtl_sim` | 实验 0 输入图、输出图、波形和仿真日志 |
| `02_hdmi_pattern` | 实验 1 HDMI 固定图和扩展 |
| `03_hdmi_sobel` | 实验 2 Sobel 显示和扩展 |
| `04_uart_hdmi` | 实验 3 串口、PS 和 HDMI 证据 |
| `05_uart_sobel` | 实验 4 Sobel 结果和阈值对比 |
| `06_pc_control` | 实验 5 控制协议、模式和叠加 |
| `07_input_scaling_extension` | 三种缩放策略及自动测试 |
| `08_resource_timing` | Vivado 资源和时序摘要 |
| `09_final_demo` | 最终联调和演示材料 |

单次记录建议使用 Markdown，至少写明日期、分支、提交号、命令、结果和遗留问题。截图命名采用 `expNN_现象_参数.ext`，例如：

```text
exp00_wave_edge_frame_done.png
exp04_hdmi_threshold80.jpg
exp05_mode_overlay_threshold40.jpg
ext_letterbox_portrait_compare.png
```

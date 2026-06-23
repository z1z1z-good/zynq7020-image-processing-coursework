# 大拓展 03 锐化扩展 证据目录

本目录的图片为**软件参考**（`host_tool/sharpen_algo.py`，numpy），与 PL/PS 定点运算逐位一致，
已用无板协同仿真证明 `RTL == 软件 golden`，因此这些软件结果等价于 HDMI 上的硬件显示，
可直接作为 B 档「软件参考对比」的离线证据。现场上板照片/录像另行补充到本目录。

| 文件 | 内容 |
| --- | --- |
| `sharpen_original.png` | 测试图原图（128×72，最近邻放大 6×） |
| `sharpen_k0.png` | 锐化强度 k=0（应与原图一致） |
| `sharpen_k64.png` / `sharpen_k128.png` / `sharpen_k255.png` | 锐化强度 64 / 128 / 255 的结果，强度越大越锐 |
| `sharpen_side_by_side_k128.png` | 原图 \| 锐化(k=128) 并排对比 |
| `sharpen_delta_heatmap_k128.png` | 锐化增量 \|delta\| 热力图（锐化作用集中在边缘/纹理） |
| `sharpen_software_reference.txt` | 各强度改变像素数统计与定点公式 |
| `sharpen_equivalence.txt` | 交叉验证：numpy 软件预览 == 软件 golden == RTL（逐位一致） |
| `cosim_summary.txt` | 无板协同仿真关键标记（11 配置逐像素 match、真实 PS 端到端 sharpen=96、自检零回归） |
| `ooc_synth_utilization.rpt` | OOC 综合资源利用率（xc7z020clg400-2） |
| `ooc_synth_timing.rpt` | OOC 综合时序报告（74.25 MHz，WNS +2.452 ns，timing met） |

软件证据图复现：`cd host_tool && python gen_evidence.py`
无板协同仿真复现：`sobel_05_pc_control_display/tools/cosim/run_exp05_cosim.sh`
现场待补：HDMI 实拍照片/录像（锐化强度由小到大、Sobel↔锐化 切换）、最终 bitstream 资源时序报告。

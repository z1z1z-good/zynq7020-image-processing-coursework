# 无板卡软硬件协同仿真方法论

本文沉淀实验 3 建立、并供实验 4 / 实验 5 复用的「无板卡软硬件协同仿真」流程。
目标：在没有开发板时，用**真实代码**把「上位机 → PS → AXI BRAM → PL → HDMI」整条链
串起来跑仿真，提前发现协议、字节序、地址、格式和算法层面的不一致，提高一次上板成功率。

这是软硬件协同仿真，不是脑测；但它有明确边界，见下。

## 1. 能验证 / 不能验证

| 层级 | 无板卡可做 | 说明 |
| --- | --- | --- |
| 上位机图像预处理与协议打包 | 可以 | 缩放、RGB888、帧头、行头、包长度 |
| 上位机控制命令 | 可以 | 模式、阈值、叠加命令字节 |
| Python/上位机 与 RTL 联合 | 可以 | 真实字节流喂给 PS 模型 / RTL |
| PS `main.c` 逻辑 | 部分可以 | 抽离协议解析编译为主机模型（见下，不改源码） |
| BRAM/PL/HDMI 数据链 | 可以 | 行为 BRAM + RTL 渲染 + 像素比对 |
| 真实串口/JTAG/HDMI/DDR/MIO/管脚 | 不可以 | 必须有板卡和外设 |
| 完整 Vitis BSP/ELF 链接 | 不可以（本环境） | 需正常 Vitis 环境，见 `REMOTE_HARDWARE_WORKFLOW_PROMPT.md` |

**诚实纪律**：协同仿真只覆盖逻辑/协议/格式/算法层。不得据此声称真实串口、摄像头、
JTAG、HDMI 物理输出、DDR/板级或完整 Vitis 构建通过——这些必须现场。仅导入上位机
打包函数 ≠ 打开真实串口/摄像头。

## 2. 链路架构

```text
真实 camera_uart_sender 打包  ──┬─ 与本地编码器逐字节比对（证明上位机打包一致）
                               │
                               └─→ UART 字节流(文件)
                                    -> 真实 main.c receive_frame（主机编译，不改源码）
                                       -> framebuffer ── 与 golden 逐像素比对
                                                      └─ 错误注入返回码核对
                                    -> RTL testbench 载入该 framebuffer
                                       -> 全分辨率渲染并捕获 HDMI 帧
                                       -> 重建 PNG 与 golden 逐像素自动比对
```

要点：**字节流是接口**。上位机产出的真实字节由真实 PS 解析，再喂给 RTL，最后渲染成图
自动比对——而不是各层各写一份互不相干的模型。

## 3. 可复用技术（关键模式）

### 3.1 导入真实上位机打包函数（不开串口/摄像头）

`host_camera_uart/camera_uart_sender.py` 顶部 `import cv2, numpy, serial`。只需其纯打包
函数时，用 `sys.modules` 注入空桩绕过重依赖：

```python
import sys, types
sys.modules["cv2"] = types.ModuleType("cv2")
serial = types.ModuleType("serial"); serial.Serial = type("Serial", (), {})  # 注解求值需要
sys.modules["serial"] = serial
import numpy as np            # miniconda base 自带
import camera_uart_sender as host
stream = bytes(host.build_frame_packet(np_rgb_image))   # 真实打包
assert stream == local_encoder_bytes                     # 证明上位机打包一致
```

### 3.2 把真实 PS `main.c` 编译为主机模型（不改源码）

用 `#include "main.c"` 纳入未修改的源码，`-Dmain=改名` 让出 `main`，再提供 host BSP 桩：

```c
#define main ps_app_main_unused
#include "main.c"            /* receive_frame 等 static 函数进入本 TU，可被调用 */
#undef main
/* 桩：UART 从字节流文件读；Xil_Out32 写 host framebuffer 数组；
   XTime 每次大步进(+2^40)让真实超时逻辑在流耗尽时立刻返回。 */
u32 XUartPs_Recv(XUartPs*, u8 *b, u32 n){ /* 从内存字节流喂入，EOF 返回 0 */ }
void Xil_Out32(UINTPTR a, u32 v){ g_fb[(a-FRAMEBUFFER_BASEADDR)/4]=v; }
void XTime_GetTime(XTime *t){ g_xtime += ((XTime)1<<40); *t=g_xtime; }
int main(int c,char**v){ /* 读流 -> receive_frame() -> dump g_fb hex */ }
```

API 声明复用 `sobel_03_uart_hdmi/tools/ps_syntax_check/include` 的桩头；主机编译器为
Vivado/Vitis 自带 `gnu/aarch32/.../arm-none-eabi-gcc`（仅做 `-c` 源码检查）或本机
host gcc（产出可在 PC 运行的模型可执行文件）。

### 3.3 RTL 全分辨率渲染捕获 + PNG 自动比对

testbench 用行为级 BRAM（1 拍同步读，`$readmemh` 载入上一步的 framebuffer），按真实
时序输出整帧，`$fwrite` 把每个有效像素按光栅序导出；Python 重建 PNG 并与 golden
逐像素 diff（PNG 用 `struct`+`zlib` 纯标准库手写，见 `generate_exp03_expected.py`）。

### 3.4 本环境的工具调用约束

本自动化环境下 Vivado/Vitis **无法派生子进程**（`launch_simulation`/`launch_runs` 报
`Spawn failed`，XSCT 连后端超时）。因此：
- 仿真直调 `xvlog` → `xelab` → `xsim`，不用 `launch_simulation`。
- bitstream 用**非项目全局综合**（`synth_design`/`opt`/`place`/`route`/`write_bitstream`，
  BD 设 `synth_checkpoint_mode None`）。
- PS 用 host gcc / 主机模型，不依赖 Vitis 后端。
正常 Vivado/Vitis（GUI 或 PowerShell）环境不受此限，可直接用项目流程。

### 3.5 一键编排

把上述步骤封进一个脚本（`run_*_cosim.sh`），工具路径用环境变量覆盖
（`EXP03_PYTHON` / `EXP03_HOSTCC` / `EXP03_VIVADO_BIN`），中间产物写入 `build/`（已忽略）。

## 4. 实验 3 参考实现（worked example）

```text
sobel_03_uart_hdmi/tools/cosim/exp03_cosim.py       gen（真实打包+golden）/check-fb/render-compare
sobel_03_uart_hdmi/tools/cosim/ps_protocol_model.c  纳入真实 main.c 的 PS 主机模型
sobel_03_uart_hdmi/sim/hdmi_bram_display_cosim_tb.v 全分辨率渲染捕获 testbench
sobel_03_uart_hdmi/tools/cosim/run_exp03_cosim.sh   一键编排
coursework/evidence/04_uart_hdmi/exp03_cosim.txt    结果证据
```

运行（Git-Bash）：`bash sobel_03_uart_hdmi/tools/cosim/run_exp03_cosim.sh`，
通过标志为 `EXP03_COSIM_CHAIN=passed`。

## 5. 扩展到实验 4（UART 图像 → PL Sobel → HDMI）

- 在 Python 侧增加 RGB→灰度→Sobel 的**软件 golden**（算法参考 `sobel_00_rtl_sim` 与
  实验 2 的 `generate_exp02_expected.py`）。
- PS 模型不变（仍是 `receive_frame` 把原图写 BRAM）；PL 侧在显示前加 Sobel。
- co-sim testbench 捕获 **Sobel 输出帧**，与软件 golden 逐像素或按阈值二值化比对；
  阈值复用实验 2 的 `EDGE_THRESHOLD` 思路，离线对比多个阈值的白边像素数。

## 6. 扩展到实验 5（上位机控制显示）

- 控制帧 `0xA5 0x5A cmd value`：`camera_uart_sender.send_control_command` 已实现，
  按 3.1 导入真实函数生成控制字节并核对。
- PS/PL 模型增加 `mode`/`threshold`/`overlay` 控制寄存器与显示模式切换。
- 分别对 `mode=0/1/2/3`（原图/灰度/边缘/叠加）、阈值与 `overlay` 渲染并比对；
  控制字地址不得与 framebuffer 冲突。

实验 5 参考实现（worked example）：

```text
sobel_05_pc_control_display/tools/cosim/ps_protocol_model.c   纳入真实 main.c，驱动 wait_for_packet_start 分发循环（非 receive_frame），g_fb 覆盖控制字 0x9000/4/8（≥9219 word）
sobel_05_pc_control_display/tools/cosim/exp05_cosim.py        gen（真实图像打包 + 真实 send_requested_controls 控制字节核对）/ check-fb（图像区+控制字）/ render-compare（逐配置）
sobel_05_pc_control_display/tools/generate_exp05_expected.py  四模式显示 mux + gray/Sobel + 红边叠加软件 golden、预期 PNG、阈值统计
sobel_05_pc_control_display/sim/hdmi_bram_sobel_display_tb.v        缩小时序自检（时序 / sobel_done / 显示映射自洽）
sobel_05_pc_control_display/sim/hdmi_bram_sobel_display_cosim_tb.v  全分辨率渲染捕获（行为 BRAM 载图像区 + 控制字）
sobel_05_pc_control_display/tools/cosim/run_exp05_cosim.sh    一键编排
coursework/evidence/06_pc_control/exp05_cosim.txt            结果证据
```

运行（Git-Bash）：`bash sobel_05_pc_control_display/tools/cosim/run_exp05_cosim.sh`，
通过标志为 `EXP05_COSIM_CHAIN=passed`（仅逻辑层：`EXP05_COSIM_QUICK=1 bash ...`）。
与实验 3/4 的关键差异：图像帧与控制帧经**同一字节流**由 `wait_for_packet_start` 分发（实验 5
没有 `receive_frame`），行为 BRAM 与 host 模型的 framebuffer 都要覆盖到控制字 `0x9008`（字索引
9218）；软件 golden 复现四模式显示 mux + 阈值 + 红边叠加，对 `mode=0/1/2/3`、阈值 40/80/120、
`overlay=0/1` 逐像素比对。

## 7. 验收与汇报口径

- 通过仅指「协同仿真链通过」：打包/解析/格式/显示/算法层一致。
- 现场项（串口、JTAG、HDMI、DDR、Vitis ELF）单独标注「待现场」，不与仿真混为一谈。
- 证据保存到对应 `coursework/evidence/<exp>/`，并在实验 README 增加协同仿真小节。

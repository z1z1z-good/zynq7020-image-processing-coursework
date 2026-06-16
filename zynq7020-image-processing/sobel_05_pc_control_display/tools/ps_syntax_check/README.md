# PS 应用源码语法检查（实验 5）

本目录是一组**最小 Xilinx standalone BSP API 桩头**，仅用于在无法生成完整 Vitis BSP 的
无头自动化环境下，对 `../../ps_uart_control_bram_app/src/main.c` 做源码级
（语法 / 类型 / 调用签名 / 控制流）编译检查。

**这不是真实 BSP 构建。** 完整的平台 / BSP / 应用编译见
`../../build_exp05_ps_app.tcl`（在正常 Vitis 2023.2 环境运行）。

实验 5 的 PS 端在实验 3/4 接收逻辑上新增了控制帧解析（`A5 5A cmd value`）和控制字写入
（`0x9000` mode / `0x9004` threshold / `0x9008` overlay），但仍只用到 XUartPs / Xil_Io /
xtime_l 这几组 API，因此这组桩头与实验 3/4 的 `tools/ps_syntax_check/include` 内容一致；
`include/xstubs.h` 中的类型与函数声明刻意与真实 XUartPs / Xil_Io / xtime_l API 对齐，其余
6 个与真实头同名的文件只是 `#include "xstubs.h"` 的薄包装，用于满足 `main.c` 的
`#include` 指令。

## 运行

用 Vitis 2023.2 自带的 ARM 交叉编译器（单进程，不需要启动 Vitis 后端）：

```bash
ARMGCC="D:/Vivado/Vitis/2023.2/gnu/aarch32/nt/gcc-arm-none-eabi/bin/arm-none-eabi-gcc.exe"
"$ARMGCC" -c -Wall -Wextra -mcpu=cortex-a9 \
    -I include \
    ../../ps_uart_control_bram_app/src/main.c -o main.o
```

预期：退出码 0，无错误无警告，生成 `main.o`。

# PS 应用源码语法检查（实验 3）

本目录是一组**最小 Xilinx standalone BSP API 桩头**，仅用于在无法生成完整
Vitis BSP 的无头自动化环境下，对 `../../ps_uart_bram_app/src/main.c` 做
源码级（语法 / 类型 / 调用签名 / 控制流）编译检查。

**这不是真实 BSP 构建。** 完整的平台 / BSP / 应用编译见
`../../build_exp03_ps_app.tcl`（在正常 Vitis 2023.2 环境运行）。

`include/xstubs.h` 中的类型与函数声明刻意与真实
XUartPs / Xil_Io / xtime_l API 对齐；其余 6 个与真实头同名的文件只是
`#include "xstubs.h"` 的薄包装，用于满足 `main.c` 的 `#include` 指令。

## 运行

用 Vitis 2023.2 自带的 ARM 交叉编译器（单进程，不需要启动 Vitis 后端）：

```bash
ARMGCC="D:/Vivado/Vitis/2023.2/gnu/aarch32/nt/gcc-arm-none-eabi/bin/arm-none-eabi-gcc.exe"
"$ARMGCC" -c -Wall -Wextra -mcpu=cortex-a9 \
    -I include \
    ../../ps_uart_bram_app/src/main.c -o main.o
```

预期：退出码 0，无错误无警告，生成 `main.o`。
实测 arm-none-eabi-gcc 12.2.0 通过。

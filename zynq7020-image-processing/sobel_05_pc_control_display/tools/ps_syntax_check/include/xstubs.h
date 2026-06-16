#ifndef EXP03_XSTUBS_H
#define EXP03_XSTUBS_H
/*
 * 实验 3 PS 源码离线编译检查用的最小 Xilinx standalone BSP API 桩。
 *
 * 仅在本无头环境无法生成完整 Vitis BSP 时，用真实 ARM 交叉编译器对
 * ps_uart_bram_app/src/main.c 做 `-c` 语法 / 类型 / 调用签名检查。
 * 这些声明刻意与真实 XUartPs / Xil_Io / xtime_l API 对齐，但
 * 不能替代真实 BSP 链接构建（完整构建见 build_exp03_ps_app.tcl）。
 */
#include <stdarg.h>
#include <stddef.h>  /* NULL，真实 Xilinx xil_types.h 同样经此提供 */

typedef unsigned char      u8;
typedef unsigned short     u16;
typedef unsigned int       u32;
typedef unsigned long      UINTPTR;
typedef unsigned long long XTime;

#define XST_SUCCESS 0
#define XST_FAILURE 1L

#define XPAR_PS7_UART_1_DEVICE_ID            1
#define XPAR_AXI_BRAM_CTRL_0_S_AXI_BASEADDR  0x40000000U

#define COUNTS_PER_SECOND 325000000ULL

#define XUARTPS_OPER_MODE_NORMAL 0x00U

typedef struct {
    u16 DeviceId;
    u32 BaseAddress;
} XUartPs_Config;

typedef struct {
    XUartPs_Config Config;
    u32 InputClockHz;
} XUartPs;

XUartPs_Config *XUartPs_LookupConfig(u16 DeviceId);
int  XUartPs_CfgInitialize(XUartPs *InstancePtr, XUartPs_Config *ConfigPtr, u32 EffectiveAddr);
void XUartPs_SetOperMode(XUartPs *InstancePtr, u8 OperationMode);
int  XUartPs_SetBaudRate(XUartPs *InstancePtr, u32 BaudRate);
u32  XUartPs_Recv(XUartPs *InstancePtr, u8 *BufferPtr, u32 NumBytes);

void Xil_Out32(UINTPTR Addr, u32 Value);
void xil_printf(const char *ctrl1, ...);
void XTime_GetTime(XTime *Xtime_Global);

#endif /* EXP03_XSTUBS_H */

/*
 * 实验 3 PS 接收路径的主机模型（联合仿真用）。
 *
 * 通过 #include 直接纳入未修改的 ps_uart_bram_app/src/main.c（仅把它的 main()
 * 改名以便本文件自带 main 驱动），再为 main.c 调用的 Xilinx API 提供主机实现：
 *   - XUartPs_Recv 从一个 UART 字节流文件按字节喂入；
 *   - Xil_Out32   把 PS 写入捕获进主机 framebuffer 数组；
 *   - XTime       每次大幅前进，让真实超时逻辑在流耗尽时快速返回。
 * 然后调用真实的 receive_frame()，把得到的 framebuffer 以 0x00RRGGBB 32 位词
 * 导出为 hex。用于证明“真实上位机字节流 -> 真实 PS C 解析 -> 期望 framebuffer”。
 *
 * 这是无板卡软硬件协同仿真的 PS 环节，不是在真实 Zynq 上运行。
 * 用主机 gcc 编译：
 *   gcc -Dmain=ps_app_main_unused \
 *       -I <sobel_03>/tools/ps_syntax_check/include \
 *       -I <sobel_03>/ps_uart_bram_app/src \
 *       ps_protocol_model.c -o ps_protocol_model
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* 主机侧接收状态 */
static unsigned char     *g_stream = NULL;
static long               g_len = 0;
static long               g_pos = 0;
static unsigned int       g_fb[128 * 72];
static unsigned long long g_xtime = 0ULL;

/* 纳入真实 PS 源码（不修改），把它的 main() 改名避免与本文件冲突。 */
#define main ps_app_main_unused
#include "main.c"
#undef main

/* main.c 调用的 Xilinx API 的主机实现（声明来自 ps_syntax_check 桩头）。 */
XUartPs_Config *XUartPs_LookupConfig(u16 DeviceId)
{
    (void)DeviceId;
    static XUartPs_Config cfg;
    cfg.DeviceId = 0;
    cfg.BaseAddress = (u32)FRAMEBUFFER_BASEADDR;
    return &cfg;
}

int XUartPs_CfgInitialize(XUartPs *InstancePtr, XUartPs_Config *ConfigPtr, u32 EffectiveAddr)
{
    (void)InstancePtr; (void)ConfigPtr; (void)EffectiveAddr;
    return XST_SUCCESS;
}

void XUartPs_SetOperMode(XUartPs *InstancePtr, u8 OperationMode)
{
    (void)InstancePtr; (void)OperationMode;
}

int XUartPs_SetBaudRate(XUartPs *InstancePtr, u32 BaudRate)
{
    (void)InstancePtr; (void)BaudRate;
    return XST_SUCCESS;
}

/* 从字节流文件按需喂入；流耗尽返回 0，触发 main.c 的超时返回路径。 */
u32 XUartPs_Recv(XUartPs *InstancePtr, u8 *BufferPtr, u32 NumBytes)
{
    (void)InstancePtr;
    u32 got = 0;
    while (got < NumBytes && g_pos < g_len) {
        BufferPtr[got++] = g_stream[g_pos++];
    }
    return got;
}

/* 捕获 PS 对 framebuffer 的 32 位写入。 */
void Xil_Out32(UINTPTR Addr, u32 Value)
{
    unsigned long idx = ((unsigned long)Addr - (unsigned long)FRAMEBUFFER_BASEADDR) / 4UL;
    if (idx < (unsigned long)(128 * 72)) {
        g_fb[idx] = Value;
    }
}

/* 每次大幅前进，使流耗尽时 (now-start) 立刻超过任何 timeout_ticks。 */
void XTime_GetTime(XTime *Xtime_Global)
{
    g_xtime += ((XTime)1 << 40);
    *Xtime_Global = g_xtime;
}

void xil_printf(const char *ctrl1, ...)
{
    (void)ctrl1;
}

int main(int argc, char **argv)
{
    if (argc < 3) {
        fprintf(stderr, "usage: %s <stream.bin> <fb_out.hex>\n", argv[0]);
        return 2;
    }

    FILE *fin = fopen(argv[1], "rb");
    if (!fin) { perror("open stream"); return 2; }
    fseek(fin, 0, SEEK_END);
    g_len = ftell(fin);
    fseek(fin, 0, SEEK_SET);
    g_stream = (unsigned char *)malloc(g_len > 0 ? (size_t)g_len : 1);
    if (!g_stream) { fclose(fin); return 2; }
    if (g_len > 0 && fread(g_stream, 1, (size_t)g_len, fin) != (size_t)g_len) {
        fclose(fin); free(g_stream); return 2;
    }
    fclose(fin);
    g_pos = 0;
    memset(g_fb, 0, sizeof(g_fb));

    /* 运行真实的 PS 帧接收。 */
    int code = receive_frame();

    FILE *fout = fopen(argv[2], "w");
    if (!fout) { perror("open out"); free(g_stream); return 2; }
    for (int i = 0; i < 128 * 72; i++) {
        fprintf(fout, "%08x\n", g_fb[i]);
    }
    fclose(fout);
    free(g_stream);

    printf("PS_MODEL_CODE=%d\n", code);
    return 0;
}

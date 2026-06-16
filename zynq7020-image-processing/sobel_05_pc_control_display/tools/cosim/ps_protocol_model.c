/*
 * 实验 5 PS 接收+控制路径的主机模型（无板卡协同仿真用）。
 *
 * 通过 #include 直接纳入未修改的 ps_uart_control_bram_app/src/main.c（仅把它的 main()
 * 改名，让本文件自带的 main 驱动），再为 main.c 调用的 Xilinx API 提供主机实现：
 *   - XUartPs_Recv 从一个 UART 字节流文件按字节喂入（流耗尽返回 0，触发真实超时路径）；
 *   - Xil_Out32   把 PS 写入捕获进主机 framebuffer 数组（含图像区与控制字区）；
 *   - XTime       每次大幅前进，让真实超时逻辑在流耗尽时立刻返回。
 *
 * 与实验 4 不同：实验 5 的 main.c 没有 receive_frame()，而是用 wait_for_packet_start()
 * 做 55AA 图像帧 / A55A 控制帧的 2 字节同步分发。本模型据此驱动真实的分发循环：
 *   while ((kind = wait_for_packet_start(UART_WAIT_MS)) != 0)
 *       kind==1 -> receive_frame_body()，kind==2 -> handle_control_packet()
 * 然后把 framebuffer（图像区 0..9215 + 控制字 0x9000/0x9004/0x9008 即字索引 9216/9217/9218）
 * 以 0x00RRGGBB / 控制值 32 位词导出为 hex，证明
 * “真实上位机字节流 -> 真实 PS C 解析 -> 期望图像区 + 期望控制字”。
 *
 * 这是无板卡软硬件协同仿真的 PS 环节，不是在真实 Zynq 上运行。
 * 用主机 gcc 编译：
 *   gcc -Wall -Dmain=ps_app_main_unused \
 *       -I <sobel_05>/tools/ps_syntax_check/include \
 *       -I <sobel_05>/ps_uart_control_bram_app/src \
 *       ps_protocol_model.c -o ps_protocol_model
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* framebuffer 词数：图像区 128*72=9216 + 控制字到 0x9008（字索引 9218）-> 9219 个词。 */
#define FB_IMG_WORDS (128 * 72)
#define FB_WORDS     ((0x9008 / 4) + 1)   /* 9219 */

/* 主机侧接收状态 */
static unsigned char     *g_stream = NULL;
static long               g_len = 0;
static long               g_pos = 0;
static unsigned int       g_fb[FB_WORDS];
static unsigned long long g_xtime = 0ULL;

/* 纳入真实 PS 源码（不修改），把它的 main() 改名避免与本文件冲突。
 * 命令行 -Dmain=ps_app_main_unused 同样改名；此处 #undef 让其后的本文件 main 保持原名。 */
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

/* 捕获 PS 对 framebuffer 与控制字的 32 位写入。 */
void Xil_Out32(UINTPTR Addr, u32 Value)
{
    unsigned long idx = ((unsigned long)Addr - (unsigned long)FRAMEBUFFER_BASEADDR) / 4UL;
    if (idx < (unsigned long)FB_WORDS) {
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

    /* 镜像 PS 上电：framebuffer 清零，控制字写默认值（mode=2/threshold=80/overlay=0）。 */
    memset(g_fb, 0, sizeof(g_fb));
    control_write_defaults();

    /* 驱动真实 PS 分发循环，直到字节流耗尽（wait_for_packet_start 超时返回 0）。 */
    int kind;
    int frames = 0;
    int ctrls = 0;
    int last_frame_code = 0;
    int last_ctrl_code = 0;
    while ((kind = wait_for_packet_start(UART_WAIT_MS)) != 0) {
        if (kind == 1) {
            last_frame_code = receive_frame_body();
            printf("PKT frame code=%d\n", last_frame_code);
            frames++;
        } else if (kind == 2) {
            last_ctrl_code = handle_control_packet();
            printf("PKT ctrl code=%d\n", last_ctrl_code);
            ctrls++;
        }
    }

    FILE *fout = fopen(argv[2], "w");
    if (!fout) { perror("open out"); free(g_stream); return 2; }
    for (int i = 0; i < FB_WORDS; i++) {
        fprintf(fout, "%08x\n", g_fb[i]);
    }
    fclose(fout);
    free(g_stream);

    printf("PS_MODEL_DONE frames=%d ctrls=%d last_frame=%d last_ctrl=%d\n",
           frames, ctrls, last_frame_code, last_ctrl_code);
    printf("PS_MODEL_CTRL mode=%u threshold=%u overlay=%u\n",
           g_fb[0x9000 / 4], g_fb[0x9004 / 4], g_fb[0x9008 / 4]);
    return 0;
}

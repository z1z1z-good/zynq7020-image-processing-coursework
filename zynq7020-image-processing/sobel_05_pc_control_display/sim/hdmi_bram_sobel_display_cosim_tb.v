`timescale 1ns/1ps

// 实验 5 联合仿真 testbench（全分辨率渲染捕获）。
// 行为级 BRAM 载入 fb_in.hex：图像区 0..9215（真实 PS 解析出的原始 RGB）+ 控制字
// 0x9000/0x9004/0x9008（字索引 9216/9217/9218 = display_mode / threshold / overlay）。
// 驱动 hdmi_bram_sobel_display 以默认 1280x720 时序、10x 放大渲染：PL 每帧先读 3 个控制字
// （SCAN_CTRL_*），再扫 128x72 做 gray + Sobel，并按 display_mode/threshold/overlay 选择
// 原图 / 灰度 / 二值边缘 / 原图+红色边缘 输出。testbench 把第一整帧有效像素按光栅序捕获到
// hdmi_capture.hex，交给 exp05_cosim.py render-compare 重建 PNG 并与软件 golden 逐像素比对。
//
// 全分辨率下扫描（9 个控制读 + 9216 扫描 + 约 200 flush ≈ 9.4k 拍）在有效区起点（第 30 行，
// 约 49.5k 拍）之前远早完成，故第一帧有效区 sobel_done 已置位、输出有效，捕获第一帧即可。
module hdmi_bram_sobel_display_cosim_tb;

localparam H_ACTIVE = 1280;
localparam H_FP = 110;
localparam H_SYNC = 40;
localparam H_BP = 220;
localparam V_ACTIVE = 720;
localparam V_FP = 5;
localparam V_SYNC = 5;
localparam V_BP = 20;
localparam H_TOTAL = H_ACTIVE + H_FP + H_SYNC + H_BP;
localparam V_TOTAL = V_ACTIVE + V_FP + V_SYNC + V_BP;
localparam FB_DEPTH = 16384;   // 真实 BRAM 深度（64KB / 4），覆盖图像区与控制字

reg clk = 1'b0;
reg rst = 1'b1;
wire hs;
wire vs;
wire de;
wire [7:0] rgb_r;
wire [7:0] rgb_g;
wire [7:0] rgb_b;

wire bram_en;
wire [3:0] bram_we;
wire [31:0] bram_addr;
wire [31:0] bram_din;
reg [31:0] bram_dout;

reg [31:0] fb_mem [0:FB_DEPTH-1];

integer frame_count = 0;
integer captured = 0;
integer cap_file = 0;
reg capturing = 1'b0;
reg previous_vs = 1'b0;
reg test_done = 1'b0;
reg test_passed = 1'b0;

always #5 clk = ~clk;

initial begin
    $readmemh("fb_in.hex", fb_mem);
end

// 端口 B 同步读：字节地址右移 2 位转字地址，单拍延迟（与 AXI BRAM / blk_mem 一致）。
always @(posedge clk) begin
    bram_dout <= fb_mem[bram_addr[15:2]];
end

// 默认参数（与综合一致：1280x720、10x）；display_mode/threshold/overlay 来自 BRAM 控制字。
hdmi_bram_sobel_display dut (
    .clk(clk),
    .rst(rst),
    .hs(hs),
    .vs(vs),
    .de(de),
    .rgb_r(rgb_r),
    .rgb_g(rgb_g),
    .rgb_b(rgb_b),
    .bram_en(bram_en),
    .bram_we(bram_we),
    .bram_addr(bram_addr),
    .bram_din(bram_din),
    .bram_dout(bram_dout)
);

always @(posedge clk) begin
    previous_vs <= vs;

    if (!rst && vs && !previous_vs) begin
        frame_count = frame_count + 1;
        if (frame_count == 1) begin
            cap_file = $fopen("hdmi_capture.hex", "w");
            capturing = 1'b1;
            captured = 0;
        end else if (frame_count == 2) begin
            capturing = 1'b0;
            $fclose(cap_file);
            if (captured == H_ACTIVE * V_ACTIVE) begin
                $display("EXP05_COSIM_CAPTURE=ok pixels=%0d", captured);
                test_passed = 1'b1;
            end else begin
                $display("EXP05_COSIM_CAPTURE=bad pixels=%0d expected=%0d",
                         captured, H_ACTIVE * V_ACTIVE);
            end
            test_done = 1'b1;
            $finish;
        end
    end

    if (capturing && de) begin
        $fwrite(cap_file, "%02x%02x%02x\n", rgb_r, rgb_g, rgb_b);
        captured = captured + 1;
    end
end

initial begin
    repeat (8) @(posedge clk);
    rst = 1'b0;

    repeat (H_TOTAL * V_TOTAL * 3) @(posedge clk);
    $display("Timeout waiting for two HDMI frames");
    test_done = 1'b1;
    $finish;
end

endmodule

`timescale 1ns/1ps

// 实验 3 联合仿真 testbench（全分辨率渲染捕获）。
// 行为 BRAM 载入由真实 PS 主机模型产出的 fb_from_ps.hex（即真实上位机字节流经真实
// main.c receive_frame 写出的 framebuffer），驱动 hdmi_bram_display 以默认 1280x720
// 时序、10x 放大和默认蓝色边框输出，并把一整帧有效像素按光栅顺序捕获到
// hdmi_capture.hex，交给 exp03_cosim.py render-compare 重建 PNG 并与 golden 比对。
module hdmi_bram_display_cosim_tb;

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
localparam IMG_PIXELS = 128 * 72;

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

reg [31:0] fb_mem [0:IMG_PIXELS-1];

integer frame_count = 0;
integer captured = 0;
integer cap_file = 0;
reg capturing = 1'b0;
reg previous_vs = 1'b0;
reg test_done = 1'b0;
reg test_passed = 1'b0;

always #5 clk = ~clk;

initial begin
    $readmemh("fb_from_ps.hex", fb_mem);
end

// 端口 B 同步读：字节地址右移 2 位转字地址，单拍延迟。
always @(posedge clk) begin
    bram_dout <= fb_mem[bram_addr[15:2]];
end

// 默认参数（与综合一致：1280x720、10x、BORDER_WIDTH=20、BORDER_COLOR=24'h0066ff）。
hdmi_bram_display dut (
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
                $display("EXP03_COSIM_CAPTURE=ok pixels=%0d", captured);
                test_passed = 1'b1;
            end else begin
                $display("EXP03_COSIM_CAPTURE=bad pixels=%0d expected=%0d",
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

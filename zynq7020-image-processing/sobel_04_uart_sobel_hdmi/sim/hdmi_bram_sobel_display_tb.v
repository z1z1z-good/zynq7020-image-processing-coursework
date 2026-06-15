`timescale 1ns/1ps

// 实验 4 PL Sobel 彩色边缘显示自检 testbench。
// 行为级 BRAM 载入 fb_from_ps.hex（真实 PS 解析出的原始 RGB framebuffer），驱动
// hdmi_bram_sobel_display 完成 BRAM 扫描 -> rgb_to_gray -> sobel_core -> edge_mem ->
// 彩色边缘显示，并校验：
//   1. HDMI 有效像素数、HS/VS 脉宽；
//   2. sobel_done 最终置 1；
//   3. 显示映射：de 有效时 RGB 仅为 EDGE_COLOR（edge_pixel>=EDGE_THRESHOLD）或全黑，
//      且与 dut 内部 edge_pixel / sobel_done 完全一致；
//   4. 至少出现若干彩色边缘像素（边缘确实被检测到）。
// 缩小时序（256x144、放大 2x2）以加快仿真：128x72 扫描与 Sobel 不受显示时序影响。
// 由于缩小时序下扫描完成（约 35 行）晚于有效区起点（第 6 行），第一帧上半部 sobel_done
// 尚未置位，因此自检统计第二整帧（此时 sobel_done 已置位、edge_mem 已写满，静态图像下
// 扫描重写与显示读取数值一致）。
module hdmi_bram_sobel_display_tb;

localparam H_ACTIVE = 256;
localparam H_FP = 2;
localparam H_SYNC = 4;
localparam H_BP = 3;
localparam V_ACTIVE = 144;
localparam V_FP = 2;
localparam V_SYNC = 2;
localparam V_BP = 2;
localparam H_TOTAL = H_ACTIVE + H_FP + H_SYNC + H_BP;
localparam V_TOTAL = V_ACTIVE + V_FP + V_SYNC + V_BP;
localparam IMG_PIXELS = 128 * 72;
localparam [7:0]  EDGE_THRESHOLD = 8'd80;
localparam [23:0] EDGE_COLOR     = 24'h00ff00;

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
integer active_pixels = 0;
integer hs_cycles = 0;
integer vs_cycles = 0;
integer green_pixels = 0;
integer errors = 0;
reg [23:0] expected_color = 24'd0;
reg counting = 1'b0;
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

hdmi_bram_sobel_display #(
    .H_ACTIVE(H_ACTIVE),
    .H_FP(H_FP),
    .H_SYNC(H_SYNC),
    .H_BP(H_BP),
    .V_ACTIVE(V_ACTIVE),
    .V_FP(V_FP),
    .V_SYNC(V_SYNC),
    .V_BP(V_BP),
    .EDGE_THRESHOLD(EDGE_THRESHOLD),
    .EDGE_COLOR(EDGE_COLOR)
) dut (
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
        if (frame_count == 2) begin
            // 统计第二整帧（sobel_done 已置位、edge_mem 已写满）。
            counting = 1'b1;
            active_pixels = 0;
            hs_cycles = 0;
            vs_cycles = 0;
            green_pixels = 0;
        end else if (frame_count == 3) begin
            counting = 1'b0;

            if (active_pixels != H_ACTIVE * V_ACTIVE) begin
                $display("ERROR: active pixel count %0d, expected %0d",
                         active_pixels, H_ACTIVE * V_ACTIVE);
                errors = errors + 1;
            end
            if (hs_cycles != H_SYNC * V_TOTAL) begin
                $display("ERROR: HS count %0d, expected %0d",
                         hs_cycles, H_SYNC * V_TOTAL);
                errors = errors + 1;
            end
            if (vs_cycles != V_SYNC * H_TOTAL) begin
                $display("ERROR: VS count %0d, expected %0d",
                         vs_cycles, V_SYNC * H_TOTAL);
                errors = errors + 1;
            end
            if (!dut.sobel_done) begin
                $display("ERROR: sobel_done not set during display frame");
                errors = errors + 1;
            end
            if (green_pixels == 0) begin
                $display("ERROR: no colored edge pixels detected");
                errors = errors + 1;
            end

            if (errors == 0) begin
                $display("EXP04_SELFCHECK_TB=passed active=%0d green=%0d",
                         active_pixels, green_pixels);
                test_passed = 1'b1;
            end else begin
                $display("EXP04_SELFCHECK_TB=failed errors=%0d", errors);
            end
            test_done = 1'b1;
            $finish;
        end
    end

    if (counting) begin
        if (hs)
            hs_cycles = hs_cycles + 1;
        if (vs)
            vs_cycles = vs_cycles + 1;
        if (de) begin
            // 与 dut 内部状态一致的期望颜色（彩色边缘显示映射）。
            expected_color = (dut.sobel_done && (dut.edge_pixel >= EDGE_THRESHOLD))
                             ? EDGE_COLOR : 24'h000000;
            if ({rgb_r, rgb_g, rgb_b} !== expected_color) begin
                if (errors < 10) begin
                    $display("ERROR: pixel %0d rgb=%h expected %h (edge=%0d sobel_done=%b)",
                             active_pixels, {rgb_r, rgb_g, rgb_b}, expected_color,
                             dut.edge_pixel, dut.sobel_done);
                end
                errors = errors + 1;
            end
            if ({rgb_r, rgb_g, rgb_b} === EDGE_COLOR)
                green_pixels = green_pixels + 1;
            active_pixels = active_pixels + 1;
        end
    end
end

initial begin
    repeat (4) @(posedge clk);
    rst = 1'b0;

    repeat (H_TOTAL * V_TOTAL * 5) @(posedge clk);
    $display("Timeout waiting for three HDMI timing frames");
    test_done = 1'b1;
    $finish;
end

endmodule

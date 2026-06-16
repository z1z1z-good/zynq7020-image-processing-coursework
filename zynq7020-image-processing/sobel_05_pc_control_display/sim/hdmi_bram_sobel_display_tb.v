`timescale 1ns/1ps

// 实验 5 PL 显示控制自检 testbench（缩小时序，加快仿真）。
// 行为级 BRAM 载入 fb_in.hex（图像区 + 控制字）。驱动 hdmi_bram_sobel_display 完成
//   每帧读控制字(SCAN_CTRL_*) -> 扫描 BRAM -> rgb_to_gray -> sobel_core -> edge_mem
//   -> 按 display_mode/threshold/overlay 选择显示。
// 校验：
//   1. HDMI 有效像素数、HS/VS 脉宽计数；
//   2. sobel_done 在统计帧内确实置位（saw_sobel_done）；
//   3. 显示映射自洽：de 有效时 {rgb_r,rgb_g,rgb_b} 与“依 dut 内部 display_mode/threshold/
//      overlay_enable/rgb_pixel/edge_pixel/sobel_done 复算的 4 模式 mux + 输出门控”逐拍一致；
//   4. 至少出现若干红色叠加像素（overlay 配置下边缘确实被标红）。
// 缩小时序（256x144、2x）下扫描完成（约 36 行）晚于有效区起点（第 6 行），第一帧上半部
// sobel_done 未置位、输出被门控为 0；自检按 dut.sobel_done 复算期望，故全帧自洽。统计第二
// 整帧（此时下半部 sobel_done 已置位、edge_mem 写满，能观察到非黑输出）。逐像素 golden 比对
// 由 cosim testbench + exp05_cosim.py render-compare 在全分辨率下完成。
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
localparam FB_DEPTH = 16384;
localparam [23:0] OVERLAY_COLOR = 24'hff2020;

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
integer active_pixels = 0;
integer hs_cycles = 0;
integer vs_cycles = 0;
integer red_pixels = 0;
integer errors = 0;
reg counting = 1'b0;
reg saw_sobel_done = 1'b0;
reg previous_vs = 1'b0;
reg test_done = 1'b0;
reg test_passed = 1'b0;

// 依 dut 内部状态复算的期望颜色（与 hdmi_bram_sobel_display.v 显示 mux 一致）。
reg [15:0] sg_sum;
reg [7:0]  sg;
reg        edge_on_e;
reg        ov_active;
reg [23:0] base_c;
reg [23:0] exp_c;

always #5 clk = ~clk;

initial begin
    $readmemh("fb_in.hex", fb_mem);
end

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
    .V_BP(V_BP)
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
            counting = 1'b1;
            active_pixels = 0;
            hs_cycles = 0;
            vs_cycles = 0;
            red_pixels = 0;
            saw_sobel_done = 1'b0;
        end else if (frame_count == 3) begin
            counting = 1'b0;

            if (active_pixels != H_ACTIVE * V_ACTIVE) begin
                $display("ERROR: active pixel count %0d, expected %0d",
                         active_pixels, H_ACTIVE * V_ACTIVE);
                errors = errors + 1;
            end
            if (hs_cycles != H_SYNC * V_TOTAL) begin
                $display("ERROR: HS count %0d, expected %0d", hs_cycles, H_SYNC * V_TOTAL);
                errors = errors + 1;
            end
            if (vs_cycles != V_SYNC * H_TOTAL) begin
                $display("ERROR: VS count %0d, expected %0d", vs_cycles, V_SYNC * H_TOTAL);
                errors = errors + 1;
            end
            if (!saw_sobel_done) begin
                $display("ERROR: sobel_done never set during display frame");
                errors = errors + 1;
            end
            if (red_pixels == 0) begin
                $display("ERROR: no colored overlay pixels detected");
                errors = errors + 1;
            end

            if (errors == 0) begin
                $display("EXP05_SELFCHECK_TB=passed active=%0d red=%0d", active_pixels, red_pixels);
                test_passed = 1'b1;
            end else begin
                $display("EXP05_SELFCHECK_TB=failed errors=%0d", errors);
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
        if (dut.sobel_done)
            saw_sobel_done = 1'b1;
        if (de) begin
            // 复算 4 模式显示 mux（与 dut 当前锁存的控制字一致），并按 sobel_done 做输出门控。
            sg_sum = dut.rgb_pixel[23:16] * 16'd77
                   + dut.rgb_pixel[15:8]  * 16'd150
                   + dut.rgb_pixel[7:0]   * 16'd29;
            sg = sg_sum[15:8];
            edge_on_e = (dut.edge_pixel >= dut.threshold);
            ov_active = dut.overlay_enable | (dut.display_mode == 2'd3);
            case (dut.display_mode)
                2'd1: base_c = {sg, sg, sg};
                2'd2: base_c = edge_on_e ? 24'hffffff : 24'h000000;
                default: base_c = dut.rgb_pixel;
            endcase
            if ((dut.display_mode != 2'd2) && ov_active && edge_on_e)
                exp_c = OVERLAY_COLOR;
            else
                exp_c = base_c;
            if (!dut.sobel_done)
                exp_c = 24'h000000;

            if ({rgb_r, rgb_g, rgb_b} !== exp_c) begin
                if (errors < 10) begin
                    $display("ERROR: pixel %0d rgb=%h expected %h (mode=%0d thr=%0d ovl=%b edge=%0d sd=%b)",
                             active_pixels, {rgb_r, rgb_g, rgb_b}, exp_c,
                             dut.display_mode, dut.threshold, dut.overlay_enable,
                             dut.edge_pixel, dut.sobel_done);
                end
                errors = errors + 1;
            end
            if ({rgb_r, rgb_g, rgb_b} === OVERLAY_COLOR)
                red_pixels = red_pixels + 1;
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

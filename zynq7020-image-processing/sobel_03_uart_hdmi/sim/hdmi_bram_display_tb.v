`timescale 1ns/1ps

// 实验 3 PL 显示链路仿真：用行为级 BRAM 模型驱动 hdmi_bram_display，
// 校验 HDMI 时序、10x 放大地址、读延迟流水线对齐以及图像边框扩展。
// 缩小时序（256x144，放大 2x2）以加快仿真，逻辑与 exp1 hdmi_image_display_tb 同构。
module hdmi_bram_display_tb;

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
localparam BORDER_WIDTH = 2;
localparam [23:0] BORDER_COLOR = 24'h0066ff;
localparam SCALE_X = H_ACTIVE / 128;
localparam SCALE_Y = V_ACTIVE / 72;
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

// 行为级 framebuffer：1 拍同步读，模拟 blk_mem_gen READ_FIRST 端口 B。
reg [31:0] fb_mem [0:IMG_PIXELS-1];

integer frame_count = 0;
integer active_pixels = 0;
integer hs_cycles = 0;
integer vs_cycles = 0;
integer errors = 0;
integer border_pixels = 0;
integer output_x = 0;
integer output_y = 0;
integer expected_addr = 0;
reg [23:0] expected_rgb = 24'd0;
reg counting = 1'b0;
reg previous_vs = 1'b0;
reg test_done = 1'b0;
reg test_passed = 1'b0;

always #5 clk = ~clk;

initial begin
    $readmemh("expected_frame.hex", fb_mem);
end

// 端口 B 同步读：字节地址右移 2 位转字地址，单拍延迟。
always @(posedge clk) begin
    bram_dout <= fb_mem[bram_addr[15:2]];
end

hdmi_bram_display #(
    .H_ACTIVE(H_ACTIVE),
    .H_FP(H_FP),
    .H_SYNC(H_SYNC),
    .H_BP(H_BP),
    .V_ACTIVE(V_ACTIVE),
    .V_FP(V_FP),
    .V_SYNC(V_SYNC),
    .V_BP(V_BP),
    .BORDER_WIDTH(BORDER_WIDTH),
    .BORDER_COLOR(BORDER_COLOR)
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
        if (frame_count == 1) begin
            counting = 1'b1;
            active_pixels = 0;
            hs_cycles = 0;
            vs_cycles = 0;
            border_pixels = 0;
        end else if (frame_count == 2) begin
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
            if (border_pixels !=
                (H_ACTIVE * V_ACTIVE -
                 (H_ACTIVE - 2 * BORDER_WIDTH) *
                 (V_ACTIVE - 2 * BORDER_WIDTH))) begin
                $display("ERROR: border pixel count %0d is incorrect", border_pixels);
                errors = errors + 1;
            end

            if (errors == 0) begin
                $display("HDMI BRAM display simulation passed");
                test_passed = 1'b1;
                test_done = 1'b1;
                $finish;
            end else begin
                $display("HDMI BRAM display simulation failed with %0d errors", errors);
                test_done = 1'b1;
                $finish;
            end
        end
    end

    if (counting) begin
        if (hs)
            hs_cycles = hs_cycles + 1;
        if (vs)
            vs_cycles = vs_cycles + 1;
        if (de) begin
            output_x = active_pixels % H_ACTIVE;
            output_y = active_pixels / H_ACTIVE;
            expected_addr = (output_y / SCALE_Y) * 128 + (output_x / SCALE_X);
            expected_rgb = fb_mem[expected_addr][23:0];

            if ((output_x < BORDER_WIDTH) ||
                (output_x >= H_ACTIVE - BORDER_WIDTH) ||
                (output_y < BORDER_WIDTH) ||
                (output_y >= V_ACTIVE - BORDER_WIDTH)) begin
                if ({rgb_r, rgb_g, rgb_b} !== BORDER_COLOR) begin
                    $display("ERROR: border pixel %0d is %h, expected %h",
                             active_pixels, {rgb_r, rgb_g, rgb_b}, BORDER_COLOR);
                    errors = errors + 1;
                end
                border_pixels = border_pixels + 1;
            end else if ({rgb_r, rgb_g, rgb_b} !== expected_rgb) begin
                $display("ERROR: pixel %0d is %h, expected %h",
                         active_pixels, {rgb_r, rgb_g, rgb_b}, expected_rgb);
                errors = errors + 1;
            end
            active_pixels = active_pixels + 1;
        end
    end
end

initial begin
    repeat (4) @(posedge clk);
    rst = 1'b0;

    repeat (H_TOTAL * V_TOTAL * 3) @(posedge clk);
    $display("Timeout waiting for two HDMI timing frames");
    test_done = 1'b1;
    $finish;
end

endmodule

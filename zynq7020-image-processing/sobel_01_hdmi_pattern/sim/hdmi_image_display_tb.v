`timescale 1ns/1ps

module hdmi_image_display_tb;

localparam H_ACTIVE = 128;
localparam H_FP = 2;
localparam H_SYNC = 4;
localparam H_BP = 3;
localparam V_ACTIVE = 72;
localparam V_FP = 2;
localparam V_SYNC = 2;
localparam V_BP = 2;
localparam H_TOTAL = H_ACTIVE + H_FP + H_SYNC + H_BP;
localparam V_TOTAL = V_ACTIVE + V_FP + V_SYNC + V_BP;

reg clk = 1'b0;
reg rst = 1'b1;
wire hs;
wire vs;
wire de;
wire [7:0] rgb_r;
wire [7:0] rgb_g;
wire [7:0] rgb_b;

integer frame_count = 0;
integer active_pixels = 0;
integer hs_cycles = 0;
integer vs_cycles = 0;
integer errors = 0;
reg counting = 1'b0;
reg previous_vs = 1'b0;
reg test_done = 1'b0;
reg test_passed = 1'b0;

always #5 clk = ~clk;

hdmi_image_display #(
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
    .rgb_b(rgb_b)
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

            if (errors == 0) begin
                $display("HDMI pattern timing simulation passed");
                test_passed = 1'b1;
                test_done = 1'b1;
                $finish;
            end else begin
                $display("HDMI pattern timing simulation failed with %0d errors", errors);
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
            if ({rgb_r, rgb_g, rgb_b} !==
                dut.u_image_rom_128x72.image_mem[active_pixels]) begin
                $display("ERROR: pixel %0d is %h, expected %h",
                         active_pixels, {rgb_r, rgb_g, rgb_b},
                         dut.u_image_rom_128x72.image_mem[active_pixels]);
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

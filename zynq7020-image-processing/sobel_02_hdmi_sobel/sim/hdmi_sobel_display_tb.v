`timescale 1ns/1ps

module hdmi_sobel_display_tb;

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
localparam SCALE_X = H_ACTIVE / 128;
localparam SCALE_Y = V_ACTIVE / 72;
localparam [7:0] EDGE_THRESHOLD = 8'd80;

reg clk = 1'b0;
reg rst = 1'b1;
wire hs;
wire vs;
wire de;
wire [7:0] rgb_r;
wire [7:0] rgb_g;
wire [7:0] rgb_b;

reg [7:0] expected_edge [0:9215];
integer write_count [0:9215];
integer gray_samples = 0;
integer edge_writes = 0;
integer done_pulses = 0;
integer active_pixels = 0;
integer hs_cycles = 0;
integer vs_cycles = 0;
integer white_pixels = 0;
integer errors = 0;
integer frame_count = 0;
integer output_x = 0;
integer output_y = 0;
integer expected_addr = 0;
integer expected_gray = 0;
integer index = 0;
reg counting = 1'b0;
reg previous_vs = 1'b0;
reg processing_checked = 1'b0;
reg test_done = 1'b0;
reg test_passed = 1'b0;

always #5 clk = ~clk;

hdmi_sobel_display #(
    .H_ACTIVE(H_ACTIVE),
    .H_FP(H_FP),
    .H_SYNC(H_SYNC),
    .H_BP(H_BP),
    .V_ACTIVE(V_ACTIVE),
    .V_FP(V_FP),
    .V_SYNC(V_SYNC),
    .V_BP(V_BP),
    .EDGE_THRESHOLD(EDGE_THRESHOLD)
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
    if (!rst && dut.gray_valid) begin
        expected_addr = dut.gray_y * 128 + dut.gray_x;
        expected_gray =
            ((dut.u_image_rom_128x72.image_mem[expected_addr][23:16] * 77) +
             (dut.u_image_rom_128x72.image_mem[expected_addr][15:8] * 150) +
             (dut.u_image_rom_128x72.image_mem[expected_addr][7:0] * 29)) >> 8;
        if (dut.gray !== expected_gray[7:0]) begin
            $display("ERROR: gray (%0d,%0d)=%0d expected=%0d",
                     dut.gray_x, dut.gray_y, dut.gray, expected_gray);
            errors = errors + 1;
        end
        gray_samples = gray_samples + 1;
    end

    if (!rst && dut.edge_valid) begin
        if ((dut.edge_x >= 128) || (dut.edge_y >= 72)) begin
            $display("ERROR: edge coordinate out of range (%0d,%0d)",
                     dut.edge_x, dut.edge_y);
            errors = errors + 1;
        end else begin
            expected_addr = dut.edge_y * 128 + dut.edge_x;
            write_count[expected_addr] = write_count[expected_addr] + 1;
            if (dut.edge_data !== expected_edge[expected_addr]) begin
                $display("ERROR: edge (%0d,%0d)=%0d expected=%0d",
                         dut.edge_x, dut.edge_y, dut.edge_data,
                         expected_edge[expected_addr]);
                errors = errors + 1;
            end
            edge_writes = edge_writes + 1;
        end
    end

    if (!rst && dut.edge_frame_done)
        done_pulses = done_pulses + 1;
end

always @(posedge clk) begin
    previous_vs <= vs;

    if (!rst && processing_checked && vs && !previous_vs) begin
        frame_count = frame_count + 1;
        if (frame_count == 1) begin
            counting = 1'b1;
            active_pixels = 0;
            hs_cycles = 0;
            vs_cycles = 0;
            white_pixels = 0;
        end else if (frame_count == 2) begin
            counting = 1'b0;
            if (active_pixels != H_ACTIVE * V_ACTIVE) begin
                $display("ERROR: active pixel count %0d expected %0d",
                         active_pixels, H_ACTIVE * V_ACTIVE);
                errors = errors + 1;
            end
            if (hs_cycles != H_SYNC * V_TOTAL) begin
                $display("ERROR: HS count %0d expected %0d",
                         hs_cycles, H_SYNC * V_TOTAL);
                errors = errors + 1;
            end
            if (vs_cycles != V_SYNC * H_TOTAL) begin
                $display("ERROR: VS count %0d expected %0d",
                         vs_cycles, V_SYNC * H_TOTAL);
                errors = errors + 1;
            end

            if (errors == 0) begin
                $display("HDMI Sobel full-chain simulation passed");
                $display("gray_samples=%0d edge_writes=%0d white_hdmi_pixels=%0d",
                         gray_samples, edge_writes, white_pixels);
                test_passed = 1'b1;
            end else begin
                $display("HDMI Sobel simulation failed with %0d errors", errors);
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
            output_x = active_pixels % H_ACTIVE;
            output_y = active_pixels / H_ACTIVE;
            expected_addr = (output_y / SCALE_Y) * 128 +
                            (output_x / SCALE_X);
            if (expected_edge[expected_addr] >= EDGE_THRESHOLD) begin
                if ({rgb_r, rgb_g, rgb_b} !== 24'hffffff) begin
                    $display("ERROR: HDMI pixel %0d is %h expected white",
                             active_pixels, {rgb_r, rgb_g, rgb_b});
                    errors = errors + 1;
                end
                white_pixels = white_pixels + 1;
            end else if ({rgb_r, rgb_g, rgb_b} !== 24'h000000) begin
                $display("ERROR: HDMI pixel %0d is %h expected black",
                         active_pixels, {rgb_r, rgb_g, rgb_b});
                errors = errors + 1;
            end
            if (({rgb_r, rgb_g, rgb_b} !== 24'h000000) &&
                ({rgb_r, rgb_g, rgb_b} !== 24'hffffff)) begin
                $display("ERROR: HDMI pixel %0d is not binary: %h",
                         active_pixels, {rgb_r, rgb_g, rgb_b});
                errors = errors + 1;
            end
            active_pixels = active_pixels + 1;
        end
    end
end

initial begin
    $readmemh("expected_edge.hex", expected_edge);
    for (index = 0; index < 9216; index = index + 1)
        write_count[index] = 0;

    repeat (4) @(posedge clk);
    rst = 1'b0;

    wait (dut.sobel_done);
    repeat (2) @(posedge clk);

    if (gray_samples != 9216) begin
        $display("ERROR: gray sample count %0d expected 9216", gray_samples);
        errors = errors + 1;
    end
    if (edge_writes != 9216) begin
        $display("ERROR: edge write count %0d expected 9216", edge_writes);
        errors = errors + 1;
    end
    if (done_pulses != 1) begin
        $display("ERROR: edge_frame_done pulse count %0d expected 1", done_pulses);
        errors = errors + 1;
    end
    for (index = 0; index < 9216; index = index + 1) begin
        if (write_count[index] != 1) begin
            $display("ERROR: edge address %0d write count %0d expected 1",
                     index, write_count[index]);
            errors = errors + 1;
        end
        if (dut.edge_mem[index] !== expected_edge[index]) begin
            $display("ERROR: edge_mem[%0d]=%0d expected=%0d",
                     index, dut.edge_mem[index], expected_edge[index]);
            errors = errors + 1;
        end
    end
    processing_checked = 1'b1;

    repeat (H_TOTAL * V_TOTAL * 3) @(posedge clk);
    $display("ERROR: timeout waiting for checked HDMI frame");
    test_done = 1'b1;
    $finish;
end

endmodule

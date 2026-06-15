set script_dir [file dirname [file normalize [info script]]]
set build_dir [file join $script_dir build vivado_2023_2]
set src_dir [file join $script_dir sobel_02_hdmi_sobel.srcs sources_1]
set rtl_dir [file join $src_dir new]
set rgb_dir [file join $src_dir ip rgb2dvi_0 src]
set clk_dir [file join $src_dir ip video_clock]
set xdc_dir [file join $script_dir sobel_02_hdmi_sobel.srcs constrs_1 new]
set evidence_dir [file normalize [file join $script_dir .. coursework evidence 03_hdmi_sobel]]

file delete -force $build_dir
file mkdir $build_dir
file mkdir $evidence_dir
create_project -force exp02_build $build_dir -part xc7z020clg400-2
set_property target_language Verilog [current_project]

foreach rtl_file {
    image_rom_128x72.v
    rgb_to_gray.v
    sobel_core.v
    hdmi_sobel_display.v
    top.v
} {
    read_verilog [file join $rtl_dir $rtl_file]
}
read_verilog [file join $clk_dir video_clock_clk_wiz.v]
read_verilog [file join $clk_dir video_clock.v]

foreach vhdl_file {
    DVI_Constants.vhd
    SyncAsync.vhd
    SyncAsyncReset.vhd
    OutputSERDES.vhd
    TMDS_Encoder.vhd
    ClockGen.vhd
    rgb2dvi.vhd
} {
    read_vhdl [file join $rgb_dir $vhdl_file]
}
read_vhdl [file join $rtl_dir rgb2dvi_0.vhd]

read_xdc [file join $xdc_dir hdmi_out_test.xdc]
read_xdc [file join $rgb_dir rgb2dvi.xdc]

set_param general.maxThreads 4
puts "EXP02_STAGE=synthesis"
synth_design -top top -part xc7z020clg400-2
report_utilization -file [file join $evidence_dir exp02_utilization.txt]

puts "EXP02_STAGE=implementation"
opt_design
place_design
phys_opt_design
route_design
report_timing_summary -delay_type min_max -report_unconstrained \
    -check_timing_verbose -max_paths 10 \
    -file [file join $evidence_dir exp02_timing_summary.txt]
report_drc -file [file join $evidence_dir exp02_drc.txt]

set bit_file [file join $build_dir top.bit]
puts "EXP02_STAGE=bitstream"
write_bitstream -force $bit_file
puts "EXP02_BITSTREAM=$bit_file"
puts "EXP02_BUILD=passed"

close_project
exit

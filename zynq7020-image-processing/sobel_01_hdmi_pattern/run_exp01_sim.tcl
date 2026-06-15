set script_dir [file dirname [file normalize [info script]]]
set build_dir [file join $script_dir build sim]
set rtl_file [file join $script_dir sobel_01_hdmi_pattern.srcs sources_1 new hdmi_image_display.v]
set tb_file [file join $script_dir sim hdmi_image_display_tb.v]

file delete -force $build_dir
create_project -force exp01_sim $build_dir -part xc7z020clg400-2
add_files $rtl_file
add_files -fileset sim_1 $tb_file
set_property top hdmi_image_display_tb [get_filesets sim_1]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1

launch_simulation
run all
set test_done [get_value /hdmi_image_display_tb/test_done]
set test_passed [get_value /hdmi_image_display_tb/test_passed]
if {$test_done ne "1" || $test_passed ne "1"} {
    error "EXP01_SIM=failed"
}
puts "EXP01_SIM=passed"
close_sim
close_project
exit

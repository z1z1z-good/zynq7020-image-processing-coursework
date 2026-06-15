set script_dir [file dirname [file normalize [info script]]]
set build_dir [file join $script_dir build sim]
set rtl_dir [file join $script_dir sobel_03_uart_hdmi.srcs sources_1 new]
set tb_file [file join $script_dir sim hdmi_bram_display_tb.v]
set tool_file [file join $script_dir tools generate_exp03_expected.py]
set evidence_dir [file normalize [file join $script_dir .. coursework evidence 04_uart_hdmi]]
set expected_hex [file join $build_dir expected_frame.hex]
if {[info exists ::env(EXP03_PYTHON)]} {
    set python_exe $::env(EXP03_PYTHON)
} elseif {[file exists "D:/Miniconda3/python.exe"]} {
    set python_exe "D:/Miniconda3/python.exe"
} else {
    set python_exe python
}

file delete -force $build_dir
file mkdir $build_dir
file mkdir $evidence_dir

unset -nocomplain ::env(PYTHONHOME)
unset -nocomplain ::env(PYTHONPATH)
exec $python_exe $tool_file \
    --evidence-dir $evidence_dir \
    --hex-output $expected_hex

create_project -force exp03_sim $build_dir -part xc7z020clg400-2
read_verilog [file join $rtl_dir hdmi_bram_display.v]
add_files -fileset sim_1 $tb_file
add_files -fileset sim_1 $expected_hex
set_property file_type {Memory Initialization Files} [get_files $expected_hex]
set_property top hdmi_bram_display_tb [get_filesets sim_1]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1

launch_simulation
run all
set test_done [get_value /hdmi_bram_display_tb/test_done]
set test_passed [get_value /hdmi_bram_display_tb/test_passed]
if {$test_done ne "1" || $test_passed ne "1"} {
    error "EXP03_SIM=failed"
}
puts "EXP03_SIM=passed"
close_sim
close_project
exit

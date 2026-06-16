# build_exp05_ps_app.tcl — 用 Vitis 2023.2 经典 XSCT 无头编译实验 5 的 PS 应用。
# 运行（PowerShell）：& D:\Vivado\Vitis\2023.2\bin\xsct.bat build_exp05_ps_app.tcl
#
# 平台来自 run_exp05_bitstream.tcl 导出的硬件规格 XSA；应用源码使用仓库中已维护的
# ps_uart_control_bram_app/src/main.c（在实验 3/4 接收逻辑上新增控制帧解析与控制字写入）。
# 目标只是证明 PS 端 C 源对该平台可成功编译出 .elf，不烧录、不在板上运行。
#
# 注意：本自动化环境下 XSCT 连接 Vitis 后端会超时（Timeout while establishing a
# connection with Vitis），因此完整 BSP/ELF 构建需在正常 Vitis 2023.2 环境运行；
# 无头环境下用 tools/ps_syntax_check 的 arm-none-eabi-gcc 源码级检查替代（见 exp05_ps_build.txt）。

set script_dir [file dirname [file normalize [info script]]]
set ws [file join $script_dir build vitis_2023_2]
# 与 run_exp05_bitstream.tcl 一致：XSA 位置可用 EXP05_BUILD_DIR 覆盖（绕过 Windows MAX_PATH）。
if {[info exists ::env(EXP05_BUILD_DIR)] && [string length $::env(EXP05_BUILD_DIR)] > 0} {
    set bdir $::env(EXP05_BUILD_DIR)
} else {
    set bdir [file join $script_dir build vivado_2023_2]
}
set xsa [file join $bdir ps_uart_bram_hdmi.xsa]
set app_src [file join $script_dir ps_uart_control_bram_app src main.c]

if {![file exists $xsa]} {
    error "XSA not found: $xsa (先运行 run_exp05_bitstream.tcl)"
}
if {![file exists $app_src]} {
    error "PS source not found: $app_src"
}

file delete -force $ws
file mkdir $ws
setws $ws

# 由硬件规格创建独立运行域平台并生成 BSP。
platform create -name exp05_plat -hw $xsa
domain create -name standalone_domain -proc ps7_cortexa9_0 -os standalone
platform generate

# 新建空应用，再用维护中的 PS 源码覆盖默认 main。
app create -name ps_uart_control_bram_app -platform exp05_plat -domain standalone_domain -template {Empty Application(C)}
set app_src_dir [file join $ws ps_uart_control_bram_app src]
foreach c [glob -nocomplain [file join $app_src_dir *.c]] {
    file delete -force $c
}
file copy -force $app_src [file join $app_src_dir main.c]

app build -name ps_uart_control_bram_app

set elf [file join $ws ps_uart_control_bram_app Debug ps_uart_control_bram_app.elf]
if {[file exists $elf]} {
    puts "EXP05_PS_ELF_BYTES=[file size $elf]"
    puts "EXP05_PS_BUILD=passed"
} else {
    error "EXP05_PS_BUILD=failed (elf not found)"
}
exit

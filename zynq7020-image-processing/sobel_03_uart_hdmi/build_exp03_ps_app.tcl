# build_exp03_ps_app.tcl — 用 Vitis 2023.2 经典 XSCT 无头编译实验 3 的 PS 应用。
# 运行（PowerShell）：& D:\Vivado\Vitis\2023.2\bin\xsct.bat build_exp03_ps_app.tcl
#
# 平台来自 run_exp03_bitstream.tcl 导出的硬件规格 XSA；应用源码使用仓库中已维护的
# ps_uart_bram_app/src/main.c。目标只是证明 PS 端 C 源对该平台可成功编译出 .elf，
# 不烧录、不在板上运行。

set script_dir [file dirname [file normalize [info script]]]
set ws [file join $script_dir build vitis_2023_2]
set xsa [file join $script_dir build vivado_2023_2 ps_uart_bram_hdmi.xsa]
set app_src [file join $script_dir ps_uart_bram_app src main.c]

if {![file exists $xsa]} {
    error "XSA not found: $xsa (先运行 run_exp03_bitstream.tcl)"
}
if {![file exists $app_src]} {
    error "PS source not found: $app_src"
}

file delete -force $ws
file mkdir $ws
setws $ws

# 由硬件规格创建独立运行域平台并生成 BSP。
platform create -name exp03_plat -hw $xsa
domain create -name standalone_domain -proc ps7_cortexa9_0 -os standalone
platform generate

# 新建空应用，再用维护中的 PS 源码覆盖默认 main。
app create -name ps_uart_bram_app -platform exp03_plat -domain standalone_domain -template {Empty Application(C)}
set app_src_dir [file join $ws ps_uart_bram_app src]
foreach c [glob -nocomplain [file join $app_src_dir *.c]] {
    file delete -force $c
}
file copy -force $app_src [file join $app_src_dir main.c]

app build -name ps_uart_bram_app

set elf [file join $ws ps_uart_bram_app Debug ps_uart_bram_app.elf]
if {[file exists $elf]} {
    puts "EXP03_PS_ELF_BYTES=[file size $elf]"
    puts "EXP03_PS_BUILD=passed"
} else {
    error "EXP03_PS_BUILD=failed (elf not found)"
}
exit

set script_dir [file dirname [file normalize [info script]]]
# build_dir 可用环境变量 EXP05_BUILD_DIR 覆盖为较短路径，绕过 Windows 260 字符 MAX_PATH 限制
# （深层工作树路径 + Vivado processing_system7 IP 生成目录会超限）。默认写入已忽略的 build/。
if {[info exists ::env(EXP05_BUILD_DIR)] && [string length $::env(EXP05_BUILD_DIR)] > 0} {
    set build_dir $::env(EXP05_BUILD_DIR)
} else {
    set build_dir [file join $script_dir build vivado_2023_2]
}
set src_dir [file join $script_dir sobel_05_pc_control_display.srcs sources_1]
set rtl_dir [file join $src_dir new]
set rgb_dir [file join $src_dir ip rgb2dvi_0 src]
set clk_dir [file join $src_dir ip video_clock]
set xdc_dir [file join $script_dir sobel_05_pc_control_display.srcs constrs_1 new]
set evidence_dir [file normalize [file join $script_dir .. coursework evidence 06_pc_control]]
set bd_name ps_uart_bram_hdmi

# 仅设置 IP 支持的属性，避免不同 IP 版本属性差异导致整脚本失败。
proc set_config_if_supported {obj config_pairs} {
    set supported [list_property $obj]
    foreach {key value} $config_pairs {
        set prop_name CONFIG.$key
        if {[lsearch -exact $supported $prop_name] >= 0} {
            if {[catch {set_property $prop_name $value $obj} msg]} {
                puts "Warning: failed to set $prop_name to {$value}: $msg"
            }
        }
    }
}

# 解析当前 Vivado 版本中某 IP 的最新可用 VLNV，避免硬编码 2017.4 版本号在 2023.2 下不被支持。
proc latest_ip {name} {
    set cand [lsort -decreasing [get_ipdefs -all "xilinx.com:ip:${name}:*"]]
    if {[llength $cand] == 0} {
        error "no IP definition found for xilinx.com:ip:${name}"
    }
    return [lindex $cand 0]
}

file delete -force $build_dir
file mkdir $build_dir
file mkdir $evidence_dir
create_project -force exp05_build $build_dir -part xc7z020clg400-2
set_property target_language Verilog [current_project]

# ---------- Block design：PS7 + SmartConnect + AXI BRAM Controller + Block Memory ----------
# 在隔离 build 工程内全新重建 BD，不触碰仓库中已提交的 2017.4 BD。与实验 3/4 同源（同一 64KB BRAM）。
create_bd_design $bd_name

create_bd_cell -type ip -vlnv [latest_ip processing_system7] processing_system7_0
apply_bd_automation -rule xilinx.com:bd_rule:processing_system7 \
    -config {make_external "FIXED_IO, DDR" apply_board_preset "0" Master "Disable" Slave "Disable"} \
    [get_bd_cells processing_system7_0]

set_config_if_supported [get_bd_cells processing_system7_0] [list \
    PCW_USE_M_AXI_GP0 1 \
    PCW_USE_M_AXI_GP1 0 \
    PCW_USE_S_AXI_GP0 0 \
    PCW_USE_S_AXI_GP1 0 \
    PCW_USE_S_AXI_ACP 0 \
    PCW_USE_S_AXI_HP0 0 \
    PCW_USE_S_AXI_HP1 0 \
    PCW_USE_S_AXI_HP2 0 \
    PCW_USE_S_AXI_HP3 0 \
    PCW_USE_FABRIC_INTERRUPT 0 \
    PCW_IRQ_F2P_INTR 0 \
    PCW_EN_CLK0_PORT 1 \
    PCW_EN_RST0_PORT 1 \
    PCW_FPGA0_PERIPHERAL_FREQMHZ 50 \
    PCW_EN_DDR 1 \
    PCW_UIPARAM_DDR_ENABLE 1 \
    PCW_UIPARAM_DDR_ADV_ENABLE 0 \
    PCW_UIPARAM_DDR_FREQ_MHZ 533.333333 \
    PCW_UIPARAM_DDR_MEMORY_TYPE {DDR 3} \
    PCW_UIPARAM_DDR_BUS_WIDTH {32 Bit} \
    PCW_UIPARAM_DDR_BL 8 \
    PCW_UIPARAM_DDR_HIGH_TEMP {Normal (0-85)} \
    PCW_UIPARAM_DDR_PARTNO {MT41J256M16 RE-125} \
    PCW_UIPARAM_DDR_TRAIN_WRITE_LEVEL 1 \
    PCW_UIPARAM_DDR_TRAIN_READ_GATE 1 \
    PCW_UIPARAM_DDR_TRAIN_DATA_EYE 1 \
    PCW_UIPARAM_DDR_CLOCK_STOP_EN 0 \
    PCW_UIPARAM_DDR_USE_INTERNAL_VREF 0 \
    PCW_EN_UART1 1 \
    PCW_EN_UART0 0 \
    PCW_UART1_PERIPHERAL_ENABLE 1 \
    PCW_UART1_UART1_IO {MIO 48 .. 49} \
    PCW_UART1_GRP_FULL_ENABLE 0 \
    PCW_UART1_BAUD_RATE 115200 \
    PCW_UART_PERIPHERAL_VALID 1 \
    PCW_UART_PERIPHERAL_FREQMHZ 100 \
    PCW_EN_EMIO_UART1 0 \
    PCW_PRESET_BANK0_VOLTAGE {LVCMOS 3.3V} \
    PCW_PRESET_BANK1_VOLTAGE {LVCMOS 1.8V} \
]

create_bd_cell -type ip -vlnv [latest_ip proc_sys_reset] rst_ps7_0_50M
create_bd_cell -type ip -vlnv [latest_ip smartconnect] axi_smc
create_bd_cell -type ip -vlnv [latest_ip axi_bram_ctrl] axi_bram_ctrl_0
create_bd_cell -type ip -vlnv [latest_ip blk_mem_gen] blk_mem_gen_0

set_config_if_supported [get_bd_cells axi_smc] [list \
    NUM_MI 1 \
    NUM_SI 1 \
]

set_config_if_supported [get_bd_cells axi_bram_ctrl_0] [list \
    DATA_WIDTH 32 \
    SINGLE_PORT_BRAM 1 \
    ECC_TYPE 0 \
]

set_config_if_supported [get_bd_cells blk_mem_gen_0] [list \
    Memory_Type True_Dual_Port_RAM \
    Enable_A Always_Enabled \
    Enable_B Use_ENB_Pin \
    Use_RSTA_Pin false \
    Use_RSTB_Pin true \
    Use_Byte_Write_Enable true \
    Byte_Size 8 \
    Write_Width_A 32 \
    Read_Width_A 32 \
    Write_Depth_A 16384 \
    Write_Width_B 32 \
    Read_Width_B 32 \
    Read_Depth_B 16384 \
    Operating_Mode_A WRITE_FIRST \
    Operating_Mode_B READ_FIRST \
    Port_B_Clock 74.25 \
    EN_SAFETY_CKT false \
]

connect_bd_net [get_bd_pins processing_system7_0/FCLK_CLK0] \
    [get_bd_pins processing_system7_0/M_AXI_GP0_ACLK] \
    [get_bd_pins axi_smc/aclk] \
    [get_bd_pins axi_bram_ctrl_0/s_axi_aclk] \
    [get_bd_pins rst_ps7_0_50M/slowest_sync_clk]

connect_bd_net [get_bd_pins processing_system7_0/FCLK_RESET0_N] \
    [get_bd_pins rst_ps7_0_50M/ext_reset_in]

connect_bd_net [get_bd_pins rst_ps7_0_50M/peripheral_aresetn] \
    [get_bd_pins axi_smc/aresetn] \
    [get_bd_pins axi_bram_ctrl_0/s_axi_aresetn]

connect_bd_intf_net [get_bd_intf_pins processing_system7_0/M_AXI_GP0] \
    [get_bd_intf_pins axi_smc/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins axi_smc/M00_AXI] \
    [get_bd_intf_pins axi_bram_ctrl_0/S_AXI]
connect_bd_intf_net [get_bd_intf_pins axi_bram_ctrl_0/BRAM_PORTA] \
    [get_bd_intf_pins blk_mem_gen_0/BRAM_PORTA]

set bram_portb_clk [create_bd_port -dir I -type clk BRAM_PORTB_clk]
set_property CONFIG.FREQ_HZ 74250000 $bram_portb_clk
set bram_portb_rst [create_bd_port -dir I -type rst BRAM_PORTB_rst]
set_property CONFIG.POLARITY ACTIVE_HIGH $bram_portb_rst
create_bd_port -dir I BRAM_PORTB_en
create_bd_port -dir I -from 3 -to 0 BRAM_PORTB_we
create_bd_port -dir I -from 31 -to 0 BRAM_PORTB_addr
create_bd_port -dir I -from 31 -to 0 BRAM_PORTB_din
create_bd_port -dir O -from 31 -to 0 BRAM_PORTB_dout

connect_bd_net [get_bd_ports BRAM_PORTB_clk]  [get_bd_pins blk_mem_gen_0/clkb]
connect_bd_net [get_bd_ports BRAM_PORTB_rst]  [get_bd_pins blk_mem_gen_0/rstb]
connect_bd_net [get_bd_ports BRAM_PORTB_en]   [get_bd_pins blk_mem_gen_0/enb]
connect_bd_net [get_bd_ports BRAM_PORTB_we]   [get_bd_pins blk_mem_gen_0/web]
connect_bd_net [get_bd_ports BRAM_PORTB_addr] [get_bd_pins blk_mem_gen_0/addrb]
connect_bd_net [get_bd_ports BRAM_PORTB_din]  [get_bd_pins blk_mem_gen_0/dinb]
connect_bd_net [get_bd_ports BRAM_PORTB_dout] [get_bd_pins blk_mem_gen_0/doutb]

assign_bd_address
set bram_seg [get_bd_addr_segs -quiet processing_system7_0/Data/SEG_axi_bram_ctrl_0_Mem0]
if {[llength $bram_seg] != 0} {
    set_property offset 0x40000000 $bram_seg
    set_property range 64K $bram_seg
}

validate_bd_design
save_bd_design

# 全局（in-context）综合：不生成 OOC 检查点，避免在本环境派生子进程。
set_property synth_checkpoint_mode None [get_files ${bd_name}.bd]
generate_target all [get_files ${bd_name}.bd]
set wrapper [make_wrapper -files [get_files ${bd_name}.bd] -top -force]
if {[llength [get_files -quiet $wrapper]] == 0} {
    add_files -norecurse $wrapper
}
update_compile_order -fileset sources_1

# ---------- PL RTL 顶层、PL 显示控制与 HDMI 归档源码 ----------
# 实验 5 在实验 4 基础上的 hdmi_bram_sobel_display 增加控制字读取与四模式显示；
# rgb_to_gray / sobel_core 为同步复位版本（勿用实验 4 异步复位版本）；
# rgb2dvi_0.vhd 是与 IP 同名同端口的源码包装，便于无 IP repository 隔离重建。
add_files -norecurse [list \
    [file join $rtl_dir top.v] \
    [file join $rtl_dir hdmi_pl_top.v] \
    [file join $rtl_dir hdmi_bram_sobel_display.v] \
    [file join $rtl_dir rgb_to_gray.v] \
    [file join $rtl_dir sobel_core.v] \
    [file join $clk_dir video_clock_clk_wiz.v] \
    [file join $clk_dir video_clock.v] \
    [file join $rgb_dir DVI_Constants.vhd] \
    [file join $rgb_dir SyncAsync.vhd] \
    [file join $rgb_dir SyncAsyncReset.vhd] \
    [file join $rgb_dir OutputSERDES.vhd] \
    [file join $rgb_dir TMDS_Encoder.vhd] \
    [file join $rgb_dir ClockGen.vhd] \
    [file join $rgb_dir rgb2dvi.vhd] \
    [file join $rtl_dir rgb2dvi_0.vhd] \
]
add_files -fileset constrs_1 [list \
    [file join $xdc_dir hdmi_out_test.xdc] \
    [file join $rgb_dir rgb2dvi.xdc] \
]
set_property top top [current_fileset]
update_compile_order -fileset sources_1

# ---------- 综合 / 实现 / Bitstream（全程进程内，不派生子进程）----------
set_param general.maxThreads 4
puts "EXP05_STAGE=synthesis"
synth_design -top top -part xc7z020clg400-2
report_utilization -file [file join $evidence_dir exp05_utilization.txt]

puts "EXP05_STAGE=implementation"
opt_design
place_design
phys_opt_design
route_design
write_checkpoint -force [file join $build_dir top_routed.dcp]
report_timing_summary -delay_type min_max -report_unconstrained \
    -check_timing_verbose -max_paths 10 \
    -file [file join $evidence_dir exp05_timing_summary.txt]
report_drc -file [file join $evidence_dir exp05_drc.txt]

set bit_file [file join $build_dir top.bit]
puts "EXP05_STAGE=bitstream"
write_bitstream -force $bit_file
puts "EXP05_BITSTREAM=$bit_file"

# 导出硬件平台 XSA（含地址映射的硬件规格），供 Vitis PS 程序编译。
# 非项目（synth_design）流程下不带 -include_bit；现场烧录使用上面的 top.bit。
set xsa_file [file join $build_dir ps_uart_bram_hdmi.xsa]
write_hw_platform -fixed -force $xsa_file
puts "EXP05_XSA=$xsa_file"
puts "EXP05_BUILD=passed"

close_project
exit

onerror {resume}
quietly WaveActivateNextPane {} 0
add wave -noupdate /TB_final_project_top/DUT0/i
add wave -noupdate -expand -group {Top Level Inputs} /TB_final_project_top/DUT0/i_CLK
add wave -noupdate -expand -group {Top Level Inputs} /TB_final_project_top/DUT0/i_RESET
add wave -noupdate -expand -group {Top Level Inputs} /TB_final_project_top/DUT0/i_ENABLE
add wave -noupdate -expand -group {Top Level Inputs} -color Orange -format Literal /TB_final_project_top/DUT0/i_MODE
add wave -noupdate -expand -group {Top Level Inputs} /TB_final_project_top/DUT0/i_temp_NEW
add wave -noupdate -expand -group {Pipeline Stage 0} /TB_final_project_top/DUT0/w0_FIFO_FULL
add wave -noupdate -expand -group {Pipeline Stage 0} -color Blue /TB_final_project_top/DUT0/w0_AVERAGE
add wave -noupdate -expand -group {Pipeline Stage 0} -color Orange -format Literal /TB_final_project_top/DUT0/reg0_MODE
add wave -noupdate -expand -group {Pipeline Stage 0} /TB_final_project_top/DUT0/reg0_num_samples
add wave -noupdate -expand -group {Pipeline Stage 0} /TB_final_project_top/DUT0/reg0_temp_FIFO
add wave -noupdate -expand -group {Pipeline Stage 0} /TB_final_project_top/DUT0/reg0_temp_TOTAL
add wave -noupdate -expand -group {Pipeline Stage 0} /TB_final_project_top/DUT0/reg0_sum_squares
add wave -noupdate -expand -group {Pipeline Stage 0} /TB_final_project_top/DUT0/reg0_VARIANCE
add wave -noupdate -expand -group {Pipeline Stage 0} -color Blue /TB_final_project_top/DUT0/reg0_AVERAGE
add wave -noupdate -expand -group {Pipeline Stage 1} /TB_final_project_top/DUT0/reg1_DONE
add wave -noupdate -expand -group {Pipeline Stage 1} -color Orange -format Literal /TB_final_project_top/DUT0/reg1_MODE
add wave -noupdate -expand -group {Pipeline Stage 1} -color Orange -format Literal /TB_final_project_top/DUT0/reg_output_mode
add wave -noupdate -expand -group {Pipeline Stage 1} /TB_final_project_top/DUT0/reg1_FIFO_FULL
add wave -noupdate -expand -group {Pipeline Stage 1} -color Blue /TB_final_project_top/DUT0/reg1_AVERAGE
add wave -noupdate -expand -group {Pipeline Stage 1} -color {Medium Slate Blue} /TB_final_project_top/DUT0/reg1_STD_DEV
add wave -noupdate -expand -group {Output Stage} -format Literal /TB_final_project_top/DUT0/o_DONE
add wave -noupdate -expand -group {Output Stage} /TB_final_project_top/DUT0/o_RESULT
add wave -noupdate -expand -group {Output Stage} -expand -group Calculated -color Blue /TB_final_project_top/average_D3
add wave -noupdate -expand -group {Output Stage} -expand -group Calculated -color {Medium Slate Blue} /TB_final_project_top/std_dev_D3
add wave -noupdate -expand -group {Output Stage} -expand -group Calculated -color Orange /TB_final_project_top/MODE_D2
add wave -noupdate -expand -group {Output Stage} -expand -group Calculated -color Orange /TB_final_project_top/MODE_D3
add wave -noupdate /TB_final_project_top/num_samples
add wave -noupdate /TB_final_project_top/temp_FIFO
TreeUpdate [SetDefaultTree]
WaveRestoreCursors {{Cursor 3} {411 ns} 0} {{Cursor 2} {60 ns} 0}
quietly wave cursor active 1
configure wave -namecolwidth 226
configure wave -valuecolwidth 100
configure wave -justifyvalue left
configure wave -signalnamewidth 1
configure wave -snapdistance 10
configure wave -datasetprefix 0
configure wave -rowmargin 4
configure wave -childrowmargin 2
configure wave -gridoffset 0
configure wave -gridperiod 1
configure wave -griddelta 40
configure wave -timeline 0
configure wave -timelineunits ns
update
WaveRestoreZoom {0 ns} {630 ns}

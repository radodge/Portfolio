# ####################################################################

#  Created by Genus(TM) Synthesis Solution 21.17-s066_1 on Fri Dec 15 09:23:10 CST 2023

# ####################################################################

set sdc_version 2.0

set_units -capacitance 1000fF
set_units -time 1000ps

# Set the current design
current_design final_project_top

create_clock -name "clk" -period 4.0 -waveform {0.0 2.0} [get_ports i_CLK]
group_path -weight 1.000000 -name cg_enable_group_clk -through [list \
  [get_pins RC_CG_HIER_INST1/enable]  \
  [get_pins RC_CG_HIER_INST1/RC_CGIC_INST/E]  \
  [get_pins RC_CG_HIER_INST3/enable]  \
  [get_pins RC_CG_HIER_INST3/RC_CGIC_INST/E]  \
  [get_pins RC_CG_HIER_INST4/enable]  \
  [get_pins RC_CG_HIER_INST4/RC_CGIC_INST/E]  \
  [get_pins RC_CG_HIER_INST5/enable]  \
  [get_pins RC_CG_HIER_INST5/RC_CGIC_INST/E]  \
  [get_pins RC_CG_HIER_INST1/enable]  \
  [get_pins RC_CG_HIER_INST1/RC_CGIC_INST/E]  \
  [get_pins RC_CG_HIER_INST3/enable]  \
  [get_pins RC_CG_HIER_INST3/RC_CGIC_INST/E]  \
  [get_pins RC_CG_HIER_INST4/enable]  \
  [get_pins RC_CG_HIER_INST4/RC_CGIC_INST/E]  \
  [get_pins RC_CG_HIER_INST5/enable]  \
  [get_pins RC_CG_HIER_INST5/RC_CGIC_INST/E]  \
  [get_pins RC_CG_DECLONE_HIER_INST/RC_CGIC_INST/E]  \
  [get_pins RC_CG_DECLONE_HIER_INST/RC_CGIC_INST/E]  \
  [get_pins RC_CG_DECLONE_HIER_INST182997/RC_CGIC_INST/E]  \
  [get_pins RC_CG_DECLONE_HIER_INST182997/RC_CGIC_INST/E]  \
  [get_pins RC_CG_HIER_INST1/enable]  \
  [get_pins RC_CG_HIER_INST1/RC_CGIC_INST/E]  \
  [get_pins RC_CG_HIER_INST3/enable]  \
  [get_pins RC_CG_HIER_INST3/RC_CGIC_INST/E]  \
  [get_pins RC_CG_HIER_INST4/enable]  \
  [get_pins RC_CG_HIER_INST4/RC_CGIC_INST/E]  \
  [get_pins RC_CG_HIER_INST5/enable]  \
  [get_pins RC_CG_HIER_INST5/RC_CGIC_INST/E]  \
  [get_pins RC_CG_DECLONE_HIER_INST/enable]  \
  [get_pins RC_CG_DECLONE_HIER_INST/RC_CGIC_INST/E]  \
  [get_pins RC_CG_DECLONE_HIER_INST182997/enable]  \
  [get_pins RC_CG_DECLONE_HIER_INST182997/RC_CGIC_INST/E]  \
  [get_pins RC_CG_HIER_INST1/enable]  \
  [get_pins RC_CG_HIER_INST1/RC_CGIC_INST/E]  \
  [get_pins RC_CG_HIER_INST3/enable]  \
  [get_pins RC_CG_HIER_INST3/RC_CGIC_INST/E]  \
  [get_pins RC_CG_HIER_INST4/enable]  \
  [get_pins RC_CG_HIER_INST4/RC_CGIC_INST/E]  \
  [get_pins RC_CG_HIER_INST5/enable]  \
  [get_pins RC_CG_HIER_INST5/RC_CGIC_INST/E]  \
  [get_pins RC_CG_DECLONE_HIER_INST/enable]  \
  [get_pins RC_CG_DECLONE_HIER_INST/RC_CGIC_INST/E]  \
  [get_pins RC_CG_DECLONE_HIER_INST182997/enable]  \
  [get_pins RC_CG_DECLONE_HIER_INST182997/RC_CGIC_INST/E] ]
set_clock_gating_check -setup 0.0 
set_wire_load_mode "segmented"

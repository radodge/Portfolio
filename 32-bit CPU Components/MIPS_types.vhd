library IEEE;
	use IEEE.std_logic_1164.all;

package MIPS_types is

	-- Example record type. Declare whatever types you need here
	type control_t is record

		reg_wr : std_logic;
		reg_to_mem : std_logic;

	end record control_t;

	--------------------------------------------------------------------------------
	--------------------------------------------------------------------------------
	--  ______                     
	--  | ___ \                    
	--  | |_/ /_   _ ___  ___  ___ 
	--  | ___ \ | | / __|/ _ \/ __|
	--  | |_/ / |_| \__ \  __/\__ \
	--  \____/ \__,_|___/\___||___/
	--                      
	--------------------------------------------------------------------------------
    subtype bus_16    is std_logic_vector(15 downto 00);
    subtype bus_32    is std_logic_vector(31 downto 00);
    type    bus_32x32 is array(31 downto 00) of  bus_32;

    constant zeroes_32: bus_32 := X"00000000"; -- primarily for $zero register
    constant F_32:      bus_32 := X"FFFFFFFF";
	--------------------------------------------------------------------------------
	--------------------------------------------------------------------------------


	--------------------------------------------------------------------------------
	--------------------------------------------------------------------------------
	--  ___  ___                                
	--  |  \/  |                                
	--  | .  . | ___ _ __ ___   ___  _ __ _   _ 
	--  | |\/| |/ _ \ '_ ` _ \ / _ \| '__| | | |
	--  | |  | |  __/ | | | | | (_) | |  | |_| |
	--  \_|  |_/\___|_| |_| |_|\___/|_|   \__, |
	--                                     __/ |
	--                                    |___/ 
	--------------------------------------------------------------------------------
	constant DATA_WIDTH: natural := 32;
	constant ADDR_WIDTH: natural := 10;

	subtype MIPS_word       is std_logic_vector(31 downto 00);

	subtype memory_address  is std_logic_vector((ADDR_WIDTH-1) downto 00);
	subtype memory_data_bus is std_logic_vector((DATA_WIDTH-1) downto 00);

	type    memory_t is array(2**ADDR_WIDTH-1 downto 00) of MIPS_word;
	--------------------------------------------------------------------------------
	--------------------------------------------------------------------------------


	--------------------------------------------------------------------------------
	--------------------------------------------------------------------------------
	--  ______           _     _             ______ _ _      
	--  | ___ \         (_)   | |            |  ___(_) |     
	--  | |_/ /___  __ _ _ ___| |_ ___ _ __  | |_   _| | ___ 
	--  |    // _ \/ _` | / __| __/ _ \ '__| |  _| | | |/ _ \
	--  | |\ \  __/ (_| | \__ \ ||  __/ |    | |   | | |  __/
	--  \_| \_\___|\__, |_|___/\__\___|_|    \_|   |_|_|\___|
	--              __/ |                                    
	--             |___/                                     
	---------------------------------------------------------------------------------
	subtype reg_address is std_logic_vector(04 downto 00);


    --------------------------------------------------------------------------------
    -- Register Names --
    --------------------------------------------------------------------------------
    constant reg_zero: reg_address := "00000"; -- 00


    constant reg_at:   reg_address := "00001"; -- 01


    constant reg_v0:   reg_address := "00010"; -- 02
    constant reg_v1:   reg_address := "00011"; -- 03


    constant reg_a0:   reg_address := "00100"; -- 04
    constant reg_a1:   reg_address := "00101"; -- 05
    constant reg_a2:   reg_address := "00110"; -- 06
    constant reg_a3:   reg_address := "00111"; -- 07

 
    constant reg_t0:   reg_address := "01000"; -- 08
    constant reg_t1:   reg_address := "01001"; -- 09
    constant reg_t2:   reg_address := "01010"; -- 10
    constant reg_t3:   reg_address := "01011"; -- 11

    constant reg_t4:   reg_address := "01100"; -- 12
    constant reg_t5:   reg_address := "01101"; -- 13
    constant reg_t6:   reg_address := "01110"; -- 14
    constant reg_t7:   reg_address := "01111"; -- 15


    constant reg_s0:   reg_address := "10000"; -- 16
    constant reg_s1:   reg_address := "10001"; -- 17
    constant reg_s2:   reg_address := "10010"; -- 18
    constant reg_s3:   reg_address := "10011"; -- 19

    constant reg_s4:   reg_address := "10100"; -- 20
    constant reg_s5:   reg_address := "10101"; -- 21
    constant reg_s6:   reg_address := "10110"; -- 22
    constant reg_s7:   reg_address := "10111"; -- 23


    constant reg_t8:   reg_address := "11000"; -- 24
    constant reg_t9:   reg_address := "11001"; -- 25


    constant reg_k0:   reg_address := "11010"; -- 26
    constant reg_k1:   reg_address := "11011"; -- 27


    constant reg_gp:   reg_address := "11100"; -- 28

    constant reg_sp:   reg_address := "11101"; -- 29

    constant reg_fp:   reg_address := "11110"; -- 30

    constant reg_ra:   reg_address := "11111"; -- 31
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Register Numbers --
    --------------------------------------------------------------------------------
    constant reg_00: reg_address := "00000"; -- 00


    constant reg_01: reg_address := "00001"; -- $at


    constant reg_02: reg_address := "00010"; -- $v0
    constant reg_03: reg_address := "00011"; -- $v1


    constant reg_04: reg_address := "00100"; -- $a0
    constant reg_05: reg_address := "00101"; -- $a1
    constant reg_06: reg_address := "00110"; -- $a2
    constant reg_07: reg_address := "00111"; -- $a3


    constant reg_08: reg_address := "01000"; -- $t0
    constant reg_09: reg_address := "01001"; -- $t1
    constant reg_10: reg_address := "01010"; -- $t2
    constant reg_11: reg_address := "01011"; -- $t3

    constant reg_12: reg_address := "01100"; -- $t4
    constant reg_13: reg_address := "01101"; -- $t5
    constant reg_14: reg_address := "01110"; -- $t6
    constant reg_15: reg_address := "01111"; -- $t7


    constant reg_16: reg_address := "10000"; -- $s0
    constant reg_17: reg_address := "10001"; -- $s1
    constant reg_18: reg_address := "10010"; -- $s2
    constant reg_19: reg_address := "10011"; -- $s3

    constant reg_20: reg_address := "10100"; -- $s4
    constant reg_21: reg_address := "10101"; -- $s5
    constant reg_22: reg_address := "10110"; -- $s6
    constant reg_23: reg_address := "10111"; -- $s7


    constant reg_24: reg_address := "11000"; -- $t8
    constant reg_25: reg_address := "11001"; -- $t9


    constant reg_26: reg_address := "11010"; -- $k0
    constant reg_27: reg_address := "11011"; -- $k1


    constant reg_28: reg_address := "11100"; -- $gp

    constant reg_29: reg_address := "11101"; -- $sp

    constant reg_30: reg_address := "11110"; -- $fp

    constant reg_31: reg_address := "11111"; -- $ra
    --------------------------------------------------------------------------------
	--------------------------------------------------------------------------------
	--------------------------------------------------------------------------------


-- By the end of this part, your processor will implement the following instructions:
-- add, addi, addiu, addu, and, andi, lui, lw, nor, xor, xori, or,
-- ori, slt, slti, sll, srl, sra, sw, sub, subu, beq, bne, j, jal,
-- jr, bgez, bgezal, bgtz, blez, bltzal, bltz

	--------------------------------------------------------------------------------
	--------------------------------------------------------------------------------
	--                             _           
	--                            | |          
	--    ___  _ __   ___ ___   __| | ___  ___ 
	--   / _ \| '_ \ / __/ _ \ / _` |/ _ \/ __|
	--  | (_) | |_) | (_| (_) | (_| |  __/\__ \
	--   \___/| .__/ \___\___/ \__,_|\___||___/
	--        | |                              
	--        |_|                              
	--------------------------------------------------------------------------------
	--------------------------------------------------------------------------------
	-- Instruction[31:26]
	--------------------------------------------------------------------------------
	subtype opcode is std_logic_vector(05 downto 00);

	constant op_R_type: opcode := "000000"; -- R-type instructions

	constant op_j: 		opcode := "000010"; -- Jump
	constant op_jal: 	opcode := "000011"; -- Jump And Link

	constant op_beq:	opcode := "000100"; -- Branch On Equal
	constant op_bne: 	opcode := "000101"; -- Branch On Not Equal
	constant op_blez: 	opcode := "000110"; -- 
	constant op_bgtz: 	opcode := "000111"; -- 

	constant op_addi: 	opcode := "001000"; -- Add Immediate
	constant op_addiu: 	opcode := "001001"; -- Add Imm. Unsigned
	constant op_slti: 	opcode := "001010"; -- Set Less Than Imm.
	constant op_sltiu: 	opcode := "001011"; -- Set Less Than Imm. Unsigned

	constant op_andi: 	opcode := "001100"; -- And Immediate
	constant op_ori: 	opcode := "001101"; -- Or Immediate
	constant op_xori: 	opcode := "001110"; -- 
	constant op_lui: 	opcode := "001111"; -- Load Upper Imm.


	constant op_fpu: 	opcode := "010001"; -- floating point instructions


	constant op_lb: 	opcode := "100000"; -- Load Byte
	constant op_lh: 	opcode := "100001"; -- 
	constant op_lwl: 	opcode := "100010"; -- 
	constant op_lw: 	opcode := "100011"; -- Load Word


	constant op_lbu: 	opcode := "100100"; -- Load Byte Unsigned
	constant op_lhu: 	opcode := "100101"; -- Load Halfword Unsigned
	constant op_lwr: 	opcode := "100110"; -- 


	constant op_sb: 	opcode := "101000"; -- Store Byte
	constant op_sh: 	opcode := "101001"; -- Store Halfword
	constant op_swl: 	opcode := "101010"; -- 
	constant op_sw: 	opcode := "101011"; -- Store Word


	constant op_swr: 	opcode := "101110"; -- 
	constant op_cache: 	opcode := "101111"; -- 

	constant op_ll: 	opcode := "110000"; -- Load Linked
	constant op_lwc1: 	opcode := "110001"; -- Load FP Single
	constant op_lwc2: 	opcode := "110010"; -- 
	constant op_pref: 	opcode := "110011"; -- 


	constant op_ldc1: 	opcode := "110101"; -- Load FP Double
	constant op_ldc2: 	opcode := "110110"; -- 


	constant op_sc: 	opcode := "111000"; -- Store Conditional
	constant op_swc1: 	opcode := "111001"; -- 
	constant op_swc2: 	opcode := "111010"; -- 


	constant op_sdc1: 	opcode := "111101"; -- Store FP Double
	constant op_sdc2: 	opcode := "111110"; -- 
	--------------------------------------------------------------------------------
	--------------------------------------------------------------------------------


	--------------------------------------------------------------------------------
	--------------------------------------------------------------------------------
	--    __                  _   _                             _           
	--   / _|                | | (_)                           | |          
	--  | |_ _   _ _ __   ___| |_ _  ___  _ __     ___ ___   __| | ___  ___ 
	--  |  _| | | | '_ \ / __| __| |/ _ \| '_ \   / __/ _ \ / _` |/ _ \/ __|
	--  | | | |_| | | | | (__| |_| | (_) | | | | | (_| (_) | (_| |  __/\__ \
	--  |_|  \__,_|_| |_|\___|\__|_|\___/|_| |_|  \___\___/ \__,_|\___||___/
	-- 
	--------------------------------------------------------------------------------
	--------------------------------------------------------------------------------
	-- Instruction bits [5:0]                                                                     
	--------------------------------------------------------------------------------                                                                  
	subtype function_code is std_logic_vector(05 downto 00);

	constant funct_sll: 	function_code := "000000";

	constant funct_srl: 	function_code := "000010";
	constant funct_sra: 	function_code := "000011";


	constant funct_sllv: 	function_code := "000100";

	constant funct_srlv: 	function_code := "000110";
	constant funct_srav: 	function_code := "000111";


	constant funct_jr: 		function_code := "001000";
	constant funct_jalr: 	function_code := "001001";
	constant funct_movz: 	function_code := "001010";
	constant funct_movn: 	function_code := "001011";


	constant funct_syscall: function_code := "001100";
	constant funct_break: 	function_code := "001101";

	constant funct_sync: 	function_code := "001111";


	constant funct_mfhi: 	function_code := "010000";
	constant funct_mthi: 	function_code := "010001";
	constant funct_mflo: 	function_code := "010010";
	constant funct_mtlo: 	function_code := "010011";


	constant funct_mult: 	function_code := "011000";
	constant funct_multu: 	function_code := "011001";
	constant funct_div: 	function_code := "011010";
	constant funct_divu: 	function_code := "011011";


	constant funct_add: 	function_code := "100000"; -- the '1' is likely driving ALU
	constant funct_addu: 	function_code := "100001";
	constant funct_sub: 	function_code := "100010";
	constant funct_subu: 	function_code := "100011";


	constant funct_and: 	function_code := "100100";
	constant funct_or: 		function_code := "100101";
	constant funct_xor: 	function_code := "100110";
	constant funct_nor: 	function_code := "100111";


	constant funct_slt: 	function_code := "101010";
	constant funct_sltu: 	function_code := "101011";


	constant funct_tge: 	function_code := "110000";
	constant funct_tgeu: 	function_code := "110001";
	constant funct_tlt: 	function_code := "110010";
	constant funct_tltu: 	function_code := "110011";


	constant funct_teq: 	function_code := "110100";

	constant funct_tne: 	function_code := "110110";

end package MIPS_types;
--------------------------------------------------------------------------------
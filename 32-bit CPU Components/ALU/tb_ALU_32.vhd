-------------------------------------------------------------------------
-- Jonathan Tan x Reece Dodge
-- Department of Electrical and Computer Engineering
-- Iowa State University
-------------------------------------------------------------------------


-- tb_ALU_32.vhd
-------------------------------------------------------------------------
-- NOTE:
-------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.std_logic_textio.all;  -- For logic types I/O
-- use IEEE.numeric_std.all;       -- For to_stdlogicvector() function
library std;
use std.env.all;                -- For hierarchical/external signals
use std.textio.all;             -- For basic I/O
use ieee.numeric_std.all;
library work;
    use work.MIPS_types.all;

entity tb_ALU_32 is
	generic(clock_period: 	time    := 20 ns;   -- Generic for half of the clock cycle period
            N: 				integer	:= 32;
			A: 				integer := 5);
end tb_ALU_32;

architecture structural of tb_ALU_32 is

	component ALU_32 is
        port
		(
			i_ALU_control:  in  std_logic_vector(03 downto 00); -- will connect to output of ALU control circuit, bits[3:2] are i_A_inv and i_B_twos_comp, bits[1:0] are ALUOp
	
			i_A:			in  bus_32;
			i_B:			in  bus_32;
	
			o_ALU_result: 	out bus_32;
			o_zero_result:	out std_logic;
			o_overflow:     out std_logic
		);
	end component;
	

    signal s_CLK    		: std_logic := '0';		-- Set signal for clock
    
	signal s_iALU_control	: std_logic_vector(03 downto 00);
	signal s_iA				: bus_32;
	signal s_iB				: bus_32;
	signal s_oALU_result	: bus_32;
	signal s_ozero_result	: std_logic;
	signal s_ooverflow		: std_logic;

	signal s_ONEs 			: std_logic_vector(N - 1 downto 0) := (others => '1');
	signal s_ZEROs 			: std_logic_vector(N - 1 downto 0) := (others => '0');

begin
	
    --------------------------------------------------
	-- Wiring
	--------------------------------------------------

    DUT0: ALU_32 
    port map(
		i_ALU_control	=> s_iALU_control,
		i_A				=> s_iA,
		i_B				=> s_iB,
		o_ALU_result	=> s_oALU_result,
		o_zero_result	=> s_ozero_result,
		o_overflow		=> s_ooverflow
    );


    --------------------------------------------------
	-- Processes
	--------------------------------------------------

    P_CLK: process	-- Process to setup the clock for the test bench
  	begin
		s_CLK <= '1';         	-- clock starts at 1
		wait for clock_period / 2; 	-- after half a cycle
		s_CLK <= '0';         	-- clock becomes a 0 (negative edge)
		wait for clock_period / 2; 	-- after half a cycle, process begins evaluation again
  	end process;

    P_TEST_CASES: process
	begin
		-- Reset
		-- s_ireset	<= '1';
		wait for clock_period * 0.25;
		
		--------------------------------------------------
		-- AND control: 0000 --
		--------------------------------------------------
		-- Test: 
		s_iALU_control 	<= "0000";
		s_iA			<= "10101010101010101010101010101010";
		s_iB			<= "01010101010101010101010101010101";
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "0000";
		s_iA			<= s_ONEs;
		s_iB			<= s_ZEROs;
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "0000";
		s_iA			<= s_ONEs;
		s_iB			<= s_ONEs;
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "0000";
		s_iA			<= s_ZEROs;
		s_iB			<= s_ZEROs;
		wait for clock_period * 0.25;

		
		--------------------------------------------------
		-- OR control: 0001 --
		--------------------------------------------------
		-- Test: 
		s_iALU_control 	<= "0001";
		s_iA			<= "10101010101010101010101010101010";
		s_iB			<= "01010101010101010101010101010101";
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "0001";
		s_iA			<= s_ONEs;
		s_iB			<= s_ZEROs;
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "0001";
		s_iA			<= s_ONEs;
		s_iB			<= s_ONEs;
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "0001";
		s_iA			<= s_ZEROs;
		s_iB			<= s_ZEROs;
		wait for clock_period * 0.25;

		
		--------------------------------------------------
		-- ADD control: 0010 --
		--------------------------------------------------
		-- Test: 
		s_iALU_control 	<= "0010";
		s_iA			<= "10101010101010101010101010101010";
		s_iB			<= "01010101010101010101010101010101";
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "0010";
		s_iA			<= s_ONEs;
		s_iB			<= s_ZEROs;
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "0010";
		s_iA			<= "11111111101100111011010011000000"; 	-- -5,000,000
		s_iB			<= "11111111110100100011100101000000"; 	-- -3,000,000
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "0010";
		s_iA			<= "11111111101100111011010011000000"; 	-- -5,000,000
		s_iB			<= "00000000001011011100011011000000"; 	-- 3,000,000
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "0010";
		s_iA			<= (0 => '1', others => '0');			-- 0x0000.0001
		s_iB			<= s_ONEs; 								-- 0xFFFF.FFFF
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "0010";
		s_iA			<= s_ONEs; 								-- 0xFFFF.FFFF
		s_iB			<= s_ONEs; 								-- 0xFFFF.FFFF
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "0010";
		s_iA			<= (0 => '1', others => '0');			-- 0x0000.0001
		s_iB			<= (0 => '1', others => '0'); 			-- 0x0000.0001
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "0010";
		s_iA			<= s_ZEROs; 							-- 0xFFFF.FFFF
		s_iB			<= s_ZEROs; 							-- 0x0000.0001
		wait for clock_period * 0.25;
		

		--------------------------------------------------
		-- SUB control: 0110 --
		--------------------------------------------------
		-- Test: 
		s_iALU_control 	<= "0110";
		s_iA			<= "10101010101010101010101010101010";
		s_iB			<= "01010101010101010101010101010101";
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "0110";
		s_iA			<= s_ONEs;
		s_iB			<= s_ZEROs;
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "0110";
		s_iA			<= "11111111101100111011010011000000"; 	-- -5,000,000
		s_iB			<= "11111111110100100011100101000000"; 	-- -3,000,000
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "0110";
		s_iA			<= "11111111101100111011010011000000"; 	-- -5,000,000
		s_iB			<= "00000000001011011100011011000000"; 	-- 3,000,000
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "0110";
		s_iA			<= (0 => '1', others => '0');			-- 0x0000.0001
		s_iB			<= s_ONEs; 								-- 0xFFFF.FFFF
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "0110";
		s_iA			<= s_ONEs; 								-- 0xFFFF.FFFF
		s_iB			<= s_ONEs; 								-- 0xFFFF.FFFF
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "0110";
		s_iA			<= (0 => '1', others => '0');			-- 0x0000.0001
		s_iB			<= (0 => '1', others => '0'); 			-- 0x0000.0001
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "0110";
		s_iA			<= s_ZEROs; 							-- 0xFFFF.FFFF
		s_iB			<= s_ZEROs; 							-- 0x0000.0000
		wait for clock_period * 0.25;
		

		--------------------------------------------------
		-- SLT control: 0111 --
		--------------------------------------------------
		-- Test: 
		s_iALU_control 	<= "0111";
		s_iA			<= "11111111101100111011010011000000"; 	-- -5,000,000
		s_iB			<= "11111111110100100011100101000000"; 	-- -3,000,000
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "0111";
		s_iA			<= "00000000010011000100101101000000"; 	-- 5,000,000
		s_iB			<= "00000000001011011100011011000000"; 	-- 3,000,000
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "0111";
		s_iA			<= s_ONEs;								-- -1
		s_iB			<= s_ZEROs;								-- 0
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "0111";
		s_iA			<= s_ZEROs;								-- 0
		s_iB			<= s_ONEs;								-- -1
		wait for clock_period * 0.25;

		
		--------------------------------------------------
		-- NOR control: 1100 --
		--------------------------------------------------
		-- Test: 
		s_iALU_control 	<= "1100";
		s_iA			<= "10101010101010101010101010101010";
		s_iB			<= "01010101010101010101010101010101";
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "1100";
		s_iA			<= (0 => '1', others => '0');			-- 0x0000.0001
		s_iB			<= s_ZEROs; 							-- 0x0000.0000
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "1100";
		s_iA			<= s_ONEs;								-- -1
		s_iB			<= s_ZEROs;								-- 0
		wait for clock_period * 0.25;
		-- Test: 
		s_iALU_control 	<= "1100";
		s_iA			<= s_ZEROs;								-- 0
		s_iB			<= s_ONEs;								-- -1
		wait for clock_period * 0.25;
		
		
	end process;

end structural;
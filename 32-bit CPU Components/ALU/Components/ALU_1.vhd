library IEEE;
	use IEEE.std_logic_1164.all;

    
-- Reece Dodge and Johnathan Tan
-- 
--      ___    __    __  __            ___
--     /   |  / /   / / / /           <  /
--    / /| | / /   / / / /            / / 
--   / ___ |/ /___/ /_/ /            / /  
--  /_/  |_/_____/\____/  ______    /_/   
--                       /_____/          
--------------------------------------------------------------------------------
-- Description --
--------------------------------------------------------------------------------
-- This is a 1-bit ALU to be used for the lower 31 bits of our ALU.
-- 
-- Functions:
-- AND - 00 00
-- OR  - 00 01
-- ADD - 00 10
-- SUB - 01 10
-- SLT - 01 11
-- NOR - 11 00 AND(~A, ~B) demorgans -> NOR(A, B)
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- Top-level Entity Definition --
--------------------------------------------------------------------------------
entity ALU_1 is
    port
    (
        i_carry_in:   in  std_logic;

        i_A: 		  in  std_logic;
        i_B: 		  in  std_logic;

        i_less:       in  std_logic; -- only used for slt, upper 31 bits of ALU_32 will be tied to zero

        i_A_inv:      in  std_logic;                      -- control
        i_B_inv:      in  std_logic;                      -- control
        i_ALUOp:      in  std_logic_vector(01 downto 00); -- control: 000=AND, 001=OR, 010=ADD, 011=SLT, 100=XOR

        o_ALU_result: out std_logic;

        o_carry_out:  out std_logic
    );
end ALU_1;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- Architecture Definitition --
--------------------------------------------------------------------------------
architecture structural of ALU_1 is
	--------------------------------------------------------------------------------
	-- Component Definitions --
	--------------------------------------------------------------------------------
    component full_adder is
        port
        (
            i_A: 		 in  std_logic;
            i_B: 		 in  std_logic;
            i_carry_in:  in  std_logic;

            o_sum: 		 out std_logic;
            o_carry_out: out std_logic
        );
	end component;

    component mux_2t1 is
		port
		(
			i_S:  in  std_logic;

			i_D0: in  std_logic;
			i_D1: in  std_logic;

			o_O:  out std_logic
		);
	end component;

    component invg is
        port
        (
            i_A: in  std_logic;

            o_F: out std_logic
        );
    end component;

    component andg2 is
        port
        (
            i_A: in  std_logic;
            i_B: in  std_logic;

            o_F: out std_logic
        );
    end component;

    component org2 is
        port
        (
            i_A: in  std_logic;
            i_B: in  std_logic;

            o_F: out std_logic
        );
    end component;

    component xorg2 is
        port
        (
            i_A : in std_logic;
            i_B : in std_logic;

            o_F : out std_logic
        );
    end component;

    component mux_4t1 is
        port
        (
            i_S: in  std_logic_vector(01 downto 00);

            i_D: in  std_logic_vector(03 downto 00);

            o_O: out std_logic
        );
    end component;
	--------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Internal Signal Definitions --
    --------------------------------------------------------------------------------
    signal s_A_inv:         std_logic;
    signal s_B_inv:         std_logic;

    signal s_A:             std_logic;  -- either A or ~A
    signal s_B:             std_logic;  -- either B or ~B

    signal s_AND_result:    std_logic;
    signal s_OR_result:     std_logic;
    signal s_ADD_result:    std_logic;
    --------------------------------------------------------------------------------

begin
    --------------------------------------------------------------------------------
    -- Logic Level 00 --
    -- Inverted operands 
    --------------------------------------------------------------------------------
    inverter_i_A: invg
        port map
        (
            i_A => i_A,

            o_F => s_A_inv
        );

    inverter_i_B: invg
        port map
        (
            i_A => i_B,

            o_F => s_B_inv
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Logic Level 01 --
    -- Selecting normal or complimented operands 
    --------------------------------------------------------------------------------
    mux_A_or_A_inv: mux_2t1
        port map
        (
            i_S  => i_A_inv, -- i_A inversion control

            i_D0 => i_A,
            i_D1 => s_A_inv,

            o_O  => s_A
        );

    mux_B_or_B_inv: mux_2t1
        port map
        (
            i_S  => i_B_inv, -- i_B inversion control

            i_D0 => i_B,
            i_D1 => s_B_inv,

            o_O  => s_B
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Logic Level 02 --
    -- AND, OR, and full_adder with selected operands
    --------------------------------------------------------------------------------
    and_A_AND_B: andg2 
        port map
        (
            i_A => s_A,
            i_B => s_B,

            o_F => s_AND_result
        );

    or_A_OR_B: org2
        port map
        (
            i_A => s_A,
            i_B => s_B,

            o_F => s_OR_result
        );

    adder_A_plus_B: full_adder
        port map
        (
            i_carry_in  => i_carry_in,   -- top-level input

            i_A         => s_A,
            i_B         => s_B,

            o_sum       => s_ADD_result,

            o_carry_out => o_carry_out   -- top-level output
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Logic Level 03 --
    -- Arithmetic/logic results multiplexed together
    -- ALUOp[1:0] will select the following:
    -- 00: AND result
    -- 01: OR result
    -- 10: ADD result
    -- 11: SLT result
    -- 00: XOR result
    --------------------------------------------------------------------------------
    ALU_results_multiplexer: mux_4t1
        port map
        (
            i_S     => i_ALUOp,

            i_D(0) => s_AND_result,
            i_D(1) => s_OR_result,
            i_D(2) => s_ADD_result,
            i_D(3) => i_less,

            o_O     => o_ALU_result
        );
    --------------------------------------------------------------------------------
end structural;
--------------------------------------------------------------------------------
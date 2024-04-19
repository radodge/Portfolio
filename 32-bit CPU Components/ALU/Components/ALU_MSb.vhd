library IEEE;
	use IEEE.std_logic_1164.all;


-- Reece Dodge and Johnathan Tan
-- 
--      ___    __    __  __            __  ________ __  
--     /   |  / /   / / / /           /  |/  / ___// /_ 
--    / /| | / /   / / / /           / /|_/ /\__ \/ __ \
--   / ___ |/ /___/ /_/ /           / /  / /___/ / /_/ /
--  /_/  |_/_____/\____/  ______   /_/  /_//____/_.___/ 
--                       /_____/                        
--------------------------------------------------------------------------------
-- Description --
--------------------------------------------------------------------------------
-- This is a 1-bit ALU to be used for the sign bit of our ALU.
-- Since only the sign bit is used to calulate overflow, overflow is built into
-- this component.
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
entity ALU_MSb is
    port
    (
        i_carry_in:   in  std_logic;

        i_A: 		  in  std_logic;
        i_B: 		  in  std_logic;

        i_less:       in  std_logic; -- only used for slt instructions, upper 31 'less' bits of ALU_32 will be tied to zero

        i_A_inv:      in  std_logic;                      -- control
        i_B_inv:      in  std_logic;                      -- control
        i_ALUOp:      in  std_logic_vector(01 downto 00); -- control: 00=AND, 01=OR, 10=ADD, 11=SLT

        o_ALU_result: out std_logic;

        o_set:        out std_logic; -- will be wired to LSb of ALU's 'less' input

        o_overflow:   out std_logic
    );
end ALU_MSb;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- Architecture Definitition --
--------------------------------------------------------------------------------
architecture structural of ALU_MSb is
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

    component mux_4t1 is
        port
        (
            i_S: in  std_logic_vector(01 downto 00);

            i_D: in  std_logic_vector(03 downto 00);

            o_O: out std_logic
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

    component xnor_2 is
        port
        (
            i_A : in std_logic;
            i_B : in std_logic;

            o_F : out std_logic
        );
    end component;
	--------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Internal Signal Definitions --
    --------------------------------------------------------------------------------
    signal s_A_inv:         std_logic;
    signal s_B_inv:         std_logic;

    signal s_A:             std_logic; -- either A or ~A
    signal s_B:             std_logic; -- either B or ~B

    signal s_AND_result:    std_logic;
    signal s_OR_result:     std_logic;
    signal s_ADD_result:    std_logic;

    signal s_carry_out:     std_logic;


    -- Overflow Circuitry --
    signal s_add_check:             std_logic;
    signal s_carry_XOR:             std_logic;

    signal s_signed_add_overflow:   std_logic;
    

    signal s_A_XOR_B:               std_logic;
    signal s_result_XNOR_B:         std_logic;
    signal s_signed_sub_overflow_1: std_logic;

    signal s_signed_sub_overflow:   std_logic;


    signal s_overflow:              std_logic;
    --------------------------------------------------------------------------------


begin
    --------------------------------------------------------------------------------
    -- Logic Level 00 --
    -- Selecting normal or complimented operands
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

            o_carry_out => s_carry_out
        );
    --------------------------------------------------------------------------------
    
    o_set <= s_ADD_result; -- making the set bit available as a top-level output

    --------------------------------------------------------------------------------
    -- Logic Level 03 --
    -- Arithmetic/logic results multiplexed together
    -- ALUOp[1:0] will select the following:
    -- 00: AND result
    -- 01: OR result
    -- 10: ADD result
    -- 11: SLT result
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


--------------------------------------------------------------------------------
--     ____                              ____   __                    
--    / __ \   _   __   ___     _____   / __/  / /  ____     _      __
--   / / / /  | | / /  / _ \   / ___/  / /_   / /  / __ \   | | /| / /
--  / /_/ /   | |/ /  /  __/  / /     / __/  / /  / /_/ /   | |/ |/ / 
--  \____/    |___/   \___/  /_/     /_/    /_/   \____/    |__/|__/  
--                                                                    
-- OVERFLOW DETECTION --
--------------------------------------------------------------------------------
    --------------------------------------------------------------------------------
    -- Signed Addition Overflow --
    -- (Cin XOR Cout) AND (NOT(i_B_inv))
    -- 
    -- For signed addition: overflow occurs when s_A(31) = s_B(31)
    -- and s_ADD_result = not(sign of operands). This can be detected by checking the carry-in 
    -- and carry-out of the sign bit. I'll also gate it with not(i_B_inv) so we are
    -- detecting addition overflow at the correct time, because we're adding when i_B_inv
    -- is 0.
    --------------------------------------------------------------------------------
    inverter_add_check: invg
        port map
        (
            i_A => i_B_inv,

            o_F => s_add_check -- if the subtraction signal is 0, this will allow overflow to pass thru via AND gate
        );
    
    C_in_C_Cout_XOR: xorg2
        port map
        (
            i_A => i_carry_in,
            i_B => s_carry_out,

            o_F => s_carry_XOR
        );
    
    and_signed_add_overflow: andg2
        port map
        (
            i_A => s_add_check,
            i_B => s_carry_XOR,

            o_F => s_signed_add_overflow
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Signed Subtraction Overflow --
    -- Overflow occurs when the sign of the two operands is different, but the sign
    -- of the result is the same as the sign of the second operand.
    -- (i_A[31] XOR i_B[31]) AND (s_ADD_result XNOR i_B[31]) = overflow
    --------------------------------------------------------------------------------
    operand_sign_XOR: xorg2 -- checks to see if the operand signs are different
        port map
        (
            i_A => i_A,
            i_B => i_B,

            o_F => s_A_XOR_B
        );

    result_XNOR_B: xnor_2 -- compares sum and sign of second operand to see if they match
        port map
        (
            i_A => s_ADD_result,
            i_B => i_B,

            o_F => s_result_XNOR_B
        );
    
    and_signed_sub_overflow_0: andg2 -- compares previous 2 comparisons
        port map
        (
            i_A => s_A_XOR_B,
            i_B => s_result_XNOR_B,

            o_F => s_signed_sub_overflow_1
        );

    and_signed_sub_overflow_1: andg2 -- gated with the subtraction signal
        port map
        (
            i_A => i_B_inv,
            i_B => s_signed_sub_overflow_1,

            o_F => s_signed_sub_overflow
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Combining the overflow signals with OR --
    -- Subsequently AND with add/sub signal --
    --------------------------------------------------------------------------------
    or_overflow_output: org2
        port map
        (
            i_A => s_signed_add_overflow,
            i_B => s_signed_sub_overflow,

            o_F => s_overflow
        );
    

    final_check: andg2
        port map
        (
            i_A => i_ALUOp(01), -- we only want to produce an overflow signal when we're adding or subtracting
            i_B => s_overflow,

            o_F => o_overflow   -- final top-level overflow output
        );
    --------------------------------------------------------------------------------
end structural;
--------------------------------------------------------------------------------
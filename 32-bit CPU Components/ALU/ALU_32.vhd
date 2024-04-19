library IEEE;
    use IEEE.std_logic_1164.all;
library work;
    use work.MIPS_types.all;


-- Reece Dodge and Johnathan Tan
-- 
-- _____/\\\\\\\\\_____/\\\______________/\\\________/\\\_______________________/\\\\\\\\\\_____/\\\\\\\\\_____        
--  ___/\\\\\\\\\\\\\__\/\\\_____________\/\\\_______\/\\\_____________________/\\\///////\\\__/\\\///////\\\___       
--   __/\\\/////////\\\_\/\\\_____________\/\\\_______\/\\\____________________\///______/\\\__\///______\//\\\__      
--    _\/\\\_______\/\\\_\/\\\_____________\/\\\_______\/\\\___________________________/\\\//_____________/\\\/___     
--     _\/\\\\\\\\\\\\\\\_\/\\\_____________\/\\\_______\/\\\__________________________\////\\\_________/\\\//_____    
--      _\/\\\/////////\\\_\/\\\_____________\/\\\_______\/\\\_____________________________\//\\\_____/\\\//________   
--       _\/\\\_______\/\\\_\/\\\_____________\//\\\______/\\\_____________________/\\\______/\\\____/\\\/___________  
--        _\/\\\_______\/\\\_\/\\\\\\\\\\\\\\\__\///\\\\\\\\\/____/\\\\\\\\\\\\\\\_\///\\\\\\\\\/____/\\\\\\\\\\\\\\\_ 
--         _\///________\///__\///////////////_____\/////////_____\///////////////____\/////////_____\///////////////__
--------------------------------------------------------------------------------
-- Description --
--------------------------------------------------------------------------------
-- This is a 32-bit ALU with built-in overflow detection within the MSb.
-- 
-- Operations:
-- AND - 00 00
-- OR  - 00 01
-- ADD - 00 10
-- SUB - 01 10
-- SLT - 01 11
-- NOR - 11 00 AND(~A, ~B) demorgans -> NOR(A, B)
-- 
-- SLL ???
-- SRL ???
-- SRA ???
-- 
-- XOR ???
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- Top-level Entity Definition --
--------------------------------------------------------------------------------
entity ALU_32 is
	port
    (
        i_ALU_control:  in  std_logic_vector(5 downto 0); -- will connect to output of ALU control circuit, bits[3:2] are i_A_inv and i_B_twos_comp, bits[1:0] are ALUOp

        i_A:			in  bus_32;
        i_B:			in  bus_32;

        i_shamt:        in  std_logic_vector(4 downto 0);

		o_ALU_output: 	out bus_32;
		o_zero_result:	out std_logic;
        o_overflow:     out std_logic
	);
end ALU_32;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- Architecture Definitition --
--------------------------------------------------------------------------------
architecture mixed of ALU_32 is
	--------------------------------------------------------------------------------
	-- Component Definitions --
	--------------------------------------------------------------------------------
    component ALU_1 is
        port
        (
            i_carry_in:    in  std_logic;

            i_A: 		   in  std_logic;
            i_B: 		   in  std_logic;

            i_less:        in  std_logic; -- only used for slt, upper 31 bits will be tied to zero

            i_A_inv:       in  std_logic;                      -- control
            i_B_inv:       in  std_logic;                      -- control, wired to first carry_in and each i_B_inv control signal
            i_ALUOp:       in  std_logic_vector(01 downto 00); -- control: 00=AND, 01=OR, 10=ADD, 11=SLT

            o_ALU_result:  out std_logic;

            o_carry_out:   out std_logic
        );
    end component;

    component ALU_MSb is
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
    
            o_overflow:  out std_logic
        );
    end component;

    component shifter_32 is
        port
        (
            i_data:		            in bus_32;	                        -- data to be shifted, A or B
            
            i_direction_select:     in std_logic;                       -- 0=shift right, 1=shift left
            i_shift_type_select:    in std_logic;                       -- 0=logical, 1=arithmetic
    
            i_shamt:	            in std_logic_vector(04 downto 00);  -- shift amount
    
            o_shifted_data:	        out bus_32			                -- shifted output
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

    component or_32 is
        port
        (
            i_A: in  bus_32;

            o_F: out std_logic
        );
    end component;

    component invg is
        port
        (
            i_A: in std_logic;

            o_F: out std_logic
        );
    end component;
	--------------------------------------------------------------------------------


	--------------------------------------------------------------------------------
	-- Internal Signal Definitions --
	-------------------------------------------------------------------------------- 
    signal s_carry_bits:        std_logic_vector(30 downto 00); -- linkage for internal carries, there are only 31 b/c final carry_out is used for overflow calculation
    signal s_set:               std_logic;                      -- will be tied directly to ALU_bit_31's pre-multiplexed adder result

    signal s_ALU_control:       std_logic_vector(03 downto 00); -- only 4 relevant signals for the ALU
    signal s_shift_direction:   std_logic;
    signal s_shift_type:        std_logic;

    signal s_ALU_result:        bus_32;
    signal s_shifter_result:    bus_32;
    signal s_XOR_result:        bus_32;

    signal s_ALU_output:        bus_32;

    signal s_ALU_output_OR:     std_logic;                      -- this is the output of the entire ALU_result OR'd together, this will be inverted to complete desired NOR
    --------------------------------------------------------------------------------
begin
    --------------------------------------------------------------------------------
    -- ALU Control --
    --------------------------------------------------------------------------------
    s_ALU_control <= i_ALU_control(5 downto 4) & i_ALU_control(1 downto 0);

    s_shift_direction <=
        '1' when (i_ALU_control(3 downto 0) = "0101") else	-- 0101 == sll
        '0' when (i_ALU_control(3 downto 0) = "0110") else
        '0' when (i_ALU_control(3 downto 0) = "0111");
    s_shift_type <=
        '0' when (i_ALU_control(3 downto 0) = "0110") else	-- 0110 == srl
        '1' when (i_ALU_control(3 downto 0) = "0111") else	-- 0111 == sra
        '0' when (i_ALU_control(3 downto 0) = "0101");		-- Just so it is not undefined
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Least Significant Bit --
    --------------------------------------------------------------------------------
    ALU_bit_0: ALU_1
        port map
        (
            i_carry_in   => s_ALU_control(02),           -- this is the i_B two's compliment input signal, this effectively adds 1 to the inverted signal

            i_A          => i_A(00),
            i_B          => i_B(00),

            i_less       => s_set,

            i_A_inv      => s_ALU_control(03),           -- i_A inverter mux control signal
            i_B_inv      => s_ALU_control(02),           -- i_B two's compliment
            i_ALUOp      => s_ALU_control(01 downto 00), -- ALUOp

            o_ALU_result => s_ALU_result(00),

            o_carry_out  => s_carry_bits(00)
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Bits [1:30] --
    --------------------------------------------------------------------------------
    -- Generate 30 ALU_1 components
    G_ALU_bit_i: for i in 01 to 30
		generate ALU_i: ALU_1
            port map
            (
                i_carry_in   => s_carry_bits(i - 1),         -- takes the carry_out from the previous bit

                i_A          => i_A(i),
                i_B          => i_B(i),

                i_less       => '0',

                i_A_inv      => s_ALU_control(03),           -- i_A inverter mux control signal
                i_B_inv      => s_ALU_control(02),           -- i_B two's compliment
                i_ALUOp      => s_ALU_control(01 downto 00), -- ALUOp

                o_ALU_result => s_ALU_result(i),

                o_carry_out  => s_carry_bits(i)
            );
        end generate G_ALU_bit_i;
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Most Significant Bit --
    -- Built-in overflow detection
    --------------------------------------------------------------------------------
    ALU_bit_31: ALU_MSb
        port map
        (
            i_carry_in   => s_carry_bits(30),

            i_A          => i_A(31),
            i_B          => i_B(31),

            i_less       => '0',

            i_A_inv      => s_ALU_control(03),           -- i_A inverter mux control signal
            i_B_inv      => s_ALU_control(02),           -- i_B two's compliment
            i_ALUOp      => s_ALU_control(01 downto 00), -- ALUOp

            o_ALU_result => s_ALU_result(31),

            o_set        => s_set,                       -- this signal is tied to the LSb of the ALU, so 32 bit ALU output will be 0x00000001 if a < b

            o_overflow   => o_overflow
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Shifter and XOR --
    --------------------------------------------------------------------------------
    shifter_component: shifter_32
        port map
        (
            i_data              => i_B,

            i_direction_select  => s_shift_direction,
            i_shift_type_select => s_shift_type,

            i_shamt             => i_shamt,

            o_shifted_data      => s_shifter_result
        );

    G_xor_i: for i in 31 downto 00
        generate xor_i: xorg2
            port map
            (
                i_A =>  i_A(i),
                i_B =>  i_B(i),

                o_F =>  s_XOR_result(i)
            );
        end generate G_xor_i;
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- muxing action
    --------------------------------------------------------------------------------
    s_ALU_output <=
		s_ALU_result        when (i_ALU_control(3 downto 0) = "0000") else
		s_ALU_result        when (i_ALU_control(3 downto 0) = "0001") else
		s_ALU_result        when (i_ALU_control(3 downto 0) = "0010") else
		s_ALU_result        when (i_ALU_control(3 downto 0) = "0011") else
		s_ALU_result        when (i_ALU_control(3 downto 0) = "1000") else
		s_XOR_result        when (i_ALU_control(3 downto 0) = "0100") else
		s_shifter_result    when (i_ALU_control(3 downto 0) = "0101") else
		s_shifter_result    when (i_ALU_control(3 downto 0) = "0110") else
		s_shifter_result    when (i_ALU_control(3 downto 0) = "0111");
    --------------------------------------------------------------------------------

    o_ALU_output <= s_ALU_output; -- making the final output available as a top-level input

    --------------------------------------------------------------------------------
    -- Zero-result NOR Gate --
    -- o_zero_result top-level output will be set when all 32 bits of the ALU output
    -- are '0'
    --------------------------------------------------------------------------------
    OR_zero_result: or_32
        port map
        (
            i_A => s_ALU_output,

            o_F => s_ALU_output_OR
        );

    NOT_zero_result: invg
        port map
        (
            i_A => s_ALU_output_OR,

            o_F => o_zero_result
        );
    --------------------------------------------------------------------------------
end mixed;
--------------------------------------------------------------------------------
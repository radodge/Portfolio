library IEEE;
	use IEEE.std_logic_1164.all;
library work;
    use work.MIPS_types.all;
--------------------------------------------------------------------------------
--       _______. __    __   __   _______ .___________. _______ .______      
--      /       ||  |  |  | |  | |   ____||           ||   ____||   _  \     
--     |   (----`|  |__|  | |  | |  |__   `---|  |----`|  |__   |  |_)  |    
--      \   \    |   __   | |  | |   __|      |  |     |   __|  |      /     
--  .----)   |   |  |  |  | |  | |  |         |  |     |  |____ |  |\  \----.
--  |_______/    |__|  |__| |__| |__|         |__|     |_______|| _| `._____|
--                                                                           
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- Top-level Entity Definition --
--------------------------------------------------------------------------------
entity shifter_32 is
    port
    (
        i_data:		            in bus_32;	                        -- data to be shifted, A or B
        
        i_direction_select:     in std_logic;                       -- 0=shift right, 1=shift left
        i_shift_type_select:    in std_logic;                       -- 0=logical, 1=arithmetic

		i_shamt:	            in std_logic_vector(04 downto 00);  -- shift amount

		o_shifted_data:	        out bus_32			                -- shifted output
    );
end shifter_32;
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- Architecture Definitition --
--------------------------------------------------------------------------------
architecture structural of shifter_32 is
    --------------------------------------------------------------------------------
    -- Component Definitions
    --------------------------------------------------------------------------------
    component mux_2t1_32 is
        port
        (
            i_S:  in  std_logic;
            i_D0: in  bus_32;
            i_D1: in  bus_32;

            o_O:  out bus_32
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

    component bit_reversal_32 is
        port
        (
            i_input:    in  bus_32;
    
            o_output:   out bus_32
        );
    end component;
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
	-- Internal Signal Definitions --
	--------------------------------------------------------------------------------
    signal s_left_data:         bus_32;
    signal s_data:              bus_32;

    signal s_shift_bit:         std_logic;

    signal s_shift_1_bit:       bus_32;
    signal s_shift_2_bits:      bus_32;
    signal s_shift_4_bits:      bus_32;
    signal s_shift_8_bits:      bus_32;
    signal s_shift_16_bits:     bus_32;


    signal s_shift_L0_output:   bus_32;
    signal s_shift_L1_output:   bus_32;
    signal s_shift_L2_output:   bus_32;
    signal s_shift_L3_output:   bus_32;
    signal s_shift_L4_output:   bus_32;

    signal s_left_output:    bus_32;
    --------------------------------------------------------------------------------
begin
    --------------------------------------------------------------------------------
    -- Direction Select and Logical/Arithmetic Select --
    --------------------------------------------------------------------------------
    data_reversal_0: bit_reversal_32
        port map
        (
            i_input     => i_data,

            o_output    => s_left_data
        );

    direction_select_mux: mux_2t1_32
        port map
        (
            i_S     => i_direction_select, 

            i_D0    => i_data,              -- shifting right
            i_D1    => s_left_data,         -- shifting left

            o_O     => s_data
        );

    shift_type_mux: mux_2t1
        port map
        (
            i_S     => i_shift_type_select, -- 0=logical 1=arithmetic

            i_D0    => '0',                 -- logical
            i_D1    => i_data(31),          -- arithmetic

            o_O     => s_shift_bit
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Shift Level 0: Shift by 1 bit --
    -- Output selected by bit 0 of shamt
    --------------------------------------------------------------------------------
    s_shift_1_bit(31) <= s_shift_bit;

    s_shift_1_bit(30 downto 00) <= s_data(31 downto 01); -- building remaining bits of the shifted output

    shift_1_bit_mux: mux_2t1_32
        port map
        (
            i_S     => i_shamt(0),

            i_D0    => s_data,                 -- no shift
            i_D1    => s_shift_1_bit,          -- shifted by 1 bit

            o_O     => s_shift_L0_output
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Shift Level 1: Shift by 2 bits --
    -- Output selected by bit 1 of shamt
    --------------------------------------------------------------------------------
    G_upper_2_bits: for i in 31 downto 30
        generate 

            s_shift_2_bits(i) <= s_shift_bit;

        end generate G_upper_2_bits;

    s_shift_2_bits(29 downto 00) <= s_shift_L0_output(31 downto 2); -- building remaining bits of the shifted output

    shift_2_bits_mux: mux_2t1_32
        port map
        (
            i_S     => i_shamt(1),

            i_D0    => s_shift_L0_output,   -- no shift
            i_D1    => s_shift_2_bits,      -- shifted by 2 bits

            o_O     => s_shift_L1_output
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Shift Level 2: Shift by 4 bits --
    -- Output selected by bit 2 of shamt
    --------------------------------------------------------------------------------
    G_upper_4_bits: for i in 31 downto 28
        generate

            s_shift_4_bits(i) <= s_shift_bit;

        end generate G_upper_4_bits;

    s_shift_4_bits(27 downto 00) <= s_shift_L1_output(31 downto 4); -- building remaining bits of the shifted output

    shift_4_bits_mux: mux_2t1_32
        port map
        (
            i_S     => i_shamt(2),

            i_D0    => s_shift_L1_output,   -- no shift
            i_D1    => s_shift_4_bits,      -- shifted by 4 bits

            o_O     => s_shift_L2_output
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Shift Level 3: Shift by 8 bits --
    -- Output selected by bit 3 of shamt
    --------------------------------------------------------------------------------
    G_upper_8_bits: for i in 31 downto 24
        generate

            s_shift_8_bits(i) <= s_shift_bit;

        end generate G_upper_8_bits;

    s_shift_8_bits(23 downto 00) <= s_shift_L2_output(31 downto 8); -- building remaining bits of the shifted output

    shift_8_bits_mux: mux_2t1_32
        port map
        (
            i_S     => i_shamt(3),

            i_D0    => s_shift_L2_output,   -- no shift
            i_D1    => s_shift_8_bits,      -- shifted by 8 bits

            o_O     => s_shift_L3_output
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Shift Level 4: Shift by 16 bits --
    -- Output selected by bit 4 of shamt
    --------------------------------------------------------------------------------
    G_upper_16_bits: for i in 31 downto 16
        generate

            s_shift_16_bits(i) <= s_shift_bit;

        end generate G_upper_16_bits;

    s_shift_16_bits(15 downto 00) <= s_shift_L3_output(31 downto 16); -- building remaining bits of the shifted output

    shift_16_bits_mux: mux_2t1_32
        port map
        (
            i_S     => i_shamt(4),

            i_D0    => s_shift_L3_output,   -- no shift
            i_D1    => s_shift_16_bits,     -- shifted by 16 bits

            o_O     => s_shift_L4_output
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Re-reversing bit order if shifting left --
    --------------------------------------------------------------------------------
    data_reversal_1: bit_reversal_32
        port map
        (
            i_input     => s_shift_L4_output,

            o_output    => s_left_output
        );

    output_direction_mux: mux_2t1_32
        port map
        (
            i_S     => i_direction_select, 

            i_D0    => s_shift_L4_output,   -- shifting right
            i_D1    => s_left_output,       -- shifting left

            o_O     => o_shifted_data       -- top-level output
        );
    --------------------------------------------------------------------------------
end structural;
--------------------------------------------------------------------------------
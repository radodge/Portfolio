library IEEE;
    use IEEE.std_logic_1164.all;

--------------------------------------------------------------------------------
-- This is a structural implementation of a 4t1 multiplexer. I used a structural
-- model to ensure fast operation.
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- Top-level Entity Definition --
--------------------------------------------------------------------------------
entity mux_4t1 is
    port
    (
        i_S: in  std_logic_vector(01 downto 00);

        i_D: in  std_logic_vector(03 downto 00);

        o_O: out std_logic
    );
end mux_4t1;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- Architecture Definition --
--------------------------------------------------------------------------------
architecture structural of mux_4t1 is
    --------------------------------------------------------------------------------
    -- Component Definitions --
    --------------------------------------------------------------------------------
    component invg is
        port
        (
            i_A: in  std_logic;

            o_F: out std_logic
        );
    end component;

    component and_3 is
        port
        (
            i_A: in  std_logic_vector(02 downto 00);

            o_F: out std_logic
        );
    end component;
    
    component or_4 is
        port
        (
            i_A: in  std_logic_vector(03 downto 00);

            o_F: out std_logic
        );
    end component;
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Internal Signal Definitions --
    --------------------------------------------------------------------------------
    signal s_S0_inv: std_logic;
    signal s_S1_inv: std_logic;

    signal s_Y0:     std_logic; -- i_D0 & ~i_S(0) & ~i_s(1) - (00)
    signal s_Y1:     std_logic; -- i_D1 & ~i_S(0) &  i_s(1) - (01)
    signal s_Y2:     std_logic; -- i_D2 &  i_S(0) & ~i_s(1) - (10)
    signal s_Y3:     std_logic; -- i_D3 &  i_S(0) &  i_s(1) - (11)
    --------------------------------------------------------------------------------
begin
    --------------------------------------------------------------------------------
    -- Logic Level 00 --
    -- Inverted select inputs  
    --------------------------------------------------------------------------------
    inverter_S0: invg
        port map
        (
            i_A => i_S(00),

            o_F => s_S0_inv
        );

    inverter_S1: invg
        port map
        (
            i_A => i_S(01),

            o_F => s_S1_inv
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Logic Level 01 --
    -- Select bits &'d with inputs
    --------------------------------------------------------------------------------
    and_signal_Y0: and_3 -- 00
        port map
        (
            i_A(00) => i_D(00),  -- data
            i_A(01) => s_S0_inv, -- select bit 0
            i_A(02) => s_S1_inv, -- select bit 1

            o_F => s_Y0
        );

    and_signal_Y1: and_3 -- 01
        port map
        (
            i_A(00) => i_D(01),  -- data
            i_A(01) => i_S(00),  -- select bit 0
            i_A(02) => s_S1_inv, -- select bit 1

            o_F => s_Y1
        );
    
    and_signal_Y2: and_3 -- 10
        port map
        (
            i_A(00) => i_D(02),  -- data
            i_A(01) => s_S0_inv, -- select bit 0
            i_A(02) => i_S(01),  -- select bit 1

            o_F => s_Y2
        );

    and_signal_Y3: and_3 -- 11
        port map
        (
            i_A(00) => i_D(03),  -- data
            i_A(01) => i_S(00),  -- select bit 0
            i_A(02) => i_S(01),  -- select bit 1

            o_F => s_Y3
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Logic Level 02 --
    -- Internal Signals or'd together
    --------------------------------------------------------------------------------
    or_Y_signals: or_4
        port map
        (
            i_A(00) => s_Y0,
            i_A(01) => s_Y1,
            i_A(02) => s_Y2,
            i_A(03) => s_Y3,

            o_F => o_O
        );
    --------------------------------------------------------------------------------
end structural;
--------------------------------------------------------------------------------
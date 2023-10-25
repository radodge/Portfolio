library IEEE;
    use IEEE.std_logic_1164.all;
library work;
    use work.MIPS_types.all;


--------------------------------------------------------------------------------
-- Top-level Entity Definition --
--------------------------------------------------------------------------------
entity register_32 is
    port
    (
        i_CLK: in  std_logic;
        i_RST: in  std_logic; -- per bit reset
        i_WE : in  std_logic; -- per bit write enable input

        i_D:   in  bus_32; -- per bit data input

        o_Q:   out bus_32 -- per bit data output
    );
end register_32;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- Architecture Definitition --
--------------------------------------------------------------------------------
architecture structure of register_32 is
    --------------------------------------------------------------------------------
    -- Component Definitions --
    --------------------------------------------------------------------------------
    component dffg is
        port
        (
            i_CLK: in  std_logic; -- Clock input
            i_RST: in  std_logic; -- Reset input

            i_WE:  in  std_logic; -- Write enable input
            i_D:   in  std_logic; -- Data value input

            o_Q:   out std_logic -- Data value output
        );
    end component;
    --------------------------------------------------------------------------------

begin

    G_register_32: for i in 31 downto 00
        generate DFF_i: dffg
            port map
            (
                i_CLK => i_CLK, -- all DFFs share same clock
                i_RST => i_RST,
                i_WE  => i_WE, -- Write enable input

                i_D   => i_D(i), -- Data value input

                o_Q   => o_Q(i)  -- Data value output
            );
        end generate G_register_32;

end structure;
--------------------------------------------------------------------------------
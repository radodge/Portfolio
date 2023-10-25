library IEEE;
	use IEEE.std_logic_1164.all;
library work;
    use work.MIPS_types.all;

--------------------------------------------------------------------------------
-- Top-level Entity Definition --
--------------------------------------------------------------------------------
entity or_32 is
  port
    (
        i_A: in  bus_32;

        o_F: out std_logic
    );
end or_32;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- Architecture Definition --
-- Chose dataflow model for maximum performance since it uses purely primitve logic
--------------------------------------------------------------------------------
architecture dataflow of or_32 is
begin

    o_F <=

    i_A(00) or i_A(01) or i_A(02) or i_A(03) or 
    i_A(04) or i_A(05) or i_A(06) or i_A(07) or 
    i_A(08) or i_A(09) or i_A(10) or i_A(11) or 
    i_A(12) or i_A(13) or i_A(14) or i_A(15) or 
    i_A(16) or i_A(17) or i_A(18) or i_A(19) or 
    i_A(20) or i_A(21) or i_A(22) or i_A(23) or 
    i_A(24) or i_A(25) or i_A(26) or i_A(27) or 
    i_A(28) or i_A(29) or i_A(30) or i_A(31);
  
end dataflow;
--------------------------------------------------------------------------------
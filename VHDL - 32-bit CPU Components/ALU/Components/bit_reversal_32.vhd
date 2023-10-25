library ieee;
    use ieee.std_logic_1164.all;
library work;
    use work.MIPS_types.all;

--------------------------------------------------------------------------------
-- Top-level Entity Definition --
--------------------------------------------------------------------------------
entity bit_reversal_32 is
    port
    (
        i_input:    in  bus_32;

        o_output:   out bus_32
    );
end bit_reversal_32;
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- Architecture Definitition --
--------------------------------------------------------------------------------
architecture structural of bit_reversal_32 is
    --------------------------------------------------------------------------------
	-- Internal Signal Definitions --
	--------------------------------------------------------------------------------
    signal s_link: bus_32;
    --------------------------------------------------------------------------------
begin

    s_link <= i_input;

    o_output(31) <= s_link(00);
    o_output(30) <= s_link(01);
    o_output(29) <= s_link(02);
    o_output(28) <= s_link(03);
    o_output(27) <= s_link(04);
    o_output(26) <= s_link(05);
    o_output(25) <= s_link(06);
    o_output(24) <= s_link(07);
    o_output(23) <= s_link(08);
    o_output(22) <= s_link(09);
    o_output(21) <= s_link(10);
    o_output(20) <= s_link(11);
    o_output(19) <= s_link(12);
    o_output(18) <= s_link(13);
    o_output(17) <= s_link(14);
    o_output(16) <= s_link(15);
    o_output(15) <= s_link(16);
    o_output(14) <= s_link(17);
    o_output(13) <= s_link(18);
    o_output(12) <= s_link(19);
    o_output(11) <= s_link(20);
    o_output(10) <= s_link(21);
    o_output(09) <= s_link(22);
    o_output(08) <= s_link(23);
    o_output(07) <= s_link(24);
    o_output(06) <= s_link(25);
    o_output(05) <= s_link(26);
    o_output(04) <= s_link(27);
    o_output(03) <= s_link(28);
    o_output(02) <= s_link(29);
    o_output(01) <= s_link(30);
    o_output(00) <= s_link(31);

end structural;
--------------------------------------------------------------------------------
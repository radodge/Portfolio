library IEEE;
    use IEEE.std_logic_1164.all;
library work;
    use work.MIPS_types.all;

--------------------------------------------------------------------------------
-- Top-level Entity Definition --
--------------------------------------------------------------------------------
entity demux_1t32_32 is
    port
    (
        i_S:    in  reg_address;
        i_D:    in  bus_32;
        
        o_data: out bus_32x32
    );
end demux_1t32_32;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- Architecture Definition --
-- Depending on speed of this implementation, I might switch to a case statement
-- similar to mux_32t1_32
--------------------------------------------------------------------------------
architecture dataflow of demux_1t32_32 is
    begin
        with i_S select o_data <=

            (00 => i_D, others => zeroes_32) when reg_zero,


            (01 => i_D, others => zeroes_32) when   reg_at,


            (02 => i_D, others => zeroes_32) when   reg_v0,
            (03 => i_D, others => zeroes_32) when   reg_v1,

            (04 => i_D, others => zeroes_32) when   reg_a0,
            (05 => i_D, others => zeroes_32) when   reg_a1,
            (06 => i_D, others => zeroes_32) when   reg_a2,
            (07 => i_D, others => zeroes_32) when   reg_a3,


            (08 => i_D, others => zeroes_32) when   reg_t0,
            (09 => i_D, others => zeroes_32) when   reg_t1,
            (10 => i_D, others => zeroes_32) when   reg_t2,
            (11 => i_D, others => zeroes_32) when   reg_t3,

            (12 => i_D, others => zeroes_32) when   reg_t4,
            (13 => i_D, others => zeroes_32) when   reg_t5,
            (14 => i_D, others => zeroes_32) when   reg_t6,
            (15 => i_D, others => zeroes_32) when   reg_t7,


            (16 => i_D, others => zeroes_32) when   reg_s0,
            (17 => i_D, others => zeroes_32) when   reg_s1,
            (18 => i_D, others => zeroes_32) when   reg_s2,
            (19 => i_D, others => zeroes_32) when   reg_s3,

            (20 => i_D, others => zeroes_32) when   reg_s4,
            (21 => i_D, others => zeroes_32) when   reg_s5,
            (22 => i_D, others => zeroes_32) when   reg_s6,
            (23 => i_D, others => zeroes_32) when   reg_s7,


            (24 => i_D, others => zeroes_32) when   reg_t8,
            (25 => i_D, others => zeroes_32) when   reg_t9,


            (26 => i_D, others => zeroes_32) when   reg_k0,
            (27 => i_D, others => zeroes_32) when   reg_k1,


            (28 => i_D, others => zeroes_32) when   reg_gp,

            (29 => i_D, others => zeroes_32) when   reg_sp,

            (30 => i_D, others => zeroes_32) when   reg_fp,

            (31 => i_D, others => zeroes_32) when   reg_ra,


            (others => zeroes_32)            when   others;

end dataflow;
--------------------------------------------------------------------------------

-------------------------------------------------------------------------------
-- Use this block if you dont want the reg address names --
--------------------------------------------------------------------------------
-- architecture dataflow of demux_1t32_32 is
--     begin
--             o_data(00) <= i_D when i_S = "00000" else zeroes_32;
--             o_data(01) <= i_D when i_S = "00001" else zeroes_32;
--             o_data(02) <= i_D when i_S = "00010" else zeroes_32;
--             o_data(03) <= i_D when i_S = "00011" else zeroes_32;

--             o_data(04) <= i_D when i_S = "00100" else zeroes_32;
--             o_data(05) <= i_D when i_S = "00101" else zeroes_32;
--             o_data(06) <= i_D when i_S = "00110" else zeroes_32;
--             o_data(07) <= i_D when i_S = "00111" else zeroes_32;

--             o_data(08) <= i_D when i_S = "01000" else zeroes_32;
--             o_data(09) <= i_D when i_S = "01001" else zeroes_32;
--             o_data(10) <= i_D when i_S = "01010" else zeroes_32;
--             o_data(11) <= i_D when i_S = "01011" else zeroes_32;

--             o_data(12) <= i_D when i_S = "01100" else zeroes_32;
--             o_data(13) <= i_D when i_S = "01101" else zeroes_32;
--             o_data(14) <= i_D when i_S = "01110" else zeroes_32;
--             o_data(15) <= i_D when i_S = "01111" else zeroes_32;

--             o_data(16) <= i_D when i_S = "10000" else zeroes_32;
--             o_data(17) <= i_D when i_S = "10001" else zeroes_32;
--             o_data(18) <= i_D when i_S = "10010" else zeroes_32;
--             o_data(19) <= i_D when i_S = "10011" else zeroes_32;

--             o_data(20) <= i_D when i_S = "10100" else zeroes_32;
--             o_data(21) <= i_D when i_S = "10101" else zeroes_32;
--             o_data(22) <= i_D when i_S = "10110" else zeroes_32;
--             o_data(23) <= i_D when i_S = "10111" else zeroes_32;

--             o_data(24) <= i_D when i_S = "11000" else zeroes_32;
--             o_data(25) <= i_D when i_S = "11001" else zeroes_32;
--             o_data(26) <= i_D when i_S = "11010" else zeroes_32;
--             o_data(27) <= i_D when i_S = "11011" else zeroes_32;

--             o_data(28) <= i_D when i_S = "11100" else zeroes_32;
--             o_data(29) <= i_D when i_S = "11101" else zeroes_32;
--             o_data(30) <= i_D when i_S = "11110" else zeroes_32;
--             o_data(31) <= i_D when i_S = "11111" else zeroes_32;

-- end dataflow;
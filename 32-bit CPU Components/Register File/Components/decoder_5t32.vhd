library IEEE;
    use IEEE.std_logic_1164.all;
library work;
    use work.MIPS_types.all;

    
--------------------------------------------------------------------------------
-- Top-level Entity Definition --
--------------------------------------------------------------------------------
entity decoder_5t32 is
    port
    (
        i_D  : in reg_address;  -- 5 bits wide
        i_En : in std_logic;

        o_F  : out bus_32 -- 32 bits wide
    );
end decoder_5t32;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- Architecture Definitition --
--------------------------------------------------------------------------------
architecture mixed of decoder_5t32 is
    begin
        process (i_En, i_D)
            begin
                if i_En = '1' then
                    case i_D is
                        when "00000" => o_F <= (00 => '1', others => '0');
                        when "00001" => o_F <= (01 => '1', others => '0');
                        when "00010" => o_F <= (02 => '1', others => '0');
                        when "00011" => o_F <= (03 => '1', others => '0');

                        when "00100" => o_F <= (04 => '1', others => '0');
                        when "00101" => o_F <= (05 => '1', others => '0');
                        when "00110" => o_F <= (06 => '1', others => '0');
                        when "00111" => o_F <= (07 => '1', others => '0');

                        when "01000" => o_F <= (08 => '1', others => '0');
                        when "01001" => o_F <= (09 => '1', others => '0');
                        when "01010" => o_F <= (10 => '1', others => '0');
                        when "01011" => o_F <= (11 => '1', others => '0');

                        when "01100" => o_F <= (12 => '1', others => '0');
                        when "01101" => o_F <= (13 => '1', others => '0');
                        when "01110" => o_F <= (14 => '1', others => '0');
                        when "01111" => o_F <= (15 => '1', others => '0');

                        when "10000" => o_F <= (16 => '1', others => '0');
                        when "10001" => o_F <= (17 => '1', others => '0');
                        when "10010" => o_F <= (18 => '1', others => '0');
                        when "10011" => o_F <= (19 => '1', others => '0');

                        when "10100" => o_F <= (20 => '1', others => '0');
                        when "10101" => o_F <= (21 => '1', others => '0');
                        when "10110" => o_F <= (22 => '1', others => '0');
                        when "10111" => o_F <= (23 => '1', others => '0');

                        when "11000" => o_F <= (24 => '1', others => '0');
                        when "11001" => o_F <= (25 => '1', others => '0');
                        when "11010" => o_F <= (26 => '1', others => '0');
                        when "11011" => o_F <= (27 => '1', others => '0');

                        when "11100" => o_F <= (28 => '1', others => '0');
                        when "11101" => o_F <= (29 => '1', others => '0');
                        when "11110" => o_F <= (30 => '1', others => '0');
                        when "11111" => o_F <= (31 => '1', others => '0');

                        when others  => o_F <=            (others => '0');
                    end case;

                else o_F <= (others => '0');
                
            end if;
        end process;
end mixed;
--------------------------------------------------------------------------------
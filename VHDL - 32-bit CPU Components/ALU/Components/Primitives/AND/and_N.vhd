library ieee;
    use ieee.std_logic_1164.all;

--------------------------------------------------------------------------------
-- Top-level Entity Definition --
--------------------------------------------------------------------------------
entity and_N is
    generic
    (
        N: integer := 32
    );
    port 
    (
        i_A : in  std_logic_vector(N-1 downto 00);

        o_F : out std_logic
    );
end and_N;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- Architecture Definition --
--------------------------------------------------------------------------------
architecture behavioral of and_N is
begin
    
    o_F <= '1' when i_A = (N-1 downto 00 => '1') else '0';

end behavioral;
--------------------------------------------------------------------------------
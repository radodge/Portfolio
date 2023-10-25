library IEEE;
	use IEEE.std_logic_1164.all;
library work;
    use work.MIPS_types.all;

--------------------------------------------------------------------------------
-- Top-level Entity Definition --
--------------------------------------------------------------------------------
entity RC_adder_32 is
	port
	(
        i_A: 		 in  bus_32;
        i_B: 		 in  bus_32;
        i_carry_in:  in  std_logic;
        o_sum: 		 out bus_32;
        o_carry_out: out std_logic
	);
end RC_adder_32;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- Architecture Definitition --
--------------------------------------------------------------------------------
architecture structure of RC_adder_32 is
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
	--------------------------------------------------------------------------------


	--------------------------------------------------------------------------------
	-- Internal Signal Definitions --
	--------------------------------------------------------------------------------
	signal s_carry_out : std_logic_vector(32 downto 00); -- linkage for internal carries
	--------------------------------------------------------------------------------


	begin
		--------------------------------------------------------------------------------
		-- Component Instantiations --
		--------------------------------------------------------------------------------
		full_adder_0: full_adder
			port map
			(
				i_A 	    => i_A(00),
				i_B 	    => i_B(00),
				i_carry_in  => i_carry_in, -- initial carry_in

				o_sum 	    => o_sum(00),
				o_carry_out => s_carry_out(01) -- 2 ^1st power carried thru
			);

		G_Nbit_RC_adder : for i in 01 to 31
		generate full_adder_i : full_adder
			port map
			(
				i_A 	   => i_A(i),
				i_B 	   => i_B(i),
				i_carry_in => s_carry_out(i), -- established by previous component's output

				o_sum 	    => o_sum(i),
				o_carry_out => s_carry_out(i + 1) -- instance no. N's carry_out will be our final
			);
		end generate G_Nbit_RC_adder;
		--------------------------------------------------------------------------------
		
		o_carry_out <= s_carry_out(32); -- connecting final internal carry out to top level out

end structure;
--------------------------------------------------------------------------------
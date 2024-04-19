library IEEE;
    use IEEE.std_logic_1164.all;
library work;
    use work.MIPS_types.all;
	

--  ___  ___ _____ ______  _____   ______               _       _                ______  _  _       
--  |  \/  ||_   _|| ___ \/  ___|  | ___ \             (_)     | |               |  ___|(_)| |      
--  | .  . |  | |  | |_/ /\ `--.   | |_/ /  ___   __ _  _  ___ | |_   ___  _ __  | |_    _ | |  ___ 
--  | |\/| |  | |  |  __/  `--. \  |    /  / _ \ / _` || |/ __|| __| / _ \| '__| |  _|  | || | / _ \
--  | |  | | _| |_ | |    /\__/ /  | |\ \ |  __/| (_| || |\__ \| |_ |  __/| |    | |    | || ||  __/
--  \_|  |_/ \___/ \_|    \____/   \_| \_| \___| \__, ||_||___/ \__| \___||_|    \_|    |_||_| \___|
--                                                __/ |                                             
--                                               |___/                                              

--------------------------------------------------------------------------------
-- Top-level Entity Definition --
--------------------------------------------------------------------------------
entity MIPS_register_file is
    port
    (
        i_clock:           in  std_logic;  
        i_reg_reset:       in  bus_32;      -- reset for each register
        i_master_write_en: in  std_logic;   -- enable input to decoder, decoder outputs 0x00000000 when this is 0

        i_write_addr:      in  reg_address; -- when RegDst=0: input is Instruction[20:16](rt); When RegDst=1: input is Instruction[15:11](rd)
        i_write_data:      in  bus_32;      -- when MemtoReg=0: input is ALU result; When MemtoReg=1: input is memory data (q from lab 2)

        i_read_0_addr:     in  reg_address; -- instruction[25:21](rs)
        i_read_1_addr:     in  reg_address; -- instruction[20:16](rt)

        o_read_0_data:     out bus_32;      -- connected directly to ALU input A
        o_read_1_data:     out bus_32       -- connected to D0 of ALUSrc mux
    );
end MIPS_register_file;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- Architecture Definitition --
--------------------------------------------------------------------------------
architecture structural of MIPS_register_file is
    --------------------------------------------------------------------------------
	-- Component Definitions --
	--------------------------------------------------------------------------------
    component decoder_5t32 is
        port
        (
            i_D:  in  reg_address;
            i_En: in  std_logic;

            o_F:  out bus_32
        );
    end component;

    component register_32 is
        port
        (
            i_CLK: in  std_logic;
            i_RST: in  std_logic;
            i_WE:  in  std_logic;
    
            i_D:   in  bus_32;
    
            o_Q:   out bus_32
        );
    end component;

    component mux_32t1_32 is
        port
        (
            i_S: in  reg_address; -- all muxes share select bits
            i_D: in  bus_32x32; -- array of "N" 32-bit wide inputs

            o_O: out bus_32 -- array of "N" 1-bit outputs
        );
    end component;

    component demux_1t32_32 is
        port
        (
            i_S:    in  reg_address;
            i_D:    in  bus_32;
            
            o_data: out bus_32x32
        );
    end component;
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
	-- Internal Signal Definitions --
	--------------------------------------------------------------------------------
    signal s_write_en:   bus_32;    -- output of 5t32 bit decoder, wired to write_en of each reg
    signal s_write_data: bus_32x32; -- output of input data demux

    signal s_read_data:  bus_32x32; -- output of each register, will be wired to both read port muxes
    --------------------------------------------------------------------------------


begin
--------------------------------------------------------------------------------
-- Instantiate Non-sequential Components
--------------------------------------------------------------------------------
    --------------------------------------------------------------------------------
    -- Write Enable Decoder --
    -- 
    -- Input wired to write address
    -- Output wired to write enable pin of each register
    -- 
    --------------------------------------------------------------------------------
    Write_Enable_Decoder: decoder_5t32
        port map
        (
            i_D  => i_write_addr,
            i_En => i_master_write_en,

            o_F  => s_write_en
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Write Data Demux --
    -- 
    -- Input wired to top-level data input
    -- Select wired to write address
    -- Output wired to 32-bit input of each register (32x32)
    -- 
    -- Functional description: 
    -- Routes data from single 32-bit input to 32x32 bus. The remaining 31 outputs
    -- are set to 0x00000000.
    -- 
    --------------------------------------------------------------------------------
    Write_Data_Demux: demux_1t32_32
        port map
        (
            i_S    => i_write_addr,
            i_D    => i_write_data,

            o_data => s_write_data
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Read Port 0 Multiplexer --
    -- 
    -- Input wired to data out bus of all 32 registers
    -- Output wired to read data port 0
    -- 
    -- This will likely form the base address for every load/store instruction.
    -- 
    --------------------------------------------------------------------------------
    Read_Port_0_mux: mux_32t1_32      -- connected to data output of each register
        port map
        (
            i_S => i_read_0_addr,
            i_D => s_read_data,

            o_O => o_read_0_data
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Read Port 1 Multiplexer --
    -- 
    -- Input wired to data out bus of all 32 registers
    -- Output wired to read data port 1
    -- 
    --------------------------------------------------------------------------------
    Read_Port_1_mux: mux_32t1_32
        port map
        (
            i_S => i_read_1_addr,
            i_D => s_read_data,

            o_O => o_read_1_data
        );
    --------------------------------------------------------------------------------
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- Instantiate MIPS Registers --
-- 
-- Inputs wired to respective index of 32x32 data input bus
-- Outputs wired to both read port multiplexers
-- 
--------------------------------------------------------------------------------
    --------------------------------------------------------------------------------
    -- Register 00: $zero --
    -- 
    -- The Constant Value 0x00000000
    -- 
    --------------------------------------------------------------------------------
    reg_00_zero: register_32
        port map
        (
            i_CLK =>         i_clock,
            i_RST => i_reg_reset(00),

            i_D   =>       zeroes_32, -- input is hard wired to 0x00000000
            i_WE  =>  s_write_en(00),

            o_Q   => s_read_data(00)
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Register 01: $at --
    -- 
    -- Assembler Temporary
    -- Not preserved across a call
    -- 
    --------------------------------------------------------------------------------
    reg_01_Assembler_Temporary: register_32
        port map
        (
            i_CLK =>          i_clock,
            i_RST =>  i_reg_reset(01),

            i_D   => s_write_data(01),
            i_WE  =>   s_write_en(01),

            o_Q   =>  s_read_data(01)
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Registers 02-03: $v0-$v1 --
    -- 
    -- Values for Function Results and Expression Evaluation
    -- Not preserved across a call
    -- 
    --------------------------------------------------------------------------------
    reg_02_Function_Results_Expr_Eval_0: register_32
        port map
        (
            i_CLK =>          i_clock,
            i_RST =>  i_reg_reset(02),

            i_D   => s_write_data(02),
            i_WE  =>   s_write_en(02),

            o_Q   =>  s_read_data(02)
        );

    reg_03_Function_Results_Expr_Eval_1: register_32
        port map
        (
            i_CLK =>          i_clock,
            i_RST =>  i_reg_reset(03),

            i_D   => s_write_data(03),
            i_WE  =>   s_write_en(03),

            o_Q   =>  s_read_data(03)
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Registers 04-07: $a0-$a3 --
    -- 
    -- Arguments
    -- Not preserved across a call
    -- 
    --------------------------------------------------------------------------------
    reg_04_Arguments_0: register_32
        port map
        (
            i_CLK =>          i_clock,
            i_RST =>  i_reg_reset(04),

            i_D   => s_write_data(04),
            i_WE  =>   s_write_en(04),

            o_Q   =>  s_read_data(04)
        );

    reg_05_Arguments_1: register_32
        port map
        (
            i_CLK =>         i_clock,
            i_RST => i_reg_reset(05),

            i_D   =>s_write_data(05),
            i_WE  =>  s_write_en(05),

            o_Q   => s_read_data(05)
        );

    reg_06_Arguments_2: register_32
        port map
        (
            i_CLK =>         i_clock,
            i_RST => i_reg_reset(06),

            i_D   =>s_write_data(06),
            i_WE  =>  s_write_en(06),

            o_Q   => s_read_data(06)
        );

    reg_07_Arguments_3: register_32
        port map
        (
            i_CLK =>         i_clock,
            i_RST => i_reg_reset(07),

            i_D   =>s_write_data(07),
            i_WE  =>  s_write_en(07),

            o_Q   => s_read_data(07)
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Registers 08-15: $t0-$t7 --
    -- 
    -- Temporaries
    -- Not preserved across a call
    -- 
    --------------------------------------------------------------------------------
    reg_08_Temporaries_0: register_32
        port map
        (
            i_CLK =>         i_clock,
            i_RST => i_reg_reset(08),

            i_D   =>s_write_data(08),
            i_WE  =>  s_write_en(08),

            o_Q   => s_read_data(08)
        );

    reg_09_Temporaries_1: register_32
        port map
        (
            i_CLK =>         i_clock,
            i_RST => i_reg_reset(09),

            i_D   =>s_write_data(09),
            i_WE  =>  s_write_en(09),

            o_Q   => s_read_data(09)
        );

    reg_10_Temporaries_2: register_32
        port map
        (
            i_CLK =>         i_clock,
            i_RST => i_reg_reset(10),

            i_D   =>s_write_data(10),
            i_WE  =>  s_write_en(10),

            o_Q   => s_read_data(10)
        );

    reg_11_Temporaries_3: register_32
        port map
        (
            i_CLK =>         i_clock,
            i_RST => i_reg_reset(11),

            i_D   =>s_write_data(11),
            i_WE  =>  s_write_en(11),

            o_Q   => s_read_data(11)
        );

    reg_12_Temporaries_4: register_32
        port map
        (
            i_CLK =>         i_clock,
            i_RST => i_reg_reset(12),

            i_D   =>s_write_data(12),
            i_WE  =>  s_write_en(12),

            o_Q   => s_read_data(12)
        );

    reg_13_Temporaries_5: register_32
        port map
        (
            i_CLK =>          i_clock,
            i_RST =>  i_reg_reset(13),

            i_D   => s_write_data(13),
            i_WE  =>   s_write_en(13),

            o_Q   =>  s_read_data(13)
        );

    reg_14_Temporaries_6: register_32
        port map
        (
            i_CLK =>          i_clock,
            i_RST =>  i_reg_reset(14),

            i_D   => s_write_data(14),
            i_WE  =>   s_write_en(14),

            o_Q   =>  s_read_data(14)
        );

    reg_15_Temporaries_7: register_32
        port map
        (
            i_CLK =>          i_clock,
            i_RST =>  i_reg_reset(15),

            i_D   => s_write_data(15),
            i_WE  =>   s_write_en(15),

            o_Q   =>  s_read_data(15)
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Registers 16-23: $s0-$s7 --
    -- 
    -- Saved Temporaries
    -- Preserved across a call
    -- 
    --------------------------------------------------------------------------------
    reg_16_Saved_Temporaries_0: register_32
        port map
        (
            i_CLK =>          i_clock,
            i_RST =>  i_reg_reset(16),

            i_D   => s_write_data(16),
            i_WE  =>   s_write_en(16),

            o_Q   =>  s_read_data(16)
        );

    reg_17_Saved_Temporaries_1: register_32
        port map
        (
            i_CLK =>          i_clock,
            i_RST =>  i_reg_reset(17),

            i_D   => s_write_data(17),
            i_WE  =>   s_write_en(17),

            o_Q   =>  s_read_data(17)
        );

    reg_18_Saved_Temporaries_2: register_32
        port map
        (
            i_CLK =>          i_clock,
            i_RST =>  i_reg_reset(18),

            i_D   => s_write_data(18),
            i_WE  =>   s_write_en(18),

            o_Q   =>  s_read_data(18)
        );

    reg_19_Saved_Temporaries_3: register_32
        port map
        (
            i_CLK =>          i_clock,
            i_RST =>  i_reg_reset(19),

            i_D   => s_write_data(19),
            i_WE  =>   s_write_en(19),

            o_Q   =>  s_read_data(19)
        );

    reg_20_Saved_Temporaries_4: register_32
        port map
        (
            i_CLK =>          i_clock,
            i_RST =>  i_reg_reset(20),

            i_D   => s_write_data(20),
            i_WE  =>   s_write_en(20),

            o_Q   =>  s_read_data(20)
        );

    reg_21_Saved_Temporaries_5: register_32
        port map
        (
            i_CLK =>          i_clock,
            i_RST =>  i_reg_reset(21),

            i_D   => s_write_data(21),
            i_WE  =>   s_write_en(21),

            o_Q   =>  s_read_data(21)
        );

    reg_22_Saved_Temporaries_6: register_32
        port map
        (
            i_CLK =>          i_clock,
            i_RST =>  i_reg_reset(22),

            i_D   => s_write_data(22),
            i_WE  =>   s_write_en(22),

            o_Q   =>  s_read_data(22)
        );

    reg_23_Saved_Temporaries_7: register_32
        port map
        (
            i_CLK =>          i_clock,
            i_RST =>  i_reg_reset(23),

            i_D   => s_write_data(23),
            i_WE  =>   s_write_en(23),

            o_Q   =>  s_read_data(23)
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Registers 24-25: $t8-$t9 --
    -- 
    -- Temporaries
    -- Not preserved across a call
    -- 
    --------------------------------------------------------------------------------
    reg_24_Temporaries_8: register_32
        port map
        (
            i_CLK =>          i_clock,
            i_RST =>  i_reg_reset(24),

            i_D   => s_write_data(24),
            i_WE  =>   s_write_en(24),

            o_Q   =>  s_read_data(24)
        );

    reg_25_Temporaries_9: register_32
        port map
        (
            i_CLK =>          i_clock,
            i_RST =>  i_reg_reset(25),

            i_D   => s_write_data(25),
            i_WE  =>   s_write_en(25),

            o_Q   =>  s_read_data(25)
        );
--------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Registers 26-27: $k0-$k1 --
    -- 
    -- Reserved for OS Kernel
    -- Not preserved across a call
    -- 
    --------------------------------------------------------------------------------
    reg_26_Reserved_for_OS_Kernel_0: register_32
        port map
        (
            i_CLK =>          i_clock,
            i_RST =>  i_reg_reset(26),

            i_D   => s_write_data(26),
            i_WE  =>   s_write_en(26),

            o_Q   =>  s_read_data(26)
        );

    reg_27_Reserved_for_OS_Kernel_1: register_32
        port map
        (
            i_CLK =>          i_clock,
            i_RST =>  i_reg_reset(27),

            i_D   => s_write_data(27),
            i_WE  =>   s_write_en(27),

            o_Q   =>  s_read_data(27)
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Register 28: $gp --
    -- 
    -- Global Pointer
    -- Preserved across a call
    -- 
    --------------------------------------------------------------------------------
    reg_28_Global_Pointer: register_32
        port map
        (
            i_CLK =>          i_clock,
            i_RST =>  i_reg_reset(28),

            i_D   => s_write_data(28),
            i_WE  =>   s_write_en(28),

            o_Q   =>  s_read_data(28)
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Register 29: $sp --
    -- 
    -- Stack Pointer
    -- Preserved across a call
    -- 
    --------------------------------------------------------------------------------
    reg_29_Stack_Pointer: register_32
        port map
        (
            i_CLK =>          i_clock,
            i_RST =>  i_reg_reset(29),

            i_D   => s_write_data(29),
            i_WE  =>   s_write_en(29),

            o_Q   =>  s_read_data(29)
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Register 30: $fp --
    -- 
    -- Frame Pointer
    -- Preserved across a call
    -- 
    --------------------------------------------------------------------------------
    reg_30_Frame_Pointer: register_32
        port map
        (
            i_CLK =>          i_clock,
            i_RST =>  i_reg_reset(30),

            i_D   => s_write_data(30),
            i_WE  =>   s_write_en(30),

            o_Q   =>  s_read_data(30)
        );
    --------------------------------------------------------------------------------


    --------------------------------------------------------------------------------
    -- Register 31: $ra --
    -- 
    -- Return Address
    -- Preserved across a call
    -- 
    --------------------------------------------------------------------------------
    reg_31_Return_Address: register_32
        port map
        (
            i_CLK =>          i_clock,
            i_RST =>  i_reg_reset(31),

            i_D   => s_write_data(31),
            i_WE  =>   s_write_en(31),

            o_Q   =>  s_read_data(31)
        );
    --------------------------------------------------------------------------------
--------------------------------------------------------------------------------
end structural;
--------------------------------------------------------------------------------
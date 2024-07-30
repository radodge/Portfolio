
module final_project_top
    (
        input i_CLK, i_RESET, i_ENABLE, i_MODE,
        input [11:0] i_temp_NEW,

        output reg o_DONE,
        output reg [11:0] o_RESULT
    );

    integer i;

//    ___ _           _ _             ___ _                     __  
//   | _ (_)_ __  ___| (_)_ _  ___   / __| |_ __ _ __ _ ___    /  \ 
//   |  _/ | '_ \/ -_) | | ' \/ -_)  \__ \  _/ _` / _` / -_)  | () |
//   |_| |_| .__/\___|_|_|_||_\___|  |___/\__\__,_\__, \___|   \__/ 
//         |_|                                    |___/             

    // STAGE 0 SIGNAL DEFINITIONS
    wire w0_FIFO_FULL;                  // set high when reg0_num_samples=16
    wire [11:0] w0_AVERAGE;             // average of current dataset

    reg reg0_MODE;                      // 0=average 1=standard deviation
    reg reg0_DONE;                      // 1 after the FIFO is full and a result has reached the output stage
    reg [4:0] reg0_num_samples;         // number of samples
    reg [11:0] reg0_temp_FIFO[0:15];    // set of 16 captured temperatures
    reg [11:0] reg0_AVERAGE;            // average
    reg [16:0] reg0_temp_TOTAL;         // summation of current dataset (total = total + newest - oldest)
    reg [27:0] reg0_sum_squares;        // summation of squared inputs
    reg [23:0] reg0_VARIANCE;           // variance = (sum of squares)/16 - (average^2)


    // STAGE 0 COMBINATIONAL LOGIC
    assign w0_FIFO_FULL = (reg0_num_samples == 16) ? 1 : 0;  // 1 if num samples is 16

    assign w0_AVERAGE = reg0_temp_TOTAL >> 4;           // average = total/16 (same as shifting right 4 bits)

//    ___ _           _ _             ___ _                    _ 
//   | _ (_)_ __  ___| (_)_ _  ___   / __| |_ __ _ __ _ ___   / |
//   |  _/ | '_ \/ -_) | | ' \/ -_)  \__ \  _/ _` / _` / -_)  | |
//   |_| |_| .__/\___|_|_|_||_\___|  |___/\__\__,_\__, \___|  |_|
//         |_|                                    |___/          

    // STAGE 1 SIGNAL DEFINITIONS
    // wire [11:0] w1_STD_DEV;     // estimated standard deviation of current dataset
    // wire w1_EN_div;             // enables/disables division circuitry

    reg reg1_DONE;
    reg reg1_MODE;
    reg reg_output_mode;
    reg reg1_FIFO_FULL;
    reg [11:0] reg1_AVERAGE;
    reg [11:0] reg1_STD_DEV;

    always @(posedge i_CLK, posedge i_RESET)
        begin
            if(i_RESET)
                begin
                    reg0_MODE <= 0;
                    reg0_DONE <= 0;
                    reg0_num_samples <= 0;
                    reg0_temp_TOTAL <= 0;
                    reg0_AVERAGE <= 0;
                    reg0_sum_squares <= 0;
                    reg0_VARIANCE <= 0;
                    for(i = 0; i < 16; i = i + 1)
                        begin
                            reg0_temp_FIFO[i] <= 0;
                        end
                    reg1_MODE <= 0;
                    reg1_DONE <= 0;
                    reg_output_mode <= 0;
                    reg1_FIFO_FULL <= 0;
                    reg1_AVERAGE <= 0;
                    reg1_STD_DEV <= 12'b010000000000;   // initial guess for standard deviation
                end
            else
                begin
                    if(i_ENABLE)
                    begin
                    //    ___ _                     __  
                    //   / __| |_ __ _ __ _ ___    /  \ 
                    //   \__ \  _/ _` / _` / -_)  | () |
                    //   |___/\__\__,_\__, \___|   \__/ 
                    //                |___/             
                    // Total computation - add newest input and subtract latest input
                    // Average computation - shift right 4 bits
                    // Variance summation - summation of (Xi^2)

                    reg0_temp_FIFO[0] <= i_temp_NEW;    // captures newest temperature
                    reg0_temp_TOTAL <= reg0_temp_TOTAL + i_temp_NEW - reg0_temp_FIFO[15];   // tracks sum using present temperature values
                    reg0_MODE <= i_MODE;
                    for(i = 1; i < 16; i = i + 1)
                        begin
                            reg0_temp_FIFO[i] <= reg0_temp_FIFO[i - 1]; // shifts FIFO
                        end
                    if(reg0_num_samples < 16)
                        begin
                            reg0_num_samples <= reg0_num_samples + 4'b0001;
                        end

                    reg1_FIFO_FULL <= w0_FIFO_FULL; // propogates FIFO FULL signal to next stage
                    reg1_MODE <= reg0_MODE;         // propogates MODE signal to next stage

                    if(w0_FIFO_FULL)
                        begin
                            reg0_AVERAGE <= w0_AVERAGE; // propogates average to next stage
                            reg0_sum_squares <= reg0_sum_squares + (i_temp_NEW * i_temp_NEW) - (reg0_temp_FIFO[15] * reg0_temp_FIFO[15]);   // rolling summation of inputs squared
                            reg0_VARIANCE <= (reg0_sum_squares >> 4) - (w0_AVERAGE * w0_AVERAGE);   // V = (sum of squares)/16 - (average^2)
                        end
                    else
                        begin
                            reg0_sum_squares <= reg0_sum_squares + (i_temp_NEW * i_temp_NEW);
                        end

                    if(w0_FIFO_FULL & !reg0_MODE)
                        begin
                            reg0_DONE <= 1;  // if calculating average, calc is done
                        end
                    

                    //    ___ _                    _ 
                    //   / __| |_ __ _ __ _ ___   / |
                    //   \__ \  _/ _` / _` / -_)  | |
                    //   |___/\__\__,_\__, \___|  |_|
                    //                |___/          
                    // Standard deviation estimation based on an initial guess of 010000000000

                    if(reg1_FIFO_FULL)
                        begin
                            reg1_AVERAGE <= reg0_AVERAGE;
                            reg_output_mode <= reg1_MODE;
                            reg1_DONE <= reg0_DONE;
                            if(reg1_MODE)
                                begin
                                    reg1_STD_DEV <= (reg1_STD_DEV + ((reg0_VARIANCE) / reg1_STD_DEV)) >> 1;   // estimated square root = 1/2 * (guess + (variance/guess))
                                    reg1_DONE <= 1;
                                    reg_output_mode <= 1;
                                end
                            o_RESULT <= reg_output_mode ? reg1_STD_DEV : reg1_AVERAGE;
                            o_DONE <= reg1_DONE;
                        end
                    
                end
                end
        end
endmodule
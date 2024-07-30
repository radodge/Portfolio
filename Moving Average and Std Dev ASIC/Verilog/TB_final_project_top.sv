`timescale 1ns/1ns


module TB_final_project_top;

    reg CLK, RESET, ENABLE, MODE;
    // reg SAMPLE;
    reg [11:0] temp_NEW;

    wire [11:0] AVG_SD;
    wire DONE;

    int CLK_period = 20;
    int i, num_samples;
    real temp_FIFO[16];     // array to store test values in scope of test bench
    real average;
    real std_dev;
    real expected_output;   // calculated standard deviation or average

    real average_D0;
    real average_D1;
    real average_D2;
    real average_D3;
    real std_dev_D0;
    real std_dev_D1;
    real std_dev_D2;
    real std_dev_D3;
    real MODE_D0;
    real MODE_D1;
    real MODE_D2;
    real MODE_D3;


    function real calc_average(real data[]);
        int i;
        automatic real sum = 0;

        foreach (data[i])
            begin
                sum += data[i];
            end

        return sum / data.size();
    endfunction

    function real calc_std_dev(real data[]);
        int i;
        automatic real mean = calc_average(data);
        automatic real squaredDiffSum = 0;

        foreach (data[i]) begin
            squaredDiffSum += (data[i] - mean) ** 2;
        end

        return $sqrt(squaredDiffSum / data.size());
    endfunction


    final_project_top DUT0
        (
            .i_CLK(CLK),
            .i_RESET(RESET),
            .i_ENABLE(ENABLE),
            .i_MODE(MODE),
            .i_temp_NEW(temp_NEW),

            .o_RESULT(AVG_SD),
            .o_DONE(DONE)
        );

    initial
        begin
            $display("Initiating NOAA IoT Motes Module");
            for(i = 0; i < 16; i++)
                begin
                    temp_FIFO[i] = 0;
                end
            num_samples = 0;
            temp_NEW = 0;
            MODE = 0;
            CLK = 0;
            RESET = 0;
            ENABLE = 0;
            #15
            RESET = 1;
            #5
            RESET = 0;
            // #15
            ENABLE = 1;
        end

    always #(CLK_period/2) CLK = ~CLK;

    always@(posedge CLK)
        begin
            temp_NEW = $urandom;
            MODE = $urandom;
            #20;
            for(i = 15; i > 0; i--)
                begin
                    temp_FIFO[i] = temp_FIFO[i - 1];
                end
            temp_FIFO[0] = temp_NEW;

            average     = calc_average(temp_FIFO);
            std_dev     = calc_std_dev(temp_FIFO);

            average_D0  <= average;
            average_D1  <= average_D0;
            average_D2  <= average_D1;
            average_D3  <= average_D2;

            std_dev_D0  <= std_dev;
            std_dev_D1  <= std_dev_D0;
            std_dev_D2  <= std_dev_D1;
            std_dev_D3  <= std_dev_D2;

            MODE_D0     <= MODE;
            MODE_D1     <= MODE_D0;
            MODE_D2     <= MODE_D1;
            MODE_D3     <= MODE_D2;

            num_samples++;
 
            if(num_samples > 16)
                begin
                    $display("Mode: %0d", MODE_D3);
                    $display("Average: %0d", average_D3);
                    $display("Std Dev: %0d", std_dev_D3);
                    $display("Output:  %0d\n", AVG_SD);


                    // expected_output = MODE ? calc_std_dev(temp_FIFO) : calc_average(temp_FIFO);
                    // $display("Mode: %s", MODE?"Std. Dev":"Average");
                    // $display("Expected Output: %0d", expected_output);
                    // $display("Actual Output:   %0d\n", AVG_SD);
                // end
                end
        end
endmodule
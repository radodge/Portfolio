#include "core_functions.h"

object_t *object_list[10]; //global variable object_list contains all info about objects after most recent scan

int main(void)
{

/** I/O INIT **/

    uart_init(115200);
    uart_interrupt_init();
    ping_init();
    servo_init();
    lcd_init();
    adc_init();
    button_init();
    init_button_interrupts();

    oi_t *sensor = oi_alloc();
    oi_init(sensor);

    servo_rotate(0);
    oi_setWheels(0,0);
    lcd_clear();

/** END I/O INIT **/


/** GLOBALS INIT **/

    int g = 0;

    for(g = 0; g<10; g++)
    {
        object_list[g] = malloc(sizeof(object_t));  //allocating space in memory for array of structs
        object_list[g]->dist = 0;                   //initializing array of structs to zeroes
        object_list[g]->end_angle = 0;              //null objects are easy to rule out
        object_list[g]->lin_width = 0;
        object_list[g]->start_angle = 0;
        object_list[g]->midpoint_angle = 0;
    }

/** END GLOBALS INIT **/


/** LOCAL VARIABLES **/

    int i = 0;
    char line[53]; 					//line for GUI printout
    float reece_distance = 0;		//distance relative to the end of the clear path ahead (clear of tall objects, not obstacles/hazards unseen by sensors)
    int reece_angle = 90;           //facing forward is 90 degrees (same as scanner)
	
/** END LOCAL VARIABLES **/


    while(1)
    {

    /** PUTTY PRINTOUT **/

        sprintf(line, "\rDist: %-03.3f       ||         Angle: %-03d %10s\r", reece_distance, reece_angle, " ");
        uart_sendStr(line); //constantly prints out relative distance and angle

    /** END PUTTY PRINTOUT **/


    /***
     *      ___          ___                  ___         _           _
     *     | __|  ___   / __| __ __ _ _ _    / __|___ _ _| |_ _ _ ___| |
     *     | _|  |___|  \__ \/ _/ _` | ' \  | (__/ _ \ ' \  _| '_/ _ \ |
     *     |___|        |___/\__\__,_|_||_|  \___\___/_||_\__|_| \___/_|
     * 
     * DESCRIPTION:
     * Scanning restablishes your relative position and outputs all the necessary
     * information to make decisions. Data about objects and gaps will be printed
     * to putty.
     * "reece_distance" is the calculated distance you can travel in a straight
     * path ahead without hitting a tall object. See "core_functions.c" for exactly how.
     **/
        if(uart_flag && (uart_data == 'e'))     //all user inputs are setup like this
        {
            uart_flag = 0;                      //flag needs reset so next input can be tracked

            ScanVals(object_list, 0, 180);      //scans from 0 to 180

            if(object_list[0]->dist > 0)        //does not print header if no objects were detected
            {      
                sprintf(line, "****************** OBJECT    LIST ******************\r\n");
                uart_sendStr(line);
                sprintf(line, "%-10s %-12s %-12s  %-12s\r\n", "Obj Num", "Ping-Dist", "Mid_Angle", "Lin-width");
                uart_sendStr(line);
            }

            for(i = 0; i < 10; i++)				//prints object data
            {
                if(object_list[i]->dist > 0)    //does not print null objects
                {
                    sprintf(line, "%-10d  %-0.3f         %-03d        %-12f \n\r", i,  object_list[i]->dist, object_list[i]->midpoint_angle,  object_list[i]->lin_width);
                    uart_sendStr(line);
                }
            }

            gap_lin_width(object_list);							//prints gap data
            reece_distance = object_clear_check(object_list);   //re-establish relative distance (max 50 cm)
            reece_angle = 90;                                   //re-establish relative angle
        }

    /** END SCAN CONTROL **/


    /***
     *     __      __         __  __               ___                           _ 
     *     \ \    / /  ___   |  \/  |_____ _____  | __|__ _ ___ __ ____ _ _ _ __| |
     *      \ \/\/ /  |___|  | |\/| / _ \ V / -_) | _/ _ \ '_\ V  V / _` | '_/ _` |
     *       \_/\_/          |_|  |_\___/\_/\___| |_|\___/_|  \_/\_/\__,_|_| \__,_|
     *                                                                             
     * DESCRIPTION:
     * Movement is restricted to incriments of reece_distance or reece_distance/2.
     * The movement functions are deisgned to return distance traveled and
     * angle deviated. This way, it's theoretically imposible to drive into a
     * tall object.
     **/
        else if(uart_flag && (uart_data == 'w') && (reece_angle == 90)) 				//will not allow you to move forward if you turn off axis
        {
            uart_flag = 0;
            reece_distance = reece_distance - move_forward(sensor, reece_distance / 2); //move forward 1/2 of safe path
        }

        else if(uart_flag && (uart_data == 'W') && (reece_angle == 90))
        {
            uart_flag = 0;
            reece_distance = reece_distance - move_forward(sensor, reece_distance);		//move forward full safe path
        }

    /** END MOVE FORWARD **/


    /***
     *        _            _____                _         __ _
     *       /_\    ___   |_   _|  _ _ _ _ _   | |   ___ / _| |_
     *      / _ \  |___|    | || || | '_| ' \  | |__/ -_)  _|  _|
     *     /_/ \_\          |_| \_,_|_| |_||_| |____\___|_|  \__|
     *
     */
        else if(uart_flag && (uart_data == 'a')) //half turn
        {
            uart_flag = 0;
            reece_angle = reece_angle + turn_counter_clockwise(sensor, 45);
        }

        else if(uart_flag && (uart_data == 'A')) //full turn
        {
            uart_flag = 0;
            reece_angle = reece_angle + turn_counter_clockwise(sensor, reece_angle);
        }

    /** END TURN LEFT **/


    /***
     *      ___           _____                ___ _      _   _
     *     |   \   ___   |_   _|  _ _ _ _ _   | _ (_)__ _| |_| |_
     *     | |) | |___|    | || || | '_| ' \  |   / / _` | ' \  _|
     *     |___/           |_| \_,_|_| |_||_| |_|_\_\__, |_||_\__|
     *                                              |___/
     */
        else if(uart_flag && (uart_data == 'd')) //half turn
        {
            uart_flag = 0;
            reece_angle = reece_angle - turn_clockwise(sensor, 45);
        }

        else if(uart_flag && (uart_data == 'D')) //full turn
        {
            uart_flag = 0;
            reece_angle = reece_angle - turn_clockwise(sensor, reece_angle);
        }

    /** END TURN RIGHT **/


    /***
     *      ___          __  __               ___          _                       _
     *     / __|  ___   |  \/  |_____ _____  | _ ) __ _ __| |____ __ ____ _ _ _ __| |___
     *     \__ \ |___|  | |\/| / _ \ V / -_) | _ \/ _` / _| / /\ V  V / _` | '_/ _` (_-<
     *     |___/        |_|  |_\___/\_/\___| |___/\__,_\__|_\_\ \_/\_/\__,_|_| \__,_/__/
     *
     */
        else if(uart_flag && (uart_data == 's')) //limited to 5 cm to minimize risk of hitting objects while reversing
        {
            uart_flag = 0;
            reece_distance = reece_distance - move_backward(sensor, 5);
        }

    /** END MOVE BACKWARDS **/


    /***
     *      ___          ___                           _ _         _            _         _____
     *     | _ \  ___   | _ \___ _ _ _ __  ___ _ _  __| (_)__ _  _| |__ _ _ _  | |_ ___  |_   _|_ _ _ __  ___
     *     |  _/ |___|  |  _/ -_) '_| '_ \/ -_) ' \/ _` | / _| || | / _` | '_| |  _/ _ \   | |/ _` | '_ \/ -_)
     *     |_|          |_| \___|_| | .__/\___|_||_\__,_|_\__|\_,_|_\__,_|_|    \__\___/   |_|\__,_| .__/\___|
     *                              |_|                                                            |_|
     */
        else if(uart_flag && (uart_data == 'p')) //optional functionality, use if youd like to get perpendicular to the white tape
        {
            uart_flag = 0;
            perp_to_tape(sensor);                //moves you back 5 cm once bot is perpendicular
            turn_counter_clockwise(sensor, 180); //180 degree turn so you're facing towards the middle of the zone

            sprintf(line, "Bot is perpendicular to boundary facing inward\r\n");
            uart_sendStr(line);
        }
		
    /** END PERPENDICULAR TO TAPE **/


    /***
     *       ___           ___      _ _ _             _   _
     *      / __|  ___    / __|__ _| (_) |__ _ _ __ _| |_(_)___ _ _
     *     | (__  |___|  | (__/ _` | | | '_ \ '_/ _` |  _| / _ \ ' \
     *      \___|         \___\__,_|_|_|_.__/_| \__,_|\__|_\___/_||_|
     *
     */
        else if(uart_flag && (uart_data == 'c')) //runs on the bot treadmill, done prior to demo
        {
            uart_flag = 0;
            calibrate_wheels(sensor);            //outputs wheel values to LCD
        }

        else if(uart_flag && (uart_data == 'C')) //interfaces with buttons an LCD to output 0 and 180 values, done prior to demo
        {
            uart_flag = 0;
            servo_calibrate();
        }

    /** END CALIBRATION **/


    /***
     *     __  __         ___     _ _
     *     \ \/ /  ___   | __|_ _(_) |_
     *      >  <  |___|  | _|\ \ / |  _|
     *     /_/\_\        |___/_\_\_|\__|
     *
     */
        else if(uart_flag && (uart_data == 'X'))
        {
            uart_flag = 0;
            oi_setWheels(0,0);
            oi_free(sensor);
            break;
        }
		
    /** END EXIT  **/
    }
}
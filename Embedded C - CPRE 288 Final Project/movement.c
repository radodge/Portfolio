#include "movement.h"


//short forward_RWP = 80;         //Default
//short c_LWP = 50;
//short cc_RWP = 50;

short cc_RWP = 68;            //Cybot 00
short c_LWP = 39;
short forward_RWP = 96;


//short forward_RWP = 95;       //Cybot 02
//short c_LWP = 42;
//short cc_RWP = 66;


//short forward_RWP = 69;       //Cybot 10
//short c_LWP = 40;
//short cc_RWP = 40;

//short forward_RWP = 80;       //Cybot 11
//short c_LWP = 47;
//short cc_RWP = 50;

//short forward_RWP = 80;       //Cybot 12
//short c_LWP = 47;
//short cc_RWP = 50;


/** 
 * OVERALL DESCRIPTION:
 * Being confident you're traveling in a straight line and pivoting on a dime is critical.
 * Each primitive movement function runs perfectly with each bot and dynamically adjusts
 * each wheel's power according to deviation of either distance or angle. The powers settle
 * into values which drive in a straight line or turn on a dime given you're still dynamically
 * correcting. The resulting powers alone will not produce clean travel, but dynamically, they're
 * excellent.
 * 
 * The robot's movement is strictly regulated to functions within this library. The calibration
 * function gives the bot a head start.
 *
 * Each primitive function returns its change in relative position since the
 * last call of another primitive movement function.
 * This is useful because relative position can be tracked or ignored based on
 * whether or not you include "relative position += mm_traveled" or 
 * "relative_angle += angle_deviated".
**/


short current_status;  // combination of all different OI sensor checks - functions as a 16 bit status register
short previous_status; // status at time of previous oi_update


/** CALIBRATE WHEELS **/

void calibrate_wheels(oi_t *sensor) // can run perfectly on treadmill, does not need to be on the ground
{
    move_forward(sensor, 150);   // moves forward so bot can settle into consistent values
    turn_clockwise(sensor, 180); // turns 360 degrees, input is a char so 360 is out of bounds
    turn_clockwise(sensor, 180);
    turn_counter_clockwise(sensor, 180); // turns 360 degrees, input is a char so 360 is out of bounds
    turn_counter_clockwise(sensor, 180);

    lcd_printf("f_RWP= %d  c_LWP= %dcc_RWP= %d", forward_RWP, c_LWP, cc_RWP); // prints cleanly to LCD
}

/** END CALIBRATE WHEELS **/


/** MOVE FORWARD **/

float move_forward(oi_t *sensor, float input_centimeters)
{
    float mm_traveled = 0;
    float angle_deviated = 0;

    while((mm_traveled < (input_centimeters * 10)) && (current_status == clear)) //loop is broken if status isn't clear and bot is stopped
    {
        oi_update(sensor);
        obstacle_check(sensor);

        mm_traveled += sensor->distance;    //incriments distance traveled
        angle_deviated += sensor->angle;    //incriments angle deviated

        if(uart_flag && (uart_data == ' ')) //brakes for manual mode
        {
            uart_flag = 0;
            break;
        }

        if(angle_deviated > degree_accuracy) //if bot veered to the left (oi_update accumulated positive angle)
        {
            forward_RWP -= 1;                //right wheel compensates by powering down
            angle_deviated = 0;              //angle is reset, corrections are made per degree deviated
        }

        else if(angle_deviated < -(degree_accuracy)) //if bot veered to the right (oi_update accumulated negative angle)
        {
            forward_RWP += 1;                        //right wheel compensates by powering up
            angle_deviated = 0;                      //angle is reset, corrections are made per degree deviated
        }

        oi_setWheels(forward_RWP, forward_LWP);
    }

    oi_setWheels(0,0);       //stops bot when complete
    return mm_traveled / 10; //returns centimeters traveled
}

/** END MOVE FORWARD **/


/** MOVE BACKWARD **/

float move_backward(oi_t *sensor, char input_centimeters) //positive input distance in cm
{
   float mm_traveled = 0;
   float angle_deviated = 0;

    while((abs(mm_traveled)) < (input_centimeters * 10.0)) //cm to mm with *10
    {
        oi_update(sensor);
        obstacle_check(sensor);

        mm_traveled += sensor->distance;
        angle_deviated += sensor->angle;

        if(uart_flag && (uart_data == ' '))       //brakes for manual mode
        {
            uart_flag = 0;
            break;
        }

        if(angle_deviated > degree_accuracy)      //if bot opened up to the left
        {
            forward_RWP += 1;                     //right wheel MAGNITUDE compensates by powering up
            angle_deviated = 0;                   //angle is reset, corrections are made per degree deviated
        }

        if(angle_deviated < -(degree_accuracy))   //if bot veered to the right
        {
            forward_RWP -= 1;                     //right wheel MAGNITUDE compensates by powering down
            angle_deviated = 0;                   //angle is reset, corrections are made per degree deviated
        }

        oi_setWheels(-forward_RWP, -forward_LWP); //power magnitude is set
    }

    uart_flag = 0; //clears flag to ensure unwanted inputs aren't counted
    oi_setWheels(0,0);
    return mm_traveled / 10; //returns distance traveled in cm
}

/** END MOVE BACKWARD **/


/** TURN CLOCKWISE **/

char turn_clockwise(oi_t *sensor, char input_angle)  //input positive angle, near perfect pivot due to due dynamic correction
{
    float mm_deviated = 0;
    float angle_deviated = 0;

    while(abs(angle_deviated) < (input_angle - 0.5)) //0.5 degree correction to account for bot's tendency to overshoot
    {
        if(uart_flag && (uart_data == ' '))          //brakes for manual mode
        {
            uart_flag = 0;
            break;
        }

        oi_update(sensor);

        mm_deviated += sensor->distance; //if the wheels have traveled an equal distance, mm_deviated will be 0
        angle_deviated += sensor->angle;

        if(mm_deviated > mm_accuracy)    //if distance is positive, left wheel needs powered down
        {
            c_LWP -= 1;
            mm_deviated = 0;
        }

        if(mm_deviated < -(mm_accuracy)) //if distance is negative, left wheel needs powered up
        {
            c_LWP += 1;
            mm_deviated = 0;
        }

        oi_setWheels(c_RWP , c_LWP);
    }

    oi_setWheels(0,0);
    uart_flag = 0;         //clears flag to ensure unwanted inputs aren't counted
    return angle_deviated; //returns angle deviated on same axis as scanner
}

/** END TURN CLOCKWISE **/


/** TURN COUNTER CLOCKWISE **/

char turn_counter_clockwise(oi_t *sensor, char input_angle) //input positive angle, near perfect pivot due to due dynamic correction
{
    float mm_deviated = 0;
    float angle_deviated = 0;

    while(angle_deviated < (input_angle - 0.5)) //0.5 degree correction to account for bot's tendency to overshoot
    {
        if(uart_flag && (uart_data == ' '))     //brakes for manual mode
        {
            uart_flag = 0;
            break;
        }

        oi_update(sensor);

        mm_deviated += sensor->distance;
        angle_deviated += sensor->angle;

        if(mm_deviated > mm_accuracy)
        {
            cc_RWP -= 1;
            mm_deviated = 0;
        }

        else if(mm_deviated < -(mm_accuracy))
        {
            cc_RWP += 1;
            mm_deviated = 0;
        }

        oi_setWheels(cc_RWP, cc_LWP);
    }

    oi_setWheels(0,0);
    uart_flag = 0;         //clears flag to ensure unwanted inputs aren't counted
    return angle_deviated; //returns angle deviated on same axis as scanner
}

/** END TURN COUNTER CLOCKWISE **/


/** TURN TO SCANNER ANGLE **/

char turn (oi_t *sensor, char input_angle) //normalizes turns to same axis as scanner data
{
    char angle_deviated = 0;

    input_angle = (180.0 / M_PI) * atan((17.5 * (tan(toRadians(input_angle)) + 10.5)) / 17.5); //corrects axis offset from scanner to wheel base

    if(input_angle > 90)      //bot starts at 90
    {
        angle_deviated = angle_deviated + turn_counter_clockwise(sensor, (input_angle - 90));  //normalizes angle to counter_clockwise input
    }

    else if(input_angle < 90) //bot starts at 90
    {
        angle_deviated = angle_deviated + turn_clockwise(sensor, (90 - input_angle));          //normalizes angle to clockwise input
    }

    else
    {
        oi_setWheels(0, 0);
    }

    return angle_deviated; //returns angle deviated on same axis as scanner
}

/** END TURN TO SCANNER ANGLE **/


/** PERPENDICULAR TO TAPE **/

void perp_to_tape(oi_t *sensor)
{
    if(!(current_status & tape_left))        //if left sensor is off the tape
    {
        oi_setWheels(0, 15);                 //crawls left wheel forward

        while(!(current_status & tape_left)) //masks all other bits in status register
        {
            oi_update(sensor);
            obstacle_check(sensor);
        }

        oi_setWheels(0, 0);
    }

    else if(!(current_status & tape_right))   //if right sensor is off the tape
    {
        oi_setWheels(15, 0);                  //crawls right wheel forward

        while(!(current_status & tape_right)) //masks all other bits in status register
        {
            oi_update(sensor);
            obstacle_check(sensor);
        }

        oi_setWheels(0, 0);
    }

    perp_to_tape(sensor);     //recursive call in case correction somehow took a wheel off the tape
    move_backward(sensor, 5); //move you back 5 cm from the tape
    oi_setWheels(0, 0);
}

/** END PERPENDICULAR TO TAPE **/


/** OBSTACLE/HAZARD CHECK **/

void obstacle_check(oi_t *sensor) // builds "status register" from each sensor check and prints the obstacle to putty
{
    previous_status = current_status; // saves status for comparison
    current_status = 0;               // clears status for new info
    char line[50];

    if (sensor->bumpLeft)
    {
        current_status |= left_bump;
        sprintf(line, "\n\r%-10s\n\r", "LEFT BUMP");
        uart_sendStr(line);
    }

    if (sensor->bumpRight)
    {
        current_status |= right_bump;
        sprintf(line, "\n\r%-10s\n\r", "RIGHT BUMP");
        uart_sendStr(line);
    }

    if (sensor->cliffLeftSignal < 10) //<10 is a hole
    {
        current_status |= hole_left;
        sprintf(line, "\n\r%-10s\n\r", "LEFT HOLE");
        uart_sendStr(line);
    }

    if (sensor->cliffRightSignal < 10) //<10 is a hole
    {
        current_status |= hole_right;
        sprintf(line, "\n\r%-10s\n\r", "RIGHT HOLE");
        uart_sendStr(line);
    }

    if (sensor->cliffFrontLeftSignal < 10) //<10 is a hole
    {
        current_status |= hole_front_left;
        sprintf(line, "\n\r%-10s\n\r", "FRONT LEFT HOLE");
        uart_sendStr(line);
    }

    if (sensor->cliffFrontRightSignal < 10) //<10 is a hole
    {
        current_status |= hole_front_right;
        sprintf(line, "\n\r%-10s\n\r", "FRONT RIGHT HOLE");
        uart_sendStr(line);
    }

    if (sensor->cliffLeftSignal > 2700) //>2700 is white tape
    {
        current_status |= tape_left;
        sprintf(line, "\n\r%-10s\n\r", "LEFT TAPE");
        uart_sendStr(line);
    }

    if (sensor->cliffRightSignal > 2700) //>2700 is white tape
    {
        current_status |= tape_right;
        sprintf(line, "\n\r%-10s\n\r", "RIGHT TAPE");
        uart_sendStr(line);
    }

    if (sensor->cliffFrontLeftSignal > 2700) //>2700 is white tape
    {
        current_status |= tape_front_left;
        sprintf(line, "\n\r%-10s\n\r", "FRONT LEFT TAPE");
        uart_sendStr(line);
    }

    if (sensor->cliffFrontRightSignal > 2700) //>2700 is white tape
    {
        current_status |= tape_front_right;
        sprintf(line, "\n\r%-10s\n\r", "FRONT RIGHT TAPE");
        uart_sendStr(line);
    }
}

/** END OBSTACLE/HAZARD CHECK **/
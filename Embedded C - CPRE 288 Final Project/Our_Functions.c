#include "Our_Functions.h"


/** IR VALUES **/

int Raw2dist(int IR_val)
{
    return 2*pow(10, 8) * pow(IR_val, -2.122); //Cybot 00
//    return 739277 * pow(IR_val, -1.461); //Cybot 02
}

/** END IR VALUES **/


/** DEGREES TO RADIANS **/

double toRadians(double degrees)
{
    return (M_PI / 180.0) * degrees;
}

/** END DEGREES TO RADIANS **/


/** LINEAR WIDTH **/

float lin_width(object_t *object)  //calculates the linear width of an object using the 1/2 * radial width and distance
{
    return 2 * (object->dist + 4.0) * tan(toRadians((object->end_angle - object->start_angle)) / 2.0); //2 * calculated opposite side of the triangle
}

/** END LINEAR WIDTH **/


/** GAP IDENTIFICATION **/

unsigned char gap_lin_width(object_t *object_list[10])
{
    unsigned char prev_obj = 0;
    unsigned char curr_obj = 0;
    unsigned max_width_angle = 0; //midpoint angle of the largest gap
    float distance;               //this is the ping distance of the closer object of the two forming the gap
    float max_lin_width = -1;     //width of largest gap, arbitrary negative number for more consistent comparisons 
    float lin_width;              //calulated linear width of gaps
    char line[70];                //for printout to putty

    sprintf(line, "%8s        %8s<----   %10s   ----->%8s      \r\n", "GAP_NUM", "St-Ang", "lin width", "End-Angle");
    uart_sendStr(line);

    for(curr_obj = 1; curr_obj < 10; curr_obj++) //previous object is always 0, current object always starts at 1
    {
        if(object_list[curr_obj]->dist > 0)      //ignores null objects
        {
            distance = (object_list[prev_obj]->dist < object_list[curr_obj]->dist) ? object_list[prev_obj]->dist : object_list[curr_obj]->dist; // gives us the smaller of the object distances
            lin_width = 2 * (distance + 4.0) * tan(toRadians((object_list[prev_obj]->start_angle - object_list[curr_obj]->end_angle)) / 2.0);   //calculates linear width of gap using the smaller distance

            sprintf(line, "%d        %4d<----   %03.3f   ----->%4d      \r\n", curr_obj, object_list[prev_obj]->start_angle, lin_width - 6.0, object_list[curr_obj]->end_angle);
            uart_sendStr(line);

            if(max_lin_width < lin_width)  //checks if new gap is wider than previous max
            {
                max_lin_width = lin_width; //tracks linear width of largest gap
                max_width_angle = (object_list[prev_obj]->start_angle - object_list[curr_obj]->end_angle) / 2.0; //midpoint of max width gap
            }

            prev_obj = curr_obj;
        }
    }

    return max_width_angle - 6; //6 cm adjustment for safety, gaps will print 6 cm narrower than calculated
}

/** END GAP IDENTIFICATION **/


/** SCANNING **/

void ScanVals(object_t *object[10], char startAngle, char endAngle)
{
    scan_data_t *sensor_data[181];                     //array of struct pointers for scan data
    int i = 0;

    for(i = 0; i<181; i++)
    {
        sensor_data[i] = malloc(sizeof(scan_data_t));  //allocates memory for array of structs
        sensor_data[i]->structIRdistance = 0;          //initializes all data to 0
        sensor_data[i]->structangle = 0;
    }


    int angle = 0;
    int j = 0;
    int total_IR = 0;
    // char line[50]; //for troubleshooting

    servo_rotate(startAngle); //rotates to start angle
    timer_waitMillis(100);    //time for servo to settle into start angle

    for(angle = startAngle; angle <= endAngle; angle += 1) //scans at any start/stop angle
    {
        total_IR = 0;                    //initializes sum to 0

        servo_rotate(angle);
        timer_waitMillis(ms_scan_delay); //wait for servo to rotate and stabilize

        for(j = 0; j < num_scans; j++)   //scans an amount of times specified in the header
        {
            total_IR += adc_read();      //sums raw IR values to be averaged
        }

        sensor_data[angle]->structIRdistance = Raw2dist(total_IR / num_scans);
        sensor_data[angle]->structangle = angle;

    //    sprintf(line, "%3d   %4d \r\n", angle, sensor_data[angle]->structIRdistance); //for IR data visibility
    //    uart_sendStr(line);
    }

    obj_detection(object, sensor_data, startAngle, endAngle); //processes scanned data into objects
    uart_flag = 0;                                            //clears flag to ensure duplicate inputs aren't counted
    servo_rotate(startAngle);                                 //sets servo back to start angle for next scan

    for(i = 0; i<181; i++) //frees memory allocated to scanner data array of structs
    {
        free(sensor_data[i]);
    }
}

/** END SCANNING **/


/** OBJECT DETECTION **/

/* NOTES:
 * The paramater object is a list of 10 pointers
 * The parameter sensor_data is a list of 180 sensor values
 * Function parses scan data starting at the end angle (closer to 180)
 * Updates global array of objects structs
 */

void obj_detection(object_t *object[10], scan_data_t *sensor_data[181], char start_angle, char end_angle)
{
    int i = 0;
    char obj_num = 0;

    for(i = 0; i<10; i++) //clears global object data (declared in main)
    {
        object[i]->dist = 0;
        object[i]->end_angle = 0;
        object[i]->lin_width = 0;
        object[i]->start_angle = 0;
        object[i]->midpoint_angle = 0;
    }

    int previous_distance = sensor_data[end_angle]->structIRdistance; //distance at end_angle to start comparing
    int distance_delta = 0;
    char radial_width = 0;

    char temp_end_angle, temp_start_angle, temp_midpoint_angle; //temporary values to track objects
    float temp_dist;                                            //temporary ping distance

    for(i = (end_angle - 1); i > start_angle; i--)                                  //first comp value would typically be 179 (if starting at 180),                                                                      
    {                                                                               //does not check distance at start angle
       distance_delta = abs(previous_distance - sensor_data[i]->structIRdistance);  //difference in distance between two IR distances

       if((distance_delta > edge_detection_threshold) && (sensor_data[i - 1]->structIRdistance < object_detection_radius)) //checks if delta is over threshold and NEXT distance is within radius
       {
           radial_width = 0;   //radial width of object
           temp_end_angle = i; //establishes start of alleged object

           while(i >= 0 && (sensor_data[i - 1]->structIRdistance < object_detection_radius))
           {
               radial_width++; //incriments width as long as values are within radius
               i--;            //continues object index (counts toward zero)
           }

           if(radial_width > disqualification_width && i > 0) 
           {
               temp_start_angle = i - 1;                                                         //establishes end of alleged object
               temp_midpoint_angle = temp_end_angle - ((temp_end_angle - temp_start_angle) / 2); //finds midpoint angle of alleged
               temp_dist = get_ping_dist_at_angle(temp_midpoint_angle);                          //finds ping distance at alleged object

               if(temp_dist < object_detection_radius)                    //rules out objects if they're outside our confidence radius
               {                                                          //data is parsed from 180 -> 0
                   object[obj_num]->end_angle = temp_end_angle;           //writes object data - end angle will be closer to 180
                   object[obj_num]->start_angle = temp_start_angle;       //writes object data - start angle will be closer to 0
                   object[obj_num]->midpoint_angle = temp_midpoint_angle;
                   object[obj_num]->dist = temp_dist;
                   object[obj_num]->lin_width = lin_width(object[obj_num]);
                   obj_num++;
               }
           }

           else
           {
               i = i + radial_width; //if object was a false positive, index is corrected here
           }
        }

        previous_distance = sensor_data[i]->structIRdistance; //sets new previous distance for comparison
     }
}

/** END OBJECT DETECTION **/


/** OBJECT VALIDATION **/

bool zone_marker_check(object_t *object[10]) //TODO: write function to verify smallest width object
{
    return;
}

/** END OBJECT VALIDATION **/


/** CLEAR PATH CHECK 
 * DESCRIPTION:
 * I used the width of the robot (35 cm), a "confidence radius" of 50 cm, and inverse tangent to find the radial width
 * of 2 triangular zones on the left and right of the robot. If any tall objects lie within these "conflict zones"
 * then the function will recognize them as "in the way" and calculate the distance you can travel in a straight path
 * without hitting them. These calculations are necessary becuase the objects can be within 50 cm without obstructing
 * the direct path ahead.
 * 
 * Calulations rely exclusively on midpoint angle and ping distance, ensuring accuracy.
 **/

float object_clear_check(object_t *object[10]) //returns how far you can travel in a straight line before hitting a tall object
{
    int i;
    float conflict_threshold = 0;   //distance for comparison with object ping distance
    float max_safe_dist = 50;       //50 cm is our "confidence radius"
    char mid_angle;                 //midpoint angle so I didn't have to write "object[i]->midpoint_angle" every time

    for(i = 0; i < 10; i++)
    {
        mid_angle = object[i]->midpoint_angle;

        if(mid_angle > 107)
        {
            conflict_threshold = (17.5 / cos(toRadians(180.0 - mid_angle))); //calulates hypotenuse of left side conflict triangle corresponding to object's midpoint angle

            if((conflict_threshold > (object[i]->dist + 4)) && (object[i]->dist < max_safe_dist)) //if object distance is within conflict threshold,
                {                                                                                 //you'll hit the object if you try and drive forward
                    max_safe_dist = object[i]->dist * sin(toRadians(181.0 - mid_angle)) - 4;      //forward distance you can travel from triangle just before conflict
                }
        }

        if(107 >= mid_angle && mid_angle >= 73)             //this isn't perfect, but objects directly ahead will return their ping distance as max_safe_distance
        {                                                   //function could be improved by splitting this middle zone at 90 and using trig in the same way as the other ranges
            conflict_threshold = object[i]->dist - 5;       //5 cm correction just to be safe 

            if(conflict_threshold < max_safe_dist)
                {
                    max_safe_dist = conflict_threshold - 5; //further 5 cm correction to be even safer
                }
        }

        if((73 > mid_angle) && (object[i]->dist > 0))                //only enters if distance is nonzero, ignoring null objects (null objects have a mid angle of 0)
        {
            conflict_threshold = (17.5 / cos(toRadians(mid_angle))); //calulates hypotenuse of right side conflict triangle corresponding to object's midpoint angle

            if((conflict_threshold > object[i]->dist + 4) && (object[i]->dist < max_safe_dist))  //if object distance is within conflict threshold,
                {                                                                                //you'll hit the object if you try and drive forward
                    max_safe_dist = object[i]->dist * sin(toRadians(mid_angle)) - 4;             //forward distance you can travel from triangle just after conflict
                }
        }
    }

    return max_safe_dist; //cm you can travel in a straight path ahead without hitting a tall object
}

/** END CLEAR PATH CHECK **/


/** IR CALIBRATION **/

void calibrate_IR(oi_t *sensor){
   char op[40];
   int i = 0, sum = 0;

   servo_rotate(90);
   for(i = 0; i<20; i++){
       sum += adc_read();
   }
   sum /= 20;

   //float ret_val = est_distance(sum);

   lcd_clear();
   sprintf(op, " %04d \r\n", sum);
   uart_sendStr(op);
}

/** END IR CALIBRATION **/
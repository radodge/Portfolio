#ifndef OUR_FUNCTIONS_H_
#define OUR_FUNCTIONS_H_


#include <math.h>
#include <stdbool.h>
#include <inc/tm4c123gh6pm.h>
#include <stdio.h>
#include <stdint.h>

#include "driverlib/interrupt.h"
#include "lcd.h"
#include "servo.h"
#include "open_interface.h"
#include "movement.h"
#include "uart_extra_help.h"
#include "adc.h"
#include "obstacle_avoidance.h"
#include "ping.h"
#include "Timer.h"
#include "button.h"


/** 
 * DESCRIPTION:
 * This is the central header file for all functionality. Each auxilliary header file contains
 * this header and no others.
**/


#define object_detection_radius 80  //distance radius - IR and ping distances outside the radius will NOT be considered
#define edge_detection_threshold 20 //deltas greater than this threshold will trigger the start/end of an object
#define disqualification_width 2    //objects narrower than this radial width will be disqualified as objects

#define num_scans 5                 //number of IR scans to be averaged
#define ms_scan_delay 40            //delay between IR scans within Scan_Vals - gives servo time to settle into angle

#define num_ping_scans 10           //number of ping scans to be averaged


typedef struct{                     //struct containing all info about objects
    char start_angle;
    char end_angle;
    char midpoint_angle;
    float lin_width;
    float dist;
}object_t;

typedef struct{                     //struct containing all info from each scan
    char structangle;
    int structIRdistance;
}scan_data_t;


double toRadians(double degrees);
void int2char(int input);
int Raw2dist(int IR_val);

float lin_width(object_t *object);
unsigned char gap_lin_width(object_t *object_list[10]);

void ScanVals(object_t *object[10], char startAngle, char endAngle);
void obj_detection(object_t *objects_list[10], scan_data_t *sensor_data[181], char start_angle, char end_angle);
float object_clear_check(object_t *objects_list[10]);


#endif /* OUR_FUNCTIONS_H_ */
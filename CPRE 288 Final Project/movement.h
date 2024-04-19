#ifndef MOVEMENT_H_
#define MOVEMENT_H_

#include "core_functions.h"

#define degree_accuracy 0.5 //this is the degree of deviation the driving forward/backward algorithim will correct for
#define mm_accuracy 1       //this is the mm deviance the turning algorithim will correct for

#define cc_LWP -50          //base wheel powers
#define c_RWP -50           //other wheel speeds are variables for dynamic correction
#define forward_LWP 80      //other wheel power variables are NOT GLOBALS becuase movement is restricted to primitive functions

typedef enum // these can be used to "mask" the status registers
{
    clear = 0,              // used for checking "if(current_status == clear)"
    left_bump = 1,          // bit 0 of current_status
    right_bump = 2,         // bit 1
    hole_left = 4,          // bit 2
    hole_front_left = 8,    // bit 3
    hole_right = 16,        // bit 4
    hole_front_right = 32,  // bit 5
    tape_right = 64,        // bit 6
    tape_left = 128,        // bit 7
    tape_front_right = 256, // bit 8
    tape_front_left = 256   // bit 8

} status;

void obstacle_check(oi_t *sensor);
void calibrate_wheels(oi_t *sensor);

float move_forward(oi_t *sensor, float input_centimeters);
float move_backward(oi_t *sensor, char input_centimeters);

char turn_clockwise(oi_t *sensor, char input_angle);
char turn_counter_clockwise(oi_t *sensor, char input_angle);
char turn (oi_t *sensor, char input_angle);

void perp_to_tape(oi_t *sensor);


#endif /* MOVEMENT_H_ */

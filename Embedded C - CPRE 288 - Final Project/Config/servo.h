#ifndef SERVO_H
#define SERVO_H


#include "Our_Functions.h"


#define servo_period 320000


void servo_init(void);
void servo_rotate(int angle);
void servo_calibrate();


#endif //SERVO_H

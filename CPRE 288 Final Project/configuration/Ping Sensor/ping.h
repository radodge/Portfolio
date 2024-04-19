#ifndef PING_H
#define PING_H

#include "core_functions.h"

extern volatile int overflow_count;


void ping_init(void);
void ping_interrupt_handler(void);
float ping_dist_est();
int ping_read();
float get_ping_dist_at_angle(char angle);


#endif /*PING_H*/

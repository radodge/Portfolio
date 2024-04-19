/*
 * button.h
 *
 *  Created on: Jul 18, 2016
 *      Author: Eric Middleton
 *
 * @edit: Phillip Jones 05/30/2019 : Removed uneeded helper functions
 */

#ifndef BUTTON_H_
#define BUTTON_H_


#include "Our_Functions.h"


extern volatile int button_event;
extern volatile int button_num;


//initialize the push buttons
void button_init();

// Initialize GPIO interrupts for buttons
void init_button_interrupts();

// handler for gpio event when button is pressed
void gpioe_handler();

///Non-blocking call
///Returns highest value button being pressed, 0 if no button pressed
uint8_t button_getButton();


#endif /* BUTTON_H_ */

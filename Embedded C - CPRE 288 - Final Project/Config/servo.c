#include "servo.h"

unsigned int Val_180 = 35800;     //Cybot 00
unsigned int Val_0 = 7950;

//unsigned int Val_180 = 35850;     //Cybot 01
//unsigned int Val_0 = 6950;

//unsigned int Val_180 = 35550;     //Cybot 02
//unsigned int Val_0 = 8150;

//unsigned int Val_180 = 34600;     //Cybot 03
//unsigned int Val_0 = 7550;

//unsigned int Val_180 = 37355;     //Cybot 07
//unsigned int Val_0 = 7881;

//unsigned int Val_180 = 37150;     //Cybot 10
//unsigned int Val_0 = 8450;

//unsigned int Val_180 = 35600;     //Cybot 11
//unsigned int Val_0 = 7250;

//unsigned int Val_180 = 35000;     //Cybot 12
//unsigned int Val_0 = 7000;


extern volatile int edge;
volatile unsigned int fallingedge;
volatile unsigned int risingedge;
int edgetime;


void servo_init(void)
{

    SYSCTL_RCGCGPIO_R   |= 0b000010;    //Enable GPIO PB Clk
    SYSCTL_RCGCTIMER_R  |= 0b000010;    //Enable Timer 1 Clk

    while((SYSCTL_PRGPIO_R  & 0b0010) == 0){};   //Waiting for the reset to go through
    while((SYSCTL_PRTIMER_R & 0b0010) == 0){};

    GPIO_PORTB_DEN_R    |= 0b00100000;      //Enable Digital Function
    GPIO_PORTB_DIR_R    |= 0b00100000;      //Set PB5 as output
    GPIO_PORTB_AFSEL_R  |= 0b00100000;      //Enable Alternate Function for PB5
    GPIO_PORTB_PCTL_R   &= 0xFF0FFFFF;      //Clear PCTL for PB5
    GPIO_PORTB_PCTL_R   |= 0x00700000;      //Alternate Function set to T1CCP1

    TIMER1_CTL_R        &= 0b011111111;     //Disable Timer1 B (TBEN)
    TIMER1_CFG_R        = 0x00000004;       //16 bit timer config
    TIMER1_TBMR_R       &= 0xFFFFFFF0;      //Clears bits 3:0
    TIMER1_TBMR_R       |= 0b1010;          //PWM Mode, Edge-Count Mode, Periodic Timer Mode
    TIMER1_CTL_R        &= 0xFFFFBFFF;      //Output is not inverted

    TIMER1_TBILR_R = servo_period; //sets 16 bit load register to 16 LSB of period
    TIMER1_TBPR_R = (servo_period >> 16); //sets 8 bit prescaler to 8 MSB of period
    TIMER1_TBMATCHR_R = 296000;
    TIMER1_TBPMR_R = (296000 >> 16);

    TIMER1_CTL_R        |= 0b100000000;     //Re-Enable Timer1 B
}

void servo_rotate(int angle)
{
    int clock_cycles;
    clock_cycles = round((((Val_180 - Val_0) / 180.0) * angle) + Val_0);

    TIMER1_TBMATCHR_R = servo_period - clock_cycles; //total period - pulse width
    TIMER1_TBPMR_R = ((servo_period - clock_cycles) >> 16);
}

void servo_calibrate()
{
    unsigned int pulse_width = 30000;
    unsigned int left, right;

    while(1)
    {
        if(uart_flag && (uart_data == 'x'))
        {
            uart_flag = 0;
            break;
        }

        TIMER1_TBMATCHR_R = servo_period - pulse_width;
        TIMER1_TBPMR_R = ((servo_period - pulse_width) >> 16);

        if((button_num == 4) && button_event)
        {
           button_event = 0;
           pulse_width -= 1000;
        }

        if((button_num == 3) && button_event)
        {
           button_event = 0;
           pulse_width -= 50;
        }

        if((button_num == 2) && button_event)
        {
           button_event = 0;
           pulse_width += 50;
        }

        if((button_num == 1) && button_event)
        {
            button_event = 0;
            pulse_width += 1000;
        }

        timer_waitMillis(100);
        lcd_printf("press x for next     Val_180= %d", pulse_width);
    }

    button_event = 0;
    left = pulse_width;
    pulse_width = 7000;

    while(1)
    {
        if(uart_flag && (uart_data == 'x'))
        {
            uart_flag = 0;
            break;
        }

        TIMER1_TBMATCHR_R = servo_period - pulse_width;
        TIMER1_TBPMR_R = ((servo_period - pulse_width) >> 16);

        if((button_num == 4) && button_event)
        {
           button_event = 0;
           pulse_width -= 1000;
        }

        if((button_num == 3) && button_event)
        {
           button_event = 0;
           pulse_width -= 50;
        }

        if((button_num == 2) && button_event)
        {
           button_event = 0;
           pulse_width += 50;
        }

        if((button_num == 1) && button_event)
        {
            button_event = 0;
            pulse_width += 1000;
        }

        timer_waitMillis(10);
        lcd_printf("press x for done     Val_0= %d", pulse_width);
    }

    right = pulse_width;
    lcd_printf("Val_180= %d Val_0= %d", left, right);

    return;
}




#include "ping.h"


//volatile unsigned int timer_val = 0 ;
volatile char flag = 0;
volatile unsigned int risingEdge = 0;
volatile unsigned int fallingEdge = 0;

volatile int overflow_count = 0;

void ping_init(void)
{
    // Clock Enable Stuff
    SYSCTL_RCGCGPIO_R  |= 0b000010;  //Enable Port B Clock
    SYSCTL_RCGCTIMER_R |= 0b001000;  //Enable Timer3 Clk

    while((SYSCTL_PRGPIO_R  & 0b0010) == 0){};   //Waiting for the reset to go through
    while((SYSCTL_PRTIMER_R & 0b1000) == 0){};

    //GPIO STUFF
    GPIO_PORTB_DEN_R   |= 0b00001000;  //Set PB3 as Digital
    GPIO_PORTB_PCTL_R  &= 0xFFFF0FFF;  //Setting 4 PMUX bits to 0
    GPIO_PORTB_PCTL_R  |= 0x7000;       //Set AF to T3CCP1
    GPIO_PORTB_AFSEL_R |= 0b00001000;  //Setting AF for GPIOB_3 to PCTL
//    timer_init(); //Initialize Timers //TODO*******************************************************


    TIMER3_CTL_R     &= 0xFFFFFEFE;     //Clear TBEN and TAEN
    TIMER3_CFG_R      = 0x4;            //Set T3 to 16/32 bit
    TIMER3_TBMR_R    |= 0b000000000111; //Edge-Time mode, Capture Mode
    TIMER3_TBMR_R    &= 0xFFFFFFEF;     //Timer counts down ~0x10
    TIMER3_CTL_R     |= 0b110000000000; //Both edges
    TIMER3_TBPR_R     = 0xFF;           //Extension
    TIMER3_TBILR_R    = 0xFFFF;         //Value where timer starts counting down
    TIMER3_IMR_R     |= 0b010000000000; //Enable timer B capture mode event interrupt
    TIMER3_ICR_R     |= 0b010000000000; //Clearing the Interrupt
    TIMER3_CTL_R     |= 0b100000000;    //Enable Timer B

    // NVIC enable
    NVIC_EN1_R      |= 0x00000010;    //Enable 16/32 T3B Interrupt
    NVIC_PRI9_R     &= 0xFFFFFF0F;
    NVIC_PRI9_R     |= 0x00000020;

    IntRegister(INT_TIMER3B, ping_interrupt_handler);
    IntMasterEnable();
}


void ping_interrupt_handler(void)
{
    int i = 0;
    if(TIMER3_MIS_R & 0b10000000000)
    {
        flag++;
//        timer_val = TIMER3_TBR_R;
        TIMER3_ICR_R |=  0b10000000000;      //Clear Timer B interrupt (CBECINT)
                if (flag == 1)
                {
                    risingEdge = TIMER3_TBR_R;
        //            timer_val = 0;
                }
                else if (flag == 2)
                {
                    fallingEdge = TIMER3_TBR_R;
        //            timer_val = 0;
                    flag++;
            }
    }

}


int ping_read(void)
{
//    unsigned int risingEdge = 0;
//    unsigned int fallingEdge = 0;
    int totalCounts = 0;



    //Initial Pulse
    TIMER3_CTL_R        &= 0xFFFFFEFF;        //Disable Timer 3B
    TIMER3_IMR_R        &= 0xFFFFFBFF;        //Mask TB3 Interrupt
    GPIO_PORTB_AFSEL_R  &= 0b11110111;        //Clear PB3 AFSEL to ensure it is function as GPIO
    GPIO_PORTB_DIR_R    |= 0b00001000;        //Set PB3 as output

    //send init pulse
    GPIO_PORTB_DATA_R   &= 0b11110111;      //Clear Initial Pulse
    GPIO_PORTB_DATA_R   |= 0b00001000;      //Begin Initial Pulse
    timer_waitMicros(5);                    //Wait 5 us
    GPIO_PORTB_DATA_R   &= 0b11110111;      //End Initial Pulse


    //Reading Values
    TIMER3_ICR_R        |= 0b010000000000;  //Clear Timer B interrupt (CBECINT)
    GPIO_PORTB_AFSEL_R  |= 0b00001000;      //Set PB3 AFSEL to Hardware Capture Mode
    TIMER3_IMR_R        |= 0b10000000000;   //Unmask TB3 Interrupt
    TIMER3_CTL_R        |= 0x100;
    GPIO_PORTB_DIR_R &= 0b11110111; //Set PB3 as input  //TODO SUS>>>>?????????**************************


    while (flag < 3)
    {
//        if (flag == 1)
//        {
//            risingEdge = timer_val;
////            timer_val = 0;
//        }
//        else if (flag == 2)
//        {
//            fallingEdge = timer_val;
////            timer_val = 0;
//            flag++;
//        }
    }
    flag = 0;

    totalCounts = risingEdge - fallingEdge;

    return totalCounts;

}

float ping_dist_est()
{
    int totalCounts = ping_read();

    const float clockPeriod = 62.5; //nanoseconds
    const int speed = 343; //meters / second

    if (totalCounts < 0)
    {
        fallingEdge = (16777216-1) - fallingEdge; //subtract falling edge from 2^24 - 1
        totalCounts = fallingEdge + risingEdge;
        overflow_count++;
    }

    return (speed*100.0 * ((totalCounts * clockPeriod) / 1000000000.0)/2.0);
}


/** PING DISTANCE **/ //moved here from Our_Functions.c

float get_ping_dist_at_angle(char angle)
{
    int j = 0;
    double ping_dist = 0;

    servo_rotate(angle);   //rotate to midpoint
    timer_waitMillis(500); //lets servo settle into new angle

    ping_dist = ping_dist_est();
    timer_waitMillis(100);

    for(j = 0; j < num_ping_scans - 1; j++)
    {
        ping_dist += ping_dist_est();
        timer_waitMillis(100);
    }

    return ping_dist / num_ping_scans; //returns average of scans
}

/** END PING DISTANCE **/
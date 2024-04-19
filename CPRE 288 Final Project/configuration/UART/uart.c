#include "uart.h"

volatile char uart_flag = 0;
volatile char uart_data = 0;


void uart_init(int baud)
{
    SYSCTL_RCGCGPIO_R  |= 0b000010;      // enable clock GPIOB (page 340)
    SYSCTL_RCGCUART_R  |= 0b00000010;    // enable clock UART1 (page 344)
    GPIO_PORTB_AFSEL_R |= 0b00000011;    // sets PB0 and PB1 as peripherals (page 671)
    GPIO_PORTB_PCTL_R  |= 0b00010001;    // pmc0 and pmc1       (page 688)  also refer to page 650
    GPIO_PORTB_PCTL_R  &= 0xFFFFFF11;    // pmc0 and pmc1       (page 688)  also refer to page 650
    GPIO_PORTB_DEN_R   |= 0b00000011;    // enables pb0 and pb1
    GPIO_PORTB_DIR_R   |= 0b00000001;    // sets pb0 as output, pb1 as input


    //compute baud values [UART clock= 16 MHz] 
    double fbrd;        //floating part
    int    ibrd;

    //16000000/(16*115200) 8.68055555556
    //.68055555556*64+0.5 = 44.0555555558 -> 44
    fbrd = 44; // page 903
    ibrd = 8;

    UART1_CTL_R &= 0xFFFFFFFE;      // disable UART1 (page 918)
    UART1_IBRD_R = ibrd;        // write integer portion of BRD to IBRD
    UART1_FBRD_R = fbrd;   // write fractional portion of BRD to FBRD
    UART1_LCRH_R = 0b01100000;        // write serial communication parameters (page 916) * 8bit and no parity
    UART1_CC_R   = 0b0000;          // use system clock as clock source (page 939)
    UART1_CTL_R |= 0x00000001;        // enable UART1

}


void uart_sendChar(char data)
{
   // write to UARTDR
    while((UART1_FR_R&0x20) !=0)
    {}
    UART1_DR_R = data;
}


char uart_receive(void)
{
    char data;

    while(UART1_FR_R&0b00010000) //FIFO is not full, we wait. Then we read.
    {}
    data = UART1_DR_R;
    return (char) (0xFF & data);
 
}


void uart_sendStr(const char *data)
{
    while(*data != 0)
    {
        uart_sendChar(*data);
        data++;
    }

}


void uart_interrupt_init()
{
    UART1_IM_R |= 0x10; //enable interrupt on receive - page 924

    // Find the NVIC enable register and bit responsible for UART1 in table 2-9
    // Note: NVIC register descriptions are found in chapter 3.4
    NVIC_EN0_R |= 0x40; //enable uart1 interrupts - page 104

    // Find the vector number of UART1 in table 2-9 ! UART1 is 22 from vector number page 104
    IntRegister(INT_UART1, uart_interrupt_handler); //give the microcontroller the address of our interrupt handler - page 104 22 is the vector number
}


void uart_interrupt_handler()
{
    if (UART1_MIS_R & 0b00010000)
    {
        uart_data = 0xFF & UART1_DR_R;
    }

    uart_flag = 1;
    UART1_ICR_R |= 0x10;
}
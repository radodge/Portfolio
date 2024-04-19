#include "adc.h"


void adc_init(void)
{
    SYSCTL_RCGCADC_R |= 0x1;
    SYSCTL_RCGCGPIO_R |= 0x2;
    GPIO_PORTB_DEN_R   &= 0b11101111;
    GPIO_PORTB_AFSEL_R |= 0b00010000;
    GPIO_PORTB_AMSEL_R |= 0b00010000;

    // Using SS3
    ADC0_ACTSS_R  &= 0b0111;    //disabling SS3
    ADC0_EMUX_R  &= 0x0FFF;    //
//    ADC0_EMUX_R |= 0x4000;  // Setting trigger to just GPIO
    ADC0_SSMUX3_R = 0xA;
    ADC0_SSCTL3_R = 0b0110;      // Interrupt and end bit
    ADC0_IM_R    |= 0b1000;      // Mask for SS3
    ADC0_ACTSS_R |= 0b1000;    // Enable SS3
//    NVIC_EN0_R |= 0x00020000; //17
}

int adc_read(void)
{
    ADC0_PSSI_R |= 0b1000;

    while(~ADC0_RIS_R & 0b1000){}

    ADC0_ISC_R |= 0b1000;
    
    return ADC0_SSFIFO3_R & 0xFFF;
}

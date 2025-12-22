#include "Utils.h"

// // Tell the library that these variables are defined in the main sketch
// extern volatile unsigned int pulse_count;
// extern const int pulses_per_rev

volatile unsigned int pulse_count = 0;
const int pulses_per_rev = 2;
const int pwm_bit_depth =65536;


int readFanSpeed() {
    noInterrupts();
    pulse_count = 0;
    interrupts();
    unsigned long start_time = millis();
    
    // Wait for 1 second to accumulate pulses
    while (millis() - start_time < 1000) {
        yield(); 
    }

    noInterrupts();
    unsigned int pulses = pulse_count;
    interrupts();

    float revolutions = (float)pulses / pulses_per_rev;
    return (int)(revolutions * 60.0);
}

int percentage_To_Pwm(int percentage) {
    return (int)(percentage * pwm_bit_depth) / 100-1;

}
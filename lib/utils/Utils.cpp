#include "Utils.h"

// // Tell the library that these variables are defined in the main sketch
// extern volatile unsigned int pulse_count;
// extern const int pulses_per_rev

volatile unsigned int fan_pulse_count = 0;
const int pulses_per_rev = 2;
const int pwm_bit_depth =65536;


int readFanSpeed() {
    noInterrupts();
    fan_pulse_count = 0;
    interrupts();
    unsigned long start_time = millis();
    
    // Wait for 1 second to accumulate pulses
    while (millis() - start_time < 1000) {
        yield(); 
    }

    noInterrupts();
    unsigned int pulses = fan_pulse_count;
    interrupts();

    float revolutions = (float)pulses / pulses_per_rev;
    return (int)(revolutions * 60.0);
}

void fan_Counter() {
  fan_pulse_count++;                // Interrupt: happens on each tach pulse
}

int readFanSpeed_Updated(int tach_pin) {
    // 1. Reset count and attach interrupt right now
    fan_pulse_count = 0;
    
    // Dynamically attach the interrupt only for this measurement
    attachInterrupt(digitalPinToInterrupt(tach_pin), fan_Counter, FALLING);
    
    unsigned long start_time = millis();
    
    // 2. Wait for 1 second to accumulate pulses
    while (millis() - start_time < 1000) {
        yield(); // Keeps the watchdog happy and background tasks running
    }

    // 3. Immediately detach the interrupt so the fan stops "poking" the CPU
    detachInterrupt(digitalPinToInterrupt(tach_pin));

    // 4. Calculate RPM
    unsigned int pulses;
    pulses = fan_pulse_count;
    float revolutions = (float)pulses / pulses_per_rev;
    return (int)(revolutions * 60.0);
}

int percentage_To_Pwm(int percentage) {
    return (int)(percentage * pwm_bit_depth) / 100-1;

}
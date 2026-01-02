#ifndef UTILS_H
#define UTILS_H
#include <Arduino.h>  // <--- Add this line

extern volatile unsigned int fan_pulse_count;

int readFanSpeed();
void fan_Counter();
int readFanSpeed_Updated(int tach_pin);
int percentage_To_Pwm(int percentage); 

#endif
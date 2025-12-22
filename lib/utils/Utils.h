#ifndef UTILS_H
#define UTILS_H
#include <Arduino.h>  // <--- Add this line

extern volatile unsigned int pulse_count;

int readFanSpeed();

int percentage_To_Pwm(int percentage); 

#endif
#ifndef UTILS_H
#define UTILS_H
#include <Arduino.h>  // <--- Add this line

extern volatile unsigned int fan_pulse_count;



int readFanSpeed();
void fan_Counter();
int readFanSpeed_Updated(int tach_pin);
int percentage_To_Pwm(int percentage); 

//for the ina3221 readings
// 🔹 Forward declaration (NO include needed here)
class Adafruit_INA3221;
struct Ina3221Reading {
  float voltage_V;
  float current_mA;
  float power_mW;
};

Ina3221Reading readIna3221Channel(Adafruit_INA3221& ina3221, uint8_t channel);

#endif
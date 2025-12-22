// PWM control is the blue wire
// green does the RPM measurement

#include <Arduino.h>
#include "Utils.h"


const int fan_pwm_pin = GPIO2;      // PWM control pin for the fan
const int tach_pin    = GPIO3;      // Tachometer signal input pin
const int fan_power_percentage = 100; //

// volatile unsigned int pulse_count = 0; // Use unsigned int for pulse count
// unsigned long last_measure = 0;

// const int pulses_per_rev = 2;   // Most PC fans produce 2 pulses per revolution

void counter(); 

void setup() {
  // Use a higher baud rate for faster serial communication
  Serial.begin(115200); 

  /****************************************************
 * CONFIGURATION FOR PWM PIN
 ****************************************************/
  pinMode(fan_pwm_pin, OUTPUT);
  // Keep INPUT_PULLUP - essential for open-drain tachometer output
  pinMode(tach_pin, INPUT_PULLUP); 

  // Set the power
  int pwm_value = percentage_To_Pwm(fan_power_percentage);
  Serial.println(pwm_value);
  analogWrite(fan_pwm_pin,pwm_value); 

  // Interrupt on tach pin
  attachInterrupt(digitalPinToInterrupt(tach_pin), counter, FALLING);
}

void loop() {

  int rpm = readFanSpeed();

  Serial.print("Fan RPM: ");
  Serial.println(rpm);
}


void counter() {
  pulse_count++;                // Interrupt: happens on each tach pulse
}
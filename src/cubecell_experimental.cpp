#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

void setup() {
  pwm.begin();
  pwm.setPWMFreq(1600); // Max frequency for quietest operation
}

/**
 * Sets the fan speed on a specific PCA9685 channel
 * @param channel: The pin number on the board (0 through 15)
 * @param percent: Speed from 0 to 100
 */
void setFanSpeed(int channel, int percent) {
  // 1. Safety: Keep inputs within physical limits
  channel = constrain(channel, 0, 15);
  percent = constrain(percent, 0, 100);
  
  // 2. Convert 0-100% to 0-4095 (12-bit resolution)
  int dutyCycle = map(percent, 0, 100, 0, 4095);
  
  // 3. Set the PWM
  // Parameters: (channel, pulse_start_time, pulse_end_time)
  pwm.setPWM(channel, 0, dutyCycle);
}

void loop() {
  // Example: Run Fan 1 (Channel 0) at 50%
  setFanSpeed(0, 0);
  delay(5000); 
  setFanSpeed(0, 50);
  delay(5000); 
  setFanSpeed(0, 100);
  delay(5000); 

}
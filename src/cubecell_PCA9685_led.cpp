#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

void setup() {
  pwm.begin();
  // Set frequency once (1000Hz is very smooth for LEDs)
  pwm.setPWMFreq(1000); 
}

void loop() {
  // Fade IN: Increase brightness from 0 to 4095
  for (int brightness = 0; brightness <= 4095; brightness += 5) {
    // setPWM(channel, on_time, off_time)
    pwm.setPWM(0, 0, brightness);
    delay(2); 
  }

  // Fade OUT: Decrease brightness from 4095 to 0
  for (int brightness = 4095; brightness >= 0; brightness -= 5) {
    pwm.setPWM(0, 0, brightness);
    delay(2);
  }
}
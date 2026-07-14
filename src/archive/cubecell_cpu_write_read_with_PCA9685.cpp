#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include "Utils.h"

// Initialize the external PWM Board
Adafruit_PWMServoDriver pwmBoard = Adafruit_PWMServoDriver();

// Configuration
const int fan_tach_pin = GPIO1;  // Green/Yellow wire
const int pwm_channel = 0;   // Where the Blue wire is on PCA9685
const int target_speed_pct = 80; // 50% Speed
const int fan_speed_measurement_timems = 500; 

void setup() {
  Serial.begin(115200);

  // 1. Initialize the I2C PWM Controller
  //check if the board is responding
    if (!pwmBoard.begin()) {
          Serial.println("PWM Board Fail!");
          while (1);
      }
  // pwmBoard.begin(0x41);
  pwmBoard.setPWMFreq(1600); // Efficient frequency for CPU fans

  // 2. Setup the Tachometer pin (from your Utils logic)
  pinMode(fan_tach_pin, INPUT_PULLUP);

  // 3. Set the Fan Speed using the new I2C hardware
  Serial.print("Setting Fan to: ");
  Serial.print(target_speed_pct);
  Serial.println("%");
  
  // We use the new external control function
  setExternalFanSpeed(pwmBoard, pwm_channel, target_speed_pct);
}

void loop() {
  // Use your Utils function to read the RPM
  // This handles the attach/detach interrupt logic you wrote
  int current_rpm = readFanSpeed_Updated(fan_tach_pin,fan_speed_measurement_timems );

  Serial.print("Monitoring Fan - RPM: ");
  Serial.println(current_rpm);

  // In a weather station, you'd insert your Deep Sleep logic here.
  // The PCA9685 will keep the fan spinning at 50% while CubeCell sleeps.
  delay(2000); 
}


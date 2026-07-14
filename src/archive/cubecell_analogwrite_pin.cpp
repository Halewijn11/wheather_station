#include <Arduino.h>


// Define the pin you want to use for analogWrite (must support PWM)
const int cubecell_analogwrite_pin = GPIO2;  // change to a valid PWM pin

// Analog value range is typically 0–255 on CubeCell
int analogValue = 32000;  // 50% duty cycle

void setup() {
  // Set the pin as output
  pinMode(cubecell_analogwrite_pin, OUTPUT);
}

void loop() {
  // Write analog (PWM) value to the pin
  analogWrite(cubecell_analogwrite_pin, analogValue);

  delay(100);

  // Example: ramp up brightness
  analogValue += 1000;
  if (analogValue > 64000) {
    analogValue = 0;
  }
}

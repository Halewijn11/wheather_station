#include <Arduino.h>
#include <Wire.h>
#include "Adafruit_INA3221.h"
#include "Utils.h" // Ensures we can use Ina3221Reading and readIna3221Channel

// Create the sensor object
Adafruit_INA3221 ina3221;

// Configuration
const float MAX_VANE_VOLTAGE = 3.3; // The voltage when the vane is at ~359 degrees

void setup() {
  Serial.begin(115200);
  
  // Initialize I2C and the INA3221
  if (!ina3221.begin(0x40, &Wire)) {
    Serial.println("Failed to find INA3221 chip");
    while (1);
  }

  // Set internal averaging for a cleaner signal
  ina3221.setAveragingMode(INA3221_AVG_16_SAMPLES);
  
  Serial.println("Direct Wind Vane Reading (Voltage to Degrees)");
}

void loop() {
  // 1. Use your custom utility function to read Channel 3 (index 2)
  Ina3221Reading r = readIna3221Channel(ina3221, 2);
  
  // 2. Extract the voltage
  float currentVoltage = r.voltage_V;

  // 3. Simple mapping: (Current Voltage / Max Voltage) * 360 degrees
  float degrees = (currentVoltage / MAX_VANE_VOLTAGE) * 360.0;

  // 4. Print the results
  Serial.print("Vane Voltage: ");
  Serial.print(currentVoltage, 3); // 3 decimal places
  Serial.print("V | Direction: ");
  Serial.print(degrees, 1);
  Serial.println("°");

  delay(500); // Wait half a second between readings
}
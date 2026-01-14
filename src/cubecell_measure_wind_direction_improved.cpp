#include <Arduino.h>
#include <Wire.h>
#include "Adafruit_INA3221.h"
#include "Utils.h" // This gives us access to getWindDirection and the Structs

// 1. Create the sensor object
Adafruit_INA3221 ina3221;

void setup() {
//   digitalWrite(Vext, HIGH);
  Serial.begin(115200);
  
  //################## Initialize the INA3221 sensor ###############################3
  Wire.begin();

  // 3. Initialize the INA3221 chip
  if (!ina3221.begin(0x40, &Wire)) {
    Serial.println("Failed to find INA3221 chip!");
    while (1); // Halt if sensor not found
  }

  // 4. Set averaging for stability (16 samples)
  ina3221.setAveragingMode(INA3221_AVG_16_SAMPLES);
  

  
  Serial.println("Weather Station: Wind Direction Test");
}

void loop() {
  // 5. Read Channel 3 (Index 2) using your utility function
  Ina3221Reading reading = readIna3221Channel(ina3221, 2);
  
  // 6. Use your helper function to convert Voltage to Degrees
  // We pass 3.3 as the maxVoltage
  float degrees = getWindDirection(reading.voltage_V, 3.3);

  // 7. Print the results
  Serial.print("Vane Voltage: ");
  Serial.print(reading.voltage_V, 3);
  Serial.print("V | Direction: ");
  Serial.print(degrees, 1);
  Serial.println("°");

  delay(500); // Take a reading every half second
}
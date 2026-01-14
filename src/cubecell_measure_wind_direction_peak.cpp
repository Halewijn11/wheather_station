#include <Arduino.h>
#include <Wire.h>
#include "Adafruit_INA3221.h"
#include "Utils.h"

Adafruit_INA3221 ina3221;
float peakVoltage = 0.0;

void setup() {
  Serial.begin(115200);
  ina3221.begin(0x40, &Wire);
  ina3221.setAveragingMode(INA3221_AVG_16_SAMPLES);
  Serial.println("--- CALIBRATION MODE ---");
  Serial.println("Spin the vane slowly 360 degrees...");
}

void loop() {
  Ina3221Reading r = readIna3221Channel(ina3221, 2);
  float v = r.voltage_V;

  if (v > peakVoltage) {
    peakVoltage = v;
  }

  // Calculate degrees based on the current peak found
  float degrees = (v / (peakVoltage > 0 ? peakVoltage : 3.3)) * 360.0;

  Serial.print("Current: "); Serial.print(v, 3);
  Serial.print("V | Peak Found: "); Serial.print(peakVoltage, 3);
  Serial.print("V | Calculated Angle: "); Serial.print(degrees, 1);
  Serial.println("°");

  delay(200);
}
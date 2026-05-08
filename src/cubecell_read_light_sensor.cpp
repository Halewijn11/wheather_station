#include <Wire.h>
#include <Adafruit_ADS1X15.h>
#include <Arduino.h>

Adafruit_ADS1115 ads;

void setup() {
  Serial.begin(115200);
  // The Davis sensor output is 0-3V, so we use GAIN_ONE (+/- 4.096V range)
  
  ads.setGain(GAIN_ONE); 
  if (!ads.begin()) {
    Serial.println("Failed to initialize ADS1115!");
    while (1);
  }
}

void loop() {
  int16_t results = ads.readADC_SingleEnded(0);
  
  // Convert raw value to millivolts (at GAIN_ONE, 1 bit = 0.125mV)
  float millivolts = results * 0.125;
  
  // Davis 6450 Scale: 1.67 mV per W/m^2
  float solarRadiation = millivolts / 1.67;

  Serial.print("Radiation: ");
  Serial.print(solarRadiation);
  Serial.println(" W/m^2");

  delay(2000);
}
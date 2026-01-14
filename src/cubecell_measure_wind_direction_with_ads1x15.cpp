#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_ADS1X15.h>
#include "Utils.h" // Assuming this still contains getWindDirection

Adafruit_ADS1115 ads;

void setup() {
  Serial.begin(115200);
  
  // Initialize the ADS1115
  // GAIN_ONE gives a range of +/- 4.096V (1 bit = 0.125mV)
  ads.setGain(GAIN_ONE); 
  
  if (!ads.begin()) {
    Serial.println("Failed to initialize ADS1115!");
    while (1);
  }

  Serial.println("Weather Station: Wind");
}

void loop() {
  // --- 1. READ WIND DIRECTION (Channel 2) ---
  int16_t windRaw = ads.readADC_SingleEnded(1);
  // Convert raw value to Volts: (Raw * 0.125mV) / 1000
  float windVolts = (windRaw * 0.125) / 1000.0;
  
  // Use your utility function for degrees
  float degrees = getWindDirection(windVolts, 3.3);
  

  // --- 3. PRINT RESULTS ---
  Serial.print("Wind Vane: ");
  Serial.print(windVolts, 3);
  Serial.print("V -> Direction: ");
  Serial.println(degrees, 1);

  delay(1000);
}
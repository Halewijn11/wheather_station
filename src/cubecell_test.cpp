#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_ADS1X15.h>
#include "Utils.h" 

Adafruit_ADS1115 ads;

// Global variables to track Min and Max
float minDegrees = 361.0; // Start higher than possible
float maxDegrees = -1.0;  // Start lower than possible

void setup() {
  Serial.begin(115200);
  
  ads.setGain(GAIN_ONE); 
  
  if (!ads.begin()) {
    Serial.println("Failed to initialize ADS1115!");
    while (1);
  }

  Serial.println("Weather Station: Wind Tracking Started");
}

void loop() {
  // --- 1. READ WIND DIRECTION ---
  int16_t windRaw = ads.readADC_SingleEnded(1);
  float windVolts = (windRaw * 0.125) / 1000.0;
  
  float degrees = getWindDirection(windVolts, 3.3);

  // --- 2. UPDATE MIN/MAX ---
  // Only update if we have a valid reading (assuming getWindDirection returns >= 0)
  if (degrees >= 0) {
    if (degrees < minDegrees) {
      minDegrees = degrees;
    }
    if (degrees > maxDegrees) {
      maxDegrees = degrees;
    }
  }

  // --- 3. PRINT RESULTS ---
  Serial.print("Current: ");
  Serial.print(degrees, 1);
  Serial.print("° | Min: ");
  Serial.print(minDegrees, 1);
  Serial.print("° | Max: ");
  Serial.print(maxDegrees, 1);
  Serial.println("°");

  // Note: In your main LoRa script, you should reset min/max 
  // after every successful transmit:
  // minDegrees = 361.0; maxDegrees = -1.0;

  delay(200);
}
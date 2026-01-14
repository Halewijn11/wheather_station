#include <Arduino.h>
#include <Utils.h>
#include "Adafruit_INA3221.h"
#include <Wire.h>


// #################### initialize the INA3221 sensor ###############################3
// 1. Create the sensor object
Adafruit_INA3221 ina3221;


// --- GLOBAL VARIABLES ---
WindDirectionTracker windStats;
const int sampleWindow = 15; // 15 seconds


void setup() {
   Serial.begin(115200);

  //################## Initialize the INA3221 sensor ###############################3
  Wire.begin();
  if (!ina3221.begin(0x40, &Wire)) {
    Serial.println("Failed to find INA3221 chip!");
    while (1); // Halt if sensor not found
  }
  ina3221.setAveragingMode(INA3221_AVG_16_SAMPLES); // 4. Set averaging for stability (16 samples)

  
}

void loop() {
    Serial.println("--- Starting New 15s Measurement Window ---");
    windStats.reset(); 

    for (int i = 1; i <= sampleWindow; i++) {
        // 1. Simulate/Read voltage from your sensor pin (e.g., A0)
        // Adjust the 4095.0 if your ADC is different (1023 for older Arduinos)
        // float rawVoltage = analogRead(A0) * (3.3f / 4095.0f);
        
        // ###################for the wind direction sensor ###############################3
        Ina3221Reading reading = readIna3221Channel(ina3221, 2);
        float currentDegrees = getWindDirection(reading.voltage_V, 3.3f);
        windStats.update(currentDegrees);



        // 4. Print live data
        Serial.print("Sample ");
        Serial.print(i);
        Serial.print("/15: ");
        Serial.print(currentDegrees);
        Serial.println("°");

        delay(1000); // Wait 1 second between samples
    }

    // 5. Final Result for this window
    Serial.println("---------------------------------------");
    Serial.print("15-SECOND AVERAGE: ");
    Serial.print(windStats.getAverage(sampleWindow),1);
    Serial.println("°");
    Serial.println("---------------------------------------\n");

    // Here is where you would normally call your LoRa send function
}
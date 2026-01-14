#include <Arduino.h>
#include <Utils.h>

// On CubeCell AB01, try using a specific GPIO pin, like GPIO1
const byte windPin = GPIO5; 

void setup() {
  Serial.begin(115200);
  
  pinMode(windPin, INPUT_PULLUP);
  
  // CubeCell supports interrupts on almost all GPIOs
  attachInterrupt(digitalPinToInterrupt(windPin), wind_Counter, FALLING);
  
  Serial.println("Wind counter initialized...");
}

void loop() {
  // Print the count every few seconds
  static uint32_t lastPrint = 0;
  if (millis() - lastPrint > 500) {
    // Serial.print("Total wind pulses: ");
    // Serial.println(wind_pulse_count);
    lastPrint = millis();
  }
}
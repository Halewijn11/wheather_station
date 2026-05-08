#include <Arduino.h>
#include <Utils.h>

// On CubeCell AB01, try using a specific GPIO pin, like GPIO1
const byte rainPin = GPIO1; 

void setup() {
  Serial.begin(115200);
  
  pinMode(rainPin, INPUT_PULLUP);
  
  // CubeCell supports interrupts on almost all GPIOs
  attachInterrupt(digitalPinToInterrupt(rainPin), rain_Counter, FALLING);
  
  Serial.println("Rain gauge initialized...");
}

void loop() {
  // Print the count every few seconds
  static uint32_t lastPrint = 0;
  if (millis() - lastPrint > 500) {
    Serial.print("Total bucket tips: ");
    Serial.println(rain_pulse_count);
    lastPrint = millis();
  }
}
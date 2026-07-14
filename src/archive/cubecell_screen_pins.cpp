#include "Arduino.h"


// Store your pins in an array for easy looping
int pins[] = {GPIO0, GPIO1, GPIO2, GPIO3, GPIO4, GPIO5};
int numPins = sizeof(pins) / sizeof(pins[0]);

void setup() {
  Serial.begin(115200);

  // Turn on Vext to ensure the pin headers have logic power
  pinMode(Vext, OUTPUT);
  digitalWrite(Vext, LOW); 

  // Initialize all pins in the array as OUTPUT
  for (int i = 0; i < numPins; i++) {
    pinMode(pins[i], OUTPUT);
    digitalWrite(pins[i], LOW); // Start with everything OFF
  }
  
  Serial.println("Starting Sequential Pin Identification...");
}

void loop() {
  for (int i = 0; i < numPins; i++) {
    // Print which pin we are currently testing
    Serial.print("Testing Pin: GPIO");
    Serial.println(i);

    // Turn the current pin ON
    digitalWrite(pins[i], HIGH);
    delay(2000); // Wait 2 seconds so you have time to see it

    // Turn the current pin OFF
    digitalWrite(pins[i], LOW);
    delay(500); // Short pause before moving to the next one
  }
  
  Serial.println("--- Cycle Complete, Restarting ---");
  delay(1000);
}
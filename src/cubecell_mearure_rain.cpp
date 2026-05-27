#include <Arduino.h>
#include "Utils.h" // Import our shared functions for tracking rain pulses

const byte rainPin = GPIO3; 
static unsigned int lastCount = 0;

// The rainTracker struct simplifies handling rain logic (provided by Utils.h if implemented there, 
// otherwise we can just read the global rain_pulse_count updated by rain_Counter)
// If you use RainTracker, initialize it here:
extern RainTracker rainTracker; 

void setup() {
    Serial.begin(115200);
    delay(100);
    
    Serial.println("Starting standalone Rain Measurement...");
    
    pinMode(rainPin, INPUT_PULLUP);
    
    // Attach the software-debounced hardware interrupt from Utils.cpp
    attachInterrupt(digitalPinToInterrupt(rainPin), rain_Counter, FALLING);
}

void loop() {
    //print the current rain pulse count if it has changed
    if (rain_pulse_count != lastCount) {
        Serial.print("Rain pulse count: ");
        Serial.println(rain_pulse_count);
        lastCount = rain_pulse_count;
    }
}
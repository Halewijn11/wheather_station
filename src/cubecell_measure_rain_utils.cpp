#include "Arduino.h"
#include "Utils.h"

/* Rain test settings */

const byte rainPin = GPIO3;
RainTracker rainTracker;

void setup() {
    Serial.begin(115200);

    pinMode(rainPin, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(rainPin), rain_Counter, FALLING);

    Serial.println("Rain test with Utils initialized...");
}

void loop() {
    static uint32_t lastPrint = 0;

    if (millis() - lastPrint > 1000) {
        rainTracker.print();
        lastPrint = millis();
    }
}

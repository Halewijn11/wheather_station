#include <Arduino.h>
#include <unity.h>
#include <Utils.h>

const byte rainPin = GPIO5;
const byte simulatorPin = GPIO0; // Connect this to GPIO1

void test_interrupt_trigger() {
    rain_pulse_count = 0;
    // Simulate a drop by pulling the pin LOW then HIGH
    digitalWrite(simulatorPin, LOW);
    delay(50); 
    digitalWrite(simulatorPin, HIGH);
    
    // The interrupt should have fired
    TEST_ASSERT_EQUAL(1, rain_pulse_count);
}

void setup() {
    delay(2000); // Wait for board
    UNITY_BEGIN();
    pinMode(rainPin, INPUT_PULLUP);
    pinMode(simulatorPin, OUTPUT);
    digitalWrite(simulatorPin, HIGH);
    attachInterrupt(digitalPinToInterrupt(rainPin), rain_Counter, FALLING);
    
    RUN_TEST(test_interrupt_trigger);
    UNITY_END();
}

void loop() {}
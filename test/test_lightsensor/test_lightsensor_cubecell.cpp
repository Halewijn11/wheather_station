#include <Arduino.h>
#include <unity.h>      // Standard PlatformIO testing library
#include "Utils.h"
#include <Adafruit_ADS1X15.h>

Adafruit_ADS1115 test_ads;



// TEST 3: Hardware Communication (Is the sensor actually on the PCB?)
void test_ads1115_connection() {
    pinMode(Vext, OUTPUT);
    digitalWrite(Vext, LOW); // Turn on power
    delay(100);
    
    bool connected = test_ads.begin();
    TEST_ASSERT_TRUE_MESSAGE(connected, "ADS1115 was not found on I2C bus!");
}

// TEST: Sanity check for indoor/disconnected state
void test_solar_is_realistic_indoors() {
    float result = getSolarRadiation(test_ads, 0);

    // If you are testing this in a normal room, 
    // the value should NOT be above 50 W/m^2. 
    // If it is 350+, this test will FAIL, alerting you to a floating pin.
    TEST_ASSERT_LESS_THAN_FLOAT(50.0, result);
}

void setup() {
    delay(2000); // Wait for board to stabilize
    UNITY_BEGIN();

    RUN_TEST(test_solar_is_realistic_indoors);
    RUN_TEST(test_ads1115_connection);

    UNITY_END();
}

void loop() {
    // Testing logic ends in setup
}
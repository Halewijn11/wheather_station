#include <Arduino.h>
#include <unity.h>
#include <Wire.h>
#include <Adafruit_BMP280.h>

#define BMP280_ADDRESS 0x76
Adafruit_BMP280 bmp;

// Setup Unity-specific requirements
void setUp(void) {
    // This runs before EACH test
}

void tearDown(void) {
    // This runs after EACH test
}

// 1. Test if the sensor is connected and communicating
void test_sensor_connection(void) {
    bool status = bmp.begin(BMP280_ADDRESS);
    TEST_ASSERT_TRUE_MESSAGE(status, "Could not find a valid BMP280 sensor! Check wiring/address.");
}

// 2. Test if the temperature readings are within the 15-25°C range
void test_temperature_range(void) {
    float temp = bmp.readTemperature();
    
    // Check if reading is between 15 and 25
    // Format: TEST_ASSERT_FLOAT_WITHIN(delta, expected, actual)
    // Or simpler:
    TEST_ASSERT_GREATER_THAN_FLOAT(15.0, temp);
    TEST_ASSERT_LESS_THAN_FLOAT(25.0, temp);
}

void setup() {
    // Necessary delay for some boards to initialize Serial
    delay(2000); 

    UNITY_BEGIN();

    // Run the connection test first
    RUN_TEST(test_sensor_connection);

    // Default settings for the sensor before reading data
    bmp.setSampling(Adafruit_BMP280::MODE_NORMAL,
                    Adafruit_BMP280::SAMPLING_X2,
                    Adafruit_BMP280::SAMPLING_X16,
                    Adafruit_BMP280::FILTER_X16,
                    Adafruit_BMP280::STANDBY_MS_500);

    // Run the data range test
    RUN_TEST(test_temperature_range);

    UNITY_END();
}

void loop() {
    // Nothing to do in loop for unit tests
}
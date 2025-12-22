#include <Arduino.h>
#include <unity.h>

// Pins (Match your hardware)
const int fan_pwm_pin = GPIO2;
const int tach_pin    = GPIO3;

// Global variables for interrupt
volatile unsigned int pulse_count = 0;
const int pulses_per_rev = 2;

void counter() {
    pulse_count++;
}

// Helper to measure RPM over a 1-second window
int measure_rpm() {
    pulse_count = 0;
    unsigned long start_time = millis();
    
    // Wait for 1 second to accumulate pulses
    while (millis() - start_time < 1000) {
        yield(); 
    }

    noInterrupts();
    unsigned int pulses = pulse_count;
    interrupts();

    float revolutions = (float)pulses / pulses_per_rev;
    return (int)(revolutions * 60.0);
}

// The actual test case
void test_fan_speeds() {
    // Duty cycles for 25%, 50%, 75%, 100% 
    // Assuming 8-bit PWM (0-255). If using 16-bit, scale accordingly.
    uint32_t speeds[] = {16384, 32768, 49152, 65535};
    const char* labels[] = {"25%", "50%", "75%", "100%"};

    for (int i = 0; i < 4; i++) {
        analogWrite(fan_pwm_pin, speeds[i]);
        
        // Allow 2 seconds for the fan to physically reach speed
        delay(2000); 

        int rpm = measure_rpm();

        Serial.print("Testing ");
        Serial.print(labels[i]);
        Serial.print(" power. Measured RPM: ");
        Serial.println(rpm);

        // Assertion: RPM must be greater than 0
        TEST_ASSERT_GREATER_THAN_INT(0, rpm);
    }
}

void setup() {
    // 1. Initialize Serial for the Test Runner
    Serial.begin(115200); 
    while(!Serial); // Wait for Serial to be ready
    delay(2000);    // Extra cushion for CubeCell bootloader
    
    UNITY_BEGIN();
    
    pinMode(fan_pwm_pin, OUTPUT);
    pinMode(tach_pin, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(tach_pin), counter, FALLING);

    RUN_TEST(test_fan_speeds);

    UNITY_END();
}

void loop() {
    // Empty for PlatformIO Unit Testing
}
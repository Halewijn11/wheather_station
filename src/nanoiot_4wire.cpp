#include <Arduino.h>

const int fan_pwm_pin = 6;      // PWM control pin for the fan
const int tach_pin    = 2;      // Tachometer signal input pin

volatile unsigned int pulse_count = 0; // Use unsigned int for pulse count
unsigned long last_measure = 0;

const int pulses_per_rev = 2;   // Most PC fans produce 2 pulses per revolution

void counter() {
  pulse_count++;                // Interrupt: happens on each tach pulse
}

void setup() {
  // Use a higher baud rate for faster serial communication
  Serial.begin(115200); 

  pinMode(fan_pwm_pin, OUTPUT);
  // Keep INPUT_PULLUP - essential for open-drain tachometer output
  pinMode(tach_pin, INPUT_PULLUP); 

  // Set fan speed (0–255)
  // Ensure the fan is actually spinning. Try 255 (full speed) to confirm.
  analogWrite(fan_pwm_pin, 128); 

  // Interrupt on tach pin
  attachInterrupt(digitalPinToInterrupt(tach_pin), counter, FALLING);

  last_measure = millis();
  Serial.println("Setup Complete. Measuring RPM...");
}

void loop() {

  // Compute RPM every 1 second
  if (millis() - last_measure >= 1000) {
    
    noInterrupts();
    // Copy the volatile counter quickly
    unsigned int pulses = pulse_count; 
    pulse_count = 0;
    interrupts();

    // --- CRITICAL FIX: Use floating-point math to prevent truncation ---
    
    // Calculate revolutions in the measurement period (1 second)
    float revolutions = (float)pulses / pulses_per_rev;
    
    // Convert to RPM: revolutions/second * 60 seconds/minute
    int rpm = (int)(revolutions * 60.0);

    Serial.print("Fan Pulses: ");
    Serial.print(pulses);
    Serial.print(" | Fan RPM: ");
    Serial.println(rpm);

    last_measure = millis();
  }
}
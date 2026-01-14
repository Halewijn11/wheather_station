#include <Arduino.h>
#include <Wire.h>

void setup() {
  // 1. MUST turn on Vext first! 
  // On AB01, Vext controls the power to the I2C header and pull-up rail.
  pinMode(Vext, OUTPUT);
  digitalWrite(Vext, LOW); // LOW = Power ON
  delay(100);              // Wait for voltage to stabilize

  Serial.begin(115200);

  // 2. Start I2C
  Wire.begin();

  // 3. Force Internal Pull-ups
  // SDA is typically GPIO29 / SCL is typically GPIO30 on AB01
  // This command tells the pin to stay at 3.3V unless pulled down
  pinMode(SDA, INPUT_PULLUP);
  pinMode(SCL, INPUT_PULLUP);

  Serial.println("I2C Bus Initialized with Internal Pull-ups");
}

void loop() {
  // Check voltage on your multimeter now
  delay(1000);
}
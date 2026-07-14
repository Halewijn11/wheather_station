#include <Arduino.h>

void setup()
{
  // initialize LED digital pin as an output.
  pinMode(RGB, OUTPUT);
  Serial.begin(115200);
}

void loop()
{
  // turn the LED on (HIGH is the voltage level)
  digitalWrite(RGB, HIGH);
  Serial.println("LED is ON");
  // wait for a second
  delay(1000);
  // turn the LED off by making the voltage LOW
  digitalWrite(RGB, LOW);
   // wait for a second
  Serial.println("LED is OFF");
  delay(1000);
}
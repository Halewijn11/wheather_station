#include <Arduino.h>
#define onboard 13

void setup() {
  pinMode(onboard, OUTPUT);
  // put your setup code here, to run once:
  // int result = myFunction(2, 3);
}

void loop() {
  digitalWrite(onboard, HIGH);   // turn the LED on (HIGH is the voltage level)
  delay(500);                   // wait for a second
  digitalWrite(onboard, LOW);    // turn the LED off by making the voltage LOW
  delay(1000);                   // wait for a second
  // put your main code here, to run repeatedly:
}
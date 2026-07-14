#include <Arduino.h>


#define LED 2

void setup() {
  // Set pin mode
  pinMode(LED,OUTPUT);
  Serial.begin(115200);
}

void loop() {
  delay(1000);
  digitalWrite(LED,HIGH);
  Serial.println("LED is ON");
  delay(1000);
  digitalWrite(LED,LOW);
  Serial.println("LED is OFF");
}
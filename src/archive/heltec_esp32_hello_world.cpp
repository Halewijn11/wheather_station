#include <Arduino.h>

void setup() {
  Serial.begin(115200);

}

void loop() {
  delay(1000); // give serial time to start
  Serial.println("Hello World");
  // nothing to do here
}
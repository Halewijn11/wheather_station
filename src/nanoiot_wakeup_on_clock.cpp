#include "ArduinoLowPower.h"
#include <RTClib.h>

RTC_DS3231 rtc;
const byte interruptPin = 2; // Connect DS3231 SQW to this pin
void alarmHandler();
void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(interruptPin, INPUT_PULLUP); 

  if (!rtc.begin()) {
    while (1); // Halt if RTC not found
  }

  // Clear any existing alarms
  rtc.disableAlarm(1);
  rtc.disableAlarm(2);
  rtc.clearAlarm(1);
  rtc.clearAlarm(2);
  
  // Stop the wave output so the pin can be used for alarms
  rtc.writeSqwPinMode(DS3231_OFF);

  // Register the external pin as the wakeup source
  LowPower.attachInterruptWakeup(interruptPin, alarmHandler, FALLING);
}

void loop() {
  digitalWrite(LED_BUILTIN, HIGH);
  delay(500);
  digitalWrite(LED_BUILTIN, LOW);

  // Set alarm for 2 seconds from now
  rtc.setAlarm1(rtc.now() + TimeSpan(0, 0, 0, 2), DS3231_A1_Second);

  // Sleep until the DS3231 pulls the interrupt pin LOW
  LowPower.sleep(); 
  
  // After waking up, clear the alarm so it can fire again
  rtc.clearAlarm(1);
}

void alarmHandler() {
  // Executed on wakeup
}
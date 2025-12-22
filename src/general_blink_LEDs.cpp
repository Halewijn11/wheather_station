#include "Arduino.h"


// void setup() {
//   pinMode(Vext, OUTPUT);
//   digitalWrite(Vext, LOW); // LOW turns the power ON
//   pinMode(1, OUTPUT);
//   pinMode(2, OUTPUT);
//   pinMode(3, OUTPUT);
//   pinMode(5, OUTPUT);
//   pinMode(4, OUTPUT);
// }

// void loop() {
//   digitalWrite(2, HIGH);
//   digitalWrite(1, HIGH);
//   digitalWrite(3, HIGH);
//   digitalWrite(5, HIGH);
//   digitalWrite(4, HIGH);
//   delay(500);
//   digitalWrite(1, LOW);
//   digitalWrite(2, LOW);
//   digitalWrite(3, LOW);
//   digitalWrite(5, LOW);
//   digitalWrite(4, LOW);
//   delay(500);

// }

// #include "Arduino.h"


// void setup() {
//   pinMode(D0, OUTPUT);
//   // pinMode(2, OUTPUT);
//   // pinMode(3, OUTPUT);
//   // pinMode(5, OUTPUT);
//   // pinMode(4, OUTPUT);
// }

// void loop() {
//   digitalWrite(D0, HIGH);
//   // digitalWrite(1, HIGH);
//   // digitalWrite(3, HIGH);
//   // digitalWrite(5, HIGH);
//   // digitalWrite(4, HIGH);
//   delay(500);
//   digitalWrite(D0, LOW);
//   // digitalWrite(2, LOW);
//   // digitalWrite(3, LOW);
//   // digitalWrite(5, LOW);
//   // digitalWrite(4, LOW);
//   delay(500);

// }

// #include "Arduino.h"

// void setup() {
//   // Set D0 as an output
//   pinMode(0, OUTPUT);
// }

// void loop() {
//   // Turn D0 HIGH
//   digitalWrite(0, HIGH);
//   delay(500);  // Wait 500 milliseconds

//   // Turn D0 LOW
//   digitalWrite(0, LOW);
//   delay(500);  // Wait 500 milliseconds
// }


/* * CubeCell Pin Finder
 * This cycles through GPIO 1 to 7. 
 * The number of blinks tells you which GPIO is active.
 */

// int pinsToTest[] = {GPIO1, GPIO2, GPIO3, GPIO4, GPIO5, GPIO6, GPIO7};
// int numPins = 7;

// void setup() {
//   // Initialize all test pins as outputs
//   for (int i = 0; i < numPins; i++) {
//     pinMode(pinsToTest[i], OUTPUT);
//     digitalWrite(pinsToTest[i], LOW);
//   }
// }

// void loop() {
//   for (int i = 0; i < numPins; i++) {
//     int currentPin = pinsToTest[i];
//     int blinkCount = i + 1; // GPIO1 = 1 blink, GPIO2 = 2 blinks, etc.

//     for (int b = 0; b < blinkCount; b++) {
//       digitalWrite(currentPin, HIGH);
//       delay(200);
//       digitalWrite(currentPin, LOW);
//       delay(200);
//     }

//     delay(2000); // 2-second pause before moving to the next GPIO
//   }
// }

// #include "Arduino.h"

// // The HTCC-AB01 generally uses pins 0 through 7 for user GPIO/Control
// int pins[] = {0, 1, 2, 3, 4, 5, 6, 7};
// int pinCount = 8;

// void setup() {
//   Serial.begin(115200);
//   Serial.println("Initializing all pins...");

//   for (int i = 0; i < pinCount; i++) {
//     pinMode(pins[i], OUTPUT);
//   }
// }

// void loop() {
//   Serial.println("All pins HIGH (ON)");
//   for (int i = 0; i < pinCount; i++) {
//     digitalWrite(pins[i], HIGH);
//   }
  
//   delay(5000); // Stay on for 5 seconds

//   Serial.println("All pins LOW (OFF)");
//   for (int i = 0; i < pinCount; i++) {
//     digitalWrite(pins[i], LOW);
//   }

//   delay(5000); // Stay off for 5 seconds
// }

#include "Arduino.h"

// The CubeCell uses GPIO0 through GPIO5 as physical header pins
// GPIO6 is internally tied to Vext control

void setup() {
  Serial.begin(115200);

  // Turn on Vext to ensure the pin headers have logic power
  pinMode(Vext, OUTPUT);
  digitalWrite(Vext, LOW); 

  // Initialize named GPIOs
  pinMode(GPIO0, OUTPUT);
  pinMode(GPIO1, OUTPUT);
  pinMode(GPIO2, OUTPUT);
  pinMode(GPIO3, OUTPUT);
  pinMode(GPIO4, OUTPUT); // Usually labeled ADC on the board
  pinMode(GPIO5, OUTPUT);
}

void loop() {
  Serial.println("Blinking GPIO 0-5");

  // All ON
  digitalWrite(GPIO0, HIGH);
  digitalWrite(GPIO1, HIGH);
  digitalWrite(GPIO2, HIGH);
  digitalWrite(GPIO3, HIGH);
  digitalWrite(GPIO4, HIGH);
  digitalWrite(GPIO5, HIGH);
  delay(1000);

  // All OFF
  digitalWrite(GPIO0, LOW);
  digitalWrite(GPIO1, LOW);
  digitalWrite(GPIO2, LOW);
  digitalWrite(GPIO3, LOW);
  digitalWrite(GPIO4, LOW);
  digitalWrite(GPIO5, LOW);
  delay(1000);
}
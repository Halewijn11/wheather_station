#include <Wire.h>
#include <SHT4x.h>
#include <DFRobot_B_LUX_V30B.h>

// SHT45 Setup
SHT4x sht;

// V30B Setup 
// Note: We pass the standard I2C pins. 
// For Arduino Uno: SDA is A4, SCL is A5. 
// For ESP32: SDA is 21, SCL is 22.
// Replace 16 with your CEN pin, and A5, A4 with your SCL/SDA pins.
DFRobot_B_LUX_V30B myLux(16, SCL, SDA); 

void setup() {
  Serial.begin(115200);
  while(!Serial); // Wait for Serial monitor
  
  Serial.println("--- Dual Sensor Initializing ---");

  // Initialize Hardware I2C for SHT45
  Wire.begin();
  Wire.setClock(100000);
  if (sht.begin()) {
    Serial.println("SHT45 found!");
  } else {
    Serial.println("SHT45 not found. Check wiring.");
  }

  // Initialize V30B
  // Note: The V30B library's begin() takes a long time (1s+) 
  // because it toggles the CEN pin and waits for a stable reading.
  myLux.begin();
  Serial.println("V30B (Lux) ready.");
  
  Serial.println("Time(us) | Temp(C) | Hum(%) | Lux");
  Serial.println("---------------------------------------");
}

void loop() {
  // 1. FORCE I2C RESET for SHT45
  // This takes the pins back from the "bit-banging" Lux library
  Wire.begin(); 
  delay(10); 

  // 2. READ SHT45
  uint32_t start = micros();
  bool success = sht.read(); 
  uint32_t stop = micros();

  float temp = sht.getTemperature();
  float hum = sht.getHumidity();

  // 3. READ V30B 
  // (This library will manually toggle pins, we don't need to do anything special here)
  float lux = myLux.lightStrengthLux();

  // 4. PRINT RESULTS
  if (!success) {
    Serial.print("SHT Error! ");
  }
  Serial.print(stop - start);
  Serial.print("\t");
  Serial.print(temp, 1);
  Serial.print("C\t");
  Serial.print(hum, 1);
  Serial.print("%\t");
  Serial.print(lux, 1);
  Serial.println(" lux");

  delay(1000);
}
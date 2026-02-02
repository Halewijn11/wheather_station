#include "Utils.h"
#include "Adafruit_INA3221.h"

// // Tell the library that these variables are defined in the main sketch
// extern volatile unsigned int pulse_count;
// extern const int pulses_per_rev

volatile unsigned int fan_pulse_count = 0;
volatile unsigned long last_micros = 0;

const int pulses_per_rev = 2;
const int pwm_bit_depth =65536;



int readFanSpeed() {
    noInterrupts();
    fan_pulse_count = 0;
    interrupts();
    unsigned long start_time = millis();
    
    // Wait for 1 second to accumulate pulses
    while (millis() - start_time < 1000) {
        yield(); 
    }

    noInterrupts();
    unsigned int pulses = fan_pulse_count;
    interrupts();

    float revolutions = (float)pulses / pulses_per_rev;
    return (int)(revolutions * 60.0);
}

void fan_Counter() {
  fan_pulse_count++;                // Interrupt: happens on each tach pulse
}

int readFanSpeed_Updated(int tach_pin) {
    // 1. Reset count and attach interrupt right now
    fan_pulse_count = 0;
    
    // Dynamically attach the interrupt only for this measurement
    attachInterrupt(digitalPinToInterrupt(tach_pin), fan_Counter, FALLING);
    
    unsigned long start_time = millis();
    
    // 2. Wait for 1 second to accumulate pulses
    while (millis() - start_time < 1000) {
        yield(); // Keeps the watchdog happy and background tasks running
    }

    // 3. Immediately detach the interrupt so the fan stops "poking" the CPU
    detachInterrupt(digitalPinToInterrupt(tach_pin));

    // 4. Calculate RPM
    unsigned int pulses;
    pulses = fan_pulse_count;
    float revolutions = (float)pulses / pulses_per_rev;
    return (int)(revolutions * 60.0);
}

int percentage_To_Pwm(int percentage) {
    return (int)(percentage * pwm_bit_depth) / 100-1;

}


Ina3221Reading readIna3221Channel(Adafruit_INA3221& ina3221,uint8_t channel) {
  Ina3221Reading reading;

  // Read voltage (V)
  reading.voltage_V = ina3221.getBusVoltage(channel);

  // Read current (mA)
  reading.current_mA = ina3221.getCurrentAmps(channel) * 1000.0;

  // Compute power (mW)
  reading.power_mW = reading.voltage_V * reading.current_mA;

  return reading;
}


// ##################### everything for the rain sensor ###############################3
volatile unsigned int rain_pulse_count = 0;
void rain_Counter() {
  unsigned long current_micros = micros();
    // Ignore pulses that happen within 200,000 microseconds (200ms) of each other
  if (current_micros - last_micros > 200000) {
    rain_pulse_count++;
    last_micros = current_micros;
  }
  // Serial.println("total read rain pulses:");
  // Serial.println(rain_pulse_count);
}



// ##################### everything for the wind sensor ###############################3
volatile unsigned int wind_pulse_count = 0;
void wind_Counter() {
  unsigned long current_micros = micros();
    // Ignore pulses that happen within 200,000 microseconds (200ms) of each other
  if (current_micros - last_micros > 200000) {
    wind_pulse_count++;
    last_micros = current_micros;
  }
  // Serial.println("pulse!");
}

// ##################### everything for the wind direction ###############################3
float getWindDirection(float voltage, float maxVoltage) {
  if (voltage < 0.01) return 0.0; // Noise floor / True North

  float degrees = (voltage / maxVoltage) * 360.0;

  // Ensure we stay within the 0-359.9 range
  if (degrees >= 360.0) {
    degrees = 0.0;
  }

  return degrees;
}

// ##################### everything for light sensor ###############################3
float getSolarRadiation(Adafruit_ADS1115& ads, uint8_t channel) {
    // 1. Read the raw ADC value from the specified channel
    int16_t rawResult = ads.readADC_SingleEnded(channel);
    
    // 2. Noise floor safety: If the reading is slightly negative due to noise, set to 0
    if (rawResult < 0) rawResult = 0;

    // 3. Convert raw value to millivolts 
    // GAIN_ONE: 1 bit = 0.125mV
    float millivolts = rawResult * 0.125;
    
    // 4. Davis 6450 Scale: 1.67 mV per W/m^2
    float solarRadiation = millivolts / 1.67;

    return solarRadiation;
}


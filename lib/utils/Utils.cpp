#include "Utils.h"
#include "Adafruit_INA3221.h"

// volatile unsigned int fan_pulse_count = 0;
volatile unsigned long last_millis_rain = 0;
volatile unsigned long last_millis_wind = 0;

// const int pulses_per_rev = 2;
// const int pwm_bit_depth = 65536;

// void setExternalFanSpeed(Adafruit_PWMServoDriver& pwmBoard, int pwm_channel, int percent) {
//     int safe_percent = constrain(percent, 0, 100);
//     int safe_channel = constrain(pwm_channel, 0, 15);
//     int dutyCycle = (safe_percent * 4095) / 100;
//     pwmBoard.setPWM(safe_channel, 0, dutyCycle);
// }

// void fan_Counter() {
//   fan_pulse_count++;
// }

// int readFanSpeed_Updated(int tach_pin, unsigned long duration_ms) {
//     fan_pulse_count = 0;
//     attachInterrupt(digitalPinToInterrupt(tach_pin), fan_Counter, FALLING);
//     unsigned long start_time = millis();
//     while (millis() - start_time < duration_ms) { yield(); }
//     detachInterrupt(digitalPinToInterrupt(tach_pin));
//     float revolutions = (float)fan_pulse_count / pulses_per_rev;
//     float rpm = revolutions * (60000.0 / duration_ms);
//     return (int)rpm;
// }

// int percentage_To_Pwm(int percentage) {
//     return (int)(percentage * pwm_bit_depth) / 100 - 1;
// }

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
volatile unsigned long last_millis_rain = 0;

void rain_Counter() {
  unsigned long current_millis = millis();
    // Ignore pulses that happen within 50 milliseconds of each other
  if (current_millis - last_millis_rain > 50) {
    rain_pulse_count++;
    // Serial.println("pulse!");
    last_millis_rain = current_millis;
  }
  
  // Serial.println("total read rain pulses:");
  // Serial.println(rain_pulse_count);
}



// ##################### everything for the wind sensor ###############################3
volatile unsigned int wind_pulse_count = 0;
volatile unsigned long last_millis_wind = 0;

void wind_Counter() {
  unsigned long current_millis = millis();
    // Ignore pulses that happen within 100 milliseconds of each other
  if (current_millis - last_millis_wind > 100) {
    wind_pulse_count++;
    last_millis_wind = current_millis;
  }
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
float getSolarRadiation(Adafruit_ADS1115& ads, uint8_t signalChannel, uint8_t refChannel) {
    // 1. Read the signal from the solar sensor
    int16_t rawSignal = ads.readADC_SingleEnded(signalChannel);
    // 2. Read the reference voltage (excitation voltage)
    int16_t rawRef = ads.readADC_SingleEnded(refChannel);

    // 3. Safety: Handle negative noise
    if (rawSignal < 0) rawSignal = 0;
    
    // 4. Prevent division by zero if reference is missing/disconnected
    if (rawRef <= 0) return 0.0; 

    // 5. Ratiometric Calculation: (Signal / Reference) * 1800
    // Note: Since both use the same Gain, we can use raw ADC steps 
    // because the 0.125mV multiplier would just cancel itself out.
    float solarRadiation = ((float)rawSignal / (float)rawRef) * 1800.0;

    return solarRadiation;
}


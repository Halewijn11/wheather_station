#include "Utils.h"
#include "Adafruit_INA3221.h"

// // Tell the library that these variables are defined in the main sketch
// extern volatile unsigned int pulse_count;
// extern const int pulses_per_rev

volatile unsigned int fan_pulse_count = 0;
volatile unsigned long last_micros_rain = 0;
volatile unsigned long last_micros_wind = 0;

const int pulses_per_rev = 2;
const int pwm_bit_depth =65536;

void setExternalFanSpeed(Adafruit_PWMServoDriver& pwmBoard, int pwm_channel, int percent) {
    // 1. Constrain for safety
    int safe_percent = constrain(percent, 0, 100);
    int safe_channel = constrain(pwm_channel, 0, 15);
    
    // 2. Map 0-100% to 12-bit (0-4095)
    // Formula: (percent / 100) * 4095
    int dutyCycle = (safe_percent * 4095) / 100;
    
    // 3. Send to the I2C board
    pwmBoard.setPWM(safe_channel, 0, dutyCycle);
}

// int readFanSpeed() {
//     noInterrupts();
//     fan_pulse_count = 0;
//     interrupts();
//     unsigned long start_time = millis();
    
//     // Wait for 1 second to accumulate pulses
//     while (millis() - start_time < 1000) {
//         yield(); 
//     }

//     noInterrupts();
//     unsigned int pulses = fan_pulse_count;
//     interrupts();

//     float revolutions = (float)pulses / pulses_per_rev;
//     return (int)(revolutions * 60.0);
// }

void fan_Counter() {
  fan_pulse_count++;                // Interrupt: happens on each tach pulse
}

int readFanSpeed_Updated(int tach_pin, unsigned long duration_ms) {
    // 1. Reset count and attach interrupt
    fan_pulse_count = 0;
    attachInterrupt(digitalPinToInterrupt(tach_pin), fan_Counter, FALLING);
    
    unsigned long start_time = millis();
    
    // 2. Wait for the CUSTOM duration (e.g., 500ms, 2000ms)
    while (millis() - start_time < duration_ms) {
        yield(); 
    }

    // 3. Detach the interrupt
    detachInterrupt(digitalPinToInterrupt(tach_pin));

    // 4. Calculate RPM
    // Formula: (Pulses / PulsesPerRev) * (60000 / MeasurementTime)
    float revolutions = (float)fan_pulse_count / pulses_per_rev;
    float rpm = revolutions * (60000.0 / duration_ms); 
    
    return (int)rpm;
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
    // Ignore pulses that happen within 800,000 microseconds (800ms) of each other
  if (current_micros - last_micros_rain > 800000) {
    rain_pulse_count++;
    // Serial.println("pulse!");
    last_micros_rain = current_micros;
  }
  
  // Serial.println("total read rain pulses:");
  // Serial.println(rain_pulse_count);
}



// ##################### everything for the wind sensor ###############################3
volatile unsigned int wind_pulse_count = 0;
void wind_Counter() {
  unsigned long current_micros = micros();
    // Ignore pulses that happen within 200,000 microseconds (200ms) of each other
  if (current_micros - last_micros_wind > 200000) {
    wind_pulse_count++;
    last_micros_wind = current_micros;
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


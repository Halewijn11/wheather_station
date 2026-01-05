#ifndef UTILS_H
#define UTILS_H
#include <Arduino.h>  // <--- Add this line

extern volatile unsigned int fan_pulse_count;



int readFanSpeed();
void fan_Counter();
int readFanSpeed_Updated(int tach_pin);
int percentage_To_Pwm(int percentage); 

//for the ina3221 readings
// 🔹 Forward declaration (NO include needed here)
class Adafruit_INA3221;
struct Ina3221Reading {
  float voltage_V;
  float current_mA;
  float power_mW;
};

Ina3221Reading readIna3221Channel(Adafruit_INA3221& ina3221, uint8_t channel);


// struct SensorStats {
//     float sum;
//     float min;
//     float max;

//     // A simple function inside the struct to update values
//     void update(float val) {
//         sum += val;
//         if (val < min) min = val;
//         if (val > max) max = val;
//     }

//     // A function to reset for the next 60s window
//     void reset(float initialMin, float initialMax) {
//         sum = 0;
//         min = initialMin;
//         max = initialMax;
//     }

//     // A function to get the average
//     float getAverage(int count) {
//         if (count == 0) return 0;
//         return sum / (float)count;
//     }
// };

struct SensorStats {
    float sum;
    float min;
    float max;

    void update(float val) {
        sum += val;
        if (val < min) min = val;
        if (val > max) max = val;
    }

    void reset(float initialMin, float initialMax) {
        sum = 0;
        min = initialMin;
        max = initialMax;
    }

  // THE PRINT FUNCTION
    void print(const char* label, int sampleCount) {
        float avg = (sampleCount > 0) ? (sum / (float)sampleCount) : 0;
        Serial.print("["); Serial.print(label); Serial.print("] ");
        Serial.print("Avg: "); Serial.print(avg);
        Serial.print(" | Min: "); Serial.print(min);
        Serial.print(" | Max: "); Serial.println(max);
    }
    // THE PACKER FUNCTION
    // multiplier: 100.0 turns 22.34 into 2234 (integer) to keep decimals
    // byteSize: 2 for small values (Temp/Humid), 4 for large (Lux/Pressure)
    void pack(uint8_t* buffer, uint16_t &index, int sampleCount, float multiplier, int byteSize) {
        float avg = (sampleCount > 0) ? (sum / (float)sampleCount) : 0;
        
        uint32_t values[3] = {
            (uint32_t)(avg * multiplier),
            (uint32_t)(min * multiplier),
            (uint32_t)(max * multiplier)
        };

        for (int i = 0; i < 3; i++) {
            if (byteSize == 4) {
                buffer[index++] = (uint8_t)(values[i] >> 24);
                buffer[index++] = (uint8_t)(values[i] >> 16);
            }
            buffer[index++] = (uint8_t)(values[i] >> 8);
            buffer[index++] = (uint8_t)(values[i]);
        }
    }
};

#endif
#ifndef UTILS_H
#define UTILS_H
#include <Arduino.h>  // <--- Add this line
#include <math.h>
#include <Adafruit_ADS1X15.h> // Make sure this is at the top


extern volatile unsigned int fan_pulse_count;

// ##################### everything for the rain sensor ###############################3
extern volatile unsigned int rain_pulse_count;
void rain_Counter();

// ##################### everything for the wind sensor ###############################3
extern volatile unsigned int wind_pulse_count;
void wind_Counter();

// ##################### everything for the wind direction sensor ###############################3
float getWindDirection(float voltage, float maxVoltage);

// ##################### everything for the light sensor ###############################3
float getSolarRadiation(Adafruit_ADS1115& ads, uint8_t channel);


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

// Helper to pack values into a buffer to avoid redundancy
inline void packValue(uint8_t* buffer, uint16_t &index, float value, float multiplier, int byteSize) {
    uint32_t packedVal = (uint32_t)(value * multiplier);

    if (byteSize == 4) {
        buffer[index++] = (uint8_t)(packedVal >> 24);
        buffer[index++] = (uint8_t)(packedVal >> 16);
    }
    buffer[index++] = (uint8_t)(packedVal >> 8);
    buffer[index++] = (uint8_t)(packedVal);
}

struct SensorStats {
    float sum;
    float min;
    float max;

    void update(float val) {
        sum += val;
        if (val < min) min = val;
        if (val > max) max = val;
    }

    void reset() {
        sum = 0;
        min = 999999.0;
        max = -999999.0;
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
        
        // Use the centralized helper for Avg, Min, and Max
        packValue(buffer, index, avg, multiplier, byteSize);
        packValue(buffer, index, min, multiplier, byteSize);
        packValue(buffer, index, max, multiplier, byteSize);
    }
};


// ##################### for the wind sensor readings ###############################3


struct WindDirectionTracker {
    float sumSin;
    float sumCos;

    // Just adds the components to the RTC-backed sums
    void update(float degrees) {
        float rad = degrees * (M_PI / 180.0f);
        sumSin += sinf(rad);
        sumCos += cosf(rad);
    }

    void reset() {
        sumSin = 0.0f;
        sumCos = 0.0f;
    }

    // Calculates the average based on an external count
    int getAverage(int sampleCount) {
        if (sampleCount == 0) return 0.0f;

        // Note: atan2 handles the sums directly; dividing by sampleCount 
        // is mathematically optional here but kept for clarity.
        float avgRad = atan2f(sumSin, sumCos);
        float avgDeg = avgRad * (180.0f / M_PI);

        if (avgDeg < 0) avgDeg += 360.0f;
        
        int roundedDeg = (int)(avgDeg + 0.5f);
        return roundedDeg;
    }

    void print(int sampleCount) {
        Serial.print("[Wind direction] Avg: ");
        Serial.print(getAverage(sampleCount));
        Serial.print("° (Samples: ");
        Serial.print(sampleCount);
        Serial.println(")");
    }

// Now uses the same logic as everything else
void pack(uint8_t* buffer, uint16_t &index, int sampleCount, float multiplier = 1.0f, int byteSize = 2) {
    float avg = getAverage(sampleCount);
    // Now this matches the signature of the other pack function exactly
    packValue(buffer, index, avg, multiplier, byteSize);
}
};



struct RainTracker {
    void reset() {
        rain_pulse_count = 0;
    }

    void print() {
        Serial.print("[Rain] Total Pulses: ");
        Serial.println(rain_pulse_count);
    }

    // byteSize 2 is enough for rain (up to 65535 tips)
    void pack(uint8_t* buffer, uint16_t &index) {
        // We pack the volatile rain_pulse_count as a float 
        // to use your existing packValue helper
        packValue(buffer, index, (float)rain_pulse_count, 1.0, 2);
    }
};

struct WindSpeedTracker {
    float total;
    float min;
    float max;

    void reset() {
        total = 0;
        min = 999999.0;
        max = -999999.0;
        wind_pulse_count = 0; // Reset the global interrupt counter
    }

    // This is called once per sample (e.g., every 1 second)
    void update() {
        float currentPulses = (float)wind_pulse_count;
        wind_pulse_count = 0; // Reset global counter for the next window

        total += currentPulses;
        if (currentPulses < min) min = currentPulses;
        if (currentPulses > max) max = currentPulses;
    }

    void print() {
        Serial.print("[Wind Speed Pulses] ");
        Serial.print("Total: "); Serial.print(total);
        Serial.print(" | Min: "); Serial.print(min);
        Serial.print(" | Max: "); Serial.println(max);
    }

    // Packs Total, Min, and Max (6 bytes total)
    void pack(uint8_t* buffer, uint16_t &index) {
        packValue(buffer, index, total, 1.0, 2);
        packValue(buffer, index, min, 1.0, 2);
        packValue(buffer, index, max, 1.0, 2);
    }
};

#endif
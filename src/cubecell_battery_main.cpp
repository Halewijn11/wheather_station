#include "LoRaWan_APP.h"
#include "Arduino.h"
#include <Adafruit_BMP280.h>
#include <Adafruit_ADS1X15.h>
#include "Adafruit_INA3221.h"
#include "Utils.h"
#include "SHT4x.h"
// #include <Adafruit_PWMServoDriver.h>
#include "secrets.h"


/****************************************************
 * LORA PREAMBLE  
 ****************************************************/

/*
 * set LoraWan_RGB to Active,the RGB active in loraWan
 * RGB red means sending;
 * RGB purple means joined done;
 * RGB blue means RxWindow1;
 * RGB yellow means RxWindow2;
 * RGB green means received done;
 */


 /*
appeui: 70B3D57ED0074824
deveui: 70B3D57ED0074825
appkey: 84FA823981303163AFE2968797AFDD49
 */
 

/* OTAA para*/
uint8_t devEui[] = SECRET_DEV_EUI;
uint8_t appEui[] = SECRET_APP_EUI;
uint8_t appKey[] = SECRET_APP_KEY;

/* ABP para*/
uint8_t nwkSKey[] = SECRET_NWK_SKEY;
uint8_t appSKey[] = SECRET_APP_SKEY;
uint32_t devAddr = SECRET_DEV_ADDR;

/*LoraWan channelsmask, default channels 0-7*/ 
uint16_t userChannelsMask[6]={ 0x00FF,0x0000,0x0000,0x0000,0x0000,0x0000 };

/*LoraWan region, select in arduino IDE tools*/
LoRaMacRegion_t loraWanRegion = ACTIVE_REGION;

/*LoraWan Class, Class A and Class C are supported*/
DeviceClass_t  loraWanClass = LORAWAN_CLASS;

/*the application data transmission duty cycle.  value in [ms].*/
uint32_t appTxDutyCycle = 60000;

/*OTAA or ABP*/
bool overTheAirActivation = LORAWAN_NETMODE;

/*ADR enable*/
bool loraWanAdr = LORAWAN_ADR;

/* set LORAWAN_Net_Reserve ON, the node could save the network info to flash, when node reset not need to join again */
bool keepNet = LORAWAN_NET_RESERVE;

/* Indicates if the node is sending confirmed or unconfirmed messages */
bool isTxConfirmed = LORAWAN_UPLINKMODE;

/* Application port */
uint8_t appPort = 2;
/*!
* Number of trials to transmit the frame, if the LoRaMAC layer did not
* receive an acknowledgment. The MAC performs a datarate adaptation,
* according to the LoRaWAN Specification V1.0.2, chapter 18.4, according
* to the following table:
*
* Transmission nb | Data Rate
* ----------------|-----------
* 1 (first)       | DR
* 2               | DR
* 3               | max(DR-1,0)
* 4               | max(DR-1,0)
* 5               | max(DR-2,0)
* 6               | max(DR-2,0)
* 7               | max(DR-3,0)
* 8               | max(DR-3,0)
*
* Note, that if NbTrials is set to 1 or 2, the MAC will not decrease
* the datarate, in case the LoRaMAC layer did not receive an acknowledgment
*/
uint8_t confirmedNbTrials = 4;

/****************************************************
 * TIME SYNC / DRIFT CORRECTION
 ****************************************************/

/*
 * The CubeCell keeps time on an RC oscillator that drifts several seconds per
 * day, so a fixed `LoRaWAN.cycle(5000)` slowly walks away from the wall clock.
 *
 * Two fixes here:
 *  1. Ask the network server for the time with the LoRaWAN DeviceTimeReq MAC
 *     command (MLME_DEVICE_TIME). The answer arrives in RX1/RX2 and the MAC
 *     layer feeds it into TimerSetSysTime(), so TimerGetSysTime() returns real
 *     Unix time. Re-requested periodically to correct ongoing drift.
 *  2. Schedule every wake against that absolute clock instead of adding a fixed
 *     delay to "now". Sleep length is recomputed each cycle as the distance to
 *     the next MEASURE_INTERVAL_S boundary, so execution lag and oscillator
 *     error are absorbed each cycle instead of accumulating.
 */

/* Sampling wakes align to these Unix-time boundaries. */
const uint32_t MEASURE_INTERVAL_S = 5;
/* An uplink is sent on every crossing of this Unix-time boundary. */
const uint32_t REPORT_INTERVAL_S = 300;
/* Never schedule a wake closer than this; leaves headroom for loop execution lag. */
const uint32_t MIN_SLEEP_MS = 500;
/* Re-request the network time after this many uplinks (288 * 5 min = 24 h). */
const uint16_t RESYNC_AFTER_REPORTS = 288;

/* False until the first DeviceTimeAns lands; until then we fall back to
 * counting samples and sleeping a fixed interval. */
bool timeSynced = false;
/* Unix-time block index (seconds / REPORT_INTERVAL_S) of the last uplink. */
uint32_t lastReportBlock = 0;
/* Uplinks since the last successful time sync. */
uint16_t reportsSinceSync = 0;
/* Set when the next uplink should carry a DeviceTimeReq. */
bool requestTimeOnNextTx = true;

/*
 * Overrides the weak stub in LoRaWan_APP.cpp. Called from MlmeConfirm() after
 * the MAC layer has already applied the new system time, so TimerGetSysTime()
 * is authoritative in here.
 */
void dev_time_updated() {
    TimerSysTime_t now = TimerGetSysTime();
    Serial.printf("[time] synced from network: unix %u.%03u\r\n",
                  (unsigned int)now.Seconds, (unsigned int)now.SubSeconds);

    /* Anchor the report schedule to the block we are in right now, otherwise
     * the clock jump would look like a missed report and fire an uplink
     * immediately after this one. */
    lastReportBlock = now.Seconds / REPORT_INTERVAL_S;
    reportsSinceSync = 0;
    requestTimeOnNextTx = false;
    timeSynced = true;
}

/*
 * Milliseconds until the next Unix-time multiple of `intervalSeconds`.
 * Skips forward whole intervals if the next boundary is too close to hit.
 */
static uint32_t msUntilNextBoundary(uint32_t intervalSeconds) {
    TimerSysTime_t now = TimerGetSysTime();
    uint32_t secondsPast = now.Seconds % intervalSeconds;
    int32_t waitMs = (int32_t)(intervalSeconds - secondsPast) * 1000 - (int32_t)now.SubSeconds;

    while (waitMs < (int32_t)MIN_SLEEP_MS) {
        waitMs += (int32_t)(intervalSeconds * 1000);
    }
    return (uint32_t)waitMs;
}

/****************************************************
 * general wheather station PREAMBLE
 ****************************************************/

/* Weather Station Variables */
/* Only used as the pre-sync fallback; once synced the schedule is time-driven. */
uint32_t numSamples = REPORT_INTERVAL_S / MEASURE_INTERVAL_S;
uint32_t measurementInterval_s = MEASURE_INTERVAL_S;
// for testing
// uint32_t numSamples = 2;
// uint32_t measurementInterval_s = 10;
int sampleCount = 0;

/*
 * True when a new REPORT_INTERVAL_S block has been entered since the last
 * uplink. Comparing block indices (rather than counting samples) keeps the
 * schedule correct even if a wake is missed or the clock is stepped.
 */
static bool isReportDue() {
    if (!timeSynced) {
        return sampleCount >= (int)numSamples;
    }
    uint32_t block = TimerGetSysTime().Seconds / REPORT_INTERVAL_S;
    if (block == lastReportBlock) {
        return false;
    }
    lastReportBlock = block;
    return true;
}

// Fan Specifics (disabled - no PWM/tachometer)
// Adafruit_PWMServoDriver pwmBoard = Adafruit_PWMServoDriver();
// const int fan_tach_pin = GPIO1;  
// const int pwm_channel = 0;   
// int target_speed_pct = 50; 
// const int fan_speed_measurement_timems = 500;
// int current_fan_rpm = 0;

/* Sensor Objects */
Adafruit_BMP280 bmp;
Adafruit_ADS1115 ads;
Adafruit_INA3221 ina3221;

SHT4x sht;

/*everything for the sht temperature humidity sensor*/
#define SHT_DEFAULT_ADDRESS   0x44

/* Statistics Trackers (Note: Removed RTC_DATA_ATTR for CubeCell) */
SensorStats bmp280Tempstats = {0, 200000.0, -200000.0};
SensorStats bmp280Pressurestats = {0, 200000.0, 0.0};
SensorStats lightIntensityStats = {0, 200000.0, 0.0};
SensorStats shtTempstats = {0, 200000.0, -200000.0};
SensorStats shtHumidityStats = {0, 200000.0, 0.0};
WindDirectionTracker windDirectionTracker = {0.0, 0.0};
WindSpeedTracker windSpeedTracker;
RainTracker rainTracker; 
SensorStats voltageStats = {0, 200000.0, 0.0};
SensorStats currentStats = {0, 200000.0, 0.0};
// SensorStats powerStats = {0, 200000.0, 0.0};


/*gpio pins*/
const byte windPin = GPIO2; 
const byte rainPin = GPIO3;

/* ADC channels for sensors */
uint32_t adcWinddirectionChannel = 1;
uint32_t adcLightIntensityChannel = 0;

// Increment this whenever you change the payload structure
uint8_t payloadVersion = 5;
uint16_t battery_voltage_mv = 0;

/* Prepares the payload of the frame */
static void prepareTxFrame( uint8_t port ) {
    uint16_t cursor = 0;

    // Version byte
    appData[cursor++] = payloadVersion;
    // pack all the stats
    windDirectionTracker.pack(appData, cursor, sampleCount, 1, 2);
    windSpeedTracker.pack(appData, cursor);
    bmp280Tempstats.pack(appData, cursor, sampleCount, 100, 2);
    bmp280Pressurestats.pack(appData, cursor, sampleCount, 100, 4);
    lightIntensityStats.pack(appData, cursor, sampleCount, 10, 2);
    shtTempstats.pack(appData, cursor, sampleCount, 100, 2);
    shtHumidityStats.pack(appData, cursor, sampleCount, 100, 2);
    rainTracker.pack(appData, cursor); 
    // voltageStats.pack(appData, cursor, sampleCount, 100, 2); 
    // currentStats.pack(appData, cursor, sampleCount, 100, 2);
    // powerStats.pack(appData, cursor, sampleCount, 100, 2);

    // 09. Battery Voltage (2 bytes, in mV, no scaling)
    appData[cursor++] = (uint8_t)(battery_voltage_mv >> 8);
    appData[cursor++] = (uint8_t)(battery_voltage_mv & 0xFF);

    // print all the stats
    windDirectionTracker.print(sampleCount);
    windSpeedTracker.print();
    bmp280Tempstats.print("temp",sampleCount);
    bmp280Pressurestats.print("pressure",sampleCount);
    lightIntensityStats.print("light",sampleCount);
    shtTempstats.print("sht temp",sampleCount);
    shtHumidityStats.print("sht humidity",sampleCount);
    rainTracker.print();
    Serial.print("Battery Voltage (mV): ");
    Serial.println(battery_voltage_mv);
    // currentStats.print("Current (mA)", sampleCount);
    // powerStats.print("Power (mW)", sampleCount);


    appDataSize = cursor;
    // --- DEBUG: PRINT RAW PAYLOAD ---
    Serial.print("Raw Payload (HEX): ");
    for (int i = 0; i < appDataSize; i++) {
        if (appData[i] < 0x10) Serial.print("0"); // Add leading zero for single digits
        Serial.print(appData[i], HEX);
        Serial.print(" ");
    }
    Serial.println();
}

void setup() {
    Serial.begin(115200);
    


    // CubeCell Power Management: Turn on Vext to power sensors
    // pinMode(Vext, OUTPUT);
    // digitalWrite(Vext, LOW);
    // ADC_CTL not used — battery voltage read via ADS1115 channel A3
    Wire.begin();
    delay(100);
    if (!ads.begin()) {
        Serial.println("ADS1115 Fail!");
        while (1);
    }
    ads.setGain(GAIN_ONE); // Sets range to +/- 4.096V, 0.125mV/step (matches Utils.cpp scale)

    if (!bmp.begin(0x76)) {
        Serial.println("BMP280 Fail!");
        while (1);
    }

    if (!sht.begin()) {
        Serial.println("SHT Fail!");
        while (1);
    }


    // ina3221.begin(0x40, &Wire);
    // if (!ina3221.begin()) { // can use other I2C addresses or buses
    //     Serial.println("Failed to find INA3221 chip");
    //     while (1)
    //     delay(10);
    // }

    // if (!ina3221.begin(0x41, &Wire)) { 
    // Serial.println("Failed to find INA3221 chip at 0x41");
    // while (1) delay(10);
    // }

    // PWM board disabled in V3
    // if (!pwmBoard.begin()) {
    //     Serial.println("PWM Board Fail!");
    //     while (1);
    // }

    // RAIN SENSOR INIT
    pinMode(rainPin, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(rainPin), rain_Counter, FALLING);

    // WIND SENSOR INIT
    pinMode(windPin, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(windPin), wind_Counter, FALLING);

    // Initialize tracker bounds/counters before first sampling window.
    windSpeedTracker.reset();

    // power sensor init
    // ina3221.setAveragingMode(INA3221_AVG_16_SAMPLES);

    // Fan controller disabled in V3
    // pwmBoard.setPWMFreq(1600); 
    // pinMode(fan_tach_pin, INPUT_PULLUP);
    // setExternalFanSpeed(pwmBoard, pwm_channel, target_speed_pct);

    // // Set shunt resistances for all channels to 0.05 ohms
    // for (uint8_t i = 0; i < 3; i++) {
    //     ina3221.setShuntResistance(i, 0.05);
    // }

    // // Set a power valid alert to tell us if ALL channels are between the two
    // ina3221.setPowerValidLimits(2.0 /* lower limit */, 15.0 /* upper limit */);


    deviceState = DEVICE_STATE_INIT;

    Serial.println("everything got properly initialized...");
}

void loop() {
    switch( deviceState ) {
        case DEVICE_STATE_INIT: {
            LoRaWAN.init(loraWanClass, loraWanRegion);
            deviceState = DEVICE_STATE_JOIN;
            break;
        }
        case DEVICE_STATE_JOIN: {
            LoRaWAN.join();
            break;
        }
        case DEVICE_STATE_SEND: {
            // 1. Collect Samples
            int16_t windRaw = ads.readADC_SingleEnded(1);
            // Convert raw value to Volts: (Raw * 0.125mV) / 1000
            float windVolts = (windRaw * 0.125) / 1000.0;
            int16_t refRaw = ads.readADC_SingleEnded(2);
            float refVolts = (refRaw * 0.125) / 1000.0;
            
            // Use your utility function for degrees
            float degrees = getWindDirection(windVolts, refVolts);

            //light intensity
            float solarRadiation = getSolarRadiation(ads, adcLightIntensityChannel);
            
            //the sht sensor
            sht.read(); 
            shtTempstats.update(sht.getTemperature());
            shtHumidityStats.update(sht.getHumidity());

            // //the power sensor
            // Ina3221Reading r = readIna3221Channel(ina3221, 0);
            // float voltage_V = r.voltage_V;
            // float current_mA = r.current_mA;
            // float power_mW = r.power_mW;
            // voltageStats.update(r.voltage_V);
            // currentStats.update(r.current_mA);
            // powerStats.update(r.power_mW);

            windDirectionTracker.update(degrees);
            windSpeedTracker.update();
            bmp280Tempstats.update(bmp.readTemperature());
            bmp280Pressurestats.update(bmp.readPressure());
            lightIntensityStats.update(solarRadiation);


            sampleCount++;

            // 2. Check if it is time to Uplink
            if (isReportDue()) {
                // Piggyback a DeviceTimeReq on this uplink when the clock is
                // unsynced or stale. The answer arrives in RX1/RX2 and lands in
                // dev_time_updated().
                if (!timeSynced || requestTimeOnNextTx) {
                    MlmeReq_t mlmeReq;
                    mlmeReq.Type = MLME_DEVICE_TIME;
                    LoRaMacMlmeRequest(&mlmeReq);
                    Serial.println("[time] DeviceTimeReq attached to this uplink");
                }

                // Read battery voltage once before sending
                // Read battery voltage from ADS1115 channel A3 (0.1875 mV/bit at default gain)
                // battery_voltage_mv = (uint16_t)(ads.readADC_SingleEnded(3) * 0.1875f);
                battery_voltage_mv = getBatteryVoltage();
                prepareTxFrame(appPort);
                LoRaWAN.send();

                if (timeSynced && ++reportsSinceSync >= RESYNC_AFTER_REPORTS) {
                    Serial.println("[time] sync is stale, will re-request next uplink");
                    requestTimeOnNextTx = true;
                }
                //reset the values

                sampleCount = 0;
                // Reset your stats here if your Utils.h has a reset function
                bmp280Tempstats.reset();     // Ensure these functions set Sum to 0
                bmp280Pressurestats.reset(); // and reset Min/Max to defaults
                windDirectionTracker.reset();
                windSpeedTracker.reset();
                lightIntensityStats.reset();
                shtTempstats.reset();
                shtHumidityStats.reset();
                rainTracker.reset(); // Resets the actual rain_pulse_count to 0
                voltageStats.reset();
                currentStats.reset();
                // powerStats.reset();
                deviceState = DEVICE_STATE_CYCLE;
            } else {
                // Not ready to send yet, just go back to sleep/cycle
                deviceState = DEVICE_STATE_CYCLE;
            }
            break;
        }
        case DEVICE_STATE_CYCLE: {
            if (timeSynced) {
                // Sleep to the next absolute boundary, so lag and oscillator
                // error are cancelled every cycle instead of accumulating.
                txDutyCycleTime = msUntilNextBoundary(MEASURE_INTERVAL_S);
            } else {
                // No network time yet: plain fixed interval.
                txDutyCycleTime = measurementInterval_s * 1000;
            }
            Serial.printf("[time] next wake in %u ms (synced=%d)\r\n",
                          (unsigned int)txDutyCycleTime, (int)timeSynced);
            LoRaWAN.cycle(txDutyCycleTime);
            deviceState = DEVICE_STATE_SLEEP;
            break;
        }
        case DEVICE_STATE_SLEEP: {
            LoRaWAN.sleep();
            break;
        }
        default: {
            deviceState = DEVICE_STATE_INIT;
            break;
        }
    }
}
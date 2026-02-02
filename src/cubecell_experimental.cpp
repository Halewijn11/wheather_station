#include "LoRaWan_APP.h"
#include "Arduino.h"
#include <Adafruit_BMP280.h>
#include <Adafruit_ADS1X15.h>
#include "Adafruit_INA3221.h"
#include "Utils.h"
#include "SHT4x.h"


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
uint8_t devEui[] = { 0x70, 0xB3, 0xD5, 0x7E, 0xD0, 0x07, 0x48, 0x25 };
uint8_t appEui[] = { 0x70, 0xB3, 0xD5, 0x7E, 0xD0, 0x07, 0x48, 0x24 };
uint8_t appKey[] = { 0x84, 0xFA, 0x82, 0x39, 0x81, 0x30, 0x31, 0x63, 0xAF, 0xE2, 0x96, 0x87, 0x97, 0xAF, 0xDD, 0x49 };

/* ABP para*/
uint8_t nwkSKey[] = { 0x15, 0xb1, 0xd0, 0xef, 0xa4, 0x63, 0xdf, 0xbe, 0x3d, 0x11, 0x18, 0x1e, 0x1e, 0xc7, 0xda,0x85 };
uint8_t appSKey[] = { 0xd7, 0x2c, 0x78, 0x75, 0x8c, 0xdc, 0xca, 0xbf, 0x55, 0xee, 0x4a, 0x77, 0x8d, 0x16, 0xef,0x67 };
uint32_t devAddr =  ( uint32_t )0x007e6ae1;

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
 * general wheather station PREAMBLE  
 ****************************************************/

/* Weather Station Variables */
uint32_t numSamples = 15; 
uint32_t measurementInterval_s = 1;
int sampleCount = 0;

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
SensorStats powerStats = {0, 200000.0, 0.0};


/*gpio pins*/
const byte rainPin = GPIO2;
const byte windPin = GPIO1; 

/* ADC channels for sensors */
uint32_t adcWinddirectionChannel = 1;
uint32_t adcLightIntensityChannel = 0;

// Increment this whenever you change the payload structure
uint8_t payloadVersion = 1; 

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
    lightIntensityStats.pack(appData, cursor, sampleCount, 100, 2);
    shtTempstats.pack(appData, cursor, sampleCount, 100, 2);
    shtHumidityStats.pack(appData, cursor, sampleCount, 100, 2);
    rainTracker.pack(appData, cursor); 
    voltageStats.pack(appData, cursor, sampleCount, 100, 2); 
    currentStats.pack(appData, cursor, sampleCount, 100, 2);
    powerStats.pack(appData, cursor, sampleCount, 100, 2);

    // print all the stats
    windDirectionTracker.print(sampleCount);
    windSpeedTracker.print();
    bmp280Tempstats.print("temp",sampleCount);
    bmp280Pressurestats.print("pressure",sampleCount);
    lightIntensityStats.print("light",sampleCount);
    shtTempstats.print("sht temp",sampleCount);
    shtHumidityStats.print("sht humidity",sampleCount);
    // print all the stats
    voltageStats.print("Voltage (V)", sampleCount);
    currentStats.print("Current (mA)", sampleCount);
    powerStats.print("Power (mW)", sampleCount);
    rainTracker.print(); 


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
    
    // CubeCell specific MCU init
    boardInitMcu();

    // CubeCell Power Management: Turn on Vext to power sensors
    pinMode(Vext, OUTPUT);
    digitalWrite(Vext, LOW); 
    delay(100); // Give sensors time to wake up

    if (!ads.begin()) {
        Serial.println("ADS1115 Fail!");
        while (1);
    }

    if (!bmp.begin(0x76)) {
        Serial.println("BMP280 Fail!");
        while (1);
    }

    if (!sht.begin()) {
        Serial.println("SHT Fail!");
        while (1);
    }

    if (!ina3221.begin(0x40, &Wire)) { // can use other I2C addresses or buses
        Serial.println("Failed to find INA3221 chip");
        while (1)
        delay(10);
    }

    // RAIN SENSOR INIT
    pinMode(rainPin, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(rainPin), rain_Counter, FALLING);

    // WIND SENSOR INIT
    pinMode(windPin, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(windPin), wind_Counter, FALLING);

    // power sensor init
    ina3221.setAveragingMode(INA3221_AVG_16_SAMPLES);

    // Set shunt resistances for all channels to 0.05 ohms
    for (uint8_t i = 0; i < 3; i++) {
        ina3221.setShuntResistance(i, 0.05);
    }

    // Set a power valid alert to tell us if ALL channels are between the two
    ina3221.setPowerValidLimits(2.0 /* lower limit */, 15.0 /* upper limit */);


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
            int16_t windRaw = ads.readADC_SingleEnded(adcWinddirectionChannel);
            float windVolts = (windRaw * 0.125) / 1000.0;
            float degrees = getWindDirection(windVolts, 3.3);

            //light intensity
            int16_t lightRaw = ads.readADC_SingleEnded(adcLightIntensityChannel);
            float lightsensor_millivolts = lightRaw * 0.125;
            float solarRadiation = lightsensor_millivolts / 1.67;
            if (solarRadiation < 0) solarRadiation = 0; // save from negative readings
            
            //the sht sensor
            sht.read(); 
            shtTempstats.update(sht.getTemperature());
            shtHumidityStats.update(sht.getHumidity());

            //the power sensor
            Ina3221Reading r = readIna3221Channel(ina3221, 0);
            float voltage_V = r.voltage_V;
            float current_mA = r.current_mA;
            float power_mW = r.power_mW;
            voltageStats.update(r.voltage_V);
            currentStats.update(r.current_mA);
            powerStats.update(r.power_mW);

            windDirectionTracker.update(degrees);
            windSpeedTracker.update();
            bmp280Tempstats.update(bmp.readTemperature());
            bmp280Pressurestats.update(bmp.readPressure());
            lightIntensityStats.update(solarRadiation);


            sampleCount++;

            // 2. Check if it is time to Uplink
            if (sampleCount >= numSamples) {
                prepareTxFrame(appPort);
                LoRaWAN.send();
                //reset the values

                sampleCount = 0;
                // Reset your stats here if your Utils.h has a reset function
                bmp280Tempstats.reset();     // Ensure these functions set Sum to 0
                bmp280Pressurestats.reset(); // and reset Min/Max to defaults
                windDirectionTracker.reset();
                lightIntensityStats.reset();
                shtTempstats.reset();
                shtHumidityStats.reset();
                rainTracker.reset(); // Resets the actual rain_pulse_count to 0
                voltageStats.reset();
                currentStats.reset();
                powerStats.reset();
                deviceState = DEVICE_STATE_CYCLE;
            } else {
                // Not ready to send yet, just go back to sleep/cycle
                deviceState = DEVICE_STATE_CYCLE;
            }
            break;
        }
        case DEVICE_STATE_CYCLE: {
            txDutyCycleTime = measurementInterval_s * 1000;
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
/* Heltec Automation LoRaWAN communication example
 *
 * Function:
 * 1. Upload node data to the server using the standard LoRaWAN protocol.
 * 2. Request timestamp data from the LoRaWAN server.
 * 
 * Description:
 * 1. Communicate using LoRaWAN protocol.
 * 
 * HelTec AutoMation, Chengdu, China
 * 成都惠利特自动化科技有限公司
 * www.heltec.org
 *
 * this project also realess in GitHub:
 * https://github.com/Heltec-Aaron-Lee/WiFi_Kit_series
 * 
 * join eui (appeui): a09926978803a4ab
 * devEUI: 70B3D57ED0074FF3
 * app_key: F25E86E02AF61AC8311025EE4A5A9BFE
 * */



#include "LoRaWan_APP.h"
#include <DFRobot_B_LUX_V30B.h>
#include "Utils.h"
#include "SHT4x.h"


/****************************************************
 * LORA PREAMBLE  
 ****************************************************/
/* OTAA para*/
uint8_t devEui[] = { 0x70, 0xB3, 0xD5, 0x7E, 0xD0, 0x07, 0x4F, 0xF3 };
uint8_t appEui[] = { 0xA0, 0x99, 0x26, 0x97, 0x88, 0x03, 0xA4, 0xAB };
uint8_t appKey[] = { 0xF2, 0x5E, 0x86, 0xE0, 0x2A, 0xF6, 0x1A, 0xC8, 0x31, 0x10, 0x25, 0xEE, 0x4A, 0x5A, 0x9B, 0xFE };

/* ABP para*/
uint8_t nwkSKey[] = { 0x15, 0xb1, 0xd0, 0xef, 0xa4, 0x63, 0xdf, 0xbe, 0x3d, 0x11, 0x18, 0x1e, 0x1e, 0xc7, 0xda,0x85 };
uint8_t appSKey[] = { 0xd7, 0x2c, 0x78, 0x75, 0x8c, 0xdc, 0xca, 0xbf, 0x55, 0xee, 0x4a, 0x77, 0x8d, 0x16, 0xef,0x67 };
uint32_t devAddr =  ( uint32_t )0x007e6ae1;

/*LoraWan channelsmask, default channels 0-7*/ 
uint16_t userChannelsMask[6]={ 0x00FF,0x0000,0x0000,0x0000,0x0000,0x0000 };

/*LoraWan region, select in arduino IDE tools*/
LoRaMacRegion_t loraWanRegion = ACTIVE_REGION;

/*LoraWan Class, Class A and Class C are supported*/
DeviceClass_t  loraWanClass = CLASS_A;

/*OTAA or ABP*/
bool overTheAirActivation = true;

/*ADR enable*/
bool loraWanAdr = true;

/* Indicates if the node is sending confirmed or unconfirmed messages */
bool isTxConfirmed = true;

/* Application port */
uint8_t appPort = 2;

/*the application data transmission duty cycle.  value in [ms].*/
uint32_t appTxDutyCycle = 15000;

// These variables survive Deep Sleep
RTC_DATA_ATTR float tempSum = 0;
RTC_DATA_ATTR float tempMin = 999.0; // Start high
RTC_DATA_ATTR float tempMax = -999.0; // Start low
RTC_DATA_ATTR int   sampleCount = 0;
RTC_DATA_ATTR int   txCounter = 0; // To track the 24h drift correction

uint32_t measurementInterval_s = 1; // 5 seconds
uint32_t totalSamplesNeeded = 15; // 12 * 5s = 60s


/****************************************************
 * V30B PREAMBLE 
 ****************************************************/
DFRobot_B_LUX_V30B    myLux(16);
RTC_DATA_ATTR SensorStats luxStats = {0, 200000.0, 0.0};


/****************************************************
 * SHT45 PRAMBLE 
 ****************************************************/
#define SHT_DEFAULT_ADDRESS   0x44
SHT4x sht;
RTC_DATA_ATTR SensorStats humidityStats = {0, 100.0, 0.0};
RTC_DATA_ATTR SensorStats temperatureStats = {0, 999.0, -999.0};

// RTC_DATA_ATTR float luxSum = 0;
// RTC_DATA_ATTR float luxMin = 200000.0; // Start higher than max sunlight (~120k lux)
// RTC_DATA_ATTR float luxMax = 0.0;      // Start at absolute darkness



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

/* Prepares the payload of the frame */
static void prepareTxFrame( uint8_t port )
{
    uint16_t cursor = 0;
    // luxStats.pack(appData,cursor, sampleCount, 100, 4);
    humidityStats.pack(appData,cursor, sampleCount, 100, 2);
    temperatureStats.pack(appData,cursor, sampleCount, 100, 2);

    // luxStats.print("LUX", sampleCount);
    humidityStats.print("HUM", sampleCount);
    temperatureStats.print("TMP", sampleCount);

    appDataSize=cursor;
    // --- DEBUG: PRINT RAW PAYLOAD ---
    Serial.print("Raw Payload (HEX): ");
    for (int i = 0; i < appDataSize; i++) {
        if (appData[i] < 0x10) Serial.print("0"); // Add leading zero for single digits
        Serial.print(appData[i], HEX);
        Serial.print(" ");
    }
    Serial.println();
}

//if true, next uplink will add MOTE_MAC_DEVICE_TIME_REQ 
RTC_DATA_ATTR bool timeReq = true;

void dev_time_updated()
{
  printf("Once device time updated, this function run\r\n");
}

void setup() {
    // Wire.begin(41, 42); 
    // Wire.setClock(100000);
    // Wire.begin();
    Serial.begin(115200);
    Mcu.begin(HELTEC_BOARD,SLOW_CLK_TPYE);

    /****************************************************
     * V30B SETUP  
     ****************************************************/
    // Serial.print("V30B (Lux) begin... ");
    // myLux.begin();
    // Serial.println("Done.");
    /****************************************************
     * SHT45 SETUP  
     ****************************************************/
    Serial.print("SHT4x (Temp/Hum) begin... ");
    Wire.begin();
    Wire.setClock(100000);
    sht.begin();
    Serial.println("Done.");
}

void loop()
{
  switch( deviceState )
  {
    case DEVICE_STATE_INIT:
    {
#if(LORAWAN_DEVEUI_AUTO)
      LoRaWAN.generateDeveuiByChipID();
#endif
      LoRaWAN.init(loraWanClass,loraWanRegion);
      //both set join DR and DR when ADR off 
      LoRaWAN.setDefaultDR(3);
      break;
    }
    case DEVICE_STATE_JOIN:
    {
      LoRaWAN.join();
      break;
    }
case DEVICE_STATE_SEND:
{

    // 1. THE SMALL GEAR: TAKE THE READING
    // float currentLux = myLux.lightStrengthLux();
    // delay(20);
    sht.read();
    float currentHumidity = sht.getHumidity();
    float currentTemperature = sht.getTemperature();

    // sht.read();
    // float currentHumidity = 5;
    // float currentTemperature = 5;

    Serial.print("Humidity: "); Serial.print(currentHumidity); Serial.print(" %\t");
    Serial.print("Temperature: "); Serial.print(currentTemperature); Serial.println(" °C");
    // Serial.print("Lux: "); Serial.print(currentLux); Serial.println(" lx");

    // 2. UPDATE STATS
    // luxStats.update(currentLux);
    humidityStats.update(currentHumidity);
    temperatureStats.update(currentTemperature);
    sampleCount++;

    // 3. THE BIG GEAR: SHOULD WE SEND TO THE INTERNET?
    if (sampleCount >= 12) { // 12 samples * 5 seconds = 60 seconds

    // Prepare the payload (sending Avg, Min, and Max)
    prepareTxFrame(appPort); 
    LoRaWAN.send();

    // RESET everything for the next 60s window
    luxStats.reset(200000.0, 0.0);
    humidityStats.reset(100.0, 0.0);         // Added
    temperatureStats.reset(999.0, -999.0);   // Added

    sampleCount = 0;

    deviceState = DEVICE_STATE_CYCLE;
    } else {
        deviceState = DEVICE_STATE_CYCLE; // Still need to sleep/cycle between samples!
    }
    break; // <--- YOU MUST ADD THIS
}


    case DEVICE_STATE_CYCLE:
    {
      // Standard Heltec cycle logic (simplified)
      txDutyCycleTime = measurementInterval_s * 1000;
      LoRaWAN.cycle(txDutyCycleTime);
      deviceState = DEVICE_STATE_SLEEP;
      break;
    }
    case DEVICE_STATE_SLEEP:
    {
      LoRaWAN.sleep(loraWanClass);
      break;
    }
    default:
    {
      deviceState = DEVICE_STATE_INIT;
      break;
    }
  }
}
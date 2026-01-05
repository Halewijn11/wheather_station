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

uint32_t measurementInterval_s = 5; // 5 seconds
uint32_t totalSamplesNeeded = 12; // 12 * 5s = 60s


/****************************************************
 * V30B PREAMBLE 
 ****************************************************/
DFRobot_B_LUX_V30B    myLux(16);
RTC_DATA_ATTR float luxSum = 0;
RTC_DATA_ATTR float luxMin = 200000.0; // Start higher than max sunlight (~120k lux)
RTC_DATA_ATTR float luxMax = 0.0;      // Start at absolute darkness



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
    // 1. Calculate the average first
    // We use (float)sampleCount to ensure floating point math
    float luxAverage = luxSum / (float)sampleCount;

    // 2. Convert floats to 32-bit integers (removes decimals, but Lux is usually precise enough as an int)
    uint32_t avgBase = (uint32_t)luxAverage;
    uint32_t minBase = (uint32_t)luxMin;
    uint32_t maxBase = (uint32_t)luxMax;

    // 3. Define payload size (3 values * 4 bytes each = 12 bytes)
    appDataSize = 12;

    // Pack Average (Bytes 0-3)
    appData[0] = (uint8_t)(avgBase >> 24);
    appData[1] = (uint8_t)(avgBase >> 16);
    appData[2] = (uint8_t)(avgBase >> 8);
    appData[3] = (uint8_t)(avgBase);

    // Pack Min (Bytes 4-7)
    appData[4] = (uint8_t)(minBase >> 24);
    appData[5] = (uint8_t)(minBase >> 16);
    appData[6] = (uint8_t)(minBase >> 8);
    appData[7] = (uint8_t)(minBase);

    // Pack Max (Bytes 8-11)
    appData[8] = (uint8_t)(maxBase >> 24);
    appData[9] = (uint8_t)(maxBase >> 16);
    appData[10] = (uint8_t)(maxBase >> 8);
    appData[11] = (uint8_t)(maxBase);
}

//if true, next uplink will add MOTE_MAC_DEVICE_TIME_REQ 
RTC_DATA_ATTR bool timeReq = true;

void dev_time_updated()
{
  printf("Once device time updated, this function run\r\n");
}

void setup() {
    Serial.begin(115200);
    Mcu.begin(HELTEC_BOARD,SLOW_CLK_TPYE);

    /****************************************************
     * V30B SETUP  
     ****************************************************/
    myLux.begin();
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
    float currentLux = myLux.lightStrengthLux(); // Your sensor function

    // 2. UPDATE STATS
    luxSum += currentLux;
    if (currentLux < luxMin) luxMin = currentLux;
    if (currentLux > luxMax) luxMax = currentLux;
    sampleCount++;

    // --- DEBUG PRINT ---
    Serial.print("Sample: "); Serial.print(sampleCount);
    Serial.print("/"); Serial.print(totalSamplesNeeded);
    Serial.print(" | current Lux: "); Serial.println(currentLux);
    Serial.print(" | lux sum: "); Serial.println(luxSum);
    Serial.print(" | Min: "); Serial.print(luxMin);
    Serial.print(" | Max: "); Serial.println(luxMax);


    // 3. THE BIG GEAR: SHOULD WE SEND TO THE INTERNET?
    if (sampleCount >= 12) { // 12 samples * 5 seconds = 60 seconds
    
    // Calculate average
    float luxAverage = luxSum / sampleCount;
    Serial.println(">> 60s limit reached. Sending LoRaWAN Uplink!");
    Serial.print(">> Avg: "); Serial.print(luxAverage);
    Serial.print(" | Min: "); Serial.print(luxMin);
    Serial.print(" | Max: "); Serial.println(luxMax);



    // Prepare the payload (sending Avg, Min, and Max)
    prepareTxFrame(appPort); 
    LoRaWAN.send();

    // RESET everything for the next 60s window
    luxSum = 0;
    luxMin = 200000.0; // Start higher than max sunlight (~120k lux)
    luxMax = 0.0;      // Start at absolute darkness
    sampleCount = 0;

    deviceState = DEVICE_STATE_CYCLE;
      }
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
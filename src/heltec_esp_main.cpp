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
#include "Utils.h" // my own library
#include <Adafruit_ADS1X15.h>//used for reading the wind direction and light intensity value
#include <Adafruit_BMP280.h>
// #include "Adafruit_INA3221.h" e
// #include <DFRobot_B_LUX_V30B.h>

/****************************************************
 * general wheather station PREAMBLE  
 ****************************************************/
// initialize the variable that stores how many samples should be taken
uint32_t numSamples = 15; //the number of samples to be taken within 1 reporting interval
// initialize the variable that stores the time between samples
uint32_t measurementInterval_s = 1; // time between samples in seconds
// initialize the adc channel to which the wind direction sensor is connected
uint32_t adcWinddirectionChannel = 2;

//pin definitions
//for heltec esp32 

//for the cubecell
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



/****************************************************
 * V30B PREAMBLE 
 ****************************************************/
// DFRobot_B_LUX_V30B    myLux(16);
// RTC_DATA_ATTR SensorStats luxStats = {0, 200000.0, 0.0};

/****************************************************
 * analog sensor PREAMBLE 
 ****************************************************/
// Adafruit_INA3221 ina3221;
Adafruit_ADS1115 ads;

/****************************************************
 * wind direction preamble 
 ****************************************************/
RTC_DATA_ATTR WindDirectionTracker windDirectionTracker = {0.0, 0.0};

/****************************************************
 * BMP 280 PREAMBLE 
 ****************************************************/
Adafruit_BMP280 bmp; // Create the sensor object
RTC_DATA_ATTR SensorStats bmp280Tempstats = {0,200000.0, -200000.0};
RTC_DATA_ATTR SensorStats bmp280Pressurestats = {0, 200000.0, 0.0};
#define BMP280_ADDRESS 0x76



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
    
    // luxStats.print("LUX", sampleCount);
    // luxStats.pack(appData,cursor, sampleCount, 100, 4);
    // pack all the stats
    windDirectionTracker.pack(appData, cursor, sampleCount, 1, 2);
    bmp280Tempstats.pack(appData, cursor, sampleCount, 100, 2);
    bmp280Pressurestats.pack(appData, cursor, sampleCount, 100, 4);

    // print all the stats
    windDirectionTracker.print(sampleCount);
    bmp280Tempstats.print("temp",sampleCount);
    bmp280Pressurestats.print("pressure",sampleCount);

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
    Serial.begin(115200);
    Mcu.begin(HELTEC_BOARD,SLOW_CLK_TPYE);

    /****************************************************
     * V30B SETUP  
     ****************************************************/
    // myLux.begin();

    //################## Initialize the adc ###############################3
    // Wire.begin();
      //Initialize the INA3221 chip
    ads.setGain(GAIN_ONE); 
    if (!ads.begin()) {
      Serial.println("Failed to initialize ADS1115!");
      while (1);
    }
    // Set averaging for stability (16 samples)
    // ina3221.setAveragingMode(INA3221_AVG_16_SAMPLES);


    //################## Initialize the BMP280 sensor ###############################3
    unsigned status;
    status = bmp.begin(BMP280_ADDRESS);
    if (!status) {
      Serial.println(F("Could not find a valid BMP280 sensor, check wiring or "
                        "try a different address!"));
      Serial.print("SensorID was: 0x"); Serial.println(bmp.sensorID(),16);
      Serial.print("        ID of 0xFF probably means a bad address, a BMP 180 or BMP 085\n");
      Serial.print("   ID of 0x56-0x58 represents a BMP 280,\n");
      Serial.print("        ID of 0x60 represents a BME 280.\n");
      Serial.print("        ID of 0x61 represents a BME 680.\n");
      while (1) delay(10);
    }
    /* Default settings from datasheet. */
    bmp.setSampling(Adafruit_BMP280::MODE_NORMAL,     /* Operating Mode. */
                    Adafruit_BMP280::SAMPLING_X2,     /* Temp. oversampling */
                    Adafruit_BMP280::SAMPLING_X16,    /* Pressure oversampling */
                    Adafruit_BMP280::FILTER_X16,      /* Filtering. */
                    Adafruit_BMP280::STANDBY_MS_500);
    

    Serial.println("Everything got initialized!");

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
    // read the wind direction with the adc
    int16_t windRaw = ads.readADC_SingleEnded(1);
    float windVolts = (windRaw * 0.125) / 1000.0;
    float degrees = getWindDirection(windVolts, 3.3);
    windDirectionTracker.update(degrees);

    // read the BMP280 temperature and pressure
    float bmpTemp = bmp.readTemperature();
    float bmpPressure = bmp.readPressure(); // Convert to hPa
    // Update BMP280 stats
    bmp280Tempstats.update(bmpTemp);
    bmp280Pressurestats.update(bmpPressure);

    // IMPORTANT: increment the sample count here
    sampleCount++;

    // 3. THE BIG GEAR: SHOULD WE SEND TO THE INTERNET?
    if (sampleCount >= numSamples) { // 12 samples * 5 seconds = 60 seconds
      // Prepare the payload (sending Avg, Min, and Max)
      prepareTxFrame(appPort); 
      LoRaWAN.send();

      // RESET everything for the next 60s window
      // luxStats.reset(200000.0, 0.0);

      // luxStats.reset();
      
      //IMPORTANT: reset the sample count
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
#include "LoRaWan_APP.h"
#include "Arduino.h"
#include "secrets.h" 

/* Mandatory global variable names for internal library linking */
uint8_t devEui[] = SECRET_DEV_EUI;
uint8_t appEui[] = SECRET_APP_EUI;
uint8_t appKey[] = SECRET_APP_KEY;
uint8_t nwkSKey[] = SECRET_NWK_SKEY;
uint8_t appSKey[] = SECRET_APP_SKEY;
uint32_t devAddr = SECRET_DEV_ADDR;

/* Core Network Parameters */
uint16_t userChannelsMask[6] = { 0x00FF, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000 };
LoRaMacRegion_t loraWanRegion = ACTIVE_REGION;
DeviceClass_t loraWanClass = LORAWAN_CLASS;
bool overTheAirActivation = LORAWAN_NETMODE;
bool loraWanAdr = LORAWAN_ADR;
bool keepNet = LORAWAN_NET_RESERVE;
bool isTxConfirmed = LORAWAN_UPLINKMODE;
uint32_t appTxDutyCycle = 15000;
uint8_t appPort = 2;
uint8_t confirmedNbTrials = 4;

bool timeReq = true;

/* Callback function triggered automatically upon successful network sync */
void dev_time_updated() {
    Serial.println("\n>>> Clock successfully calibrated via Network Server!");
}

static void prepareTxFrame(uint8_t port) {
    appDataSize = 4;
    appData[0] = 0x00;
    appData[1] = 0x01;
    appData[2] = 0x02;
    appData[3] = 0x03;
}

void setup() {
    Serial.begin(115200);
    deviceState = DEVICE_STATE_INIT;
}

void loop() {
    switch(deviceState) {
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
            TimerSysTime_t sysTimeCurrent = TimerGetSysTime();
            Serial.printf("Unix time: %u.%d\r\n", (unsigned int)sysTimeCurrent.Seconds, sysTimeCurrent.SubSeconds);
            
            if(timeReq) {
                MlmeReq_t mlmeReq;  
                mlmeReq.Type = MLME_DEVICE_TIME;
                LoRaMacMlmeRequest(&mlmeReq);
                Serial.println("Forced MLME_DEVICE_TIME command into uplink queue.");
            }
            
            prepareTxFrame(appPort);
            LoRaWAN.send();
            deviceState = DEVICE_STATE_CYCLE;
            break;
        }
        case DEVICE_STATE_CYCLE: {
            txDutyCycleTime = appTxDutyCycle + randr(0, APP_TX_DUTYCYCLE_RND);
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
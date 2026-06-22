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
uint8_t appPort = 2;
uint8_t confirmedNbTrials = 4;

// We start with a short duty cycle (e.g., 15s) until we are synced
uint32_t appTxDutyCycle = 15000; 
bool timeSynced = false;

// Time tracking and skipping counters
uint16_t txCounter = 0;
bool forceSyncThisTurn = true; // True by default so it runs immediately on startup

/* Callback function triggered automatically upon successful network sync */
void dev_time_updated() {
    Serial.println("\n>>> Clock successfully calibrated via Network Server!");
    timeSynced = true;
    forceSyncThisTurn = false; // Sync succeeded, turn off forcing
    txCounter = 0;             // Reset counter
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
            Serial.printf("Current Unix time: %u | Tx Count: %u\r\n", (unsigned int)sysTimeCurrent.Seconds, txCounter);
            
            // Check if we haven't synced yet OR if we've hit our 200-transmission window
            if (!timeSynced || forceSyncThisTurn) {
                MlmeReq_t mlmeReq;  
                mlmeReq.Type = MLME_DEVICE_TIME;
                LoRaMacMlmeRequest(&mlmeReq);
                Serial.println(">>> Appending MLME_DEVICE_TIME request to this uplink packet...");
            }
            
            prepareTxFrame(appPort);
            LoRaWAN.send();
            
            // Increment our transmission counter
            txCounter++;
            
            // If we've transmitted 200 times since our last sync, request a refresh next time
            if (txCounter >= 200) {
                Serial.println(">>> 200 transmissions reached. Forcing a time resync on next loop.");
                forceSyncThisTurn = true;
            }

            deviceState = DEVICE_STATE_CYCLE;
            break;
        }
        case DEVICE_STATE_CYCLE: {
            if (timeSynced) {
                TimerSysTime_t sysTimeCurrent = TimerGetSysTime();
                uint32_t currentSeconds = sysTimeCurrent.Seconds;

                // 5 minutes = 300 seconds
                uint32_t interval = 300; 
                uint32_t secondsPastInterval = currentSeconds % interval;
                uint32_t secondsToWait = interval - secondsPastInterval;

                // Protect against execution lag boundary overlaps
                if (secondsToWait < 2) {
                    secondsToWait += interval;
                }

                txDutyCycleTime = secondsToWait * 1000; 
                Serial.printf("Aligned. Next TX in %u seconds.\r\n", secondsToWait);
            } else {
                // Keep polling quickly (every 15 seconds) if the clock isn't aligned yet
                txDutyCycleTime = appTxDutyCycle;
                Serial.println("Initial time sync pending. Retrying in 15 seconds.");
            }
            
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
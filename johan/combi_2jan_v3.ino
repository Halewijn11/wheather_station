#include <Wire.h>
#include <Adafruit_SHT4x.h>
#include <RTClib.h>
#include <math.h>

// Intervallen
const unsigned long tempInterval = 3000;
const unsigned long windInterval = 3000;

// Timing
unsigned long lastTempTime = 0;
unsigned long lastWindTime = 0;
int lastReportMinute = -1; // Houdt bij in welke minuut voor het laatst gerapporteerd is

// Hardware Pins
const byte windPin = 2;
const byte rainPin = 3;
const byte directionPin = A0;
const byte solarPin = A1; 

// Sensoren
Adafruit_SHT4x sht4 = Adafruit_SHT4x();
RTC_DS3231 rtc;

// Volatile voor interrupts
volatile unsigned long pulseCount = 0;
volatile unsigned long rainTips = 0;
const float rainPerTip = 0.2;

// Variabelen voor gemiddelden
float sumTemp = 0, sumHum = 0, sumSolar = 0;
int countTemp = 0;
float sumWindSpeed = 0, maxWindSpeed = 0;
int countWindSpeed = 0;
float sumSin = 0, sumCos = 0;
int countDir = 0;

void countWindPulse() { pulseCount++; }
void countRainPulse() {
  static unsigned long lastTimeRain = 0;
  if (millis() - lastTimeRain > 20) { rainTips++; lastTimeRain = millis(); }
}

void setup() {
  Serial.begin(115200);
  if (!sht4.begin()) { Serial.println("SHT45 fout!"); while (1); }
  if (!rtc.begin()) { Serial.println("RTC fout!"); while (1); }
  
  // Optioneel: zet de tijd gelijk aan de computertijd bij compileren als de RTC niet loopt
  // if (rtc.lostPower()) { rtc.adjust(DateTime(F(__DATE__), F(__TIME__))); }

  pinMode(windPin, INPUT_PULLUP);
  pinMode(rainPin, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(windPin), countWindPulse, FALLING);
  attachInterrupt(digitalPinToInterrupt(rainPin), countRainPulse, FALLING);
  
  Serial.println("Weerstation gestart (Rapportage exact op de minuut)...");
}

void loop() {
  unsigned long currentTime = millis();
  DateTime nu = rtc.now(); // Haal de huidige tijd op

  // --- 1. METINGEN (Temp, vochtigheid & Licht elke 3s) ---
  if (currentTime - lastTempTime >= tempInterval) {
    sensors_event_t humidity, temp;
    sht4.getEvent(&humidity, &temp);
    sumTemp += temp.temperature;
    sumHum += humidity.relative_humidity;
    
    int rawSolar = analogRead(solarPin);
    float mVolt = (rawSolar * 3300) / 1024.0;
    float solarWm2 = mVolt * 0.6 - 6; 
    if (solarWm2 < 0) solarWm2 = 0;
    sumSolar += solarWm2;
    
    countTemp++;
    lastTempTime = currentTime;
  }

  // --- 2. METINGEN (Wind elke 3s) ---
  if (currentTime - lastWindTime >= windInterval) {
    noInterrupts();
    unsigned long pulses = pulseCount;
    pulseCount = 0;
    interrupts();
    
    float currentSpeed = (pulses / 3.0) * 2.4; 
    sumWindSpeed += currentSpeed;
    countWindSpeed++;
    if (currentSpeed > maxWindSpeed) maxWindSpeed = currentSpeed;

    int rawDir = analogRead(directionPin);
    float rad = map(rawDir, 0, 1023, 0, 359) * DEG_TO_RAD;
    sumSin += sin(rad);
    sumCos += cos(rad);
    countDir++;
    lastWindTime = currentTime;
  }

  // --- 3. RAPPORTAGE (Exact op de minuut) ---
  // Controleer of de seconde 0 is en of we deze minuut al geprint hebben
  if (nu.second() == 0 && nu.minute() != lastReportMinute) {
    lastReportMinute = nu.minute(); // Onthoud deze minuut

    noInterrupts();
    unsigned long currentRainTips = rainTips;
    rainTips = 0;
    interrupts();

    // Bereken gemiddelden (check tegen delen door 0)
    float avgTemp = (countTemp > 0) ? sumTemp / countTemp : 0;
    float avgHum  = (countTemp > 0) ? sumHum / countTemp : 0;
    float avgSolar = (countTemp > 0) ? sumSolar / countTemp : 0;
    float avgSpeed = (countWindSpeed > 0) ? sumWindSpeed / countWindSpeed : 0;
    float avgRad = (countDir > 0) ? atan2(sumSin / countDir, sumCos / countDir) : 0;
    int avgDeg = (int)(avgRad * RAD_TO_DEG);
    if (avgDeg < 0) avgDeg += 360;

    Serial.print("\n--- RAPPORT: ");
    if(nu.hour() < 10) Serial.print('0'); Serial.print(nu.hour()); 
    Serial.print(':'); 
    if(nu.minute() < 10) Serial.print('0'); Serial.print(nu.minute());
    Serial.print(':');
    if(nu.second() < 10) Serial.print('0'); Serial.println(nu.second());

    Serial.print("Temperatuur  : "); Serial.print(avgTemp, 1); Serial.println(" C");
    Serial.print("Luchtvochtigh: "); Serial.print(avgHum, 1);  Serial.println(" %");
    Serial.print("Zonnestraling: "); Serial.print(avgSolar, 0); Serial.println(" W/m2");
    Serial.print("Wind Gem/Max : "); Serial.print(avgSpeed, 1); Serial.print(" / "); Serial.print(maxWindSpeed, 1); Serial.println(" km/u");
    Serial.print("Windrichting : "); Serial.print(avgDeg); Serial.println(" graden");
    Serial.print("Neerslag     : "); Serial.print(currentRainTips * rainPerTip, 1); Serial.println(" mm");
    Serial.println("------------------------------------------");

    // Reset tellers voor de nieuwe minuut
    sumTemp = 0; sumHum = 0; sumSolar = 0; countTemp = 0;
    sumWindSpeed = 0; maxWindSpeed = 0; countWindSpeed = 0;
    sumSin = 0; sumCos = 0; countDir = 0;
  }
}
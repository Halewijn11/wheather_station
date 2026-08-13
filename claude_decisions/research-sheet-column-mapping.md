# Research: Sheet column mapping for iPhone widget `doGet` (issue #108)

Parent map issue: #106 "iPhone Weather Widget"

## 1. Production firmware source — CLAUDE.md is STALE

`CLAUDE.md` currently says:

> The `CubeCell-AB01` env currently builds `cubecell_timing_test_stripped_calibration.cpp`, but the production firmware is `src/cubecell_battery_main.cpp`.

That was true as of the commit CLAUDE.md was last edited, but it is **no longer accurate**. Commit `7a69aca` ("Fix ADS1115 gain mismatch and switch build to production firmware", authored today 2026-08-13) changed `platformio.ini`:

```diff
-build_src_filter = +<cubecell_timing_test_stripped_calibration.cpp>
+build_src_filter = +<cubecell_battery_main.cpp>
```

Reading the current `platformio.ini` on this branch confirms the `[env:CubeCell-AB01]` section now has:

```ini
build_src_filter = +<cubecell_battery_main.cpp>
```

**Resolution: production source file is `src/cubecell_battery_main.cpp`, and it now matches what CLAUDE.md claims as the "production firmware" — but the discrepancy CLAUDE.md describes (env builds the calibration file) no longer exists.** CLAUDE.md's sentence describing the *current* build_src_filter is stale and should be updated/removed by a human — it now reads as if there's still a mismatch between the built file and the production file, when in fact they're the same file post-7a69aca.

## 2. Firmware payload version and field order

`src/cubecell_battery_main.cpp`:

```cpp
uint8_t payloadVersion = 5;
```

`prepareTxFrame()` (line ~148) packs fields in this order:

1. Version byte (`payloadVersion` = 5)
2. `windDirectionTracker.pack(...)` — wind direction
3. `windSpeedTracker.pack(...)` — wind speed (pulses total/min/max)
4. `bmp280Tempstats.pack(...)` — BMP280 temperature (avg/min/max, x100 scale, 2 bytes each)
5. `bmp280Pressurestats.pack(...)` — BMP280 pressure (avg/min/max, x100 scale, 4 bytes each)
6. `lightIntensityStats.pack(...)` — light intensity / solar radiation (avg/min/max, **x10 scale** in v5, 2 bytes each)
7. `shtTempstats.pack(...)` — SHT sensor temperature (avg/min/max, x100 scale, 2 bytes each)
8. `shtHumidityStats.pack(...)` — SHT sensor humidity (avg/min/max, x100 scale, 2 bytes each)
9. `rainTracker.pack(...)` — rain pulse count
10. Battery voltage (2 bytes, raw mV, no scaling)

**Payload version = 5** is what the currently-built firmware sends. Version 5's only difference from version 4 is the light-intensity scale factor (x10 instead of x100, to support a higher max range ~6553 W/m²).

## 3. Payload formatter (`src/payload_formatter`) — version 5 decode output field names

`decodeUplink()` switches on `payloadVersion`; the currently-relevant branch is `case 5`. It produces this `data` object (all nested under `case 5`'s `data = {...}`):

```js
data = {
  version: 5,
  wind: {
    direction_deg: <number>,
    pulses_total: <number>,
    pulses_min: <number>,
    pulses_max: <number>,
    speed_kmh: { avg: <number>, max: <number> }   // derived, NOT raw pulses
  },
  bmp_temperature: { avg, min, max },   // °C, BMP280 sensor
  pressure_pa:     { avg, min, max },   // hPa (despite the name pressure_pa, values are /100 → hPa-ish, not raw Pa)
  light_solar:     { avg, min, max },   // W/m², v5 divides raw uint16 by 10.0
  sht_temperature: { avg, min, max },   // °C, SHT sensor (separate from bmp_temperature)
  sht_humidity:    { avg, min, max },   // %RH
  rain_pulses: <number>,
  rain_mm: <number>,                    // rain_pulses * 0.2
  battery_v: <number>                   // battery mV / 1000
}
```

**Key fields for the widget:**
- **Temperature**: there are TWO temperature fields — `bmp_temperature.{avg,min,max}` (BMP280) and `sht_temperature.{avg,min,max}` (SHT sensor). There is no single unambiguous "temperature" field. A human/product decision is needed on which sensor's temperature the widget should show (or average both). This document does not resolve that choice — flagging it explicitly.
- **Light intensity**: `light_solar.avg` / `.min` / `.max` (W/m², solar radiation, not raw lux).
- **Wind speed**: `wind.speed_kmh.avg` / `wind.speed_kmh.max` — these are the pre-converted km/h values (computed by the payload formatter from `pulses_total`/`pulses_max` using `PULSE_PER_SEC_TO_KMH = 3.61`). Do NOT use `wind.pulses_total`/`pulses_max` directly for a widget — those are raw pulse counts, not km/h.

## 4. Google Apps Script `doPost(e)` — Sheet1 column mapping

`src/google_appscript`'s `doPost(e)` builds `rowData` as an array and calls `sheet.appendRow(rowData)` on `Sheet1`. There is **no header-row-setup code in the script** — headers (if any exist in the sheet) are set up manually and not visible in this repo. The column mapping below is inferred purely from `rowData`'s array order (Sheets columns are 1-indexed, A=1):

| Col | Index (0-based) | Value | Source field |
|-----|------|-------|--------------|
| A | 0 | `timeStamp` | `payload.received_at` |
| B | 1 | `deviceId` | `end_device_ids.device_id` |
| C | 2 | `rssi` | `rx_metadata[0].rssi` |
| D | 3 | `snr` | `rx_metadata[0].snr` |
| E | 4 | `rawPayload` | `frm_payload` (base64) |
| F | 5 | `decoded.version` | payload version (5) |
| G | 6 | `bmp_temperature.avg` | **BMP280 temp avg** |
| H | 7 | `bmp_temperature.max` | BMP280 temp max |
| I | 8 | `bmp_temperature.min` | BMP280 temp min |
| J | 9 | `sht_temperature.avg` | **SHT temp avg** |
| K | 10 | `sht_temperature.max` | SHT temp max |
| L | 11 | `sht_temperature.min` | SHT temp min |
| M | 12 | `sht_humidity.avg` | SHT humidity avg |
| N | 13 | `sht_humidity.max` | SHT humidity max |
| O | 14 | `sht_humidity.min` | SHT humidity min |
| P | 15 | `pressure_pa.avg` | pressure avg |
| Q | 16 | `pressure_pa.max` | pressure max |
| R | 17 | `pressure_pa.min` | pressure min |
| S | 18 | `light_solar.avg` | **light intensity avg (W/m²)** |
| T | 19 | `light_solar.max` | light intensity max |
| U | 20 | `light_solar.min` | light intensity min |
| V | 21 | `wind.direction_deg` | wind direction |
| W | 22 | `wind.pulses_max` | wind raw pulses max |
| X | 23 | `wind.pulses_min` | wind raw pulses min |
| Y | 24 | `wind.pulses_total` | wind raw pulses total |
| Z | 25 | `decoded.rain_pulses` | rain pulses |
| AA | 26 | `decoded.battery_v` | battery voltage (V) |
| AB | 27 | `wind.speed_kmh.avg` | **wind speed avg (km/h)** — appended later, not contiguous with other wind cols |
| AC | 28 | `wind.speed_kmh.max` | wind speed max (km/h) |
| AD | 29 | `decoded.rain_mm` | rain in mm |

Note the comment in the script: `// 14. Wind Speed (km/h) - new fields appended at the end, existing columns untouched` — confirms columns AB/AC were added later and are NOT adjacent to the other wind columns (V–Y). Any new `doGet` reading by column letter must account for this.

## 5. Recommended columns for the widget

Given the ticket's ask (temperature, light intensity, wind speed) and the "no payload-version handling" constraint:

- **Wind speed**: read column **AB** (`wind.speed_kmh.avg`), the already-converted km/h value. (Column AC for max/gust if the widget wants a gust reading.)
- **Light intensity**: read column **S** (`light_solar.avg`), W/m² solar radiation.
- **Temperature**: **ambiguous — needs a decision.** Two candidate columns exist:
  - Column **G** (`bmp_temperature.avg`, BMP280)
  - Column **J** (`sht_temperature.avg`, SHT sensor)

  Recommend picking one canonical source (SHT sensors are typically more accurate for ambient air temp vs. BMP280, which can read warm from self-heating/enclosure effects) — but this is a product/hardware decision, not something resolvable from code alone. Flagging for a human to decide before `doGet` is implemented.

## 6. No explicit Sheet1 header row found

No code in this repo sets up Sheet1's header row (no `setValues` on row 1, no header array). The column mapping above is derived solely from the `rowData` array order in `doPost`. If `doGet` needs to read by header name rather than column letter/index, someone should check the live Google Sheet directly to confirm actual header text (not discoverable from the codebase).

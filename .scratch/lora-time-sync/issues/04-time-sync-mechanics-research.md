Type: research
Status: resolved
Context: research/time-sync-mechanics branch (see below)

## Question

On the CubeCell ASR6501 (`LoRaWan_APP` / LoRaMac-node stack this project builds against, platform `https://github.com/HelTecAutomation/heltec-cubecell.git`), when an `MLME_DEVICE_TIME` request is answered by the network (`DeviceTimeAns` MAC command):

1. Does the stack invoke the user-defined `dev_time_updated()` callback automatically (as assumed by every archived prototype: `cubecell_timing_test_stripped_calibration.cpp`, `cubecell_timing_test.cpp`, `heltec_esp_send_lorrawan_correct_drif.cpp`)?
2. Does `TimerGetSysTime()` immediately reflect the network-corrected epoch after that callback fires, or does the app need to read/apply the correction itself (e.g. via `TimerSetSysTime()`)?
3. Does the corrected epoch (and the underlying timer it's built on) survive the `LoRaWAN.sleep()` / low-power cycle the device enters between `DEVICE_STATE_CYCLE` and the next wake — or does it reset/drift-reset across that sleep on the ASR6501 specifically (unlike ESP32 boards, which have `RTC_DATA_ATTR`-backed deep sleep retention that CubeCell's code explicitly lacks per `cubecell_battery_main.cpp`'s comment)?

Repo's local package cache does not have the CubeCell core downloaded (`.pio/libdeps` only has the ESP32 Heltec board's `LoRaWan_APP.cpp`, not ASR6501's) — this needs either fetching the CubeCell core source (from the platform repo/PlatformIO package cache) or authoritative HelTecAutomation/Heltec-CubeCell documentation.

This blocks [[06-integration-plan-two-tier-loop]] — if the epoch doesn't survive sleep, the whole "resync every ~week and coast on the local timer between" premise breaks and the design needs rethinking (e.g. resync every wake instead).

## Answer

Full research with source citations: [`docs/research/cubecell-device-time-sync.md`](../../../docs/research/cubecell-device-time-sync.md). Read directly from the installed `framework-arduinocubecell` 1.6.0 package (mirrors upstream `HelTecAutomation/CubeCell-Arduino`, exactly what this repo's `heltec-cubecell` platform pulls in).

1. **Yes, automatically.** `dev_time_updated()` is declared `extern "C"` in `LoRaWan_APP.h` and given a weak default definition in `LoRaWan_APP.cpp`. The stack's `MlmeConfirm()` calls it directly in the `MLME_DEVICE_TIME` / `LORAMAC_EVENT_INFO_STATUS_OK` case. Any project-defined `dev_time_updated()` (like the archived prototypes') overrides the weak symbol at link time — no manual registration needed.

2. **Already corrected — the app doesn't need to call `TimerSetSysTime()` itself.** `LoRaMac.c`'s `SRV_MAC_DEVICE_TIME_ANS` MAC-command handler parses `DeviceTimeAns`, computes the corrected epoch, and calls `TimerSetSysTime()` *before* `MlmeConfirm()`/`dev_time_updated()` fire for that RX cycle. `TimerGetSysTime()` (ASR650x `timeServer.c`) is just `RtcGetTimerValue()` (a free-running hw ms counter) + a RAM offset (`g_systime_ref`) that `TimerSetSysTime()` maintains — so it's live and correct immediately.

3. **Yes, survives `LoRaWAN.sleep()`.** `LoRaWAN.sleep()` → `TimerLowPowerHandler()` → `CySysPmDeepSleep()`, which is PSoC4 **Deep Sleep** (WFI-based, explicitly not Hibernate — SRAM stays fully powered, only clock-gated). Ordinary globals like `g_systime_ref` survive untouched; no `RTC_DATA_ATTR`-equivalent is needed because nothing is powered off (unlike ESP32 deep sleep). The hardware counter backing `TimerGetSysTime()` (Timer 2, `CySysTimerGetCount(2)`) is clocked by the always-on ILO oscillator — the same clock source that drives the WDT wake timer — so it necessarily keeps ticking through sleep too. Only a full reset/power-cycle clears the RAM offset and forces a resync from scratch, which issue 03 already treats as acceptable.

**Conclusion for the broader effort:** the "resync ~weekly, coast on local timer between wakes" premise holds up. `LoRaWAN.sleep()` between uplinks does not require re-deriving time on every wake.

# CubeCell ASR6501: MLME_DEVICE_TIME sync mechanics

Research capture for `.scratch/lora-time-sync/issues/04-time-sync-mechanics-research.md`.

## Source

Upstream core: [`HelTecAutomation/CubeCell-Arduino`](https://github.com/HelTecAutomation/CubeCell-Arduino) — this is exactly what `platformio.ini`'s `platform = https://github.com/HelTecAutomation/heltec-cubecell.git` pulls in as the `framework-arduinocubecell` PlatformIO package (confirmed via the installed package's own `package.json`: `"repository": {"url": "https://github.com/HelTecAutomation/CubeCell-Arduino"}`, version `1.6.0`).

All findings below are read directly from the locally-installed package at:
`C:\Users\halewijnvanden\.platformio\packages\framework-arduinocubecell\` (framework-arduinocubecell 1.6.0, the exact version this repo's `CubeCell-AB01` PlatformIO env builds against). File paths quoted are relative to that root, which mirrors the upstream `CubeCell-Arduino` repo layout 1:1 (e.g. `libraries/LoRa/src/LoRaWan_APP.cpp` ⇄ same path upstream).

## Q1: Is `dev_time_updated()` invoked automatically?

**Yes.** It is declared as a weak C symbol and given a default (overridable) implementation in the ASR650x Arduino core itself:

- Declaration: `libraries/LoRa/src/LoRaWan_APP.h:82` — `extern "C" void dev_time_updated( void );`
- Default weak definition: `libraries/LoRa/src/LoRaWan_APP.cpp:371-374`:
  ```cpp
  void __attribute__((weak)) dev_time_updated()
  {
      printf("device time updated\r\n");
  }
  ```
- It is called from the stack's `MlmeConfirm()` handler, in the `MLME_DEVICE_TIME` case, on successful status (`libraries/LoRa/src/LoRaWan_APP.cpp:429-436`):
  ```cpp
  case MLME_DEVICE_TIME:
  {
      if( mlmeConfirm->Status == LORAMAC_EVENT_INFO_STATUS_OK )
      {
          dev_time_updated();
      }
      break;
  }
  ```

Any `.cpp` in this repo that defines its own `void dev_time_updated()` (e.g. `src/archive/cubecell_timing_test_stripped_calibration.cpp:33`) transparently overrides the weak default via normal linker weak-symbol resolution — no explicit registration/callback-pointer wiring is needed anywhere in application code. This confirms the assumption baked into every archived prototype.

`MlmeConfirm()` itself fires from the stack's internal processing loop after an uplink completes and a `DeviceTimeAns` MAC command was present in the downlink — triggered by the app having queued `MLME_DEVICE_TIME` via `LoRaMacMlmeRequest()` before the uplink (as the prototypes do).

## Q2: Does `TimerGetSysTime()` immediately reflect the corrected epoch, or must the app apply the correction itself?

**It's already applied by the time `dev_time_updated()` fires — the app does not need to call `TimerSetSysTime()` itself.**

The actual `DeviceTimeAns` MAC-command parsing and system-time correction happen inside the LoRaMac-node MAC layer, *before* the `MLME_DEVICE_TIME` confirm (and hence `dev_time_updated()`) is dispatched. In `libraries/LoraWan104/src/LoRaMac/mac/LoRaMac.c:2190-2221` (the `SRV_MAC_DEVICE_TIME_ANS` case of the downlink MAC-command parser):

```c
// Convert the fractional second received in ms
gpsEpochTime.SubSeconds = ...
sysTime = gpsEpochTime;
sysTime.Seconds += UNIX_GPS_EPOCH_OFFSET;

// Compensate time difference between Tx Done time and now
sysTimeCurrent = TimerGetSysTime( );
sysTime = TimerAddSysTime( sysTimeCurrent, TimerSubSysTime( sysTime, MacCtx.LastTxSysTime ) );

// Apply the new system time.
TimerSetSysTime( sysTime );
LoRaMacClassBDeviceTimeAns( );
MacCtx.McpsIndication.DeviceTimeAnsReceived = true;
```

This runs as part of downlink MAC-command processing (`ProcessMacCommands`), which completes before the higher-level `MlmeConfirm()` (and its `dev_time_updated()` call) runs for that same RX cycle. So by the time the app's `dev_time_updated()` callback fires, `TimerGetSysTime()` already returns the network-corrected Unix epoch (GPS epoch converted via `UNIX_GPS_EPOCH_OFFSET`, plus a compensation term for elapsed time since the original Tx). No app-level `TimerSetSysTime()` call is required or expected — calling it manually from application code would in fact be redundant/wrong here.

`TimerGetSysTime()` / `TimerSetSysTime()` are implemented in the ASR650x-specific system layer, not LoRaMac-node's generic `SysTime.c` — `cores/asr650x/lora/system/timeServer.c:414-431`:

```c
void TimerSetSysTime( TimerSysTime_t sysTime )
{
    TimerTime_t cur_time = RtcGetTimerValue( );
    TimerTime_t set_time = (TimerTime_t)sysTime.Seconds*1000 + sysTime.SubSeconds;
    g_systime_ref = set_time - cur_time;
}

TimerSysTime_t TimerGetSysTime( void )
{
    TimerSysTime_t sysTime = { 0 };
    TimerTime_t curTime = TimerGetCurrentTime();   // = RtcGetTimerValue() + g_systime_ref
    sysTime.Seconds = (uint32_t)(curTime/1000);
    ...
}
```

i.e. "system time" is just a free-running hardware millisecond counter (`RtcGetTimerValue()`) plus a RAM offset (`g_systime_ref`) that `TimerSetSysTime()` recalculates on each correction. `TimerGetSysTime()` always reflects `counter + last-known-offset`, so once the offset is set it's live immediately and continuously (no re-read/re-apply step needed elsewhere).

## Q3: Does the corrected time — and the timer peripheral backing it — survive `LoRaWAN.sleep()`?

**Yes, both the RAM offset and the underlying hardware counter survive the low-power cycle used between uplinks.** This is a different (milder) sleep mode than ESP32 deep sleep, which is why CubeCell doesn't need an `RTC_DATA_ATTR` equivalent.

Call chain: `LoRaWAN.sleep()` → `libraries/LoRa/src/LoRaWan_APP.cpp:681-684` → `TimerLowPowerHandler()` → `cores/asr650x/lora/system/low_power.c:58-84`:

```c
void TimerLowPowerHandler( void )
{
    if( HasLoopedThroughMain < 5 ) { HasLoopedThroughMain++; }
    else { HasLoopedThroughMain = 0; lowPowerHandler( ); }
}

void lowPowerHandler( void )
{
    if ( wakeByUart == false)
    {
        ...
        CySysPmDeepSleep();
        systime = (uint32_t)RtcGetTimerValue();
        ...
    }
}
```

`CySysPmDeepSleep()` is a **PSoC4 "Deep Sleep"** power mode (`cores/asr650x/projects/PSoC4/cyPm.c:64-…`), not the Cypress "Hibernate" mode — the code explicitly clears the hibernate-select bit before sleeping (`CY_PM_PWR_CONTROL_REG &= ~CY_PM_PWR_CONTROL_HIBERNATE`) and puts the CPU into a `WFI` (wait-for-interrupt) low-power wait state via `SLEEPDEEP` + `WFI`. Per Cypress's own doc comment on the function: "The wakeup occurs when an interrupt is received from a DeepSleep or Hibernate peripheral." Unlike Hibernate (or ESP32's true deep sleep, which powers down the CPU/RAM domain and needs `RTC_DATA_ATTR`-tagged variables placed in a surviving RTC memory island to persist anything), PSoC4 Deep Sleep **retains full SRAM contents** — it just clock-gates the CPU and non-essential peripherals. Ordinary C globals (like `g_systime_ref` in `timeServer.c`) are therefore untouched across a `LoRaWAN.sleep()` cycle; nothing needs the special-attribute treatment ESP32 requires.

The counter itself (`RtcGetTimerValue()`, reading `CySysTimerGetCount(2)` — hardware Timer/Counter 2) also keeps ticking through the sleep. This is architecturally required for the mechanism to work at all: Timer 2 (and the WDT that actually wakes the chip on schedule) are clocked from the **ILO** (Internal Low-speed Oscillator), the always-on low-power oscillator (`cores/asr650x/projects/PSoC4/CyLFClk.c`) that Cypress's own Deep Sleep documentation confirms keeps running specifically so DeepSleep/WDT peripherals can still generate the wake interrupt. Since the same free-running counter both (a) drives the wake-up timer and (b) backs `TimerGetSysTime()`'s millisecond base, it cannot stop during sleep without breaking the device's own wake scheduling — so no drift-reset or re-derivation is needed on wake; `TimerGetSysTime()` continues to return a correct, continuously-advancing Unix time across any number of `LoRaWAN.sleep()` cycles.

**Caveat — this only covers the sleep-between-uplinks case, not a full reset/power-cycle.** A hard reset, brown-out, or manual reboot does clear SRAM (`g_systime_ref` resets to 0, `RTC_counts`/`RTC_last_count` reset), losing the epoch and forcing a resync from scratch — consistent with this project's existing decision in `.scratch/lora-time-sync/issues/03-persistence.md` ("state loss on reboot is acceptable, reboot just forces an immediate resync"). The `cubecell_battery_main.cpp` comment "Removed RTC_DATA_ATTR for CubeCell" reflects that CubeCell's Deep Sleep doesn't need that attribute at all (SRAM already persists) — not that CubeCell lacks retention. It is *not* evidence that state is lost across `LoRaWAN.sleep()`.

## Bottom line for the "resync weekly, coast on local timer between" design

Holds up. `TimerGetSysTime()`'s epoch is derived from a hardware counter that keeps running (and a RAM offset that keeps its value) through every `LoRaWAN.sleep()` cycle between uplinks, so the device does not need to re-sync on every wake — only reset/power-loss forces a fresh `MLME_DEVICE_TIME` round-trip, which issue 03 already treats as acceptable.

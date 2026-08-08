# LoRaWAN Time-Sync Send Scheduling

## Destination

An implementation-ready design for `cubecell_battery_main.cpp` (production firmware) that: (a) aligns 5-min uplinks to fixed wall-clock marks, correcting the drift each wake introduces via a "how long till next mark" loop, and (b) refreshes the device's notion of true time only ~weekly via a LoRaWAN `MLME_DEVICE_TIME` request piggybacked on a regular uplink — not every send. Map is done when the integration plan is precise enough to code directly, no decisions left open.

## Notes

- Domain: CubeCell (ASR6501) LoRaWAN firmware, `LoRaWan_APP` / LoRaMac-node stack. See `CLAUDE.md` for repo layout (`src/`, `src/archive/`, active build target).
- Prior art already exists in `src/archive/`: `cubecell_timing_test_stripped_calibration.cpp` (closest match — wall-clock align + count-based resync), `cubecell_timing_test_stripped.cpp`, `cubecell_timing_test.cpp`, `heltec_esp_send_lorrawan_correct_drif.cpp`. Read these before re-deriving the pattern.
- Production sampling loop (`cubecell_battery_main.cpp`): 5s sample tick × 60 = one 5-min uplink. Any scheduling change must slot into this two-tier `DEVICE_STATE_SEND`/`DEVICE_STATE_CYCLE` structure, not replace it.
- Skills: use `/grilling` for remaining tickets; `/research` subagent already dispatched for the one research ticket.

## Decisions so far

- [Align sends to wall-clock marks](issues/01-align-mode.md) — absolute :00/:05/:10 UTC marks, not relative spacing.
- [Resync trigger is count-based](issues/02-resync-trigger.md) — tx-count threshold since last sync, not calendar days.
- [State loss on reboot is acceptable](issues/03-persistence.md) — no flash persistence for the resync counter; reboot just forces an immediate resync.
- [Time-sync mechanics confirmed](issues/04-time-sync-mechanics-research.md) — `dev_time_updated()` fires automatically (weak symbol) and `TimerGetSysTime()` is already network-corrected by then; the corrected epoch and its hw timer survive `LoRaWAN.sleep()` (PSoC4 Deep Sleep retains SRAM, unlike ESP32), so weekly-resync-and-coast holds up.

## Not yet specified

- Whether/how to surface time-sync health (last-sync tx count, current sync status) to the backend/dashboard for observability — deferred until the integration plan ([[06-integration-plan-two-tier-loop]]) exists and it's clear whether this needs a payload field.

## Out of scope

- Actual code changes to `cubecell_battery_main.cpp` — this map produces the plan; implementation happens after, in a normal coding session.
- Hardware-in-the-loop testing / flashing.
- Changes to `src/payload_formatter`, `src/google_appscript`, or the Streamlit dashboard — this effort is device-side scheduling only, no payload shape changes anticipated.
- Timezone/DST display concerns — network time is UTC unix epoch; any local-time display is already the dashboard's concern, untouched here.

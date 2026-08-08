Type: grilling
Status: open
Blocked by: 04, 05

## Question

`cubecell_battery_main.cpp` runs a two-tier loop the prototype never had to deal with: `DEVICE_STATE_SEND` fires every `measurementInterval_s` (5s) to take one sensor sample, and only uplinks once `sampleCount >= numSamples` (60 → every 5min). `DEVICE_STATE_CYCLE` currently always sets `txDutyCycleTime = measurementInterval_s * 1000` unconditionally.

Produce the precise integration plan:

1. Where does the wall-clock-align calculation (`Seconds % interval` → `secondsToWait`) get applied — only on the iteration where `sampleCount` just hit `numSamples` (i.e. right after an uplink), leaving the other 59 iterations on flat 5s ticks? Or does every tick need to re-check alignment?
2. Does cumulative 5s-tick drift across the 5-min sampling window matter (i.e. could the 60th sample/send fire noticeably early/late relative to the wall-clock mark even though each individual CYCLE call is "correct" for its own tick), and if so does the last tick before send need its own shortened/lengthened correction step?
3. Where does the `dev_time_updated()` callback, tx counter, and `MLME_DEVICE_TIME` request attachment slot into `DEVICE_STATE_SEND` — gated on the same condition as the uplink (`sampleCount >= numSamples`), since `LoRaMacMlmeRequest` piggybacks on an actual uplink and sampling ticks don't send anything?
4. Confirm final state-machine shape (pseudocode or diff-ready description) for `cubecell_battery_main.cpp`, informed by [[04-time-sync-mechanics-research]]'s findings and [[05-weekly-threshold-and-presync-duty-cycle]]'s threshold/pre-sync answers.

This ticket's answer is the destination: an implementation-ready plan. Actual code changes to `cubecell_battery_main.cpp` happen after, outside this map.

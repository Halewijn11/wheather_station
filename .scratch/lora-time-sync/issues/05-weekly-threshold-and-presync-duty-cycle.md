Type: grilling
Status: open

## Question

Given count-based resync ([[02-resync-trigger]]) at the production 5-min send interval:

1. Exact tx-count threshold to approximate "a week" (naively 2016 = 7d × 24h × 12/hr — confirm or adjust, e.g. round number, margin for missed/failed sends).
2. What duty cycle to run on *before* the first successful sync (device just booted/joined, clock not yet trustworthy)? The prototype (`cubecell_timing_test_stripped_calibration.cpp`) retries every 15s until synced. Production's sampling loop already ticks every 5s independently (60 samples × 5s = 5min) — decide whether pre-sync state reuses that existing cadence or needs its own.
3. What happens on a failed/unanswered `DeviceTimeAns` (no network response within the RX window) — does `forceSyncThisTurn` stay set and retry next send automatically (as prototype implies), or does it need an explicit backoff/retry-limit?

Type: grilling
Status: resolved

## Question

Does the resync tx-counter / last-sync state need to survive a power loss or reboot (flash-persisted), or is losing it on reboot acceptable?

## Answer

OK to lose on reboot. A reboot just forces an immediate resync on the next uplink (cheap, self-healing) — no flash/EEPROM writes, no wear. Consistent with production code's existing note that `RTC_DATA_ATTR` (ESP32-only) was removed for CubeCell; no persistent-across-reboot storage mechanism is being introduced by this effort.

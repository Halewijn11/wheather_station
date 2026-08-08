Type: grilling
Status: resolved

## Question

Should the ~weekly LoRaWAN MLME_DEVICE_TIME resync fire on a transmission count (N sends since last sync) or on elapsed calendar days?

## Answer

Count-based. Track tx count since last successful `dev_time_updated()` callback, resync at a threshold approximating a week at the 5-min send interval. Matches the existing prototype's 200-tx counter pattern. Calendar-based is circular — judging "a week" needs a clock that's already roughly right, which is the thing being corrected.

Exact threshold value deferred to [[05-weekly-threshold-and-presync-duty-cycle]].

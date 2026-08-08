Type: grilling
Status: resolved

## Question

Should uplinks land on absolute wall-clock marks (e.g. :00/:05/:10 UTC) or just keep ~5min spacing relative to the last send?

## Answer

Wall-clock marks. Matches the pattern already prototyped in `src/archive/cubecell_timing_test_stripped_calibration.cpp` (align to `Seconds % interval`). Needed for predictable, cross-device-comparable timestamps downstream.

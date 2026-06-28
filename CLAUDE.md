# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A LoRaWAN weather station using a Heltec CubeCell (ASR6501) that transmits sensor data to The Things Network (TTN), which webhooks into Google Sheets via a Google Apps Script, visualized through a Streamlit dashboard.

**Data flow:** CubeCell firmware → LoRaWAN (EU868) → TTN → TTN Webhook → Google Apps Script → Google Sheets → Streamlit app

The active source file is controlled per environment via `build_src_filter` in `platformio.ini`. The `CubeCell-AB01` env currently builds `cubecell_timing_test_stripped_calibration.cpp`, but the production firmware is `src/cubecell_battery_main.cpp`.

## Communication style
- Use caveman mode (full) for all internal thinking, code comments, debugging and reasoning.
- For output that the user reads (ADRs, PRDs, glossary, distilled decisionshandoff docs): Be extremely concise. Sacrifice grammar for the sake of concision.

## Run Streamlit App

```bash
cd streamlit_app
streamlit run streamlit_app.py
```

## Architecture

### Payload Decoder (`src/payload_formatter`)

JavaScript function deployed in TTN as an uplink formatter. Decodes the binary payload into named fields using the same field order as the firmware's `prepareTxFrame()`. Supports versions 1–5 via a switch statement. Wind speed conversion constants (`WIND_SAMPLE_INTERVAL_S`, `WIND_SAMPLES_PER_REPORT`, `PULSE_PER_SEC_TO_KMH`) must match the firmware.

### TTN Webhook Handler (`src/google_appscript`)

Google Apps Script `doPost(e)` deployed as a web app. Receives TTN webhook POST, extracts decoded payload fields, and appends a row to Google Sheet (Sheet1). The Sheet ID is stored in Script Properties under key `SHEET_ID`.

### Streamlit Dashboard (`streamlit_app/`)

Multi-page app: `dashboard.py` (main charts), `status.py` (device health), `info.py`. All shared utilities are in `utils.py`.

`utils.get_data()` fetches from a public Google Sheets CSV export URL (hardcoded) and caches for 3 minutes. `utils.get_forecast_df()` fetches a separate forecast sheet (5-minute cache). `tidy_google_sheet_df()` adds derived columns (`seconds_since_now`, `battery_percentage`, time deltas).

`TimeSeriesDashboardItem` is the primary chart component — it renders a metric card + Altair line chart with hover interactivity and optional forecast overlay.

## Secrets

LoRaWAN credentials (DevEUI, AppEUI, AppKey, NwkSKey, AppSKey, DevAddr) live in `src/secrets.h`, which is not gitignored. Do not commit real credentials to this file.

## Repository Conventions

- `claude_decisions/` — handoff documents between Claude sessions
- `claude_session/` — raw conversation logs
- `docs/` — ADRs, PRDs, design documents
- `src/` contains many experimental `.cpp` files from hardware bring-up; only the files referenced by `build_src_filter` in `platformio.ini` are compiled

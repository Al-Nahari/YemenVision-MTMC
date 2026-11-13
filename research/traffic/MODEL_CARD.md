# Traffic Intelligence model card

## Measurements

- **Vehicle count:** distinct local track IDs observed/entering the configured zone in a time bin.
- **Traffic flow:** vehicle count divided by bin duration, normalized to vehicles/hour.
- **Directional/class flow:** the same aggregation partitioned by direction/class.
- **Occupancy:** occupied usable frames / usable frames; missing frames are excluded and reported separately.
- **Density/queue:** withheld unless camera geometry, scale and zone calibration support a physical estimate.
- **Travel time:** aggregate only across validated temporary associations; do not expose a vehicle-level history.

## Forecasting and anomalies

All evaluation uses chronological walk-forward splits. Moving average, exponential smoothing/ARIMA/SARIMA and boosted/deep models may be compared only with features available at prediction time. MAPE omits zero actuals and is reported alongside WAPE/sMAPE. Traffic anomalies and system-quality anomalies are separate outputs.

## Status

No traffic event ledger, camera calibration, ground truth, or historical time series exists in this workspace. No operational traffic measurement or future forecast accuracy is claimed.

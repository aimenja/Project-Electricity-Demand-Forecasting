# PowerPlus Dashboard

Web dashboard for PowerPlus — the "final application/dashboard" stage of this project.

A FastAPI backend loads the trained XGBoost artifact from `processed_data/` and serves
1/7/30-day recursive forecasts to a browser front-end. The forecasting logic mirrors
`PowerPlus_User_Input_XGBoost_Weather_NoHouse_PowerBI_Final.ipynb`, so the dashboard
produces the same numbers as the notebook.

The forecast model, its metrics and the model dataset are read directly from
`processed_data/`, so re-exporting them from the notebooks updates the dashboard with no
code changes here. Only the companion profile model below is trained and stored by the
dashboard itself.

## Running it

```bash
./run.sh                 # local only  -> http://127.0.0.1:8000
./run.sh --share         # public URL  -> https://<random>.serveousercontent.com
```

`--share` opens an [SSH tunnel via serveo.net](https://serveo.net) and prints a link that
works from any device. It needs nothing installed — just `ssh`, which macOS already has —
and no account.

```
  ============================================================
   PowerPlus dashboard is live — open this on any device:

     https://402842b41e296dbc-39-58-214-240.serveousercontent.com

   The URL changes every run.  Ctrl+C here takes it offline.
  ============================================================
```

Notes on sharing:

- **Why serveo and not cloudflared or ngrok.** This network throttles
  `api.trycloudflare.com` to ~30 seconds per request, which is longer than cloudflared's
  internal timeout, so Cloudflare quick tunnels never register here. ngrok needs an account
  and shows every visitor an interstitial page. Serveo tunnels over plain SSH on port 22,
  which is not throttled, and serves the dashboard directly with no interstitial.
- **The URL is different every run.** Set `POWERPLUS_SUBDOMAIN` to reserve a stable
  hostname, but note serveo only honours it once you have registered an SSH key with them:
  ```bash
  POWERPLUS_SUBDOMAIN=powerplus-hamna ./run.sh --share
  ```
- **The link has no password.** Anyone who has it can open the dashboard and read the
  dataset, so treat the URL itself as the secret and stop the tunnel when you are done.
- The public hostname embeds this machine's public IP address, which is normal for serveo
  but worth knowing before sharing the link widely.
- If the tunnel drops, the script retries three times and leaves the local server running
  either way.

## Setup

Everything below runs from this `dashboard/` directory.

```bash
cd dashboard
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python scripts/train_profile_model.py
```

The last step trains the companion profile model into `dashboard/data/`. Re-run it whenever
the notebooks export a new forecast model, so both models describe the same data.

This repository stores its datasets with Git LFS, so run `git lfs install` once and make
sure `processed_data/` holds real files rather than LFS pointer stubs before starting.

`scikit-learn` is pinned to 1.6.1 because the published `.pkl` was trained on 1.5.0 and
newer releases cannot unpickle its column transformer.

## What the dashboard does

- **Inputs** — pick a city and house from the dataset, set a forecast start date and a
  1/7/30-day horizon. Six household fields and ten appliance counts are pre-filled from the
  selected house's latest profile and can be edited freely for what-if scenarios. The
  remaining 66 model features fill in automatically.
- **Forecast** — daily predicted kWh, period total, daily average and peak day, charted
  against the house's recorded history.
- **Appliance what-if** — change in predicted daily kWh per additional appliance.
- **Models** — both models, their features and their test-set metrics.

## Two models, and why

| | Forecast model | Profile model |
|---|---|---|
| File | `processed_data/powerplus_xgboost_forecast_model.pkl` (from the notebooks) | `dashboard/data/powerplus_profile_model.pkl` (trained here) |
| Uses demand history | Yes (lag + rolling) | No |
| Test MAE / R² | 3.39 kWh / 0.851 | 6.49 kWh / 0.544 |
| Drives | Forecast chart and totals | Appliance what-if panel |

The forecasting model uses 104 of its 235 encoded features and takes 70% of its signal
from recent consumption, led by `lag_1_day_kwh` (29%) and `rolling_3_day_avg_kwh` (29%).
Appliance counts carry a combined importance of about 0.05 and weather about 0.11, so both
matter, but only a little next to yesterday's usage. Appliance counts are constant over time
within a house, so once the model can see recent consumption it has little reason to lean on
them. That makes it a good short-horizon forecaster but a weak tool for "what if I add an air
conditioner".

The 14 `*_weather` columns the notebook adds are a second, identical copy of weather columns
already in the model dataset: the merge against `daily_weather.csv` collides on column names
and pandas suffixes the duplicates. The two copies split the weather importance roughly in
half. The dashboard reproduces them by mirroring the originals rather than re-reading the
weather file.

`scripts/train_profile_model.py` therefore trains a companion model on the same data with the
lag/rolling features **and the house-identity columns** removed, forcing household and
appliance characteristics to carry the signal. Each panel states which model produced it.

## Known data limitations

These are properties of the upstream dataset, not of the dashboard. The dashboard displays
the models' true output and does not rescale anything.

1. **Future weather is a seasonal proxy**, averaged from historical weather for the selected
   city. It is not a real forecast, so longer horizons carry more uncertainty.
2. **The appliance what-if is approximate.** The profile model has to predict a house's
   usage without any history, and with only 59 houses whose characteristics never change
   there is little to learn from: test R² is 0.54 (MAE 6.5 kWh/day) against 0.93 on the
   training data. Treat its per-appliance figures as directional, not as metered values.
3. **`Islamabad / House#41`** ends with 12 consecutive days of exactly 0 kWh, so its
   forecast starts low. The dashboard warns when you select it.

Earlier versions of this dashboard warned that 53 of 59 houses averaged under 1 kWh/day.
That was a bug in `PowerPlus_Data_Processing_Feature_Engineering.ipynb`, not a property of
the data: midnight readings are stored as bare dates and every other minute with a time,
and `pd.to_datetime` inferred the format from the first row, so in 63 of 69 files it
silently dropped every reading except midnight. Parsing with `format="mixed"` keeps all
1,440 readings a day, and every house now averages between 1.3 and 49 kWh/day.

## Layout

```
dashboard/backend/model.py   forecasting engine (mirrors the notebook)
dashboard/backend/app.py     FastAPI routes
dashboard/frontend/          dashboard UI (no build step, no external dependencies)
dashboard/scripts/           profile-model training
dashboard/data/              the companion profile model only
processed_data/              forecast model, metrics and dataset (shared with the notebooks)
```

## API

| Route | Purpose |
|---|---|
| `GET /api/meta` | cities, houses, default selection, both models' info |
| `GET /api/house/{city}/{house}` | input defaults, recent history, data-quality flags |
| `POST /api/forecast` | daily forecast, totals, appliance sensitivity |

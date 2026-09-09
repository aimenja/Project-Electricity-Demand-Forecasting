"""PowerPlus forecasting engine.

Replicates the logic of PowerPlus_User_Input_XGBoost_Weather_NoHouse_PowerBI_Final.ipynb
so the dashboard produces the same numbers as the notebook.

The forecast model and dataset are read from the repository's processed_data/ directory,
so the dashboard always uses whatever artifact the notebooks last exported. Only the
companion profile model, which this dashboard trains itself, lives under dashboard/data/.
"""

from __future__ import annotations

import json
import warnings
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

DASHBOARD_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = DASHBOARD_DIR / "data"
PROCESSED_DIR = DASHBOARD_DIR.parent / "processed_data"

MODEL_PKL = PROCESSED_DIR / "powerplus_xgboost_forecast_model.pkl"
MODEL_DATA = PROCESSED_DIR / "powerplus_model_data.csv"
METRICS_CSV = PROCESSED_DIR / "powerplus_xgboost_model_metrics.csv"
PROFILE_PKL = DATA_DIR / "powerplus_profile_model.pkl"
PROFILE_METRICS = DATA_DIR / "powerplus_profile_model_metrics.json"

WEATHER_COLUMNS = [
    "temperature_mean", "humidity_mean", "dew_mean", "wind_speed_mean",
    "wind_direction_mean", "pressure_mean", "solar_radiation_mean",
    "temperature_max", "humidity_max", "wind_speed_max", "solar_radiation_max",
    "uv_index_max", "precipitation_sum", "solar_energy_sum",
]

USER_INPUT_FEATURE_LABELS = [
    "No. of people (Temp+Perm)", "Covered Area", "No. of rooms", "house_age",
    "Ceiling Type", "Roof Type",
    "Air Conditioners", "Air Coolers", "Refrigerators", "Washing Machines",
    "Celling Fans", "Ceiling Fans", "Water Pumps", "Electric heaters",
    "Electric Heaters", "Electric Cooker", "Geysers", "LED Bulbs",
]

APPLIANCE_KEYWORDS = [
    "aircondition", "aircool", "refriger", "washingmachine", "ledbulb",
    "tubel", "fan", "waterdispenser", "waterpump", "electriccooker",
    "electricheater", "electriciron", "sewingmachine", "microwave",
    "geyser", "ups", "electronicdevice",
]

PLAUSIBLE_DAILY_KWH = 1.0

INTEGER_HINTS = [
    "numberof", "noof", "people", "residents", "floors", "rooms",
    "washrooms", "stores", "children", "adults", "seniors",
]


def norm_name(x: object) -> str:
    return "".join(ch.lower() for ch in str(x) if ch.isalnum())


def season_from_month(month: int) -> str:
    if month in (12, 1, 2):
        return "Winter"
    if month in (3, 4, 5):
        return "Spring"
    if month in (6, 7, 8):
        return "Summer"
    return "Autumn"


class PowerPlusEngine:
    def __init__(self) -> None:
        artifact = joblib.load(MODEL_PKL)
        self.pipeline = artifact["pipeline"]
        self.feature_columns = list(artifact["feature_columns"])
        self.numeric_features = list(artifact.get("numeric_features", []))
        self.categorical_features = list(artifact.get("categorical_features", []))
        self.target = artifact.get("target", "electricity_kwh")
        self.date_col = artifact.get("date_column", "date")
        self.city_col = artifact.get("city_column", "city")
        self.house_col = artifact.get("house_column", "house")
        self.best_parameters = artifact.get("best_parameters", {})
        self.train_end_date = str(artifact.get("train_end_date", ""))

        df = pd.read_csv(MODEL_DATA)
        df[self.date_col] = pd.to_datetime(df[self.date_col])
        self.df = df.sort_values(self.date_col).reset_index(drop=True)

        self.lag_map = {
            lag: f"lag_{lag}_day_kwh"
            for lag in (1, 2, 3, 7, 14, 30)
            if f"lag_{lag}_day_kwh" in self.feature_columns
        }
        self.rolling_map = {
            w: f"rolling_{w}_day_avg_kwh"
            for w in (3, 7, 14, 30)
            if f"rolling_{w}_day_avg_kwh" in self.feature_columns
        }

        feature_norm = {norm_name(c): c for c in self.feature_columns}
        self.user_features: list[str] = []
        for label in USER_INPUT_FEATURE_LABELS:
            col = feature_norm.get(norm_name(label))
            if col and col not in self.user_features:
                self.user_features.append(col)

        self.all_appliance_columns = [
            c for c in self.feature_columns
            if any(k in norm_name(c) for k in APPLIANCE_KEYWORDS)
        ]
        self.appliance_columns = [
            c for c in self.user_features if c in self.all_appliance_columns
        ]
        self.household_columns = [
            c for c in self.user_features if c not in self.all_appliance_columns
        ]

        self.build_year_col = next(
            (c for c in self.feature_columns
             if norm_name(c) in {"buildyearofhouse", "buildyear"}),
            None,
        )

        # The Weather_NoHouse notebook merges daily_weather.csv onto the model data
        # keyed on (city, date). Both frames already carry the same weather column
        # names, so pandas suffixes the merged copies with "_weather" and the model
        # ends up with each weather reading twice, identically. Mirroring the columns
        # we already have reproduces that exactly, with no second file to read.
        self.weather_aliases = {
            f"{c}_weather": c
            for c in WEATHER_COLUMNS
            if f"{c}_weather" in self.feature_columns and c in self.df.columns
        }
        for alias, base in self.weather_aliases.items():
            self.df[alias] = self.df[base]
        self.weather_columns = WEATHER_COLUMNS + list(self.weather_aliases)

        self._weather_by_doy = self._precompute_weather()
        self._weather_median = {
            c: float(pd.to_numeric(self.df[c], errors="coerce").median())
            for c in self.weather_columns if c in self.df.columns
        }
        self.metrics = self._load_metrics()
        self.profile_model = self._load_profile_model()

    # ------------------------------------------------------------------ setup

    def _precompute_weather(self) -> dict:
        cols = [c for c in self.weather_columns
                if c in self.feature_columns and c in self.df.columns]
        out: dict = {}
        work = self.df[[self.city_col, self.date_col] + cols].copy()
        work["_doy"] = work[self.date_col].dt.dayofyear
        work["_month"] = work[self.date_col].dt.month
        for city, g in work.groupby(work[self.city_col].astype(str)):
            out[city.casefold()] = {
                "doy": g.groupby("_doy")[cols].mean(),
                "month": g.groupby("_month")[cols].mean(),
            }
        self._weather_cols = cols
        return out

    def _load_profile_model(self) -> dict | None:
        """The appliance-aware companion model. See scripts/train_profile_model.py."""
        if not PROFILE_PKL.exists():
            return None
        artifact = joblib.load(PROFILE_PKL)
        if PROFILE_METRICS.exists():
            artifact["metrics"] = json.loads(PROFILE_METRICS.read_text())
        return artifact

    def _load_metrics(self) -> list[dict]:
        if not METRICS_CSV.exists():
            return []
        m = pd.read_csv(METRICS_CSV)
        return m.round(4).to_dict(orient="records")

    # ------------------------------------------------------------- accessors

    def cities(self) -> list[str]:
        return sorted(self.df[self.city_col].dropna().astype(str).unique(),
                      key=str.lower)

    def houses(self, city: str) -> list[str]:
        mask = self.df[self.city_col].astype(str).str.casefold() == city.casefold()
        return sorted(self.df.loc[mask, self.house_col].dropna().astype(str).unique(),
                      key=str.lower)

    def allowed_values(self, label: str) -> list[str]:
        if label in self.df.columns:
            return sorted(self.df[label].dropna().astype(str).unique(), key=str.lower)
        return []

    def house_history(self, city: str, house: str) -> pd.DataFrame:
        d = self.df
        mask = (
            (d[self.city_col].astype(str).str.casefold() == city.casefold())
            & (d[self.house_col].astype(str).str.casefold() == house.casefold())
        )
        h = d.loc[mask].sort_values(self.date_col)
        if h.empty:
            raise ValueError(f"No historical records for {house} in {city}.")
        return h

    def is_integer_field(self, label: str) -> bool:
        n = norm_name(label)
        return label in self.all_appliance_columns or any(k in n for k in INTEGER_HINTS)

    def field_spec(self, label: str, latest: pd.Series) -> dict:
        default = latest[label] if label in latest.index and pd.notna(latest[label]) else None
        if label in self.categorical_features:
            return {
                "name": label,
                "type": "categorical",
                "options": self.allowed_values(label),
                "default": None if default is None else str(default),
            }
        series = pd.to_numeric(self.df[label], errors="coerce").dropna() \
            if label in self.df.columns else pd.Series(dtype=float)
        return {
            "name": label,
            "type": "numeric",
            "integer": self.is_integer_field(label),
            "min": float(series.min()) if len(series) else 0.0,
            "max": float(series.max()) if len(series) else None,
            "default": None if default is None else float(default),
        }

    def data_quality(self, history: pd.DataFrame) -> dict:
        values = history[self.target].dropna()
        mean_daily = float(values.mean()) if len(values) else 0.0

        trailing_zeros = 0
        for v in values.values[::-1]:
            if v == 0:
                trailing_zeros += 1
            else:
                break

        flags = []
        if trailing_zeros >= 7:
            flags.append(
                f"The last {trailing_zeros} days of recorded consumption for this house "
                f"are exactly 0 kWh, so the forecast will be flat and near zero."
            )
        if mean_daily < PLAUSIBLE_DAILY_KWH:
            flags.append(
                f"This house averages {mean_daily:.4f} kWh/day in the dataset. A real "
                f"household uses roughly 10-40 kWh/day, which suggests a units problem in "
                f"the upstream kW-to-kWh conversion. Forecasts below are the model's true "
                f"output on this data and are not rescaled."
            )
        return {
            "mean_daily_kwh": round(mean_daily, 4),
            "trailing_zero_days": trailing_zeros,
            "implausible_scale": mean_daily < PLAUSIBLE_DAILY_KWH,
            "flags": flags,
        }

    def default_selection(self) -> dict:
        """Pick a house whose recorded consumption is in a physically plausible range."""
        means = self.df.groupby([self.city_col, self.house_col])[self.target].mean()
        plausible = means[means >= PLAUSIBLE_DAILY_KWH].sort_values(ascending=False)
        city, house = (plausible.index[0] if len(plausible) else means.idxmax())
        return {"city": str(city), "house": str(house)}

    def house_profile(self, city: str, house: str) -> dict:
        history = self.house_history(city, house)
        latest = history.iloc[-1]
        recent = history.tail(60)[[self.date_col, self.target]]
        return {
            "data_quality": self.data_quality(history),
            "city": city,
            "house": house,
            "latest_date": latest[self.date_col].date().isoformat(),
            "default_start_date": (latest[self.date_col] + pd.Timedelta(days=1)).date().isoformat(),
            "household_fields": [self.field_spec(c, latest) for c in self.household_columns],
            "appliance_fields": [self.field_spec(c, latest) for c in self.appliance_columns],
            "history": [
                {"date": r[self.date_col].date().isoformat(),
                 "kwh": round(float(r[self.target]), 4)}
                for _, r in recent.iterrows() if pd.notna(r[self.target])
            ],
            "auto_filled_feature_count": len(self.feature_columns) - len(self.user_features),
            "user_feature_count": len(self.user_features),
        }

    # ------------------------------------------------------------ forecasting

    def _weather_for(self, city: str, d: pd.Timestamp) -> dict:
        table = self._weather_by_doy.get(city.casefold())
        if table is None:
            return {}
        row = {}
        doy_tbl, month_tbl = table["doy"], table["month"]
        src = doy_tbl.loc[d.dayofyear] if d.dayofyear in doy_tbl.index else (
            month_tbl.loc[d.month] if d.month in month_tbl.index else None
        )
        for c in self._weather_cols:
            val = None if src is None else src[c]
            if val is None or pd.isna(val):
                val = self._weather_median.get(c)
            if val is not None and not pd.isna(val):
                row[c] = float(val)
        return row

    def _build_row(self, future_date, latest_profile, user_inputs, demand,
                   start_date, city, house) -> pd.DataFrame:
        row = latest_profile.to_dict()
        row[self.city_col] = city
        row[self.house_col] = house

        for c, v in user_inputs.items():
            if c in self.feature_columns and v is not None:
                row[c] = v

        calendar = {
            "year": future_date.year,
            "month": future_date.month,
            "day": future_date.day,
            "day_of_week": future_date.dayofweek,
            "week_of_year": int(future_date.isocalendar().week),
            "day_of_year": future_date.dayofyear,
            "is_weekend": int(future_date.dayofweek >= 5),
            "season": season_from_month(future_date.month),
        }
        for c, v in calendar.items():
            if c in self.feature_columns:
                row[c] = v

        if "total_appliance_count" in self.feature_columns:
            total = 0.0
            for c in self.all_appliance_columns:
                v = row.get(c, 0)
                try:
                    total += float(v) if pd.notna(v) else 0.0
                except (TypeError, ValueError):
                    pass
            row["total_appliance_count"] = total

        if "house_age" in self.feature_columns and self.build_year_col:
            by = row.get(self.build_year_col)
            if by is not None and pd.notna(by):
                row["house_age"] = max(0.0, future_date.year - float(by))

        row.update(self._weather_for(city, future_date))

        for lag, col in self.lag_map.items():
            target_date = future_date - pd.Timedelta(days=lag)
            match = demand[demand[self.date_col] == target_date]
            if not match.empty:
                row[col] = float(match[self.target].iloc[-1])
            else:
                row[col] = float(demand[self.target].iloc[-1])

        past = demand[demand[self.date_col] < future_date].sort_values(self.date_col)[self.target]
        for window, col in self.rolling_map.items():
            if len(past) >= window:
                row[col] = float(past.tail(window).mean())
            elif len(past):
                row[col] = float(past.mean())

        for c in self.numeric_features:
            if c in row:
                row[c] = pd.to_numeric(pd.Series([row[c]]), errors="coerce").iloc[0]
        for c in self.categorical_features:
            if c in row and row[c] is not None and not pd.isna(row[c]):
                row[c] = str(row[c])

        return pd.DataFrame([row])

    def forecast(self, city: str, house: str, start_date: date, horizon: int,
                 overrides: dict | None = None) -> list[dict]:
        history = self.house_history(city, house)
        latest_profile = history.iloc[-1]
        user_inputs = {self.city_col: city, self.house_col: house}
        user_inputs.update(overrides or {})

        start = pd.Timestamp(start_date)
        dates = pd.date_range(start, periods=horizon, freq="D")
        demand = history[[self.date_col, self.target]].dropna().copy()

        results = []
        for d in dates:
            X = self._build_row(d, latest_profile, user_inputs, demand, start, city, house)
            pred = max(0.0, float(self.pipeline.predict(X.reindex(columns=self.feature_columns))[0]))
            results.append({"date": d.date().isoformat(), "kwh": round(pred, 4)})
            demand = pd.concat(
                [demand, pd.DataFrame([{self.date_col: d, self.target: pred}])],
                ignore_index=True,
            )
        return results

    def profile_predict(self, city: str, house: str, day: date,
                        overrides: dict | None = None) -> float:
        """Predict daily kWh from household/appliance characteristics alone.

        Uses the companion profile model, which excludes demand-history features
        so appliance and household inputs actually influence the result.
        """
        if self.profile_model is None:
            raise ValueError("Profile model not available. Run scripts/train_profile_model.py.")

        history = self.house_history(city, house)
        latest_profile = history.iloc[-1]
        user_inputs = {self.city_col: city, self.house_col: house}
        user_inputs.update(overrides or {})
        demand = history[[self.date_col, self.target]].dropna()

        stamp = pd.Timestamp(day)
        row = self._build_row(stamp, latest_profile, user_inputs, demand, stamp, city, house)
        X = row.reindex(columns=self.profile_model["features"])
        pred = float(self.profile_model["pipeline"].predict(X)[0])
        if self.profile_model.get("log_target"):
            pred = float(np.expm1(pred))
        return max(0.0, pred)

    def sensitivity(self, city: str, house: str, start_date: date,
                    overrides: dict | None = None) -> dict:
        """Change in predicted daily kWh when one more of each appliance is added.

        This is model sensitivity, not measured per-appliance consumption.
        """
        if self.profile_model is None:
            return {"available": False, "baseline_kwh": None, "rows": []}

        overrides = dict(overrides or {})
        latest = self.house_history(city, house).iloc[-1]
        baseline = self.profile_predict(city, house, start_date, overrides)

        rows = []
        for appliance in self.appliance_columns:
            base = overrides.get(appliance)
            if base is None and appliance in latest.index:
                base = latest[appliance]
            try:
                base = 0.0 if base is None or pd.isna(base) else float(base)
            except (TypeError, ValueError):
                continue

            trial = dict(overrides)
            trial[appliance] = base + 1
            changed = self.profile_predict(city, house, start_date, trial)
            rows.append({
                "appliance": appliance,
                "base_count": base,
                "baseline_kwh": round(baseline, 4),
                "plus_one_kwh": round(changed, 4),
                "delta_kwh": round(changed - baseline, 4),
            })

        rows.sort(key=lambda r: r["delta_kwh"], reverse=True)
        return {"available": True, "baseline_kwh": round(baseline, 4), "rows": rows}

    def profile_model_info(self) -> dict | None:
        if self.profile_model is None:
            return None
        return {
            "model": "XGBoost profile model (what-if)",
            "purpose": "Estimates daily kWh from household and appliance characteristics.",
            "excluded": self.profile_model.get("excluded"),
            "feature_count": len(self.profile_model["features"]),
            "metrics": self.profile_model.get("metrics", {}),
        }

    def model_info(self) -> dict:
        return {
            "model": "XGBoost (tuned)",
            "target": self.target,
            "feature_count": len(self.feature_columns),
            "train_end_date": self.train_end_date,
            "best_parameters": self.best_parameters,
            "metrics": self.metrics,
            "data_start": self.df[self.date_col].min().date().isoformat(),
            "data_end": self.df[self.date_col].max().date().isoformat(),
            "house_count": int(self.df[self.house_col].nunique()),
            "city_count": int(self.df[self.city_col].nunique()),
        }

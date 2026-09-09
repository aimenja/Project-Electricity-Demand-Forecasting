"""Train the PowerPlus 'profile' model used by the dashboard's what-if panel.

The shipped forecasting model draws 74% of its signal from rolling/lag demand
features and assigns exactly 0.0 importance to every appliance feature, so it
cannot answer "what happens if I add an air conditioner". This model removes the
historical-demand features and the house-identity columns, forcing household and
appliance characteristics to carry the signal.

It is a complement to the forecasting model, not a replacement: it is less
accurate at short-horizon prediction and is only used for what-if comparisons.
"""

import json
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PROCESSED = ROOT.parent / "processed_data"
OUT_PKL = DATA / "powerplus_profile_model.pkl"
OUT_METRICS = DATA / "powerplus_profile_model_metrics.json"

TRAIN_END = "2024-08-24"
HOUSE_IDENTITY = {"house", "House"}


def main() -> None:
    artifact = joblib.load(PROCESSED / "powerplus_xgboost_forecast_model.pkl")
    numeric = list(artifact["numeric_features"])
    categorical = list(artifact["categorical_features"])
    target = artifact["target"]

    def is_demand_history(col: str) -> bool:
        return col.startswith("lag_") or col.startswith("rolling_")

    # The forecast notebook re-merges daily_weather.csv onto data that already carries
    # those columns, so every weather reading arrives twice: once plain and once with a
    # "_weather" suffix, with identical values. Keep a single copy.
    numeric_set = set(numeric)
    def is_weather_duplicate(col: str) -> bool:
        return col.endswith("_weather") and col[: -len("_weather")] in numeric_set

    numeric = [c for c in numeric
               if not is_demand_history(c)
               and c not in HOUSE_IDENTITY
               and not is_weather_duplicate(c)]
    categorical = [c for c in categorical if c not in HOUSE_IDENTITY]
    features = numeric + categorical

    df = pd.read_csv(PROCESSED / "powerplus_model_data.csv")
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=[target])

    train = df[df["date"] <= TRAIN_END]
    test = df[df["date"] > TRAIN_END]

    pre = ColumnTransformer([
        ("num", SimpleImputer(strategy="median"), numeric),
        ("cat", Pipeline([
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("encode", OneHotEncoder(handle_unknown="ignore")),
        ]), categorical),
    ])

    model = XGBRegressor(
        n_estimators=600, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        reg_lambda=1.0, random_state=42, n_jobs=-1,
    )
    pipeline = Pipeline([("pre", pre), ("model", model)])

    # The target spans 0 to 82 kWh with a heavy right skew, so training in log
    # space stops the four highest-consumption houses from dominating the fit.
    pipeline.fit(train[features], np.log1p(train[target]))

    def evaluate(frame: pd.DataFrame) -> dict:
        pred = np.expm1(pipeline.predict(frame[features])).clip(min=0)
        actual = frame[target].values
        return {
            "MAE": float(mean_absolute_error(actual, pred)),
            "RMSE": float(np.sqrt(mean_squared_error(actual, pred))),
            "R2": float(r2_score(actual, pred)),
            "n": int(len(frame)),
        }

    metrics = {"train": evaluate(train), "test": evaluate(test)}

    joblib.dump({
        "pipeline": pipeline,
        "features": features,
        "numeric_features": numeric,
        "categorical_features": categorical,
        "target": target,
        "log_target": True,
        "train_end_date": TRAIN_END,
        "excluded": "lag/rolling demand history and house identity",
    }, OUT_PKL)

    OUT_METRICS.write_text(json.dumps(metrics, indent=2))

    print(f"features: {len(features)} ({len(numeric)} numeric, {len(categorical)} categorical)")
    for split, m in metrics.items():
        print(f"{split:5s} n={m['n']:6d}  MAE={m['MAE']:.4f}  RMSE={m['RMSE']:.4f}  R2={m['R2']:.4f}")

    names = pipeline.named_steps["pre"].get_feature_names_out()
    importance = pd.Series(pipeline.named_steps["model"].feature_importances_, index=names)
    print("\ntop features:")
    print(importance.sort_values(ascending=False).head(12).round(4).to_string())


if __name__ == "__main__":
    main()

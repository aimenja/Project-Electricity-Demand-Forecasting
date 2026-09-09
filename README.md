# PowerPlus --- Electricity Demand Forecasting

PowerPlus is a machine-learning project for predicting household
electricity consumption and forecasting future electricity demand using
historical electricity usage, household characteristics, weather
conditions, and calendar patterns.

The project currently covers the complete workflow from raw
electricity-data processing through **feature engineering, ML baseline
modelling, and short-term demand forecasting**.

------------------------------------------------------------------------

------------------------------------------------------------------------

## Web Dashboard

The final stage of the project lives in [`dashboard/`](dashboard/) — a web
application that turns the trained forecasting model into something a
non-technical user can operate from a browser.

```bash
cd dashboard
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python scripts/train_profile_model.py
./run.sh                 # http://127.0.0.1:8000
./run.sh --share         # also prints a public link for any device
```

It lets the user pick a city and house, edit the household and appliance
inputs, and forecast 1, 7 or 30 days ahead, charted against recorded
history. A companion "profile" model answers the appliance what-if
question — how predicted daily kWh changes per additional appliance —
which the forecasting model cannot do, because it assigns the appliance
features an importance of ~0 once it can see recent consumption.

The dashboard reads `processed_data/` directly, so re-exporting the model
from the notebooks updates it with no code changes. See
[`dashboard/README.md`](dashboard/README.md) for details, including known
limitations inherited from the dataset.

------------------------------------------------------------------------

# PowerPlus — Electricity Demand Forecasting

PowerPlus is a machine-learning project for predicting **total household electricity demand** and forecasting future electricity consumption using historical electricity usage, household characteristics, weather conditions, calendar patterns, and historical demand features.

The project covers the complete workflow from raw electricity-data processing through **data cleaning, feature engineering, exploratory analysis, supervised regression, XGBoost modelling, hyperparameter tuning, leakage prevention, recursive forecasting, and web application integration**.

---

## Project Status

| Stage                                     | Status    |
| ----------------------------------------- | --------- |
| Raw electricity data processing           | Completed |
| Daily electricity consumption calculation | Completed |
| Household metadata processing             | Completed |
| Weather data processing                   | Completed |
| Data integration                          | Completed |
| Data quality checks                       | Completed |
| Exploratory Data Analysis                 | Completed |
| Feature engineering                       | Completed |
| Model-ready dataset                       | Completed |
| ML baseline modelling                     | Completed |
| Decision Tree modelling                   | Completed |
| XGBoost baseline modelling                | Completed |
| XGBoost hyperparameter tuning             | Completed |
| Weather integration into XGBoost          | Completed |
| House feature removal from model          | Completed |
| Leakage-safe preprocessing                | Completed |
| Recursive forecasting                     | Completed |
| 1-day forecasting                         | Completed |
| 7-day forecasting                         | Completed |
| 30-day forecasting                        | Completed |
| FastAPI backend                           | Completed |
| Web application/dashboard                 | Completed |

---

# Problem Statement

Electricity demand varies across households, cities, seasons, weather conditions, and appliance usage.

The goal of PowerPlus is to use historical household electricity consumption together with household, weather, calendar, and historical-demand information to estimate **future total household electricity demand**.

The project focuses on daily electricity consumption measured in **kWh**.

The target variable is:

```text
electricity_kwh
```

PowerPlus is a **supervised regression problem** because electricity demand is a continuous numerical value.

---

# Project Objectives

The main objectives are to:

* Convert raw minute-level electricity measurements into daily electricity consumption.
* Combine electricity data with household metadata.
* Integrate city-wise weather information.
* Perform data-quality checks.
* Perform exploratory data analysis.
* Engineer household, appliance, weather, calendar, lag, and rolling features.
* Remove the `House` identifier from the final model training features.
* Build a leakage-safe machine-learning pipeline.
* Compare simple forecasting baselines with machine-learning models.
* Train an XGBoost regression model.
* Tune important XGBoost hyperparameters.
* Evaluate the model using MAE, RMSE, and R².
* Generate recursive 1-day, 7-day, and 30-day forecasts.
* Integrate the trained model into a web application.

---

# Data Sources

PowerPlus uses three main data sources:

1. Electricity data
2. Household metadata
3. Weather data

---

## 1. Electricity Data

The electricity data is organized city-wise:

```text
city-wise_house_dataset/
├── Islamabad/
├── Karachi/
├── Lahore/
├── Multan/
├── Peshawar/
└── Skardu/
```

The raw electricity files contain time-based electricity usage measurements.

The minute-level power readings are converted into daily energy consumption in kWh.

The daily calculation is:

```text
Daily Electricity (kWh)
= Sum of minute-level power readings (kW) / 60
```

The resulting target variable is:

```text
electricity_kwh
```

---

## 2. Household Metadata

Household information is obtained from:

```text
metadata_ultimate.xlsx
```

The metadata contains household and building characteristics such as:

* Number of residents
* Covered area
* Number of rooms
* Construction year
* Ceiling type
* Roof type
* Air conditioners
* Air coolers
* Refrigerators
* Washing machines
* Fans
* Water pumps
* Electric heaters
* Electric cookers
* Geysers
* Other household appliances

These variables provide information about differences in electricity demand between households.

---

## 3. Weather Data

Weather data is available city-wise:

```text
weather_dataset/
├── Islamabad.csv
├── Karachi.csv
├── Lahore.csv
├── Multan.csv
├── Peshawar.csv
└── Skardu.csv
```

Weather information includes variables such as:

* Temperature
* Humidity
* Dew
* Precipitation
* Wind speed
* Wind direction
* Pressure
* Solar radiation
* Solar energy
* UV index

Weather data is aggregated to the daily level and merged with electricity data using:

```text
City + Date
```

Weather is therefore used as a genuine predictive input in the final XGBoost model.

---

# Data Processing Pipeline

The overall workflow is:

```text
Raw Electricity Data
        ↓
Minute-Level Cleaning
        ↓
Daily Electricity (kWh)
        ↓
Household Metadata Cleaning
        ↓
Daily Weather Processing
        ↓
Data Integration
        ↓
Data Quality Checks
        ↓
Exploratory Data Analysis
        ↓
Feature Engineering
        ↓
Chronological Train/Test Split
        ↓
Leakage-Safe Preprocessing
        ↓
XGBoost Training & Tuning
        ↓
Model Evaluation
        ↓
Recursive Forecasting
        ↓
Web Application
```

---

# Electricity Data Processing

The electricity-processing workflow:

1. Reads city-wise electricity files.
2. Identifies relevant datetime and usage columns.
3. Standardizes household and city identifiers.
4. Converts timestamps to datetime.
5. Converts electricity usage to numeric values.
6. Removes invalid readings.
7. Removes duplicate timestamps.
8. Aggregates minute-level measurements to daily level.
9. Calculates daily electricity consumption in kWh.
10. Performs data-quality checks.

The processed data contains supporting information such as:

* Number of readings
* Average power
* Maximum power
* Minimum power
* Expected readings
* Coverage percentage
* Low-coverage indicators

These supporting fields are used for data-quality analysis and are not used as same-day predictors of the target.

---

# Data Integration

The three main datasets are integrated using appropriate identifiers.

The resulting dataset combines:

```text
Electricity
+
Household Metadata
+
Weather
+
Calendar Information
+
Historical Demand Features
```

The final modelling dataset contains approximately:

```text
19,181 household-day records
6 cities
59 households
2023-08-15 to 2024-11-27
```

The target variable is:

```text
electricity_kwh
```

---

# Exploratory Data Analysis

Exploratory Data Analysis was performed to understand the electricity-demand data before modelling.

The analysis included:

* Mean
* Median
* Mode
* Missing-value analysis
* Distribution analysis
* Outlier inspection
* Categorical-value analysis
* Household and appliance information
* Weather relationships
* Electricity-demand patterns

The EDA helped identify missing values, unusual observations, skewed distributions, and important characteristics of the dataset.

---

# Feature Engineering

Feature engineering was performed to provide XGBoost with information about household characteristics, weather, calendar patterns, and previous electricity demand.

## Historical Demand Features

Lag features include:

```text
lag_1_day_kwh
lag_2_day_kwh
lag_3_day_kwh
lag_7_day_kwh
lag_14_day_kwh
lag_30_day_kwh
```

Rolling demand features include:

```text
rolling_3_day_avg_kwh
rolling_7_day_avg_kwh
rolling_14_day_avg_kwh
rolling_30_day_avg_kwh
```

These features allow the model to learn from recent electricity-demand behaviour.

---

## Calendar Features

Calendar features include:

* Year
* Month
* Day
* Day of week
* Week of year
* Day of year
* Weekend indicator
* Season

These features help the model capture daily, weekly, monthly, and seasonal patterns.

---

## Household and Appliance Features

The final user-facing system uses household and appliance information such as:

* Number of people
* Covered area
* Number of rooms
* House age
* Ceiling type
* Roof type
* Air conditioners
* Air coolers
* Refrigerators
* Washing machines
* Ceiling fans
* Water pumps
* Electric heaters
* Electric cooker
* Geysers
* LED bulbs

A derived `house_age` feature is also used.

The `House` identifier itself is **removed from model training** so that the model does not simply memorize individual household identities.

---

# Categorical Feature Encoding

Categorical variables are converted into numerical representations using **One-Hot Encoding**.

The preprocessing uses:

```python
OneHotEncoder(handle_unknown="ignore")
```

`handle_unknown="ignore"` allows the model pipeline to handle categories that were not present during training.

One-hot encoding is applied only to categorical variables.

---

# Missing-Value Imputation

Missing values are handled inside the Scikit-learn preprocessing pipeline.

For numerical variables:

```python
SimpleImputer(strategy="median")
```

For categorical variables:

```python
SimpleImputer(strategy="most_frequent")
```

Median imputation is used for numerical model features because it is less affected by extreme values than the mean.

---

# Normalization and Standardization

The final XGBoost pipeline **does not use feature normalization or standardization**.

No:

```text
StandardScaler
MinMaxScaler
```

is applied.

This is appropriate because XGBoost is a tree-based model and does not require features to be on the same numerical scale.

---

# Leakage Prevention

Data leakage was specifically considered during the modelling process.

Same-day electricity measurement fields such as:

```text
readings
avg_power_kw
max_power_kw
min_power_kw
coverage_pct
```

are not used as predictors for the same day's electricity demand because they are derived from the electricity observation being predicted.

Using these fields would provide information about the prediction day to the model.

The final model therefore focuses on information that would realistically be available when making a forecast.

---

# Leak-Free Preprocessing Pipeline

The Scikit-learn preprocessing is implemented as part of a pipeline.

Conceptually:

```text
Training Data
     ↓
Numerical Features → Median Imputation
     ↓
Categorical Features → Most-Frequent Imputation
     ↓
One-Hot Encoding
     ↓
XGBoost
```

The preprocessing parameters are **learned only from the training data**.

The same learned preprocessing is then applied to the test data.

This prevents information from the test set from being used while training the model.

---

# Chronological Train/Test Split

Because electricity demand is a time-dependent forecasting problem, a chronological split is used instead of a random split.

The final evaluation split is approximately:

```text
Training:
2023-08-15 → 2024-08-24

Testing:
2024-08-25 → 2024-11-27
```

Therefore:

```text
Earlier dates → Training
Later dates   → Testing
```

This better represents real-world forecasting, where the model learns from historical data and predicts future demand.

---

# Machine Learning Models

PowerPlus evaluates both simple forecasting baselines and machine-learning models.

The evaluated approaches include:

1. Training Mean
2. Previous Day (`lag_1`)
3. Previous Week (`lag_7`)
4. Decision Tree Regressor
5. XGBoost baseline
6. Tuned XGBoost Regressor

The models are evaluated using:

* MAE — Mean Absolute Error
* RMSE — Root Mean Squared Error
* R² — Coefficient of Determination

---

# XGBoost Model

The final PowerPlus forecasting model is **XGBoost Regressor**.

XGBoost was selected because it can model nonlinear relationships between:

* Historical electricity demand
* Household characteristics
* Appliance information
* Weather
* Calendar patterns

The final model also uses weather features that are merged into the training data.

---

# XGBoost Hyperparameter Tuning

Important XGBoost hyperparameters were tuned to improve model performance.

The tuning search included:

```text
n_estimators:
300, 500

max_depth:
3, 6, 9

learning_rate:
0.03, 0.05

subsample:
0.8, 1.0

colsample_bytree:
0.8, 1.0
```

The best-performing configuration was:

```text
n_estimators     = 300
max_depth        = 3
learning_rate    = 0.03
subsample        = 0.8
colsample_bytree = 1.0
```

The relatively shallow tree depth helps control model complexity while maintaining strong predictive performance.

---

# XGBoost Results

The final tuned XGBoost model achieved:

| Model                  |        MAE |       RMSE |         R² |
| ---------------------- | ---------: | ---------: | ---------: |
| Previous Day (`lag_1`) |     0.0911 |     0.7002 |     0.8875 |
| Decision Tree — Tuned  |     0.1027 |     0.7656 |     0.8655 |
| XGBoost — Baseline     |     0.0976 |     0.7372 |     0.8753 |
| **XGBoost — Tuned**    | **0.0891** | **0.6536** | **0.9020** |

The tuned XGBoost model produced the best overall performance among the evaluated machine-learning models.

It also improved on the previous-day baseline in the recorded test evaluation.

---

# Recursive Forecasting

PowerPlus supports recursive forecasting for future electricity demand.

The system can generate:

```text
1-day forecast
7-day forecast
30-day forecast
```

For future days, actual electricity consumption is not available.

Therefore, the model predicts one day at a time.

For example:

```text
Day 1
  ↓
Prediction
  ↓
Used as historical demand
  ↓
Day 2
  ↓
Prediction
  ↓
Used as historical demand
  ↓
Day 3
  ↓
...
```

This approach allows lag and rolling features to be generated for future days without using future actual electricity consumption.

---

# Future Weather

The available dataset contains historical weather rather than guaranteed future weather forecasts.

For future forecasting, the system can use available future weather data when supplied.

When future weather is not available, the current system uses a historical weather proxy based on available city and seasonal information.

This historical proxy should **not be interpreted as an actual weather forecast**.

A future production version can integrate a dedicated weather forecasting service or forecast dataset.

---

# Final User Input System

The final PowerPlus web application allows users to provide a manageable set of household and appliance inputs.

The user-facing inputs include:

1. Number of people
2. Covered area
3. Number of rooms
4. House age
5. Ceiling type
6. Roof type
7. Air conditioners
8. Air coolers
9. Refrigerators
10. Washing machines
11. Ceiling fans
12. Water pumps
13. Electric heaters
14. Electric cooker
15. Geysers
16. LED bulbs

The user also selects:

```text
City
Forecast start date
Forecast horizon
```

The system automatically generates the required:

* Calendar features
* Lag features
* Rolling features
* Weather features
* Other model-required features

The user does not need to manually enter weather or lag values.

---

# Web Application

The trained XGBoost model is integrated into a web application through a backend API.

The application workflow is:

```text
User Inputs
     ↓
Backend
     ↓
Feature Generation
     ↓
Weather Features
     ↓
Lag/Rolling Features
     ↓
Trained XGBoost Model
     ↓
Electricity Demand Prediction
     ↓
1 / 7 / 30-Day Forecast
     ↓
Charts and Results
```

The backend provides predictions through a FastAPI service.

---

# Model Outputs

The trained system stores:

* Trained XGBoost model
* Preprocessing pipeline
* Model feature information
* Evaluation metrics
* Forecast outputs

The saved model artifact can then be loaded by the backend application without retraining the model for every prediction.

---

# Technologies Used

* Python
* Pandas
* NumPy
* Matplotlib
* Scikit-learn
* XGBoost
* Joblib
* FastAPI
* Jupyter Notebook
* VS Code
* HTML
* CSS
* JavaScript

---

# Main Python Libraries

```text
pandas
numpy
matplotlib
scikit-learn
xgboost
joblib
fastapi
uvicorn
openpyxl
```

---

# Key Findings

The modelling process produced several important findings:

* Historical electricity demand is highly useful for forecasting.
* The previous-day demand is a strong baseline.
* The tuned XGBoost model outperformed the previous-day baseline on the recorded test evaluation.
* Tuned XGBoost achieved the best MAE, RMSE, and R² among the evaluated models.
* Weather information provides additional predictive features.
* Household and appliance characteristics allow user-specific demand scenarios.
* Calendar features help capture recurring temporal patterns.
* Same-day electricity measurements can cause target leakage and were therefore excluded from predictive use.
* Chronological evaluation provides a more realistic forecasting assessment than random splitting.
* Recursive forecasting allows the system to generate multi-day forecasts without using future actual demand.

---

# Current Limitations

The current project has several limitations:

1. The dataset contains a relatively limited number of households and historical years.
2. Future weather is not always available and may therefore require a historical seasonal proxy.
3. Recursive forecasting can accumulate prediction errors over longer horizons.
4. Electricity behaviour varies considerably between households.
5. The target distribution is highly skewed, so error metrics should be interpreted carefully.
6. Future performance may differ from the recorded test performance.
7. A larger and longer-term dataset would improve generalization.
8. Real-world deployment would benefit from actual weather forecasts and continuous model monitoring.

---

# Future Development

Future versions of PowerPlus can focus on:

* Integrating real future weather forecasts.
* Increasing the number of households and cities.
* Adding longer historical datasets.
* Comparing XGBoost with advanced time-series models.
* Improving 7-day and 30-day forecast accuracy.
* Performing city-specific and household-specific evaluation.
* Improving cold-start forecasting for new households.
* Adding electricity tariff and bill estimation.
* Adding energy-efficiency recommendations.
* Integrating solar/net-metering scenarios.
* Deploying the system as a production decision-support platform.

---

# Project Structure

A simplified project structure is:

```text
PowerPlus/
│
├── city-wise_house_dataset/
│   ├── Islamabad/
│   ├── Karachi/
│   ├── Lahore/
│   ├── Multan/
│   ├── Peshawar/
│   └── Skardu/
│
├── weather_dataset/
│   ├── Islamabad.csv
│   ├── Karachi.csv
│   ├── Lahore.csv
│   ├── Multan.csv
│   ├── Peshawar.csv
│   └── Skardu.csv
│
├── metadata_ultimate.xlsx
│
├── processed_data/
│   ├── daily_electricity_clean.csv
│   ├── powerplus_daily_merged.csv
│   ├── powerplus_model_data.csv
│   └── ...
│
├── PowerPlus_Data_Processing_Feature_Engineering.ipynb
├── PowerPlus_XGBoost_Baseline_Comparison_Weather_NoHouse_Final.ipynb
├── PowerPlus_User_Input_XGBoost_Weather_NoHouse_PowerBI_Final.ipynb
│
├── model/
│   └── powerplus_xgboost_forecast_model.pkl
│
├── backend/
│   ├── forecast.py
│   └── ...
│
└── frontend/
    ├── index.html
    ├── style.css
    └── script.js
```

---

# How to Run

## 1. Install dependencies

```bash
pip install pandas numpy matplotlib scikit-learn xgboost joblib openpyxl fastapi uvicorn
```

## 2. Run the data-processing notebook

```text
PowerPlus_Data_Processing_Feature_Engineering.ipynb
```

This prepares the cleaned and integrated modelling data.

## 3. Train and evaluate XGBoost

Run:

```text
PowerPlus_XGBoost_Baseline_Comparison_Weather_NoHouse_Final.ipynb
```

This notebook performs:

```text
Feature preparation
        ↓
Chronological split
        ↓
Preprocessing pipeline
        ↓
XGBoost baseline
        ↓
Hyperparameter tuning
        ↓
Final XGBoost
        ↓
Evaluation
        ↓
Forecasting
```

## 4. Run the user-input forecasting notebook

```text
PowerPlus_User_Input_XGBoost_Weather_NoHouse_PowerBI_Final.ipynb
```

This prepares the model for user-provided household and appliance inputs.

## 5. Run the web backend

Start the FastAPI backend and connect the frontend to the prediction endpoint.

---

# Conclusion

PowerPlus provides an end-to-end system for **household electricity demand forecasting**.

The project transforms raw minute-level electricity measurements into daily kWh consumption, integrates household and weather information, performs exploratory analysis, engineers historical and calendar features, and applies a leakage-safe machine-learning pipeline.

The final forecasting model is a **tuned XGBoost Regressor** with:

```text
n_estimators     = 300
max_depth        = 3
learning_rate    = 0.03
subsample        = 0.8
colsample_bytree = 1.0
```

The model achieved:

```text
MAE  = 0.0891
RMSE = 0.6536
R²   = 0.9020
```

The system supports **1-day, 7-day, and 30-day recursive electricity-demand forecasting** and is integrated into a web application where users can enter household and appliance information without manually providing technical model features such as lags, rolling averages, or weather variables.

PowerPlus therefore provides a foundation for a practical **household electricity demand forecasting and energy-management decision-support system**.

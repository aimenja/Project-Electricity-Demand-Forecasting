# PowerPlus — Household Electricity Demand Forecasting

## 📌 Project Overview

**PowerPlus** is a household electricity demand forecasting project that uses **household characteristics, appliance information, historical electricity consumption, and weather conditions** to predict future electricity demand.

The main goal is to develop a machine-learning system that can estimate how much electricity a household is likely to consume and eventually provide **7-day and 30-day demand forecasts**.

The project combines:

* 🏠 Household characteristics
* ⚡ Appliance information
* 📊 Historical electricity consumption
* 🌤️ Historical weather data
* 📅 Calendar/seasonal information
* 🤖 Machine learning
* 📈 Electricity demand forecasting

---

# 🎯 Problem Statement

Household electricity consumption changes according to several factors, including:

* Number of residents
* Household size
* Appliances
* Number of air conditioners
* Refrigerators
* Fans
* Washing machines
* Water pumps
* Heating/cooling requirements
* Temperature
* Humidity
* Seasonal patterns
* Previous electricity consumption

PowerPlus aims to combine these factors to predict future household electricity demand.

The final system is intended to answer:

> **"Based on this household's characteristics, appliances, recent electricity usage, and expected conditions, how much electricity is it likely to consume?"**

---

# 🗂️ Data Sources

The project currently uses three main datasets.

## 1. Household Metadata

The household metadata contains information about individual houses, including:

* House ID
* City
* Owner/Rented status
* Number of residents
* Children
* Adults
* Seniors
* Property area
* Covered area
* Number of floors
* Construction year
* Electricity connection type
* Ceiling information
* Roof type
* Flooring type
* Number of rooms
* Number of washrooms
* Air conditioners
* Air coolers
* Refrigerators
* Washing machines
* LED bulbs
* Tube lights
* Ceiling fans
* Wall fans
* Stand fans
* Water dispensers
* Water pumps
* Electric cookers
* Electric heaters
* Electric irons
* Microwave ovens
* Geysers
* UPS
* Other electronic devices

**File:**

```text
metadata_ultimate.xlsx
```

---

## 2. Historical Electricity Consumption

The electricity datasets contain household-level electricity readings at approximately **one-minute intervals**.

Example:

```text
datetime              Usage (kW)
2023-11-01 00:00      0.63
2023-11-01 00:01      0.64
2023-11-01 00:02      0.63
...
```

The raw readings are measured in **kW**.

For the forecasting model, the minute-level readings are converted into **daily electricity consumption in kWh**.

### Conversion

```text
Daily kWh = Σ(kW × 1/60)
```

This converts the approximately one-minute power readings into daily energy consumption.

---

## 3. Historical Weather Data

The project currently uses historical weather data instead of relying on a live weather API.

Example weather dataset:

```text
Islamabad.csv
```

Weather variables include:

* Temperature
* Humidity
* Dew
* Precipitation
* Wind Speed
* Wind Direction
* Pressure
* Solar Radiation
* Solar Energy
* UV Index

The original weather data is hourly.

It is aggregated into **daily weather features** so that it can be aligned with the daily electricity consumption data.

---

# 🔄 Data Processing Pipeline

The current data-processing pipeline is:

```text
Raw Electricity Data
        │
        ▼
Clean datetime & usage
        │
        ▼
Convert minute-level kW
to daily kWh
        │
        ▼
Daily Electricity Dataset
        │
        ├───────────────┐
        │               │
        ▼               ▼
Household Metadata   Weather CSV
        │               │
        │               ▼
        │          Hourly → Daily
        │          Weather Features
        │               │
        └───────┬───────┘
                ▼
          Dataset Merging
                │
                ▼
        Feature Engineering
                │
                ▼
          Data Preprocessing
                │
                ▼
       Decision Tree Regression
                │
                ▼
          Electricity Prediction
```

---

# ✅ Work Completed

## 1. Electricity Data Processing

The raw minute-level electricity readings have been processed.

The data was:

* Loaded using Python/Pandas
* Converted to datetime
* Sorted chronologically
* Grouped by household and date
* Converted from minute-level kW readings to daily kWh consumption

### Result

The model now works with **daily electricity consumption** instead of thousands of individual minute readings.

---

# 2. Weather Data Processing

The historical `Islamabad.csv` weather dataset has been processed.

The hourly observations were aggregated into daily features.

Examples include:

```text
Temperature_Avg_C
Temperature_Min_C
Temperature_Max_C
Humidity_Avg_pct
Dew_Avg
Precipitation_mm
WindSpeed_Avg
Pressure_Avg
SolarRadiation_Avg
SolarEnergy_Sum
UVIndex_Avg
```

This makes the weather data compatible with the daily electricity consumption data.

---

# 3. Household + Weather + Electricity Integration

The three types of information are combined.

### Household information

Joined using:

```text
House
```

### Weather information

Joined using:

```text
City + Date
```

### Electricity information

Identified using:

```text
House + Date
```

The resulting dataset represents a household's electricity consumption together with its:

* Household characteristics
* Appliances
* Weather
* Calendar information
* Historical consumption

---

# 4. Calendar Feature Engineering

Date information was transformed into useful machine-learning features.

Features include:

```text
Year
Month
Day
Day of Week
Weekend
Day of Year
```

Seasonal information was also represented using cyclic transformations.

This allows the model to learn patterns associated with:

* Months
* Weekdays
* Weekends
* Seasonal changes

---

# 5. Lag Feature Engineering

Historical electricity consumption is important for demand forecasting.

The following lag features were created:

### `lag_1_kWh`

Previous day's electricity consumption.

```text
Today ← Yesterday
```

### `lag_7_kWh`

Electricity consumption seven days earlier.

```text
Today ← Same day of previous week
```

### `rolling_7_kWh`

Average electricity consumption over the previous seven days.

These features allow the model to learn the household's recent consumption behavior and weekly patterns.

---

# 6. Data Preprocessing

The dataset contains both numerical and categorical features.

### Numerical features

Missing numerical values are handled using **median imputation**.

### Categorical features

Missing categorical values are handled using the **most frequent category**.

Categorical variables are then converted into numerical features using:

```text
One-Hot Encoding
```

This makes the data suitable for the Decision Tree model.

---

# 7. Target Variable

The target variable is:

```text
Electricity_Consumption_kWh
```

The model therefore performs **regression**, because electricity consumption is a continuous numerical value.

---

# 8. Train/Test Split

A chronological train/test split was used.

```text
80% → Training Data
20% → Testing Data
```

The data was **not randomly shuffled**.

This is important for a forecasting project because the model should learn from the past and be tested on later observations.

```text
PAST                         FUTURE
│                               │
▼                               ▼
Training Data              Test Data
```

---

# 9. Machine Learning Model

The current machine-learning model is:

## Decision Tree Regressor

The Decision Tree was selected because the target variable is continuous and the model can learn nonlinear relationships between:

* Household characteristics
* Appliances
* Weather
* Calendar features
* Historical electricity consumption

Current model configuration includes:

```text
max_depth = 8
min_samples_split = 10
min_samples_leaf = 5
random_state = 42
```

---

# 10. Initial Model Evaluation

The initial Decision Tree model has been trained and tested.

Current evaluation results:

| Metric |       Result |
| ------ | -----------: |
| MAE    | 0.000154 kWh |
| RMSE   | 0.000383 kWh |
| R²     |       0.9992 |

An **Actual vs Predicted** visualization has also been generated to compare model predictions with actual electricity consumption.

### Important

These are **initial model results**, not the final performance of the complete PowerPlus forecasting system.

The dataset currently represents a limited number of households, so additional validation is required before making strong claims about generalization.

---

# 🌦️ Weather API Issue

## Initial Plan

The original plan was to use **OpenWeatherMap API** to retrieve weather information automatically.

The intended architecture was:

```text
Consumer enters location
        │
        ▼
OpenWeatherMap API
        │
        ▼
Weather data
        │
        ▼
Feature Engineering
        │
        ▼
ML Model
```

## Problem

The OpenWeatherMap API currently returns:

```text
HTTP 401 Unauthorized
```

because of the available API/subscription access.

Therefore, the project is **not currently dependent on the live OpenWeatherMap API**.

## Current Solution

For the model-development stage, historical weather data is being used:

```text
Historical Weather CSV
        │
        ▼
Weather Processing
        │
        ▼
Daily Weather Features
        │
        ▼
Machine Learning Model
```

This allows the data-processing and machine-learning pipeline to continue without depending on the external API.

---

# 🧠 Why Historical Weather Is Still Useful

The purpose of weather data during model development is to allow the model to learn relationships such as:

```text
Higher Temperature
       ↓
More Cooling
       ↓
Higher Electricity Demand
```

and:

```text
Lower Temperature
       ↓
Possible Heating Demand
       ↓
Higher Electricity Demand
```

Historical weather therefore remains useful for **training and evaluating the model**.

However, a true future forecast requires future weather information or a documented weather-estimation method.

---

# ⚠️ Current Project Limitation

The current model predicts **daily electricity consumption**.

The overall project objective is broader:

```text
Next 7 Days
Next 30 Days
```

Therefore, the current daily prediction model still needs to be converted into a proper **multi-day forecasting system**.

The OpenWeatherMap issue also means that the final application still needs a solution for obtaining future weather conditions.

---

# 🚧 Remaining Milestones

## Milestone 1 — Improve Forecast Validation

**Status: ⏳ Pending**

Further validation is required to ensure that the model genuinely predicts future electricity demand.

Tasks:

* Validate chronological predictions
* Check possible data leakage
* Compare predicted vs actual consumption
* Analyze prediction errors
* Test different Decision Tree configurations
* Establish a reliable baseline model

---

# Milestone 2 — Build 7-Day Forecast

**Status: ⏳ Pending**

Convert the current daily prediction model into a **next-7-day forecasting system**.

Target output:

```text
Day 1 → predicted kWh
Day 2 → predicted kWh
Day 3 → predicted kWh
Day 4 → predicted kWh
Day 5 → predicted kWh
Day 6 → predicted kWh
Day 7 → predicted kWh

Total → predicted 7-day consumption
```

---

# Milestone 3 — Build 30-Day Forecast

**Status: ⏳ Pending**

Extend the forecasting system to estimate:

```text
Day 1
Day 2
...
Day 30
```

and calculate:

```text
Total predicted monthly electricity consumption
```

---

# Milestone 4 — Future Weather Integration

**Status: ⏳ Pending**

Find a reliable method to obtain future weather information.

Possible approaches include:

```text
Weather Forecast API
        OR
Alternative Weather Provider
        OR
Historical/Seasonal Weather Estimation
```

The final choice will be documented according to availability and project requirements.

---

# Milestone 5 — Consumer Input System

**Status: ⏳ Pending**

Create an interface where the consumer can enter household information.

Example:

```text
City: Islamabad

Number of people: 6

Air Conditioners: 3

Refrigerators: 2

Washing Machines: 1

Fans: 6

Water Pump: 1

Microwave: 1

...
```

The consumer will not need to understand the machine-learning process.

---

# Milestone 6 — Consumer Profile → Prediction

**Status: ⏳ Pending**

The consumer information will be transformed into the same features used during model training.

The final pipeline will be:

```text
Consumer Input
      │
      ▼
Consumer Profile
      │
      ▼
Household Features
      │
      +
Weather Features
      │
      +
Historical Consumption
      │
      ▼
Feature Engineering
      │
      ▼
Trained Decision Tree
      │
      ▼
Electricity Demand
```

---

# Milestone 7 — Final PowerPlus Output

**Status: ⏳ Pending**

The final system should provide an easy-to-understand result such as:

```text
⚡ Estimated Electricity Demand

Next 7 Days:
XX kWh

Next 30 Days:
XX kWh

Average Daily Demand:
XX kWh
```

Additional visualizations can include:

* Daily predicted consumption
* Weekly demand trend
* Monthly demand trend
* Actual vs predicted consumption
* Weather vs electricity demand

---

# Milestone 8 — Final Application

**Status: ⏳ Pending**

The final PowerPlus application will connect:

```text
Consumer
   │
   ▼
Household Input
   │
   ▼
Weather Data
   │
   ▼
Historical Consumption
   │
   ▼
Feature Engineering
   │
   ▼
Decision Tree Model
   │
   ▼
7-Day Forecast
   │
   ▼
30-Day Forecast
```


---

# 🛠️ Technology Stack

```text
Python
Pandas
NumPy
Scikit-learn
Matplotlib
Jupyter Notebook
VS Code
Git
GitHub
```


---

# 🎯 Final Project Goal

The final PowerPlus system will allow a consumer to provide information about their household and appliances.

The system will combine that information with historical consumption and weather information to estimate future electricity demand.

### Final concept

```text
                 ⚡ POWERPLUS
                     │
                     ▼
             Consumer Profile
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
      Household   Appliances   Location
          │          │          │
          │          │          ▼
          │          │      Future Weather
          │          │          │
          └──────────┼──────────┘
                     ▼
             Historical Usage
                     │
                     ▼
            Feature Engineering
                     │
                     ▼
             Decision Tree
                     │
              ┌──────┴──────┐
              ▼             ▼
          7-Day Demand   30-Day Demand
              │             │
              └──────┬──────┘
                     ▼
              Consumer Result
```

---

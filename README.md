PowerPlus --- Electricity Demand Forecasting

PowerPlus is a machine-learning project for predicting household
electricity consumption and forecasting future electricity demand using
historical electricity usage, household characteristics, weather
conditions, and calendar patterns.

The project currently covers the complete workflow from raw
electricity-data processing through feature engineering, ML baseline
modelling, and short-term demand forecasting.

Project Status

Stage                                       Status

Raw electricity data processing             Completed
Daily electricity consumption calculation   Completed
Household metadata processing               Completed
Weather data processing                     Completed
Data integration                            Completed
Data quality checks                         Completed
Feature engineering                         Completed
Model-ready dataset                         Completed
ML baseline modelling                       Completed
Decision Tree tuning                        Completed
7-day forecasting                           Completed
30-day forecasting                          Completed
Final application/dashboard                 Next stage

Problem Statement

Electricity demand varies across households, cities, seasons, weather
conditions, and appliance usage.

The goal of PowerPlus is to use historical household electricity
consumption together with household, weather, and calendar information
to estimate future electricity demand.

The project is designed around daily electricity consumption measured in
kWh.

Project Objectives

The main objectives are to:

Convert raw electricity measurements into daily electricity
consumption.

Combine electricity data with household metadata.

Integrate city-wise weather information.

Perform data-quality checks before modelling.

Engineer historical demand, weather, household, and calendar
features.

Build a leakage-safe machine-learning baseline.

Compare ML performance with simple forecasting baselines.

Forecast electricity demand for the next 7 and 30 days.

Save the trained model and evaluation results for later application
use.

Data Sources

PowerPlus uses three main data sources.

1. Electricity Data

The electricity data is stored city-wise:

city-wise_house_dataset/
├── Islamabad/
├── Karachi/
├── Lahore/
├── Multan/
├── Peshawar/
└── Skardu/

The raw electricity files contain time-based electricity usage
measurements.

The electricity readings are converted from minute-level power
measurements in kW into daily energy consumption in kWh.

The daily calculation used in the preprocessing notebook is:

Daily Electricity (kWh)
= Sum of minute-level power readings (kW) / 60

The resulting modelling target is:

electricity_kwh

2. Household Metadata

Household-level information is taken from:

metadata_ultimate.xlsx

The metadata includes information such as:

Number of residents

Children, adults, and seniors

Property area

Covered area

Number of floors

Construction year

Ceiling and roof information

Number of rooms

Kitchen

Washrooms

Air conditioners

Refrigerators

Washing machines

Fans

Water pumps

Electric cookers

Electric heaters

Microwave ovens

Geysers

UPS

Other electronic devices

This information provides household characteristics that can help
explain differences in electricity demand.

3. Weather Data

Historical weather data is available city-wise:

weather_dataset/
├── Islamabad.csv
├── Karachi.csv
├── Lahore.csv
├── Multan.csv
├── Peshawar.csv
└── Skardu.csv

Weather variables used in the project include:

Temperature

Humidity

Dew

Precipitation

Wind speed

Wind direction

Pressure

Solar radiation

Solar energy

UV index

The weather data is aggregated to daily level before integration with
electricity data.

Historical weather data is used in this project. OpenWeatherMap API is
not required for the current preprocessing workflow.

Data Processing Pipeline

The preprocessing workflow follows this sequence:

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
Feature Engineering
        ↓
Model-Ready Dataset

Electricity Data Processing

The electricity-processing notebook:

Finds the city-wise electricity folders.

Reads the electricity CSV files.

Detects the relevant datetime and usage columns.

Standardizes household and city identifiers.

Converts timestamps to datetime.

Converts electricity usage to numeric form.

Removes invalid readings.

Removes duplicate timestamps.

Aggregates electricity measurements to daily level.

Calculates daily kWh and coverage information.

Saves the processed daily electricity dataset.

The daily electricity dataset also keeps supporting measurements such
as:

Number of readings

Average power

Maximum power

Minimum power

Expected readings

Coverage percentage

Low-coverage flag

These fields are useful for data-quality analysis.

Household Metadata Processing

Household metadata is cleaned and standardized before merging with the
daily electricity data.

The metadata is joined using the household and city identifiers.

The resulting dataset combines:

Household
+
City
+
Household characteristics
+
Appliances
+
Daily electricity consumption

This allows the model to learn differences between households rather
than relying only on historical demand.

Weather Processing

The city-wise weather files are converted to daily-level features.

Daily aggregation includes:

Mean temperature

Mean humidity

Mean dew

Total precipitation

Mean wind speed

Mean wind direction

Mean pressure

Mean solar radiation

Total solar energy

Mean/max UV-related information where available

The resulting weather data is merged with electricity data using:

City + Date

Data Integration

After processing the three sources, the project creates an integrated
daily dataset containing:

Electricity
+
Household Metadata
+
Weather
+
Calendar
+
Historical Demand Features

The feature-engineering notebook saved the master merged dataset as:

processed_data/powerplus_daily_merged.csv

The model dataset was saved as:

processed_data/powerplus_model_data.csv

The model-ready dataset used for the ML baseline contained:

19,181 rows
91 columns
6 cities
59 households

The date range used in that model-ready dataset was:

2023-08-15 to 2024-11-27

The modelling target was:

electricity_kwh

Feature Engineering

Feature engineering was performed to provide the model with information
about previous demand, household characteristics, weather, and calendar
patterns.

Historical Demand Features

Lag features were created for:

lag_1_day_kwh
lag_2_day_kwh
lag_3_day_kwh
lag_7_day_kwh
lag_14_day_kwh
lag_30_day_kwh

Rolling demand features included:

rolling_3_day_avg_kwh
rolling_7_day_avg_kwh
rolling_14_day_avg_kwh
rolling_30_day_avg_kwh

These features allow the model to use recent consumption history.

Calendar Features

Calendar features include:

Year

Month

Day

Day of week

Week of year

Day of year

Weekend indicator

Season

These features help capture recurring calendar and seasonal patterns.

Household Features

Household and appliance information is retained as predictive
information, including:

Residents

Property characteristics

Building age

Rooms

Air conditioners

Refrigerators

Fans

Water pumps

Electric appliances

Other electronic devices

A derived house_age feature and total_appliance_count were also
included.

Leakage Prevention

Leakage prevention is an important part of the modelling workflow.

Same-day electricity measurement fields such as:

readings
avg_power_kw
max_power_kw
min_power_kw
coverage_pct

were not used as predictive inputs for forecasting the target because
these values are derived from the electricity observation for the day
being predicted.

Using them would allow information from the prediction day to enter the
model.

The modelling workflow therefore focuses on information that would be
available when making a forecast.

Train/Test Strategy

Because electricity demand is a time-dependent problem, the ML notebook
uses a chronological train/test split rather than a random split.

This prevents future observations from being used to train the model
before earlier observations are evaluated.

The preprocessing pipeline also uses:

ColumnTransformer
Pipeline
OneHotEncoder
SimpleImputer

to handle categorical and numerical features consistently.

ML Baseline

The first machine-learning model is a:

DecisionTreeRegressor

The Decision Tree was selected as the initial nonlinear regression model
because it can capture relationships between electricity demand and
household, weather, calendar, and historical-demand features.

The model was evaluated using:

MAE --- Mean Absolute Error

RMSE --- Root Mean Squared Error

R² --- Coefficient of Determination

Baseline Comparison

The ML notebook compares the Decision Tree against simple forecasting
baselines.

The evaluated baselines were:

Training Mean

Previous Day (lag_1)

Previous Week (lag_7)

Tuned Decision Tree

The recorded test results were:

Model                            MAE       RMSE          R²

Previous Day (lag_1)      0.091112   0.700165    0.887494
Decision Tree --- Tuned     0.102742   0.765637    0.865470
Previous Week (lag_7)     0.138870   1.107834    0.718341
Training Mean               1.797734   2.446776   -0.373924

For this evaluation, the Previous Day (lag_1) baseline achieved the
lowest MAE.

This is an important result: a simple previous-day forecasting strategy
performed better than the tuned Decision Tree on the recorded test set.

Therefore, the Decision Tree should not automatically be considered the
best forecasting method simply because it is an ML model.

Decision Tree Tuning

Important Decision Tree hyperparameters were tuned using chronological
validation.

The purpose of tuning was to control tree complexity and improve
generalization.

The tuning process focused on parameters such as:

max_depth

min_samples_split

min_samples_leaf

The tuned Decision Tree was then evaluated on the held-out test period.

Forecasting

The ML notebook also implements recursive forecasting.

7-Day Forecast

The forecasting workflow can generate a recursive:

7-day electricity demand forecast

The model uses previous predictions as historical inputs for subsequent
forecast days.

30-Day Forecast

The same recursive approach is extended to:

30-day electricity demand forecast

This provides a longer forecast horizon for future electricity-demand
planning.

Future Weather Limitation

The current dataset contains historical weather, not actual future
weather forecasts.

Therefore, future-weather handling works in two ways:

Option 1 --- Future Weather Input

If a future-weather dataset is supplied, the forecasting functions can
use it.

Option 2 --- Historical Seasonal Proxy

If future weather is not supplied, the notebook can create a historical
seasonal weather proxy for demonstration.

The historical seasonal proxy is not a real weather forecast and
should not be presented as one.

Model Outputs

The ML notebook is designed to save:

Trained model pipeline

Model metrics

Feature information

Forecast outputs

Comparison results

These outputs can later be used by the final application/dashboard.

Project Structure

A simplified project structure is:

Project-Electricity-Demand-Forecasting/
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
├── PowerPlus_ML_Baseline_and_Forecasting.ipynb
└── README.md

Technologies Used

Python

Pandas

NumPy

Matplotlib

Scikit-learn

Joblib

Jupyter Notebook

VS Code

Main Python Libraries

pandas
numpy
matplotlib
scikit-learn
joblib

How to Run

1. Clone the repository

git clone <your-repository-url>
cd Project-Electricity-Demand-Forecasting

2. Install dependencies

pip install pandas numpy matplotlib scikit-learn joblib openpyxl jupyter

3. Run the notebooks in order

First run:

PowerPlus_Data_Processing_Feature_Engineering.ipynb

Then run:

PowerPlus_ML_Baseline_and_Forecasting.ipynb

The second notebook depends on the processed/model-ready data generated
by the previous workflow.

Key Findings

The current ML evaluation produced several useful findings:

Historical electricity demand is strongly useful for forecasting.

The previous-day demand (lag_1) is a strong baseline.

The previous-day baseline achieved lower MAE than the tuned Decision
Tree on the recorded test set.

The previous-week baseline performed worse than the previous-day
baseline.

The training-mean baseline performed substantially worse than the
time-series baselines.

Household, weather, calendar, and historical-demand features are
available for more advanced modelling.

Forecasting must avoid same-day target leakage.

Future weather availability is an important consideration for
real-world forecasting.

Current Limitations

The current project has several limitations:

The available weather data is historical rather than a genuine
future weather forecast.

The current Decision Tree did not outperform the simple previous-day
baseline on the recorded test evaluation.

Longer recursive forecasts can accumulate prediction errors.

Household electricity behaviour can vary considerably between
households.

The current dataset covers a limited historical period compared with
long-term grid datasets.

These limitations should be considered before deploying the forecasting
system in a production environment.

Next Development Stage

The next stage of PowerPlus can focus on:

Comparing additional regression/time-series models.

Improving forecasting accuracy.

Testing stronger feature-selection strategies.

Evaluating models across individual cities and households.

Improving 7-day and 30-day forecast reliability.

Building the electricity bill calculator.

Integrating the trained model into the final application/dashboard.

Team Workflow

The PowerPlus project is being developed as a team project with
responsibilities covering:

Electricity data processing

Household metadata

Weather processing

Data integration

EDA and feature engineering

Train/test modelling

Consumption estimation

7/30-day forecasting

Bill calculation

Final application/dashboard

Conclusion

PowerPlus establishes an end-to-end foundation for household electricity
demand forecasting.

The project transforms raw electricity measurements into daily kWh
consumption, integrates household and weather information, creates
historical demand and calendar features, and evaluates machine-learning
forecasting against simple time-series baselines.

At the current milestone, the project has completed data processing,
feature engineering, ML baseline modelling, Decision Tree tuning, and
recursive 7-day/30-day forecasting.

The most important current modelling result is that the previous-day
demand baseline outperformed the tuned Decision Tree on the recorded
test set, demonstrating why simple forecasting baselines are essential
when evaluating machine-learning models.

The next stage is to improve the forecasting approach and integrate the
modelling pipeline into the final PowerPlus application.

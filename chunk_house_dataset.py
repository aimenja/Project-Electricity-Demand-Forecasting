import pandas as pd

file_path = r"D:\Project-Electricity-Demand-Forecasting\metadata_ultimate.xlsx"

metadata = pd.read_excel(file_path)

print("Shape:", metadata.shape)

print("\nColumns:")
print(metadata.columns.tolist())

print("\nFirst 5 rows:")
print(metadata.head())

print("\nData Types:")
print(metadata.dtypes)

print("\nMissing Values:")
print(metadata.isnull().sum())

print("\nUnique Values:")
for col in metadata.columns:
    print(f"\n{col}:")
    print(metadata[col].unique()[:20])


"""
import pandas as pd

file_path = r"D:\Project-Electricity-Demand-Forecasting\processed_data\daily_electricity_dataset.csv"

df_electricity = pd.read_csv(file_path)

print("Shape:", df_electricity.shape)
print("\nColumns:")
print(df_electricity.columns.tolist())

print("\nFirst 5 rows:")
print(df_electricity.head())

print("\nData types:")
print(df_electricity.dtypes)

print("\nMissing values:")
print(df_electricity.isnull().sum())

print("\nDate range:")
print("Start:", df_electricity["date"].min())
print("End:", df_electricity["date"].max())

print(df_electricity["Usage_kWh"].describe())

df_electricity = df_electricity.rename(
    columns={"Usage_kWh": "Electricity_Consumption_kWh"}
)

print(df_electricity["Electricity_Consumption_kWh"].describe())


df_electricity = df_electricity.rename(
    columns={"Usage_kWh": "Electricity_Consumption_kWh"}
)

print(df_electricity["Electricity_Consumption_kWh"].describe())

"""
'''
import pandas as pd
import os
import glob


# ============================================================
# 1. PATHS
# ============================================================

data_path = r"D:\Project-Electricity-Demand-Forecasting\city-wise_house_dataset"

output_path = r"D:\Project-Electricity-Demand-Forecasting\processed_data"

os.makedirs(output_path, exist_ok=True)


# ============================================================
# 2. FIND ALL CSV FILES
# ============================================================

files = glob.glob(
    os.path.join(data_path, "**", "*.csv"),
    recursive=True
)

# Don't process files inside processed_data
files = [
    f for f in files
    if os.path.abspath(output_path).lower()
    not in os.path.abspath(f).lower()
]

print(f"Found {len(files)} CSV files.")


# ============================================================
# 3. PROCESS EACH HOUSE
# ============================================================

all_daily_data = []


for input_file in files:

    filename = os.path.basename(input_file)

    house_name = os.path.splitext(filename)[0]

    # City = parent folder name
    city = os.path.basename(
        os.path.dirname(input_file)
    )

    print("\n" + "=" * 60)
    print(f"Processing: {city} - {house_name}")
    print("=" * 60)


    # --------------------------------------------------------
    # Read only the columns that actually exist
    # --------------------------------------------------------

    sample = pd.read_csv(
        input_file,
        nrows=5
    )

    available_columns = sample.columns.tolist()

    numeric_columns = [
        col for col in available_columns
        if col != "datetime"
    ]

    print("Columns:", available_columns)


    # --------------------------------------------------------
    # Store hourly results from chunks
    # --------------------------------------------------------

    hourly_chunks = []


    # --------------------------------------------------------
    # Read large file in chunks
    # --------------------------------------------------------

    for chunk_number, chunk in enumerate(
        pd.read_csv(
            input_file,
            chunksize=50000
        ),
        start=1
    ):

        print(
            f"  Chunk {chunk_number}: "
            f"{len(chunk):,} rows"
        )


        # ----------------------------------------------------
        # Convert datetime
        # ----------------------------------------------------

        chunk["datetime"] = pd.to_datetime(
            chunk["datetime"],
            errors="coerce"
        )


        # ----------------------------------------------------
        # Convert numeric columns
        # ----------------------------------------------------

        for col in numeric_columns:

            chunk[col] = pd.to_numeric(
                chunk[col],
                errors="coerce"
            )


        # ----------------------------------------------------
        # Remove invalid datetime
        # ----------------------------------------------------

        chunk = chunk.dropna(
            subset=["datetime"]
        )


        # ----------------------------------------------------
        # Set datetime as index
        # ----------------------------------------------------

        chunk = chunk.set_index("datetime")


        # ----------------------------------------------------
        # HOURLY AGGREGATION
        #
        # Numeric power columns → hourly mean
        # ----------------------------------------------------

        hourly = (
            chunk[numeric_columns]
            .resample("1h")
            .mean()
        )


        hourly_chunks.append(hourly)


    # ========================================================
    # 4. COMBINE HOURLY CHUNKS
    # ========================================================

    hourly_data = pd.concat(
        hourly_chunks
    )


    # ========================================================
    # 5. IMPORTANT
    #
    # A single hour can appear in two chunks.
    # Combine those duplicate hours correctly.
    # ========================================================

    hourly_data = (
        hourly_data
        .groupby(hourly_data.index)
        .mean()
    )


    # ========================================================
    # 6. DAILY ENERGY
    #
    # Hourly average kW × 1 hour = kWh
    #
    # Therefore:
    # daily kWh = sum of hourly kW
    # ========================================================

    daily_data = (
        hourly_data
        .resample("1D")
        .sum(min_count=1)
    )


    # ========================================================
    # 7. RENAME COLUMNS
    # ========================================================

    rename_dict = {}

    for col in daily_data.columns:

        rename_dict[col] = (
            col.replace(" (kW)", "")
               + "_kWh"
        )

    daily_data = daily_data.rename(
        columns=rename_dict
    )


    # ========================================================
    # 8. ADD CITY + HOUSE
    # ========================================================

    daily_data["City"] = city

    daily_data["House"] = house_name


    # ========================================================
    # 9. RESET INDEX
    # ========================================================

    daily_data = daily_data.reset_index()

    daily_data = daily_data.rename(
        columns={
            "datetime": "date"
        }
    )


    # ========================================================
    # 10. STORE RESULT
    # ========================================================

    all_daily_data.append(
        daily_data
    )


    print(
        f"  ✓ Daily records created: "
        f"{len(daily_data):,}"
    )


# ============================================================
# 11. COMBINE ALL HOUSES
# ============================================================

final_daily_dataset = pd.concat(
    all_daily_data,
    ignore_index=True,
    sort=False
)


# ============================================================
# 12. SORT
# ============================================================

final_daily_dataset = final_daily_dataset.sort_values(
    ["City", "House", "date"]
).reset_index(drop=True)


# ============================================================
# 13. SAVE ONE FILE
# ============================================================

output_file = os.path.join(
    output_path,
    "daily_electricity_dataset.csv"
)

final_daily_dataset.to_csv(
    output_file,
    index=False
)


# ============================================================
# 14. FINAL CHECK
# ============================================================

print("\n" + "=" * 60)
print("PROCESSING COMPLETE")
print("=" * 60)

print(
    "Final dataset shape:",
    final_daily_dataset.shape
)

print("\nColumns:")
print(final_daily_dataset.columns.tolist())

print("\nFirst 5 rows:")
print(final_daily_dataset.head())

print("\nMissing values:")
print(final_daily_dataset.isnull().sum())

print("\nSaved to:")
print(output_file)
'''
'''
import pandas as pd
import os
import glob

# Main dataset folder
data_path = r"D:\Project-Electricity-Demand-Forecasting\city-wise_house_dataset"

# Folder for chunked files
output_path = r"D:\Project-Electricity-Demand-Forecasting\city-wise_house_dataset\chunks"

os.makedirs(output_path, exist_ok=True)

# Find CSV files inside all city folders
files = glob.glob(
    os.path.join(data_path, "**", "*.csv"),
    recursive=True
)

# Don't process files from the chunks folder
files = [
    file for file in files
    if output_path.lower() not in os.path.abspath(file).lower()
]

print(f"Found {len(files)} CSV files.")

if len(files) == 0:

    print("❌ No CSV files found.")

else:

    for input_file in files:

        filename = os.path.basename(input_file)

        name, extension = os.path.splitext(filename)

        print(f"\nProcessing: {filename}")

        # Read CSV in chunks of 50,000 rows
        chunks = pd.read_csv(
            input_file,
            chunksize=50000
        )

        for part_number, chunk in enumerate(chunks, start=1):

            output_file = os.path.join(
                output_path,
                f"{name}_{part_number:02d}.csv"
            )

            chunk.to_csv(
                output_file,
                index=False
            )

            print(
                f"Saved: {name}_{part_number:02d}.csv "
                f"| Rows: {len(chunk)}"
            )

    print("\n All files processed successfully.")
    '''
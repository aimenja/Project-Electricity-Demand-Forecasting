import pandas as pd
import os
import glob


cities = ["Islamabad", 'Lahore', "Karachi", "Peshawar", "Multan", "Sakardu"]

data_path = r"D:\Project-Electricity-Demand-Forecasting\city-wise_house_dataset\city-wise_house_dataset"
output_path = r"D:\Project-Electricity-Demand-Forecasting\city-wise_house_dataset\chunks"

os.makedirs(output_path, exist_ok=True)

# Find every CSV file in the raw data folder
files = glob.glob(os.path.join(data_path, "*.csv"))

for input_file in files:

    filename = os.path.basename(input_file)
    name, extension = os.path.splitext(filename)

    print(f"\nProcessing: {filename}")

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
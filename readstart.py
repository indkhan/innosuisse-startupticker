import pandas as pd

# Path to data
file_startupticker = "Data-startupticker.xlsx"

# Mapping of the sheets to treat
sheets_to_process = {
    "startupticker_companies": (file_startupticker, "Companies", "Company description"),
    "startupticker_deals": (file_startupticker, "Deals", "Deal description"),
}


def load_startup_data():
    data = {}

    for table_name, (
        file_path,
        sheet_name,
        description_col,
    ) in sheets_to_process.items():
        # Load the Excel sheet
        df = pd.read_excel(file_path, sheet_name=sheet_name)

        # Store the DataFrame
        data[table_name] = df

        # Display basic information about the data
        print(f"\n=== {table_name} ===")
        print("Data Shape:", df.shape)
        print("Columns:", df.columns.tolist())
        print("First few rows:")
        print(df.head())
        print("\n")

    return data


if __name__ == "__main__":
    data = load_startup_data()

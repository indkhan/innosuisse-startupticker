import pandas as pd
import os
import numpy as np


def convert_excel_to_csv():
    """Convert Excel sheets to CSV files and clean the data"""
    print("Converting Excel sheets to CSV...")

    # Read the Excel file
    excel_file = "Data-startupticker.xlsx"

    # Read all sheets
    xls = pd.ExcelFile(excel_file)
    print(f"Found sheets: {xls.sheet_names}")

    # Create a directory for CSV files if it doesn't exist
    os.makedirs("data_csv", exist_ok=True)

    # Convert each sheet to CSV
    for sheet_name in xls.sheet_names:
        if sheet_name in ["Companies", "Deals"]:  # Only process main data sheets
            print(f"\nConverting sheet: {sheet_name}")
            df = pd.read_excel(excel_file, sheet_name=sheet_name)

            # Clean column names - remove extra spaces and special characters
            df.columns = [col.strip() for col in df.columns]

            # Replace empty strings with NaN
            df = df.replace("", np.nan)

            # Drop rows where all columns are NaN
            df = df.dropna(how="all")

            # Clean string data - strip whitespace
            for col in df.select_dtypes(include=["object"]).columns:
                df[col] = df[col].astype(str).str.strip()
                # Replace 'nan' strings with empty strings
                df[col] = df[col].replace("nan", "")

            # Save to CSV
            csv_file = f"data_csv/{sheet_name.lower()}.csv"
            df.to_csv(csv_file, index=False)
            print(f"Saved {csv_file}")

            # Display sample data
            print(f"\nColumns in {sheet_name} ({len(df.columns)}):")
            print(df.columns.tolist())
            print(f"Total rows: {len(df)}")
            print("\nSample data:")
            print(df.head(2).to_string())

    print("\nConversion complete. CSV files saved to data_csv/ directory.")


if __name__ == "__main__":
    convert_excel_to_csv()

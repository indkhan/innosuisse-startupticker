import pandas as pd

# Load the Excel file
print("Loading Excel file...")
df = pd.read_excel("Data-startupticker.xlsx")

# Print column names
print("\nColumns in the Excel file:")
print(df.columns.tolist())

# Print data types
print("\nData types:")
print(df.dtypes)

# Print first row
print("\nFirst row sample:")
print(df.iloc[0])

# Check for null values
print("\nNull value counts per column:")
print(df.isnull().sum()) 
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import os


class StartupDataLoader:
    def __init__(self, data_dir: str = None):
        # Get the absolute path to the project root
        self.project_root = Path(data_dir) if data_dir else Path(os.getcwd())
        self.data_dir = self.project_root
        self.startupticker_df = None
        self.crunchbase_df = None

    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load both Startupticker and Crunchbase datasets"""
        try:
            # Load Startupticker data
            startupticker_path = self.data_dir / "Data-startupticker.xlsx"
            print(f"Looking for Startupticker data at: {startupticker_path}")
            if not startupticker_path.exists():
                raise FileNotFoundError(
                    f"Startupticker data file not found at: {startupticker_path}"
                )
            self.startupticker_df = pd.read_excel(startupticker_path)

            # Load Crunchbase data
            crunchbase_path = self.data_dir / "Data-crunchbase.xlsx"
            print(f"Looking for Crunchbase data at: {crunchbase_path}")
            if not crunchbase_path.exists():
                raise FileNotFoundError(
                    f"Crunchbase data file not found at: {crunchbase_path}"
                )
            self.crunchbase_df = pd.read_excel(crunchbase_path)

            return self.startupticker_df, self.crunchbase_df
        except Exception as e:
            print(f"Error loading data: {e}")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Project root: {self.project_root}")
            print(f"Data directory: {self.data_dir}")
            raise

    def preprocess_data(self) -> pd.DataFrame:
        """Preprocess and combine datasets"""
        if self.startupticker_df is None or self.crunchbase_df is None:
            self.load_data()

        # Clean Startupticker data
        startupticker_clean = self._clean_startupticker_data()

        # Clean Crunchbase data
        crunchbase_clean = self._clean_crunchbase_data()

        # Combine datasets
        combined_df = pd.concat(
            [startupticker_clean, crunchbase_clean], ignore_index=True
        )

        return combined_df

    def _clean_startupticker_data(self) -> pd.DataFrame:
        """Clean and standardize Startupticker data"""
        df = self.startupticker_df.copy()

        # Standardize column names
        df.columns = [col.lower().replace(" ", "_") for col in df.columns]

        # Handle missing values
        df = df.replace("", np.nan)

        # Convert date columns
        date_columns = ["founding_date", "last_funding_date"]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Convert numeric columns
        numeric_columns = ["funding_amount", "valuation"]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Clean location data
        if "location" in df.columns:
            df["location"] = df["location"].str.strip()
            df["location"] = df["location"].str.replace("Switzerland", "CH")
            df["location"] = df["location"].str.replace("Zürich", "Zurich")
            df["location"] = df["location"].str.replace("Genève", "Geneva")
            df["location"] = df["location"].str.replace("Lausanne", "Lausanne")

        # Clean industry data
        if "industry" in df.columns:
            df["industry"] = df["industry"].str.strip()
            df["industry"] = df["industry"].str.replace("AI", "Artificial Intelligence")
            df["industry"] = df["industry"].str.replace("FinTech", "Fintech")
            df["industry"] = df["industry"].str.replace("HealthTech", "Healthtech")

        return df

    def _clean_crunchbase_data(self) -> pd.DataFrame:
        """Clean and standardize Crunchbase data"""
        df = self.crunchbase_df.copy()

        # Standardize column names
        df.columns = [col.lower().replace(" ", "_") for col in df.columns]

        # Handle missing values
        df = df.replace("", np.nan)

        # Convert date columns
        date_columns = ["founded_date", "last_funding_date"]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Convert numeric columns
        numeric_columns = ["total_funding", "last_valuation"]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Clean location data
        if "location" in df.columns:
            df["location"] = df["location"].str.strip()
            df["location"] = df["location"].str.replace("Switzerland", "CH")
            df["location"] = df["location"].str.replace("Zürich", "Zurich")
            df["location"] = df["location"].str.replace("Genève", "Geneva")
            df["location"] = df["location"].str.replace("Lausanne", "Lausanne")

        # Clean industry data
        if "industry" in df.columns:
            df["industry"] = df["industry"].str.strip()
            df["industry"] = df["industry"].str.replace("AI", "Artificial Intelligence")
            df["industry"] = df["industry"].str.replace("FinTech", "Fintech")
            df["industry"] = df["industry"].str.replace("HealthTech", "Healthtech")

        return df

    def get_company_descriptions(self) -> Dict[str, str]:
        """Extract company descriptions for semantic search"""
        if self.startupticker_df is None or self.crunchbase_df is None:
            self.load_data()

        descriptions = {}

        # Extract from Startupticker
        for idx, row in self.startupticker_df.iterrows():
            # Create a description from available fields
            desc_parts = []
            if pd.notna(row.get("name")):
                desc_parts.append(f"Company: {row['name']}")
            if pd.notna(row.get("industry")):
                desc_parts.append(f"Industry: {row['industry']}")
            if pd.notna(row.get("location")):
                desc_parts.append(f"Location: {row['location']}")
            if pd.notna(row.get("founding_date")):
                desc_parts.append(
                    f"Founded: {row['founding_date'].strftime('%Y-%m-%d')}"
                )
            if pd.notna(row.get("funding_amount")):
                desc_parts.append(f"Funding: ${row['funding_amount']:,.2f}")
            if pd.notna(row.get("description")):
                desc_parts.append(f"Description: {row['description']}")

            # Join all parts to create a description
            description = ". ".join(desc_parts)
            if description:  # Only add if we have some information
                descriptions[f"startupticker_{idx}"] = description

        # Extract from Crunchbase
        for idx, row in self.crunchbase_df.iterrows():
            # Create a description from available fields
            desc_parts = []
            if pd.notna(row.get("name")):
                desc_parts.append(f"Company: {row['name']}")
            if pd.notna(row.get("industry")):
                desc_parts.append(f"Industry: {row['industry']}")
            if pd.notna(row.get("location")):
                desc_parts.append(f"Location: {row['location']}")
            if pd.notna(row.get("founded_date")):
                desc_parts.append(
                    f"Founded: {row['founded_date'].strftime('%Y-%m-%d')}"
                )
            if pd.notna(row.get("total_funding")):
                desc_parts.append(f"Funding: ${row['total_funding']:,.2f}")
            if pd.notna(row.get("description")):
                desc_parts.append(f"Description: {row['description']}")

            # Join all parts to create a description
            description = ". ".join(desc_parts)
            if description:  # Only add if we have some information
                descriptions[f"crunchbase_{idx}"] = description

        return descriptions

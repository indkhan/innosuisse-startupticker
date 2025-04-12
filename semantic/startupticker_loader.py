import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import os


class StartuptickerDataLoader:
    def __init__(self, data_dir: str = None):
        # Get the absolute path to the project root
        self.project_root = Path(data_dir) if data_dir else Path(os.getcwd())
        self.data_dir = (
            self.project_root / "data_csv"
        )  # Look for CSV files in data_csv directory
        self.data = {}

    def load_data(self) -> Dict[str, pd.DataFrame]:
        """Load Startupticker datasets from CSV files"""
        try:
            # Ensure data directory exists
            if not self.data_dir.exists():
                raise FileNotFoundError(
                    f"Data directory not found at: {self.data_dir}. Please run convert_to_csv.py first."
                )

            # Load Companies data
            companies_path = self.data_dir / "companies.csv"
            if companies_path.exists():
                print(f"Loading companies data from: {companies_path}")
                self.data["companies"] = pd.read_csv(companies_path)
                print(f"Loaded {len(self.data['companies'])} companies")
                print("Companies columns:", self.data["companies"].columns.tolist())

            # Load Deals data
            deals_path = self.data_dir / "deals.csv"
            if deals_path.exists():
                print(f"Loading deals data from: {deals_path}")
                self.data["deals"] = pd.read_csv(deals_path)
                print(f"Loaded {len(self.data['deals'])} deals")
                print("Deals columns:", self.data["deals"].columns.tolist())

            return self.data
        except Exception as e:
            print(f"Error loading data: {e}")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Project root: {self.project_root}")
            print(f"Data directory: {self.data_dir}")
            raise

    def _clean_companies_data(self) -> pd.DataFrame:
        """Clean and standardize Companies data"""
        df = self.data["companies"].copy()
        print("\nCleaning companies data:")
        print("Original columns:", df.columns.tolist())

        # Handle missing values
        df = df.replace("", np.nan)

        # Convert Year to datetime
        if "Year" in df.columns:
            df["founding_date"] = pd.to_datetime(
                df["Year"].astype(str), format="%Y", errors="coerce"
            )

        # Create location string
        if "City" in df.columns and "Canton" in df.columns:
            df["location"] = df.apply(
                lambda x: f"{x['City']}, {x['Canton']}"
                if pd.notna(x["City"]) and pd.notna(x["Canton"])
                else x["City"]
                if pd.notna(x["City"])
                else x["Canton"]
                if pd.notna(x["Canton"])
                else "",
                axis=1,
            )

        # Map columns to standardized names
        df = df.rename(
            columns={
                "Title": "name",
                "Industry": "industry",
                "Highlights": "description",
                "Funded": "funding_status",
            }
        )

        return df

    def _clean_deals_data(self) -> pd.DataFrame:
        """Clean and standardize Deals data"""
        if "deals" not in self.data:
            return pd.DataFrame()

        df = self.data["deals"].copy()
        print("\nCleaning deals data:")
        print("Original columns:", df.columns.tolist())

        # Handle missing values
        df = df.replace("", np.nan)

        return df

    def get_descriptions(self) -> Dict[str, str]:
        """Extract descriptions from both Companies and Deals for semantic search"""
        if not self.data:
            self.load_data()

        descriptions = {}

        # Extract from Companies
        if "companies" in self.data:
            companies_df = self._clean_companies_data()
            print(f"\nProcessing {len(companies_df)} companies")

            for idx, row in companies_df.iterrows():
                desc_parts = []

                # Always include name if available
                if pd.notna(row.get("Title")):
                    desc_parts.append(f"Company: {row['Title']}")

                # Add industry
                if pd.notna(row.get("Industry")):
                    desc_parts.append(f"Industry: {row['Industry']}")

                # Add location (city and canton)
                location_parts = []
                if pd.notna(row.get("City")):
                    location_parts.append(row["City"])
                if pd.notna(row.get("Canton")):
                    location_parts.append(row["Canton"])
                if location_parts:
                    desc_parts.append(f"Location: {', '.join(location_parts)}")

                # Add founding year
                if pd.notna(row.get("Year")):
                    desc_parts.append(f"Founded: {row['Year']}")

                # Add funding status
                if pd.notna(row.get("Funded")):
                    desc_parts.append(f"Funding Status: {row['Funded']}")

                # Add highlights/description
                if pd.notna(row.get("Highlights")):
                    desc_parts.append(f"Description: {row['Highlights']}")

                description = ". ".join(desc_parts)
                if description:
                    descriptions[f"company_{idx}"] = description
                    if idx < 2:  # Print first two descriptions for debugging
                        print(f"\nSample description {idx}:")
                        print(description)

        # Extract from Deals
        if "deals" in self.data:
            deals_df = self._clean_deals_data()
            print(f"\nProcessing {len(deals_df)} deals")

            for idx, row in deals_df.iterrows():
                desc_parts = []
                for col in deals_df.columns:
                    if pd.notna(row[col]):
                        desc_parts.append(f"{col}: {row[col]}")

                description = ". ".join(desc_parts)
                if description:
                    descriptions[f"deal_{idx}"] = description
                    if idx < 2:  # Print first two descriptions for debugging
                        print(f"\nSample description {idx}:")
                        print(description)

        print(f"\nTotal descriptions generated: {len(descriptions)}")
        return descriptions

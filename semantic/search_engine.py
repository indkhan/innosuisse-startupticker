from typing import List, Dict, Any, Optional
import pandas as pd
from startupticker_loader import StartuptickerDataLoader
from vector_store import StartupVectorStore
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv


class StartupSearchEngine:
    def __init__(self, data_dir: Optional[str] = None):
        load_dotenv()
        self.data_loader = StartuptickerDataLoader(data_dir)
        self.vector_store = StartupVectorStore()
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-001",
            temperature=0,
            convert_system_message_to_human=True,
        )

    def initialize(self):
        """Initialize the search engine by loading and processing data"""
        try:
            # Load data
            data = self.data_loader.load_data()
            print("Loaded data:", list(data.keys()))

            # Get descriptions from both companies and deals
            descriptions = self.data_loader.get_descriptions()
            print("Generated descriptions:", len(descriptions))

            if not descriptions:
                raise ValueError(
                    "No descriptions were generated from the data. Please check the data format and column names."
                )

            # Create metadata
            metadata = {}

            # Process companies metadata
            if "companies" in data:
                companies_df = data["companies"]
                print(f"Processing {len(companies_df)} companies")
                print(f"Companies columns: {companies_df.columns.tolist()}")
                for idx, row in companies_df.iterrows():
                    # Store all original columns in metadata
                    metadata_dict = {
                        "type": "company"  # Add type explicitly
                    }
                    # Add all columns from the dataframe
                    for col in companies_df.columns:
                        if pd.notna(row.get(col)):
                            metadata_dict[col] = str(row[col])

                    metadata[f"company_{idx}"] = metadata_dict

            # Process deals metadata
            if "deals" in data:
                deals_df = data["deals"]
                print(f"Processing {len(deals_df)} deals")
                print(f"Deals columns: {deals_df.columns.tolist()}")
                for idx, row in deals_df.iterrows():
                    # Store all original columns in metadata
                    metadata_dict = {
                        "type": "deal"  # Add type explicitly
                    }
                    # Add all columns from the dataframe
                    for col in deals_df.columns:
                        if pd.notna(row.get(col)):
                            metadata_dict[col] = str(row[col])

                    metadata[f"deal_{idx}"] = metadata_dict

            print(f"Created metadata for {len(metadata)} items")

            # Build vector store
            self.vector_store.build_index(descriptions, metadata)
            print("Successfully built vector store index")

        except Exception as e:
            print(f"Error during initialization: {str(e)}")
            raise

    def semantic_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search on startup data"""
        # First, use LLM to enhance the query
        enhanced_query = self._enhance_query(query)

        # Perform vector search
        results = self.vector_store.search(enhanced_query, k)

        # Post-process results
        processed_results = []
        for result in results:
            metadata = result["metadata"]
            # Pass through all metadata fields
            processed_result = {
                "similarity_score": result["score"],
                "description": result["text"],  # Add the matched text
            }
            # Add all metadata fields
            for key, value in metadata.items():
                processed_result[key] = value

            processed_results.append(processed_result)

        return processed_results

    def _enhance_query(self, query: str) -> str:
        """Use LLM to enhance the search query"""
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "human",
                    """You are a helpful assistant that enhances search queries for startup data. 
            Your task is to expand the query to include relevant terms and context while maintaining the original intent.
            
            Original query: {query}
            
            Please provide an enhanced version of this query that would be better for searching startup data.
            The enhanced query should:
            1. Maintain the original meaning
            2. Include relevant industry terms
            3. Include location information if relevant
            4. Include funding stage information if relevant
            5. Include technology terms if relevant
            
            Enhanced query:
            """,
                )
            ]
        )

        chain = prompt | self.llm
        result = chain.invoke({"query": query})

        return result.content

    def analyze_trends(self, query: str) -> Dict[str, Any]:
        """Analyze trends based on search results"""
        # Get relevant startups
        results = self.semantic_search(query, k=20)

        # Convert to DataFrame for analysis
        df = pd.DataFrame(results)

        # Check if 'type' column exists
        if "type" not in df.columns:
            print("Warning: 'type' column not found in results")
            print(f"Available columns: {df.columns.tolist()}")
            return {
                "industry_distribution": {},
                "location_distribution": {},
                "founding_trends": self._empty_founding_trends(),
                "deal_trends": self._empty_deal_trends(),
            }

        # Separate companies and deals
        companies_df = df[df["type"] == "company"]
        deals_df = df[df["type"] == "deal"]

        # Basic trend analysis
        trends = {}

        # Company trends
        if not companies_df.empty:
            # Industry distribution (use "Industry" column if available)
            industry_col = (
                "Industry" if "Industry" in companies_df.columns else "industry"
            )
            if industry_col in companies_df.columns:
                trends["industry_distribution"] = (
                    companies_df[industry_col].value_counts().to_dict()
                )
            else:
                trends["industry_distribution"] = {}

            # Location distribution
            # Try different possible location column names
            location_columns = ["Location", "location", "Canton", "City"]
            location_col = next(
                (col for col in location_columns if col in companies_df.columns), None
            )

            if location_col:
                trends["location_distribution"] = (
                    companies_df[location_col].value_counts().to_dict()
                )
            else:
                trends["location_distribution"] = {}

            # Founding trends
            trends["founding_trends"] = self._analyze_founding_trends(companies_df)
        else:
            trends["industry_distribution"] = {}
            trends["location_distribution"] = {}
            trends["founding_trends"] = self._empty_founding_trends()

        # Deal trends
        if not deals_df.empty:
            trends["deal_trends"] = self._analyze_deal_trends(deals_df)
        else:
            trends["deal_trends"] = self._empty_deal_trends()

        return trends

    def _empty_founding_trends(self) -> Dict[str, Any]:
        """Return empty founding trends structure"""
        return {
            "startups_per_year": {},
            "average_age": 0,
            "oldest_startup": None,
            "newest_startup": None,
            "total_startups": 0,
        }

    def _empty_deal_trends(self) -> Dict[str, Any]:
        """Return empty deal trends structure"""
        return {"deal_types": {}, "deals_by_year": {}, "total_deals": 0}

    def _analyze_founding_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze founding trends from search results"""
        # Try different possible year column names
        year_columns = ["Year", "year", "founding_date", "Founded"]
        year_col = next((col for col in year_columns if col in df.columns), None)

        if not year_col:
            return self._empty_founding_trends()

        # Convert Year to numeric, handling any errors
        df["year_numeric"] = pd.to_numeric(
            df[year_col].astype(str).str[:4], errors="coerce"
        )

        # Calculate startups per year
        startups_per_year = df["year_numeric"].value_counts().sort_index().to_dict()

        # Calculate statistics
        current_year = pd.Timestamp.now().year
        avg_age = (
            current_year - df["year_numeric"].mean()
            if not df["year_numeric"].empty
            else 0
        )

        return {
            "startups_per_year": startups_per_year,
            "average_age": round(avg_age, 1) if not pd.isna(avg_age) else 0,
            "oldest_startup": int(df["year_numeric"].min())
            if not df["year_numeric"].empty
            else None,
            "newest_startup": int(df["year_numeric"].max())
            if not df["year_numeric"].empty
            else None,
            "total_startups": len(df),
        }

    def _analyze_deal_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trends in deals data"""
        deal_trends = {"total_deals": len(df)}

        # Deal types
        deal_type_columns = ["deal_type", "Deal Type", "Type"]
        deal_type_col = next(
            (col for col in deal_type_columns if col in df.columns), None
        )

        if deal_type_col:
            deal_trends["deal_types"] = df[deal_type_col].value_counts().to_dict()
        else:
            deal_trends["deal_types"] = {}

        # Deal years
        date_columns = ["deal_date", "Deal Date", "Date"]
        date_col = next((col for col in date_columns if col in df.columns), None)

        if date_col:
            # Try to extract year from the date field
            try:
                df["deal_year"] = pd.to_datetime(df[date_col], errors="coerce").dt.year
                deal_trends["deals_by_year"] = (
                    df["deal_year"].value_counts().sort_index().to_dict()
                )
            except:
                deal_trends["deals_by_year"] = {}
        else:
            deal_trends["deals_by_year"] = {}

        return deal_trends

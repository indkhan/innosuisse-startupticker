from typing import List, Dict, Any, Optional
import pandas as pd
from semantic.data_loader import StartupDataLoader
from semantic.vector_store import StartupVectorStore
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv


class StartupSearchEngine:
    def __init__(self, data_dir: Optional[str] = None):
        load_dotenv()
        self.data_loader = StartupDataLoader(data_dir)
        self.vector_store = StartupVectorStore()
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-001",
            temperature=0,
            convert_system_message_to_human=True,
        )

    def initialize(self):
        """Initialize the search engine by loading and processing data"""
        # Load data
        startupticker_df, crunchbase_df = self.data_loader.load_data()

        # Get company descriptions
        descriptions = self.data_loader.get_company_descriptions()

        # Create metadata
        metadata = {}
        for idx, row in startupticker_df.iterrows():
            metadata[f"startupticker_{idx}"] = {
                "name": row.get("name", ""),
                "industry": row.get("industry", ""),
                "location": row.get("location", ""),
                "founding_date": row.get("founding_date", ""),
                "funding_amount": row.get("funding_amount", ""),
                "description": row.get("description", ""),
            }

        for idx, row in crunchbase_df.iterrows():
            metadata[f"crunchbase_{idx}"] = {
                "name": row.get("name", ""),
                "industry": row.get("industry", ""),
                "location": row.get("location", ""),
                "founding_date": row.get("founded_date", ""),
                "funding_amount": row.get("total_funding", ""),
                "description": row.get("description", ""),
            }

        # Build vector store
        self.vector_store.build_index(descriptions, metadata)

    def semantic_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search on startup data"""
        # First, use LLM to enhance the query
        enhanced_query = self._enhance_query(query)

        # Perform vector search
        results = self.vector_store.search(enhanced_query, k)

        # Post-process results
        processed_results = []
        for result in results:
            processed_result = {
                "name": result["metadata"].get("name", "Unknown"),
                "industry": result["metadata"].get("industry", "Unknown"),
                "location": result["metadata"].get("location", "Unknown"),
                "founding_date": result["metadata"].get("founding_date", "Unknown"),
                "funding_amount": result["metadata"].get("funding_amount", "Unknown"),
                "description": result["metadata"].get("description", result["text"]),
                "similarity_score": result["score"],
            }
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

        # Convert funding amounts to numeric
        df["funding_amount"] = pd.to_numeric(df["funding_amount"], errors="coerce")

        # Convert founding dates to datetime
        df["founding_date"] = pd.to_datetime(df["founding_date"], errors="coerce")

        # Basic trend analysis
        trends = {
            "industry_distribution": df["industry"].value_counts().to_dict(),
            "location_distribution": df["location"].value_counts().to_dict(),
            "funding_trends": self._analyze_funding_trends(df),
            "founding_trends": self._analyze_founding_trends(df),
            "industry_funding": self._analyze_industry_funding(df),
            "location_funding": self._analyze_location_funding(df),
        }

        return trends

    def _analyze_funding_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze funding trends from search results"""
        # Calculate basic statistics
        return {
            "total_funding": df["funding_amount"].sum(),
            "average_funding": df["funding_amount"].mean(),
            "median_funding": df["funding_amount"].median(),
            "max_funding": df["funding_amount"].max(),
            "min_funding": df["funding_amount"].min(),
            "funding_by_year": self._calculate_funding_by_year(df),
        }

    def _analyze_founding_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze founding trends from search results"""
        # Calculate startups per year
        df["founding_year"] = df["founding_date"].dt.year
        startups_per_year = df["founding_year"].value_counts().sort_index().to_dict()

        return {
            "startups_per_year": startups_per_year,
            "average_age": (pd.Timestamp.now().year - df["founding_year"]).mean(),
            "oldest_startup": df["founding_year"].min(),
            "newest_startup": df["founding_year"].max(),
        }

    def _analyze_industry_funding(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze funding by industry"""
        industry_funding = (
            df.groupby("industry")["funding_amount"]
            .agg(["sum", "mean", "count"])
            .to_dict("index")
        )

        return industry_funding

    def _analyze_location_funding(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze funding by location"""
        location_funding = (
            df.groupby("location")["funding_amount"]
            .agg(["sum", "mean", "count"])
            .to_dict("index")
        )

        return location_funding

    def _calculate_funding_by_year(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate total funding by year"""
        df["founding_year"] = df["founding_date"].dt.year
        funding_by_year = df.groupby("founding_year")["funding_amount"].sum().to_dict()

        return funding_by_year

import streamlit as st
from typing import Dict, Any, List
import pandas as pd
from search_engine import StartupSearchEngine
import os
from pathlib import Path

# Set page config
st.set_page_config(page_title="Startup Search Engine", page_icon="🚀", layout="wide")

# Initialize session state
if "search_engine" not in st.session_state:
    st.session_state.search_engine = None
if "initialized" not in st.session_state:
    st.session_state.initialized = False


def initialize_search_engine():
    """Initialize the search engine"""
    try:
        # Get the current working directory
        current_dir = os.getcwd()

        # Initialize search engine with the current directory
        search_engine = StartupSearchEngine(current_dir)
        search_engine.initialize()

        # Store in session state
        st.session_state.search_engine = search_engine
        st.session_state.initialized = True

        return True
    except Exception as e:
        st.error(f"Error initializing search engine: {str(e)}")
        return False


def display_search_results(results: List[Dict[str, Any]]):
    """Display search results in a nice format"""
    if not results:
        st.info("No results found. Try a different search query.")
        return

    # Check if 'type' column exists
    if not results or "type" not in results[0]:
        st.warning("Search results don't contain proper type information.")
        # Display as generic results
        for i, result in enumerate(results):
            with st.expander(
                f"Result {i + 1} (Score: {result['similarity_score']:.2f})"
            ):
                # Display all attributes
                for key, value in result.items():
                    if key not in ["similarity_score", "description", "type"]:
                        st.markdown(f"**{key}:** {value}")
                st.markdown("---")
                st.markdown(f"**Description:** {result['description']}")
        return

    # Separate companies and deals
    companies = [r for r in results if r.get("type") == "company"]
    deals = [r for r in results if r.get("type") == "deal"]

    # Display companies
    if companies:
        st.subheader("Companies")
        for i, result in enumerate(companies):
            # Use Title or name for the header if available
            company_name = result.get("Title", result.get("name", f"Company {i + 1}"))

            with st.expander(
                f"🏢 {company_name} (Score: {result['similarity_score']:.2f})"
            ):
                col1, col2 = st.columns(2)

                # Column 1: Industry, Location, Year
                with col1:
                    # Display Industry
                    if "Industry" in result:
                        st.markdown(f"**Industry:** {result['Industry']}")

                    # Display Location (City and/or Canton)
                    location_parts = []
                    if "City" in result:
                        location_parts.append(result["City"])
                    if "Canton" in result:
                        location_parts.append(result["Canton"])
                    if location_parts:
                        st.markdown(f"**Location:** {', '.join(location_parts)}")

                    # Display Year
                    if "Year" in result:
                        st.markdown(f"**Founded:** {result['Year']}")

                # Column 2: Other info
                with col2:
                    # Display Funding Status
                    if "Funded" in result:
                        st.markdown(f"**Funding Status:** {result['Funded']}")

                    # Add other important fields
                    for key, value in result.items():
                        if key not in [
                            "Title",
                            "Industry",
                            "City",
                            "Canton",
                            "Year",
                            "Funded",
                            "type",
                            "similarity_score",
                            "description",
                        ]:
                            st.markdown(f"**{key}:** {value}")

                    st.markdown("---")
                    # Display Description (from Highlights or description)
                    description = result.get(
                        "Highlights", result.get("description", "")
                    )
                    st.markdown(f"**Description:** {description}")

    # Display deals
    if deals:
        st.subheader("Deals")
        for i, result in enumerate(deals):
            # Get deal name
            deal_name = result.get("Company", result.get("name", f"Deal {i + 1}"))

            with st.expander(
                f"💰 {deal_name} (Score: {result['similarity_score']:.2f})"
            ):
                col1, col2 = st.columns(2)

                with col1:
                    # Display all available fields in first column
                    for key, value in result.items():
                        if key not in [
                            "Company",
                            "type",
                            "similarity_score",
                            "description",
                        ]:
                            st.markdown(f"**{key}:** {value}")

                with col2:
                    st.markdown("---")
                    # Display Description
                    description = result.get("description", "")
                    st.markdown(f"**Description:** {description}")

    # If no companies or deals found with the type field
    if not companies and not deals and results:
        st.warning("Results found but not categorized as companies or deals.")
        # Display as generic results
        for i, result in enumerate(results):
            with st.expander(
                f"Result {i + 1} (Score: {result['similarity_score']:.2f})"
            ):
                # Display all attributes
                for key, value in result.items():
                    if key not in ["similarity_score", "description"]:
                        st.markdown(f"**{key}:** {value}")
                st.markdown("---")
                st.markdown(f"**Description:** {result['description']}")


def display_trends(trends: Dict[str, Any]):
    """Display trend analysis results"""
    # Industry Distribution
    if trends["industry_distribution"]:
        st.subheader("Industry Distribution")
        industry_df = pd.DataFrame(
            list(trends["industry_distribution"].items()), columns=["Industry", "Count"]
        )
        st.bar_chart(industry_df.set_index("Industry"))

    # Location Distribution
    if trends["location_distribution"]:
        st.subheader("Location Distribution")
        location_df = pd.DataFrame(
            list(trends["location_distribution"].items()), columns=["Location", "Count"]
        )
        st.bar_chart(location_df.set_index("Location"))

    # Founding Trends
    founding_data = trends["founding_trends"]
    if founding_data["total_startups"] > 0:
        st.subheader("Founding Trends")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Average Age", f"{founding_data['average_age']:.1f} years")
        with col2:
            st.metric("Oldest Startup", str(founding_data["oldest_startup"]))
        with col3:
            st.metric("Newest Startup", str(founding_data["newest_startup"]))
        with col4:
            st.metric("Total Startups", founding_data["total_startups"])

        # Startups per Year
        if founding_data["startups_per_year"]:
            st.subheader("Startups Founded per Year")
            startups_per_year = pd.DataFrame(
                list(founding_data["startups_per_year"].items()),
                columns=["Year", "Count"],
            )
            st.line_chart(startups_per_year.set_index("Year"))

    # Deal Trends
    deal_data = trends["deal_trends"]
    if deal_data["total_deals"] > 0:
        st.subheader("Deal Analysis")

        # Deal Types
        if deal_data["deal_types"]:
            st.subheader("Deal Types Distribution")
            deal_types_df = pd.DataFrame(
                list(deal_data["deal_types"].items()), columns=["Type", "Count"]
            )
            st.bar_chart(deal_types_df.set_index("Type"))

        # Deals by Year
        if deal_data["deals_by_year"]:
            st.subheader("Deals per Year")
            deals_by_year = pd.DataFrame(
                list(deal_data["deals_by_year"].items()), columns=["Year", "Count"]
            )
            st.line_chart(deals_by_year.set_index("Year"))

        st.metric("Total Deals", deal_data["total_deals"])


# Main app
def main():
    st.title("🚀 Startup Search Engine")

    # Initialize if not already done
    if not st.session_state.initialized:
        with st.spinner("Initializing search engine..."):
            if not initialize_search_engine():
                st.error(
                    "Failed to initialize search engine. Please check the error message above."
                )
                return

    # Search interface
    query = st.text_input(
        "Search for startups:", placeholder="e.g., AI startups in Zurich"
    )

    if query:
        # Perform search
        with st.spinner("Searching..."):
            results = st.session_state.search_engine.semantic_search(query)
            trends = st.session_state.search_engine.analyze_trends(query)

        # Display results
        st.subheader("Search Results")
        display_search_results(results)

        # Display trends
        st.subheader("Trend Analysis")
        display_trends(trends)


if __name__ == "__main__":
    main()

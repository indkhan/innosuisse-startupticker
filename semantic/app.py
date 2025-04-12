import streamlit as st
from typing import Dict, Any, List
import pandas as pd
from semantic.search_engine import StartupSearchEngine
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

    # Convert to DataFrame for better display
    df = pd.DataFrame(results)

    # Display results
    for _, row in df.iterrows():
        with st.expander(f"🚀 {row['name']} (Score: {row['similarity_score']:.2f})"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Industry:** {row['industry']}")
                st.markdown(f"**Location:** {row['location']}")
                st.markdown(f"**Founded:** {row['founding_date']}")
            with col2:
                st.markdown(
                    f"**Funding:** ${float(row['funding_amount']):,.2f}"
                    if pd.notna(row["funding_amount"])
                    else "**Funding:** Unknown"
                )
                st.markdown("---")
                st.markdown(f"**Description:** {row['description']}")


def display_trends(trends: Dict[str, Any]):
    """Display trend analysis results"""
    # Industry Distribution
    st.subheader("Industry Distribution")
    industry_df = pd.DataFrame(
        list(trends["industry_distribution"].items()), columns=["Industry", "Count"]
    )
    st.bar_chart(industry_df.set_index("Industry"))

    # Location Distribution
    st.subheader("Location Distribution")
    location_df = pd.DataFrame(
        list(trends["location_distribution"].items()), columns=["Location", "Count"]
    )
    st.bar_chart(location_df.set_index("Location"))

    # Funding Trends
    st.subheader("Funding Trends")
    funding_data = trends["funding_trends"]
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Funding", f"${funding_data['total_funding']:,.2f}")
    with col2:
        st.metric("Average Funding", f"${funding_data['average_funding']:,.2f}")
    with col3:
        st.metric("Max Funding", f"${funding_data['max_funding']:,.2f}")
    with col4:
        st.metric("Min Funding", f"${funding_data['min_funding']:,.2f}")

    # Funding by Year
    st.subheader("Funding by Year")
    funding_by_year = pd.DataFrame(
        list(funding_data["funding_by_year"].items()), columns=["Year", "Funding"]
    )
    st.line_chart(funding_by_year.set_index("Year"))

    # Industry Funding
    st.subheader("Industry Funding Analysis")
    industry_funding = pd.DataFrame(trends["industry_funding"]).T
    industry_funding.columns = [
        "Total Funding",
        "Average Funding",
        "Number of Startups",
    ]
    st.dataframe(industry_funding)

    # Location Funding
    st.subheader("Location Funding Analysis")
    location_funding = pd.DataFrame(trends["location_funding"]).T
    location_funding.columns = [
        "Total Funding",
        "Average Funding",
        "Number of Startups",
    ]
    st.dataframe(location_funding)

    # Founding Trends
    st.subheader("Founding Trends")
    founding_data = trends["founding_trends"]
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Average Age", f"{founding_data['average_age']:.1f} years")
    with col2:
        st.metric("Oldest Startup", founding_data["oldest_startup"])
    with col3:
        st.metric("Newest Startup", founding_data["newest_startup"])
    with col4:
        st.metric("Total Startups", sum(founding_data["startups_per_year"].values()))

    # Startups per Year
    st.subheader("Startups Founded per Year")
    startups_per_year = pd.DataFrame(
        list(founding_data["startups_per_year"].items()), columns=["Year", "Count"]
    )
    st.line_chart(startups_per_year.set_index("Year"))


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

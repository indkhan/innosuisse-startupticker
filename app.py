import streamlit as st
import json
from llm import process_query, chat_history
import pandas as pd
import matplotlib.pyplot as plt
import re
import os
from web_scrapper import download_sogc_data
import PyPDF2
import tempfile

st.set_page_config(
    page_title="Startup Funding SPARQL Query System", page_icon="📊", layout="wide"
)

st.title("Startup Funding Analysis")
st.subheader("Ask questions about Swiss startup funding data")

with st.sidebar:
    st.header("About")
    st.write(
        """
        This application allows you to query Swiss startup funding data using natural language.
        
        The system converts your questions into SPARQL queries and provides analysis of the results.
        
        **Example queries:**
        - Show funding trends in the cleantech industry
        - What are the top medtech companies by funding amount?
        - Compare funding between biotech and ICT industries
        - Which cantons have the most healthcare startups?
        - Compare SwissDrones to the cleantech market
        """
    )

    st.header("Available Industries")
    industries = [
        "cleantech",
        "biotech",
        "medtech",
        "healthcare IT",
        "ICT",
        "ICT (fintech)",
        "micro / nano",
        "Life-Sciences",
    ]
    st.write(", ".join(industries))


# Function to get UID from the database based on company name
def get_company_uid(company_name):
    # This is a placeholder function
    # In a real implementation, you would search your database for the UID
    # For demo purposes, we'll use a hardcoded mapping
    company_uid_map = {
        "swissdrones": "CHE-236.101.881",
        "climeworks": "CHE-215.350.964",
        # Add more mappings as needed
    }

    # Normalize company name for lookup
    normalized_name = company_name.lower().strip()

    # Check if we have a direct match
    for company, uid in company_uid_map.items():
        if company in normalized_name or normalized_name in company:
            return uid

    # Return a default UID if company not found
    return "CHE-215.350.964"  # Default to Climeworks as an example


# Function to extract text from PDF file
def extract_text_from_pdf(pdf_path):
    try:
        with open(pdf_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"


# Function to summarize PDF content using LLM
def summarize_pdf_content(text, company_name):
    # In a real implementation, you would call your LLM here
    # For demo purposes, we'll return a simple summary

    # Here you could use the same process_query function or a different LLM function
    # For now, we'll create a placeholder summary
    summary = f"""
    ## SOGC Registry Information for {company_name}
    
    The Swiss Official Gazette of Commerce (SOGC) report for this company includes:
    
    - Registration information and legal status
    - Company formation details
    - Management and board members
    - Official legal notices
    
    The full document contains {len(text)} characters of information from the official registry.
    """
    return summary


# Create a layout with two columns for the input and SOGC button
col1, col2 = st.columns([4, 1])

# Input for query in the first column
with col1:
    query = st.text_input(
        "Enter your question:",
        placeholder="e.g., Compare SwissDrones Operating AG to the cleantech industry",
    )

# SOGC button in the second column
with col2:
    sogc_button = st.button("Get SOGC Data")

# Handle SOGC button click
if sogc_button:
    if query:
        with st.spinner("Fetching SOGC data..."):
            # Extract company name from query
            # For a simple approach, just use the query itself
            company_name = query

            # Get UID for the company
            uid = get_company_uid(company_name)

            st.info(f"Searching SOGC registry for company UID: {uid}")

            # Create a temporary directory for downloads
            with tempfile.TemporaryDirectory() as download_dir:
                # Download SOGC data
                download_sogc_data(
                    uid=uid, output_format="pdf", download_dir=download_dir
                )

                # Check if the PDF was downloaded
                pdf_path = os.path.join(download_dir, f"{uid}.pdf")
                if os.path.exists(pdf_path):
                    # Extract text from PDF
                    pdf_text = extract_text_from_pdf(pdf_path)

                    # Summarize PDF content
                    summary = summarize_pdf_content(pdf_text, company_name)

                    # Display summary
                    st.subheader(f"SOGC Registry Information for '{company_name}'")
                    st.markdown(summary)

                    # Option to view raw PDF text
                    with st.expander("View raw PDF text"):
                        st.text(
                            pdf_text[:5000] + "..."
                            if len(pdf_text) > 5000
                            else pdf_text
                        )
                else:
                    st.error(
                        f"Failed to download SOGC data for {company_name} (UID: {uid})"
                    )
    else:
        st.warning("Please enter a company name or query first.")

# Process button
if st.button("Process Query") or query:
    if query:
        with st.spinner("Processing your query..."):
            # Process the query
            response = process_query(query)

            try:
                # Parse the response JSON
                response_data = json.loads(response)

                # Request all results from LLM.py, not just first 10
                if "query" in response_data:
                    total_results = response_data["total_results"]
                    st.session_state.total_results = total_results

                # Check if this is a comparison query
                is_comparison = response_data.get("is_comparison", False)

                # Create tabs for different views
                if is_comparison:
                    tab1, tab2, tab3, tab4 = st.tabs(
                        ["Analysis", "Comparison Chart", "Raw Results", "SPARQL Query"]
                    )
                else:
                    tab1, tab2, tab3, tab4 = st.tabs(
                        ["Analysis", "Visualization", "Raw Results", "SPARQL Query"]
                    )

                with tab1:
                    st.header("Analysis")
                    st.markdown(response_data["llm_analysis"])

                with tab2:
                    if is_comparison:
                        st.header("Company vs. Market Comparison")

                        # Get comparison data
                        comparison_data = response_data.get("comparison_data", {})

                        if (
                            comparison_data
                            and "companies" in comparison_data
                            and "market_trends" in comparison_data
                        ):
                            companies = comparison_data["companies"]
                            market_trends = comparison_data["market_trends"]

                            # Show company funding data
                            st.subheader("Company Funding Information")

                            # Create company summary table
                            company_summary = []
                            for company_name, company_data in companies.items():
                                company_summary.append(
                                    {
                                        "Company Name": company_name,
                                        "Industry": company_data.get(
                                            "industry", "Unknown"
                                        ),
                                        "Total Funding (CHF)": company_data.get(
                                            "total_funding", 0
                                        ),
                                        "Total Funding (Millions CHF)": company_data.get(
                                            "total_funding", 0
                                        )
                                        / 1000000,
                                        "Number of Rounds": len(
                                            company_data.get("funding_rounds", [])
                                        ),
                                        "Location": company_data.get(
                                            "location", "Unknown"
                                        ),
                                    }
                                )

                            if company_summary:
                                company_df = pd.DataFrame(company_summary)
                                st.dataframe(company_df, use_container_width=True)

                            # Plot company funding against industry trends
                            for company_name, company_data in companies.items():
                                if (
                                    company_data.get("industry")
                                    and company_data.get("industry") in market_trends
                                ):
                                    industry_name = company_data["industry"]
                                    industry_trends = market_trends[industry_name].get(
                                        "yearly_trends", []
                                    )

                                    if industry_trends and company_data.get(
                                        "funding_rounds"
                                    ):
                                        st.subheader(
                                            f"{company_name} vs. {industry_name} Industry"
                                        )

                                        # Create a year-based dictionary of company funding
                                        company_yearly_funding = {}
                                        for round_data in company_data[
                                            "funding_rounds"
                                        ]:
                                            if round_data.get("date"):
                                                year = str(round_data["date"])[:4]
                                                if year.isdigit() and len(year) == 4:
                                                    if (
                                                        year
                                                        not in company_yearly_funding
                                                    ):
                                                        company_yearly_funding[year] = 0
                                                    company_yearly_funding[year] += (
                                                        round_data.get("amount", 0)
                                                    )

                                        # Create dataframe for visualization
                                        industry_df = pd.DataFrame(industry_trends)

                                        # Plot comparison chart
                                        fig, ax1 = plt.subplots(figsize=(12, 6))

                                        # Industry total funding by year (bars)
                                        ax1.bar(
                                            industry_df["year"],
                                            industry_df["total_funding"],
                                            alpha=0.5,
                                            color="blue",
                                            label=f"{industry_name} Industry Total Funding",
                                        )
                                        ax1.set_xlabel("Year")
                                        ax1.set_ylabel(
                                            "Industry Funding (CHF)", color="blue"
                                        )
                                        ax1.tick_params(axis="y", labelcolor="blue")

                                        # Add company funding markers
                                        company_years = list(
                                            company_yearly_funding.keys()
                                        )
                                        company_amounts = [
                                            company_yearly_funding[year]
                                            for year in company_years
                                        ]

                                        if company_years:
                                            ax1.scatter(
                                                company_years,
                                                company_amounts,
                                                color="red",
                                                s=100,
                                                label=f"{company_name} Funding Rounds",
                                            )

                                            # Connect company funding points with lines
                                            ax1.plot(
                                                company_years,
                                                company_amounts,
                                                "r--",
                                                alpha=0.7,
                                            )

                                        # Create secondary y-axis for funding rounds count
                                        ax2 = ax1.twinx()
                                        ax2.plot(
                                            industry_df["year"],
                                            industry_df["funding_rounds"],
                                            color="green",
                                            marker="o",
                                            label="Industry Funding Rounds Count",
                                        )
                                        ax2.set_ylabel(
                                            "Number of Funding Rounds", color="green"
                                        )
                                        ax2.tick_params(axis="y", labelcolor="green")

                                        # Format y-axis labels in millions for funding
                                        ax1.yaxis.set_major_formatter(
                                            lambda x, pos: f"{x / 1000000:.1f}M"
                                        )

                                        # Combine legends
                                        lines1, labels1 = (
                                            ax1.get_legend_handles_labels()
                                        )
                                        lines2, labels2 = (
                                            ax2.get_legend_handles_labels()
                                        )
                                        ax1.legend(
                                            lines1 + lines2,
                                            labels1 + labels2,
                                            loc="upper left",
                                        )

                                        plt.title(
                                            f"{company_name} Funding vs. {industry_name} Industry Trends"
                                        )
                                        plt.grid(True, alpha=0.3)
                                        plt.xticks(rotation=45)
                                        st.pyplot(fig)

                                        # Create a table with market position metrics
                                        st.subheader(
                                            f"Market Position Metrics for {company_name}"
                                        )

                                        # Calculate company vs industry metrics
                                        total_industry_funding = market_trends[
                                            industry_name
                                        ].get("total_funding", 0)
                                        avg_round_size_industry = market_trends[
                                            industry_name
                                        ].get("avg_round_size", 0)
                                        total_companies = market_trends[
                                            industry_name
                                        ].get("total_companies", 0)

                                        company_total_funding = company_data.get(
                                            "total_funding", 0
                                        )
                                        company_rounds = len(
                                            company_data.get("funding_rounds", [])
                                        )
                                        avg_round_size_company = (
                                            company_total_funding / company_rounds
                                            if company_rounds > 0
                                            else 0
                                        )

                                        # Market share and other metrics
                                        market_share = (
                                            (
                                                company_total_funding
                                                / total_industry_funding
                                            )
                                            * 100
                                            if total_industry_funding > 0
                                            else 0
                                        )
                                        round_size_ratio = (
                                            (
                                                avg_round_size_company
                                                / avg_round_size_industry
                                            )
                                            * 100
                                            if avg_round_size_industry > 0
                                            else 0
                                        )

                                        metrics_df = pd.DataFrame(
                                            [
                                                {
                                                    "Metric": "Total Funding (Millions CHF)",
                                                    "Company Value": f"{company_total_funding / 1000000:.2f}M",
                                                    "Industry Average": f"{(total_industry_funding / total_companies) / 1000000:.2f}M"
                                                    if total_companies > 0
                                                    else "N/A",
                                                    "Market Share/Ratio": f"{market_share:.2f}%",
                                                },
                                                {
                                                    "Metric": "Average Round Size (Millions CHF)",
                                                    "Company Value": f"{avg_round_size_company / 1000000:.2f}M",
                                                    "Industry Average": f"{avg_round_size_industry / 1000000:.2f}M",
                                                    "Market Share/Ratio": f"{round_size_ratio:.2f}%",
                                                },
                                                {
                                                    "Metric": "Number of Funding Rounds",
                                                    "Company Value": f"{company_rounds}",
                                                    "Industry Average": f"{sum(year_data['funding_rounds'] for year_data in industry_trends) / total_companies:.2f}"
                                                    if total_companies > 0
                                                    else "N/A",
                                                    "Market Share/Ratio": "N/A",
                                                },
                                            ]
                                        )

                                        st.dataframe(
                                            metrics_df, use_container_width=True
                                        )

                                        # Show yearly details table
                                        st.subheader(
                                            f"Yearly Industry Trends for {industry_name}"
                                        )

                                        # Convert yearly trend data to a nice table
                                        yearly_trend_table = []
                                        for year_data in industry_trends:
                                            yearly_trend_table.append(
                                                {
                                                    "Year": year_data["year"],
                                                    "Total Funding (Millions CHF)": f"{year_data['total_funding'] / 1000000:.2f}M",
                                                    "Number of Rounds": year_data[
                                                        "funding_rounds"
                                                    ],
                                                    "Companies Active": year_data[
                                                        "companies_count"
                                                    ],
                                                    "Avg Round Size (Millions CHF)": f"{(year_data['total_funding'] / year_data['funding_rounds']) / 1000000:.2f}M"
                                                    if year_data["funding_rounds"] > 0
                                                    else "N/A",
                                                    "Company Funding This Year": f"{company_yearly_funding.get(year_data['year'], 0) / 1000000:.2f}M"
                                                    if year_data["year"]
                                                    in company_yearly_funding
                                                    else "None",
                                                }
                                            )

                                        yearly_df = pd.DataFrame(yearly_trend_table)
                                        st.dataframe(
                                            yearly_df, use_container_width=True
                                        )
                    else:
                        st.header("Visualizations")

                        # Check if this appears to be trend data with years
                        year_pattern = re.compile(r"20\d\d")

                        # Function to extract trend data from LLM analysis
                        def extract_trend_data(analysis_text):
                            years = []
                            funding_amounts = []

                            # Look for years followed by funding data
                            lines = analysis_text.split("\n")
                            for line in lines:
                                if year_pattern.search(line) and (
                                    "funding" in line.lower()
                                    or "amount" in line.lower()
                                    or "CHF" in line
                                    or "million" in line
                                ):
                                    # Try to extract year and amount
                                    year_match = year_pattern.search(line)
                                    if year_match:
                                        year = year_match.group(0)

                                        # Look for funding amount (numbers followed by M, million, or CHF)
                                        amount_pattern = re.compile(
                                            r"(\d+\.?\d*)\s*(million|M|CHF|million CHF)"
                                        )
                                        amount_match = amount_pattern.search(line)

                                        if amount_match:
                                            amount = float(amount_match.group(1))
                                            # If in millions, convert to absolute value
                                            if "million" in amount_match.group(
                                                2
                                            ) or "M" in amount_match.group(2):
                                                amount = amount * 1000000

                                            years.append(year)
                                            funding_amounts.append(amount)

                            return years, funding_amounts

                        # Extract yearly funding from the raw results if available
                        if (
                            "raw_results" in response_data
                            and len(response_data["raw_results"]) > 0
                        ):
                            # Check if raw results have date and amount
                            has_date = any(
                                "date" in item or "round_date" in item
                                for item in response_data["raw_results"]
                            )
                            has_amount = any(
                                "amount" in item
                                for item in response_data["raw_results"]
                            )

                            if has_date and has_amount:
                                # Process by extracting year from date
                                df = pd.DataFrame(response_data["raw_results"])

                                # Display message about data shown
                                st.info(
                                    f"Visualizing data from {len(df)} records out of {response_data['total_results']} total results."
                                )

                                # Determine which column has date info
                                date_col = (
                                    "date" if "date" in df.columns else "round_date"
                                )

                                # Extract year and convert amount to float where possible
                                yearly_data = {}

                                for _, row in df.iterrows():
                                    if (
                                        pd.notna(row[date_col])
                                        and row[date_col] != "None"
                                    ):
                                        year = str(row[date_col])[:4]  # Extract year

                                        if year.isdigit() and len(year) == 4:
                                            if year not in yearly_data:
                                                yearly_data[year] = 0

                                            # Add amount if available
                                            if (
                                                "amount" in row
                                                and pd.notna(row["amount"])
                                                and row["amount"] != "None"
                                            ):
                                                try:
                                                    amount = float(row["amount"])
                                                    yearly_data[year] += amount
                                                except ValueError:
                                                    pass

                                if yearly_data:
                                    years = list(yearly_data.keys())
                                    years.sort()
                                    funding_amounts = [
                                        yearly_data[year] for year in years
                                    ]

                                    fig, ax = plt.subplots(figsize=(10, 6))
                                    ax.bar(years, funding_amounts)
                                    ax.set_title("Funding by Year")
                                    ax.set_xlabel("Year")
                                    ax.set_ylabel("Amount (CHF)")

                                    # Format y-axis labels in millions
                                    ax.yaxis.set_major_formatter(
                                        lambda x, pos: f"{x / 1000000:.1f}M"
                                    )

                                    plt.xticks(rotation=45)
                                    st.pyplot(fig)

                                    # Create a table showing the data
                                    st.subheader("Yearly Funding Data")
                                    yearly_df = pd.DataFrame(
                                        {
                                            "Year": years,
                                            "Total Funding (CHF)": funding_amounts,
                                            "Total Funding (Millions CHF)": [
                                                amount / 1000000
                                                for amount in funding_amounts
                                            ],
                                        }
                                    )
                                    st.dataframe(yearly_df, use_container_width=True)
                                else:
                                    # If no structured data, try to extract from LLM analysis
                                    years, funding_amounts = extract_trend_data(
                                        response_data["llm_analysis"]
                                    )

                                    if years and funding_amounts:
                                        fig, ax = plt.subplots(figsize=(10, 6))
                                        ax.bar(years, funding_amounts)
                                        ax.set_title(
                                            "Funding by Year (Extracted from Analysis)"
                                        )
                                        ax.set_xlabel("Year")
                                        ax.set_ylabel("Amount (CHF)")

                                        # Format y-axis labels in millions
                                        ax.yaxis.set_major_formatter(
                                            lambda x, pos: f"{x / 1000000:.1f}M"
                                        )

                                        plt.xticks(rotation=45)
                                        st.pyplot(fig)
                                    else:
                                        st.info(
                                            "No time series data available for visualization."
                                        )
                            else:
                                st.info(
                                    "This query doesn't contain time series data that can be visualized."
                                )
                        else:
                            st.info("No results available for visualization.")

                with tab3:
                    st.header("Results")
                    st.write(f"Total results: {response_data['total_results']}")

                    # Convert results to dataframe if possible
                    if response_data["raw_results"]:
                        df = pd.DataFrame(response_data["raw_results"])

                        # Add pagination for large datasets
                        page_size = 50  # Show 50 rows per page
                        total_pages = (len(df) + page_size - 1) // page_size

                        if "page" not in st.session_state:
                            st.session_state.page = 0

                        def next_page():
                            st.session_state.page = min(
                                st.session_state.page + 1, total_pages - 1
                            )

                        def prev_page():
                            st.session_state.page = max(st.session_state.page - 1, 0)

                        # Display pagination controls
                        col1, col2, col3 = st.columns([1, 3, 1])
                        with col1:
                            if st.session_state.page > 0:
                                st.button("Previous", on_click=prev_page)
                        with col2:
                            if total_pages > 1:
                                st.write(
                                    f"Page {st.session_state.page + 1} of {total_pages}"
                                )
                        with col3:
                            if st.session_state.page < total_pages - 1:
                                st.button("Next", on_click=next_page)

                        # Display current page of data
                        start_idx = st.session_state.page * page_size
                        end_idx = min(start_idx + page_size, len(df))
                        st.dataframe(
                            df.iloc[start_idx:end_idx], use_container_width=True
                        )

                        # Add option to download full dataset
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="Download complete data as CSV",
                            data=csv,
                            file_name="query_results.csv",
                            mime="text/csv",
                        )
                    else:
                        st.write("No results found.")

                with tab4:
                    st.header("Generated SPARQL Query")
                    st.code(response_data["query"], language="sparql")

            except json.JSONDecodeError:
                st.error("Error processing the query. Please try again.")
                st.code(response)
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.code(response)
    else:
        st.info("Please enter a query.")

# Footer
st.markdown("---")
st.caption("Powered by Google Gemini 2.0 Flash")

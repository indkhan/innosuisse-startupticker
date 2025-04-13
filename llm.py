from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from rdflib import Graph, Namespace
import json
import os
import re

load_dotenv()

# Initialize RDF graph
graph = Graph()
graph.parse("startups_graph.ttl", format="turtle")

# Define namespaces
EX = Namespace("http://example.org/ontology#")
RES = Namespace("http://example.org/resource/")

# Initialize LLM
model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-001",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.0,
)

# Create system message for SPARQL generation
system_prompt = """You are an expert in GENERATING SPARQL QUERIES to extract data from an RDF graph.
Your PRIMARY RESPONSIBILITY is to CONVERT natural language questions into VALID SPARQL QUERIES.
DO NOT attempt to analyze data or provide insights in your initial response - just create a SPARQL query.

The graph uses the following ontology structure:

Namespaces:
- EX (http://example.org/ontology#) - for ontology terms
- RES (http://example.org/resource/) - for resource instances

Core Classes:
- Startup - Represents companies
- Industry - Represents industry classifications
- FundingEvent - Represents funding rounds
- Investor - Represents investors
- Canton - Represents Swiss regions
- City - Represents cities

Important Relationships:
- Startup hasIndustry Industry (connects companies to their industry)
- Startup hasFunding FundingEvent (connects companies to funding events)
- Startup foundedIn Year (year of founding)
- Startup hasLocation City/Canton (where the company is located) - NOT locatedIn
- FundingEvent amount (funding amount in CHF)
- FundingEvent type (funding type)
- FundingEvent phase (funding phase)
- FundingEvent investor Investor (links to investor)
- FundingEvent round_date (when the funding occurred) - NOT date
- City isIn Canton (connects cities to their canton/region)

SPARQL Query Guidelines:
1. For aggregations (SUM, COUNT, etc.), use GROUP BY and HAVING clauses
2. Put aggregations in the SELECT clause, not in BIND
3. Use HAVING for filtering on aggregated values
4. Always include proper PREFIX declarations
5. When selecting multiple variables, make sure to bind them properly in the SELECT clause
6. IMPORTANT: Make location information OPTIONAL in queries using 'OPTIONAL' clauses
7. For funding analysis, the ex:hasFunding relationship should be REQUIRED, not optional
8. Only make the funding properties (round_date, amount, phase) optional, not the main hasFunding relationship

IMPORTANT FACTS TO REMEMBER:
- Industry names are stored as lowercase (e.g., "cleantech" not "Cleantech")
- Funding amounts are stored in actual CHF (not millions). For example, 50 million CHF would be stored as 50000000
- The predicate to connect startups to industries is ex:hasIndustry
- The property for funding date is ex:round_date (NOT ex:date)
- The predicate for locations is ex:hasLocation (NOT ex:locatedIn)
- Location data might be missing for some companies - always make location patterns OPTIONAL
- Queries using generic patterns like ?otherAttribute ?otherAttributeValue may cause performance issues
- When data might be missing, use OPTIONAL patterns
- For trend analysis, select all relevant fields including dates and amounts

SAMPLE QUERY STRUCTURE FOR FUNDING ANALYSIS:
```
PREFIX ex: <http://example.org/ontology#>
PREFIX res: <http://example.org/resource/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?company_name ?date ?amount ?phase
WHERE {
    ?company a ex:Startup ;
            ex:name ?company_name ;
            ex:hasIndustry ?industry .
    ?industry ex:name "cleantech" .
    
    # Funding information - required when analyzing funding
    ?company ex:hasFunding ?funding .
    OPTIONAL { ?funding ex:round_date ?date }
    OPTIONAL { ?funding ex:amount ?amount }
    OPTIONAL { ?funding ex:phase ?phase }
    
    # Location info - always optional
    OPTIONAL { 
        ?company ex:hasLocation ?location .
        ?location ex:name ?location_name .
    }
}
ORDER BY ?date
```

YOUR RESPONSE MUST ONLY CONTAIN A VALID SPARQL QUERY, WITHOUT ANY ANALYSIS OR EXPLANATION.
Analysis will be done in a separate step after the query results are obtained."""

# Initialize chat history
chat_history = [SystemMessage(content=system_prompt)]


def normalize_industry_name(industry_name):
    """
    Maps common industry search terms to their actual case-sensitive names in the database
    """
    industry_mapping = {
        "healthcare": "healthcare IT",
        "health": "healthcare IT",
        "health care": "healthcare IT",
        "ict": "ICT",
        "tech": "ICT",
        "fintech": "ICT (fintech)",
        "nano": "micro / nano",
        "micro": "micro / nano",
        "micro/nano": "micro / nano",
        "life sciences": "Life-Sciences",
        "lifesciences": "Life-Sciences",
        "clean": "cleantech",
        "med": "medtech",
        "medical": "medtech",
        "bio": "biotech",
    }

    # Check for exact match first
    industry_name = industry_name.lower().strip()

    # Known industry names
    known_industries = [
        "cleantech",
        "biotech",
        "medtech",
        "healthcare IT",
        "ICT",
        "ICT (fintech)",
        "micro / nano",
        "Life-Sciences",
    ]

    # Check exact matches (case-insensitive)
    for known in known_industries:
        if industry_name.lower() == known.lower():
            return known

    # Check for mapped names
    if industry_name in industry_mapping:
        return industry_mapping[industry_name]

    # Check for partial matches
    for key, value in industry_mapping.items():
        if key in industry_name:
            return value

    # Default to original input if no match
    return industry_name


def execute_sparql(query):
    """Execute SPARQL query and return results"""
    try:
        results = graph.query(query)
        # Convert results to a list of dictionaries
        result_list = []
        for row in results:
            # Handle different types of results (single variables, multiple variables)
            if len(row) == 1:
                result_list.append({"result": str(row[0])})
            else:
                result_dict = {}
                for i, var in enumerate(results.vars):
                    result_dict[str(var)] = str(row[i])
                result_list.append(result_dict)
        return result_list
    except Exception as e:
        return f"Error executing SPARQL query: {str(e)}"


def analyze_results(data, query_context):
    """Analyze the query results based on the query context"""
    if not isinstance(data, list):
        return data  # Return error message if query failed

    # Basic analysis for all queries
    analysis = {
        "total_results": len(data),
        "summary": "Query executed successfully",
        "data": data[:10]
        if len(data) > 10
        else data,  # Only show first 10 results to keep output manageable
    }

    # Check if this is a trend analysis query
    if (
        "trend" in query_context.lower()
        or "over time" in query_context.lower()
        or "growth" in query_context.lower()
    ):
        # Enhanced analysis for trend queries
        analysis["trend_analysis"] = perform_trend_analysis(data, query_context)

    # Check if this is a funding analysis query
    if "funding" in query_context.lower() and "amount" in str(data):
        analysis["funding_analysis"] = analyze_funding_data(data)

    return analysis


def perform_trend_analysis(data, query_context):
    """Perform comprehensive trend analysis similar to industry_trends.py"""
    trend_analysis = {
        "overview": "Trend analysis of the results",
        "yearly_trends": {},
        "growth_metrics": {},
        "insights": [],
    }

    # Check if we have date and amount information for trend analysis
    has_date = any("date" in row or "round_date" in row for row in data)
    has_amount = any("amount" in row for row in data)

    if not has_date:
        trend_analysis["insights"].append(
            "No date information available for proper trend analysis"
        )
        return trend_analysis

    # Get the date field name (could be 'date' or 'round_date')
    date_field = "date" if any("date" in row for row in data) else "round_date"

    # Organize data by year
    yearly_data = {}

    for row in data:
        # Skip rows without date information
        if date_field not in row:
            continue

        date_str = str(row[date_field])
        if len(date_str) >= 4:  # Ensure we can extract a year
            year = int(date_str[:4])  # Extract year from date string

            # Initialize year data if not exists
            if year not in yearly_data:
                yearly_data[year] = {
                    "total_funding": 0,
                    "rounds": 0,
                    "companies": set(),
                    "phases": {},
                }

            # Update yearly data
            if "amount" in row and row["amount"]:
                try:
                    yearly_data[year]["total_funding"] += float(row["amount"])
                except ValueError:
                    pass  # Skip if amount can't be converted to float

            yearly_data[year]["rounds"] += 1

            # Add company to the set if available
            if "company_name" in row or "name" in row:
                company_name = row.get("company_name", row.get("name", ""))
                yearly_data[year]["companies"].add(company_name)

            # Track funding phases if available
            if "phase" in row and row["phase"]:
                phase = str(row["phase"])
                if phase not in yearly_data[year]["phases"]:
                    yearly_data[year]["phases"][phase] = 0
                yearly_data[year]["phases"][phase] += 1

    # If no yearly data could be organized, return limited analysis
    if not yearly_data:
        trend_analysis["insights"].append(
            "Could not organize data by year for trend analysis"
        )
        return trend_analysis

    # Add yearly data to the analysis
    for year, year_data in sorted(yearly_data.items()):
        # Calculate average round size if funding information is available
        avg_round_size = 0
        if year_data["rounds"] > 0 and year_data["total_funding"] > 0:
            avg_round_size = year_data["total_funding"] / year_data["rounds"]

        trend_analysis["yearly_trends"][str(year)] = {
            "total_funding": year_data["total_funding"],
            "funding_rounds": year_data["rounds"],
            "companies_count": len(year_data["companies"]),
            "avg_round_size": avg_round_size,
            "phases": year_data["phases"],
        }

    # Calculate growth rates between years
    years = sorted(yearly_data.keys())
    if len(years) >= 2:
        funding_growth = []
        rounds_growth = []
        companies_growth = []

        for i in range(1, len(years)):
            prev_year = years[i - 1]
            curr_year = years[i]

            # Calculate funding growth
            prev_funding = yearly_data[prev_year]["total_funding"]
            curr_funding = yearly_data[curr_year]["total_funding"]
            if prev_funding > 0:
                growth_pct = ((curr_funding - prev_funding) / prev_funding) * 100
                funding_growth.append(growth_pct)
                trend_analysis["growth_metrics"][f"{prev_year}-{curr_year}_funding"] = (
                    growth_pct
                )

            # Calculate rounds growth
            prev_rounds = yearly_data[prev_year]["rounds"]
            curr_rounds = yearly_data[curr_year]["rounds"]
            if prev_rounds > 0:
                growth_pct = ((curr_rounds - prev_rounds) / prev_rounds) * 100
                rounds_growth.append(growth_pct)
                trend_analysis["growth_metrics"][f"{prev_year}-{curr_year}_rounds"] = (
                    growth_pct
                )

            # Calculate companies growth
            prev_companies = len(yearly_data[prev_year]["companies"])
            curr_companies = len(yearly_data[curr_year]["companies"])
            if prev_companies > 0:
                growth_pct = ((curr_companies - prev_companies) / prev_companies) * 100
                companies_growth.append(growth_pct)
                trend_analysis["growth_metrics"][
                    f"{prev_year}-{curr_year}_companies"
                ] = growth_pct

        # Calculate average growth rates
        if funding_growth:
            avg_funding_growth = sum(funding_growth) / len(funding_growth)
            trend_analysis["growth_metrics"]["avg_annual_funding_growth"] = (
                avg_funding_growth
            )

            # Add insight about funding trend
            if avg_funding_growth > 0:
                trend_analysis["insights"].append(
                    f"Funding is growing at an average rate of {avg_funding_growth:.1f}% per year"
                )
            else:
                trend_analysis["insights"].append(
                    f"Funding is decreasing at an average rate of {abs(avg_funding_growth):.1f}% per year"
                )

        if rounds_growth:
            avg_rounds_growth = sum(rounds_growth) / len(rounds_growth)
            trend_analysis["growth_metrics"]["avg_annual_rounds_growth"] = (
                avg_rounds_growth
            )

            # Add insight about rounds trend
            if avg_rounds_growth > 0:
                trend_analysis["insights"].append(
                    f"Number of funding rounds is growing at an average rate of {avg_rounds_growth:.1f}% per year"
                )
            else:
                trend_analysis["insights"].append(
                    f"Number of funding rounds is decreasing at an average rate of {abs(avg_rounds_growth):.1f}% per year"
                )

        # Add insights about maturity based on most recent years
        if len(years) >= 3:
            recent_years = years[-3:]
            recent_funding = [yearly_data[y]["total_funding"] for y in recent_years]
            recent_rounds = [yearly_data[y]["rounds"] for y in recent_years]

            # Check for acceleration or deceleration
            if (
                len(recent_funding) >= 3
                and recent_funding[0] > 0
                and recent_funding[1] > 0
            ):
                growth_rate_1 = (
                    recent_funding[1] - recent_funding[0]
                ) / recent_funding[0]
                growth_rate_2 = (
                    recent_funding[2] - recent_funding[1]
                ) / recent_funding[1]

                if growth_rate_2 > growth_rate_1:
                    trend_analysis["insights"].append(
                        "Funding growth is accelerating in recent years"
                    )
                    trend_analysis["maturity"] = "accelerating growth"
                else:
                    trend_analysis["insights"].append(
                        "Funding growth is decelerating in recent years"
                    )
                    trend_analysis["maturity"] = "decelerating growth"

            # Analyze funding stage evolution
            latest_year = max(years)
            earliest_analyzed_year = min(years)

            early_stage_count = sum(
                yearly_data[earliest_analyzed_year]["phases"].get(phase, 0)
                for phase in ["Seed", "Angel", "Pre-Seed"]
                if phase in yearly_data[earliest_analyzed_year]["phases"]
            )

            late_stage_count = sum(
                yearly_data[earliest_analyzed_year]["phases"].get(phase, 0)
                for phase in ["Series C", "Series D", "Late Stage", "Growth"]
                if phase in yearly_data[earliest_analyzed_year]["phases"]
            )

            current_early_stage = sum(
                yearly_data[latest_year]["phases"].get(phase, 0)
                for phase in ["Seed", "Angel", "Pre-Seed"]
                if phase in yearly_data[latest_year]["phases"]
            )

            current_late_stage = sum(
                yearly_data[latest_year]["phases"].get(phase, 0)
                for phase in ["Series C", "Series D", "Late Stage", "Growth"]
                if phase in yearly_data[latest_year]["phases"]
            )

            # Compare early vs late stage evolution
            if (
                early_stage_count > 0
                and current_early_stage > 0
                and late_stage_count > 0
                and current_late_stage > 0
            ):
                early_growth = (
                    current_early_stage - early_stage_count
                ) / early_stage_count
                late_growth = (current_late_stage - late_stage_count) / late_stage_count

                if late_growth > early_growth:
                    trend_analysis["insights"].append(
                        "The industry is maturing with more late-stage funding rounds"
                    )
                else:
                    trend_analysis["insights"].append(
                        "The industry continues to see strong early-stage investment activity"
                    )

    return trend_analysis


def analyze_funding_data(data):
    """Perform specific analysis for funding-related queries"""
    funding_analysis = {
        "overview": "Analysis of funding data",
        "statistics": {},
        "insights": [],
    }

    # Extract funding amounts
    amounts = []
    for row in data:
        if "amount" in row and row["amount"]:
            try:
                amount = float(row["amount"])
                amounts.append(amount)
            except ValueError:
                continue

    if not amounts:
        funding_analysis["insights"].append(
            "No valid funding amounts found in the data"
        )
        return funding_analysis

    # Calculate funding statistics
    total_funding = sum(amounts)
    avg_funding = total_funding / len(amounts)
    median_funding = sorted(amounts)[len(amounts) // 2]
    max_funding = max(amounts)
    min_funding = min(amounts)

    funding_analysis["statistics"] = {
        "total_funding": total_funding,
        "average_funding": avg_funding,
        "median_funding": median_funding,
        "max_funding": max_funding,
        "min_funding": min_funding,
        "number_of_rounds": len(amounts),
    }

    # Add funding insights
    if len(amounts) >= 3:
        top_rounds = sorted(amounts, reverse=True)[:3]
        top_rounds_sum = sum(top_rounds)
        concentration_ratio = top_rounds_sum / total_funding

        funding_analysis["statistics"]["top_3_rounds_sum"] = top_rounds_sum
        funding_analysis["statistics"]["concentration_ratio"] = concentration_ratio

        if concentration_ratio > 0.5:
            funding_analysis["insights"].append(
                f"Funding is highly concentrated: top 3 rounds account for {concentration_ratio * 100:.1f}% of total funding"
            )
        else:
            funding_analysis["insights"].append(
                f"Funding is well distributed: top 3 rounds account for only {concentration_ratio * 100:.1f}% of total funding"
            )

    # Classify average round size
    if avg_funding > 50000000:  # 50M
        funding_analysis["insights"].append(
            "Very large average round size, indicating mature/late-stage market"
        )
    elif avg_funding > 10000000:  # 10M
        funding_analysis["insights"].append(
            "Large average round size, indicating growth-stage market"
        )
    elif avg_funding > 1000000:  # 1M
        funding_analysis["insights"].append(
            "Moderate average round size, indicating early-stage market"
        )
    else:
        funding_analysis["insights"].append(
            "Small average round size, indicating seed/angel-stage market"
        )

    return funding_analysis


def perform_company_market_comparison(company_names, results):
    """
    Perform a comparative analysis between specific companies and their market/industry

    Args:
        company_names: List of company names to analyze
        results: Results from the company query

    Returns:
        Dictionary with company data and market trends for comparison
    """
    comparison_data = {"companies": {}, "market_trends": {}, "insights": []}

    # Extract company data from results
    for item in results:
        if "company_name" in item and item["company_name"] in company_names:
            company_name = item["company_name"]

            # Initialize company in the dictionary if not already present
            if company_name not in comparison_data["companies"]:
                comparison_data["companies"][company_name] = {
                    "industry": None,
                    "funding_rounds": [],
                    "total_funding": 0,
                    "location": None,
                }

            # Extract industry
            if "industry_name" in item and item["industry_name"]:
                comparison_data["companies"][company_name]["industry"] = item[
                    "industry_name"
                ]

            # Extract funding round data
            if "amount" in item and item["amount"] and item["amount"] != "None":
                try:
                    amount = float(item["amount"])
                    date = (
                        item["date"]
                        if "date" in item and item["date"] != "None"
                        else None
                    )
                    phase = (
                        item["phase"]
                        if "phase" in item and item["phase"] != "None"
                        else None
                    )

                    funding_round = {"amount": amount, "date": date, "phase": phase}

                    comparison_data["companies"][company_name]["funding_rounds"].append(
                        funding_round
                    )
                    comparison_data["companies"][company_name]["total_funding"] += (
                        amount
                    )
                except ValueError:
                    pass

            # Extract location
            if (
                "location_name" in item
                and item["location_name"]
                and item["location_name"] != "None"
            ):
                comparison_data["companies"][company_name]["location"] = item[
                    "location_name"
                ]

    # Get industry trends for each company
    for company_name, company_data in comparison_data["companies"].items():
        if company_data["industry"]:
            industry_name = company_data["industry"]

            # Query to get industry trends
            industry_query = f"""
            PREFIX ex: <http://example.org/ontology#>
            PREFIX res: <http://example.org/resource/>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            SELECT ?company_name ?date ?amount ?phase
            WHERE {{
                ?company a ex:Startup ;
                        ex:name ?company_name ;
                        ex:hasIndustry ?industry .
                ?industry ex:name "{industry_name}" .
                ?company ex:hasFunding ?funding .
                OPTIONAL {{ ?funding ex:round_date ?date }}
                OPTIONAL {{ ?funding ex:amount ?amount }}
                OPTIONAL {{ ?funding ex:phase ?phase }}
            }}
            ORDER BY ?date
            """

            industry_results = execute_sparql(industry_query)

            # Process industry results to get yearly trends
            industry_yearly_data = {}

            for item in industry_results:
                if "date" in item and item["date"] and item["date"] != "None":
                    year = str(item["date"])[:4]

                    if year.isdigit() and len(year) == 4:
                        if year not in industry_yearly_data:
                            industry_yearly_data[year] = {
                                "count": 0,
                                "total_funding": 0,
                                "companies": set(),
                            }

                        industry_yearly_data[year]["count"] += 1

                        # Add amount if available
                        if (
                            "amount" in item
                            and item["amount"]
                            and item["amount"] != "None"
                        ):
                            try:
                                amount = float(item["amount"])
                                industry_yearly_data[year]["total_funding"] += amount
                            except ValueError:
                                pass

                        # Add company name
                        if "company_name" in item and item["company_name"]:
                            industry_yearly_data[year]["companies"].add(
                                item["company_name"]
                            )

            # Convert to list for easier processing
            yearly_trend_list = []
            for year in sorted(industry_yearly_data.keys()):
                yearly_trend_list.append(
                    {
                        "year": year,
                        "funding_rounds": industry_yearly_data[year]["count"],
                        "total_funding": industry_yearly_data[year]["total_funding"],
                        "total_funding_millions": industry_yearly_data[year][
                            "total_funding"
                        ]
                        / 1000000,
                        "companies_count": len(industry_yearly_data[year]["companies"]),
                    }
                )

            # Add to comparison data
            comparison_data["market_trends"][industry_name] = {
                "yearly_trends": yearly_trend_list,
                "total_companies": len(
                    set(
                        item["company_name"]
                        for item in industry_results
                        if "company_name" in item
                    )
                ),
                "total_funding": sum(
                    item["total_funding"] for item in yearly_trend_list
                ),
                "avg_round_size": sum(
                    item["total_funding"] for item in yearly_trend_list
                )
                / sum(item["funding_rounds"] for item in yearly_trend_list)
                if sum(item["funding_rounds"] for item in yearly_trend_list) > 0
                else 0,
            }

    return comparison_data


def process_query(user_query):
    """Process a natural language query through the agent using a two-step approach"""
    # Check if this is a comparison query
    is_comparison_query = any(
        term in user_query.lower()
        for term in [
            "compare",
            "comparison",
            "versus",
            "vs",
            "against",
            "relative to",
            "compared to",
            "benchmark",
            "how does",
            "performance of",
            "stack up",
        ]
    )

    # Extract company names if it's a comparison query
    company_names = []
    if is_comparison_query:
        # Use regex to try to identify company names in quotes
        import re

        quoted_companies = re.findall(r'"([^"]+)"', user_query)
        if quoted_companies:
            company_names.extend(quoted_companies)

        # If no quoted names found, try to identify company names using a more advanced prompt
        if not company_names:
            company_extraction_prompt = f"""
            From the following query, extract ONLY the company names that need to be compared to market trends:
            
            "{user_query}"
            
            Return ONLY a comma-separated list of company names, with no additional text or explanation.
            If no specific company names are mentioned, return "NONE".
            """

            chat_history.append(HumanMessage(content=company_extraction_prompt))
            company_response = model.invoke(chat_history)
            company_text = company_response.content.strip()
            chat_history.append(AIMessage(content=company_text))

            # Process the response to extract company names
            if company_text and company_text.lower() != "none":
                extracted_companies = [name.strip() for name in company_text.split(",")]
                company_names.extend(extracted_companies)

    # Step 1: Get SPARQL query from LLM - be very explicit that we need a SPARQL query
    query_instruction = f"""USER QUERY: {user_query}

IMPORTANT INSTRUCTIONS:
1. Your task is to GENERATE a SPARQL query that will extract the data needed to answer this question.
2. DO NOT analyze the data or provide insights yet - that will be done in the next step.
3. ONLY return a valid SPARQL query.
4. Format your response as a valid SPARQL query with PREFIX declarations.
5. For trend analysis, ensure your query retrieves temporal data (dates) and relevant metrics.
6. IMPORTANT NOTE: Industry names are case-sensitive. The following industry names are available:
   - "cleantech" (not "Cleantech")
   - "biotech" (not "Biotech")
   - "medtech" (not "Medtech") 
   - "healthcare IT" (not just "healthcare")
   - "ICT" (exactly as written)
   - "micro / nano" (with spaces as shown)
   - "Life-Sciences" (with hyphen)
7. When analyzing funding trends, make sure the relationship ?company ex:hasFunding ?funding is REQUIRED (not optional).
   Only make the funding properties (round_date, amount, phase) optional.

GENERATE SPARQL QUERY:"""

    # Modify the query instruction if this is a comparison query with specific companies
    if is_comparison_query and company_names:
        query_instruction = f"""USER QUERY: Get data for the following companies: {", ".join(company_names)}

IMPORTANT INSTRUCTIONS:
1. Your task is to GENERATE a SPARQL query that will extract ALL data needed about these specific companies.
2. Include company name, industry name, funding amounts, dates, phases, and locations.
3. Use VALUES clause to filter for the exact company names.
4. ONLY return a valid SPARQL query.
5. Format your response as a valid SPARQL query with PREFIX declarations.

GENERATE SPARQL QUERY:"""

    # Add the specific query instruction to chat history
    chat_history.append(HumanMessage(content=query_instruction))

    # Get SPARQL query from LLM
    response = model.invoke(chat_history)
    response_content = response.content
    chat_history.append(AIMessage(content=response_content))

    # Extract SPARQL query from response - be more robust in extraction
    try:
        sparql_query = None
        if "```sparql" in response_content.lower():
            sparql_query = (
                response_content.split("```sparql")[1].split("```")[0].strip()
            )
        elif "```" in response_content:
            sparql_query = response_content.split("```")[1].split("```")[0].strip()
        else:
            # If no code blocks, try to extract just the query part
            if (
                "prefix" in response_content.lower()
                or "select" in response_content.lower()
            ):
                sparql_query = response_content.strip()
            else:
                # If still no clear query, provide error feedback
                error_msg = "Response does not contain a valid SPARQL query. Please ensure your response contains only a SPARQL query."
                chat_history.append(HumanMessage(content=error_msg))
                return f"Error: {error_msg}"

        print(f"Extracted SPARQL Query:\n{sparql_query}")

        # Check for industry filters and modify if needed to use correct case
        import re

        # Look for FILTER statements with industry names
        filter_pattern = r'FILTER\s*\(\s*\?industry_name\s*=\s*["\']([^"\']+)["\']\s*\)'
        industry_matches = re.findall(filter_pattern, sparql_query)

        if industry_matches:
            for industry_name in industry_matches:
                # Normalize the industry name
                normalized_name = normalize_industry_name(industry_name)
                if normalized_name != industry_name:
                    print(
                        f"Replacing industry name '{industry_name}' with '{normalized_name}'"
                    )
                    sparql_query = sparql_query.replace(
                        f'"{industry_name}"', f'"{normalized_name}"'
                    )
                    sparql_query = sparql_query.replace(
                        f"'{industry_name}'", f"'{normalized_name}'"
                    )

        # Also check for direct triple patterns like ?industry ex:name "healthcare"
        triple_pattern = r'\?industry\s+ex:name\s+["\']([^"\']+)["\']'
        industry_triples = re.findall(triple_pattern, sparql_query)

        if industry_triples:
            for industry_name in industry_triples:
                # Normalize the industry name
                normalized_name = normalize_industry_name(industry_name)
                if normalized_name != industry_name:
                    print(
                        f"Replacing industry name '{industry_name}' with '{normalized_name}'"
                    )
                    sparql_query = sparql_query.replace(
                        f'"{industry_name}"', f'"{normalized_name}"'
                    )
                    sparql_query = sparql_query.replace(
                        f"'{industry_name}'", f"'{normalized_name}'"
                    )

        # Fix date property - replace ex:date with ex:round_date
        if "ex:date" in sparql_query:
            print("Replacing 'ex:date' with 'ex:round_date' in query")
            sparql_query = sparql_query.replace("ex:date", "ex:round_date")

        # Fix location predicate - replace ex:locatedIn with ex:hasLocation
        if "ex:locatedIn" in sparql_query:
            print("Replacing 'ex:locatedIn' with 'ex:hasLocation' in query")
            sparql_query = sparql_query.replace("ex:locatedIn", "ex:hasLocation")

        # Make sure location is optional - with more careful pattern matching
        if (
            "ex:hasLocation" in sparql_query
            and "OPTIONAL"
            not in sparql_query[
                sparql_query.index("ex:hasLocation") - 10 : sparql_query.index(
                    "ex:hasLocation"
                )
            ]
        ):
            print("Making location patterns OPTIONAL")

            # Find the location triple pattern more carefully
            location_pattern = re.search(
                r"(\?company\s+ex:hasLocation\s+\?[a-zA-Z_]+\s*\.)", sparql_query
            )
            if location_pattern:
                # Extract the whole pattern, including follow-up triples about the location
                start_pos = location_pattern.start()
                pattern_text = location_pattern.group(1)

                # Follow-up location properties might exist - find them
                end_of_location_block = start_pos + len(pattern_text)
                remaining_query = sparql_query[end_of_location_block:]

                # Find if there are follow-up triples for the location
                follow_up_match = re.search(
                    r"(\?[a-zA-Z_]+\s+[^\.\}]+\s*\.)", remaining_query
                )

                if follow_up_match and not re.search(
                    r"OPTIONAL", sparql_query[start_pos - 10 : start_pos]
                ):
                    # Complete location block includes the main triple and follow-up properties
                    complete_location_block = pattern_text + follow_up_match.group(1)

                    # Replace with OPTIONAL
                    optional_block = f"OPTIONAL {{ {complete_location_block.strip()} }}"
                    sparql_query = sparql_query.replace(
                        complete_location_block, optional_block
                    )
                elif not re.search(
                    r"OPTIONAL", sparql_query[start_pos - 10 : start_pos]
                ):
                    # Only the main location triple needs to be made optional
                    optional_pattern = f"OPTIONAL {{ {pattern_text.strip()} }}"
                    sparql_query = sparql_query.replace(pattern_text, optional_pattern)

        # Check if we're analyzing funding trends
        is_funding_analysis = any(
            term in user_query.lower()
            for term in ["funding", "investment", "money", "financial", "trend"]
        )

        # Check if the hasFunding relationship is inside an OPTIONAL block when it should be required
        if (
            is_funding_analysis
            and "OPTIONAL {" in sparql_query
            and "ex:hasFunding" in sparql_query
        ):
            funding_pattern = re.search(
                r"OPTIONAL\s*\{\s*\?company\s+ex:hasFunding\s+\?funding", sparql_query
            )
            if funding_pattern:
                print("Making funding relationship required for funding analysis")
                # Extract the whole OPTIONAL block
                start_pos = funding_pattern.start()
                open_braces = 1
                end_pos = start_pos + len("OPTIONAL {")

                while open_braces > 0 and end_pos < len(sparql_query):
                    if sparql_query[end_pos] == "{":
                        open_braces += 1
                    elif sparql_query[end_pos] == "}":
                        open_braces -= 1
                    end_pos += 1

                # Keep the ?company ex:hasFunding ?funding line but remove the OPTIONAL wrapper
                optional_block = sparql_query[start_pos:end_pos]
                funding_line = re.search(
                    r"\?company\s+ex:hasFunding\s+\?funding", optional_block
                ).group(0)

                # Replace the OPTIONAL block with just the funding line followed by optional funding properties
                replacement = f"{funding_line} .\n        OPTIONAL {{ ?funding ex:round_date ?date }}\n        OPTIONAL {{ ?funding ex:amount ?amount }}\n        OPTIONAL {{ ?funding ex:phase ?phase }}"
                sparql_query = (
                    sparql_query[:start_pos] + replacement + sparql_query[end_pos:]
                )

        print(f"Modified SPARQL Query:\n{sparql_query}")

        # Execute query
        results = execute_sparql(sparql_query)

        # If this is a comparison query with companies, run the company-market comparison
        if is_comparison_query and company_names and len(results) > 0:
            print(
                f"Performing comparison analysis for companies: {', '.join(company_names)}"
            )
            comparison_data = perform_company_market_comparison(company_names, results)

            # Create a special analysis prompt for company-market comparison
            analysis_prompt = f"""I've executed a SPARQL query to compare specific companies against their industry/market trends.

Company Query: 
```sparql
{sparql_query}
```

I've analyzed the data and prepared a comprehensive comparison:

1. COMPANY DATA:
```
{json.dumps(comparison_data["companies"], indent=2)}
```

2. RELEVANT MARKET/INDUSTRY TRENDS:
```
{json.dumps(comparison_data["market_trends"], indent=2)}
```

NOW, please provide a detailed comparative analysis between these companies and their respective industry/market trends based on the original question: "{user_query}"

For this comparison analysis:
1. Compare each company's funding history against their industry trends
2. Analyze whether the companies are outperforming or underperforming the market
3. Identify any unique patterns or anomalies in the companies' performance relative to the market
4. Consider timing of funding rounds relative to industry trends
5. Discuss company funding compared to industry averages

Be data-driven and thorough in your comparison. The analysis should highlight specific insights about how these companies stack up against broader market/industry trends."""

            # Send comparison analysis to LLM
            chat_history.append(HumanMessage(content=analysis_prompt))
            analysis_response = model.invoke(chat_history)
            analysis_content = analysis_response.content
            chat_history.append(AIMessage(content=analysis_content))

            # Format response with comparison data
            response = {
                "query": sparql_query,
                "raw_results": results,
                "total_results": len(results),
                "llm_analysis": analysis_content,
                "is_comparison": True,
                "comparison_data": comparison_data,
            }

            return json.dumps(response, indent=2)

        # Pre-process results to aggregate by year for trend analysis
        is_trend_analysis = any(
            term in user_query.lower()
            for term in [
                "trend",
                "over time",
                "growth",
                "evolution",
                "development",
                "history",
            ]
        )

        # If this appears to be a trend query with dates and amounts, provide year-by-year summaries
        yearly_summary = {}
        has_date = False
        has_amount = False

        # Check if results have date and amount fields
        if results and len(results) > 0:
            has_date = any("date" in item or "round_date" in item for item in results)
            has_amount = any("amount" in item for item in results)

            # If it's trend analysis with dates and amounts, aggregate by year
            if is_trend_analysis and has_date and has_amount:
                print("Aggregating results by year for trend analysis...")

                # Process results to get yearly data
                for item in results:
                    date_field = "date" if "date" in item else "round_date"

                    if item[date_field] and item[date_field] != "None":
                        year = str(item[date_field])[:4]

                        if year.isdigit() and len(year) == 4:
                            if year not in yearly_summary:
                                yearly_summary[year] = {
                                    "count": 0,
                                    "total_funding": 0,
                                    "companies": set(),
                                }

                            yearly_summary[year]["count"] += 1

                            # Add amount if available
                            if (
                                "amount" in item
                                and item["amount"]
                                and item["amount"] != "None"
                            ):
                                try:
                                    amount = float(item["amount"])
                                    yearly_summary[year]["total_funding"] += amount
                                except ValueError:
                                    pass

                            # Add company name if available
                            if "company_name" in item and item["company_name"]:
                                yearly_summary[year]["companies"].add(
                                    item["company_name"]
                                )

        # Step 2: Send results back to LLM for analysis - with enhanced yearly summary if applicable
        if is_trend_analysis and yearly_summary:
            # Convert yearly_summary to a list sorted by year for the analysis prompt
            yearly_data_list = []
            for year in sorted(yearly_summary.keys()):
                yearly_data_list.append(
                    {
                        "year": year,
                        "funding_rounds": yearly_summary[year]["count"],
                        "total_funding": yearly_summary[year]["total_funding"],
                        "total_funding_millions": yearly_summary[year]["total_funding"]
                        / 1000000,
                        "companies_count": len(yearly_summary[year]["companies"]),
                    }
                )

            # Create an analysis prompt with the full yearly summary
            analysis_prompt = f"""I've executed your SPARQL query and obtained results for {len(results)} records.

Query: 
```sparql
{sparql_query}
```

I've aggregated the data by year to show trends over time. Here's the yearly summary:

```
{json.dumps(yearly_data_list, indent=2)}
```

Sample of individual records (first 10 shown):
```
{json.dumps(results[:10], indent=2)}
```

Total number of results: {len(results)}

NOW, please analyze these results and provide insights based on the original question: "{user_query}"

For this trend analysis:
1. Analyze patterns over time using the COMPLETE yearly data provided above
2. Calculate growth rates between years, especially 2018-2023
3. Identify significant changes or anomalies
4. Explain what the data reveals about the industry or market

Important Notes:
- The yearly_summary shows data from ALL {len(results)} records, not just a sample
- Make sure to analyze ALL years present in the data, from {min(yearly_summary.keys()) if yearly_summary else "N/A"} to {max(yearly_summary.keys()) if yearly_summary else "N/A"}
- Pay special attention to recent trends in the last 3-5 years

Your analysis should be data-driven and based on ALL the yearly data provided above."""

        else:
            # Standard analysis prompt for non-trend queries or queries without proper date/amount data
            analysis_prompt = f"""I've executed your SPARQL query and obtained the following results:

Query: 
```sparql
{sparql_query}
```

Results (first 20 items shown if there are more):
```
{json.dumps(results[:20], indent=2)}
```

Total number of results: {len(results)}

NOW, please analyze these results and provide insights based on the original question: "{user_query}"

If this is trend-related:
1. Analyze patterns over time in the data
2. Calculate growth rates between periods
3. Identify significant changes or anomalies
4. Explain what the data reveals about the industry or market

Important Notes:
- Funding dates are stored as "round_date" in the database
- Some funding events may not have dates or other attributes
- When analyzing trends, focus on the available data points

Your analysis should be data-driven and based ONLY on the results provided above.
If the data is insufficient for certain conclusions, clearly state what's missing."""

        # Special case for funding analysis with missing dates - keep existing code
        if (
            is_funding_analysis
            and all(result.get("date") == "None" for result in results[:20])
            and len(results) > 0
        ):
            # If we're analyzing funding but no dates are found, try a direct query approach
            print(
                "No funding dates found in the results. Using direct query for funding data..."
            )

            # Extract industry name from the query
            industry_name = None
            if industry_matches:
                industry_name = normalized_name
            elif industry_triples:
                industry_name = normalized_name

            if industry_name:
                print(f"Analyzing {industry_name} funding directly...")
                # Use a direct query pattern that ensures we get funding data
                direct_query = f"""
                PREFIX ex: <http://example.org/ontology#>
                PREFIX res: <http://example.org/resource/>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

                SELECT ?company_name ?date ?amount ?phase
                WHERE {{
                    ?company a ex:Startup ;
                            ex:name ?company_name ;
                            ex:hasIndustry ?industry .
                    ?industry ex:name "{industry_name}" .
                    ?company ex:hasFunding ?funding .
                    OPTIONAL {{ ?funding ex:round_date ?date }}
                    OPTIONAL {{ ?funding ex:amount ?amount }}
                    OPTIONAL {{ ?funding ex:phase ?phase }}
                }}
                ORDER BY ?date
                """

                # Execute the direct query and update results
                direct_results = execute_sparql(direct_query)

                if (
                    direct_results
                    and len(direct_results) > 0
                    and any(result.get("date") != "None" for result in direct_results)
                ):
                    print(
                        f"Direct query found {len(direct_results)} results with funding data"
                    )
                    results = direct_results
                    sparql_query = direct_query

                    # Update the analysis prompt with new results
                    analysis_prompt = f"""I've executed a direct SPARQL query for {industry_name} funding data and obtained the following results:

Query: 
```sparql
{sparql_query}
```

Results (first 20 items shown if there are more):
```
{json.dumps(results[:20], indent=2)}
```

Total number of results: {len(results)}

NOW, please analyze these results and provide insights based on the original question: "{user_query}"

If this is trend-related:
1. Analyze patterns over time in the data
2. Calculate growth rates between periods
3. Identify significant changes or anomalies
4. Explain what the data reveals about the industry or market

Important Notes:
- Funding dates are stored as "round_date" in the database
- Some funding events may not have dates or other attributes
- When analyzing trends, focus on the available data points

Your analysis should be data-driven and based ONLY on the results provided above.
If the data is insufficient for certain conclusions, clearly state what's missing."""

        # Send results to LLM for analysis
        chat_history.append(HumanMessage(content=analysis_prompt))
        analysis_response = model.invoke(chat_history)
        analysis_content = analysis_response.content
        chat_history.append(AIMessage(content=analysis_content))

        # Format response - return ALL results
        response = {
            "query": sparql_query,
            "raw_results": results,
            "total_results": len(results),
            "llm_analysis": analysis_content,
        }

        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error processing query: {str(e)}"


# Example usage
if __name__ == "__main__":
    # Provide detailed feedback on the semicolon issue
    semicolon_fix = """Your latest query STILL has a critical error with semicolons:

```sparql
OPTIONAL { ?company ex:hasFunding ?fundingEvent .
           ?fundingEvent ex:date ?date ;
                        ex:amount ?amount .
           BIND(STRDT(SUBSTR(STR(?date), 1, 4), xsd:integer) AS ?year)
         }
```

THE SEMICOLON IS THE PROBLEM! In SPARQL, the semicolon (;) continues the subject, but STILL MAKES THOSE PROPERTIES REQUIRED.

So while you put the entire block in OPTIONAL, you're still requiring that when a funding event exists, it MUST have BOTH:
- ex:date 
- ex:amount

But many funding events might have only one or the other!

THE CORRECT APPROACH is to use separate OPTIONAL blocks for EACH property:

```sparql
PREFIX ex: <http://example.org/ontology#>
PREFIX res: <http://example.org/resource/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?company_name ?date ?amount ?phase
WHERE {
  ?company a ex:Startup ;
          ex:name ?company_name ;
          ex:hasIndustry ?industry .
  ?industry ex:name "cleantech" .
  
  OPTIONAL {
    ?company ex:hasFunding ?funding .
    OPTIONAL { ?funding ex:date ?date }
    OPTIONAL { ?funding ex:amount ?amount }
    OPTIONAL { ?funding ex:phase ?phase }
  }
}
ORDER BY ?date
```

DO NOT use semicolons to join properties that should be optional! Each property needs its own OPTIONAL block.

Also, please:
1. Use the exact variable names shown above
2. Don't use GROUP BY in the initial query
3. Return the raw data first, then do aggregation in the analysis phase
4. Drop the BIND statement entirely

The query isn't returning data because your approach with semicolons is making too many properties required. This is a common mistake in SPARQL."""

    # Add this semicolon feedback first in the chat history
    chat_history.append(HumanMessage(content=semicolon_fix))

    # BEST PRACTICES FEEDBACK FOR FUTURE LLMs WORKING WITH THIS CODE
    llm_feedback = """
IMPORTANT ADVICE FOR LLMs WORKING WITH SPARQL QUERIES:

1. AVOID THE SEMICOLON TRAP:
   - In SPARQL, semicolons (;) make properties MANDATORY in their context
   - Even if inside an OPTIONAL block, semicolons still make ALL properties they connect REQUIRED
   - Always use nested OPTIONAL blocks for properties that might be missing

2. BUILDING QUERIES FOR INDUSTRY TRENDS:
   - REFERENCE industry_trends.py as the model for correct query structure
   - Follow its pattern: first get raw data, then process it in Python
   - Use parameterized queries with Literal().n3() to safely inject parameters
   - Prefer generic, reusable functions that accept parameters

3. QUERY STRUCTURE BEST PRACTICES:
   - Get basic, mandatory data first (company, industry)
   - Put ALL optional patterns in separate OPTIONAL blocks
   - Return raw data instead of aggregating in SPARQL
   - Process/aggregate data in Python after retrieving it
   - ORDER BY dates or other relevant fields

4. PROCESSING TIPS:
   - Extract years from dates in Python, not in SPARQL
   - Handle missing data gracefully - use defaultdict and conditional checks
   - Calculate growth rates with checks for division by zero
   - Build proper data structures that separate data organization from analysis

5. CORRECT APPROACH TO TREND ANALYSIS:
   - Follow the industry_trends.py pattern exactly
   - First collect all data with properly structured OPTIONALs
   - Process in Python: organize by year, calculate metrics, analyze trends
   - Report on yearly data, growth rates, funding stages, and market indicators

Remember: The industry_trends.py file is THE reference implementation. Copy its query structure and processing approach exactly.
"""

    # Add the LLM feedback to chat history
    chat_history.append(HumanMessage(content=llm_feedback))

    # Add parameterization feedback
    parameterization_feedback = """SPARQL QUERY FEEDBACK - PARAMETERIZATION BEST PRACTICES

The current hardcoded query approach has a critical problem with parameter handling:

INCORRECT APPROACH (hardcoded values):
```sparql
PREFIX ex: <http://example.org/ontology#>
PREFIX res: <http://example.org/resource/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?company_name ?date ?amount ?phase
WHERE {
  ?company a ex:Startup ;
          ex:name ?company_name ;
          ex:hasIndustry ?industry .
  ?industry ex:name "cleantech" .

  OPTIONAL {
    ?company ex:hasFunding ?funding .
    OPTIONAL { ?funding ex:date ?date }
    OPTIONAL { ?funding ex:amount ?amount }
    OPTIONAL { ?funding ex:phase ?phase }
  }
}
ORDER BY ?date
```

CORRECT APPROACH (parameterized):
```sparql
SELECT ?company_name ?date ?amount ?phase
WHERE {
    ?company a ex:Startup ;
            ex:name ?company_name ;
            ex:hasIndustry ?industry .
    ?industry ex:name ?industry_name .
    OPTIONAL {
        ?company ex:hasFunding ?funding .
        OPTIONAL { ?funding ex:date ?date }
        OPTIONAL { ?funding ex:amount ?amount }
        OPTIONAL { ?funding ex:phase ?phase }
    }
    FILTER(?industry_name = %s)
}
ORDER BY ?date
```

Problems with hardcoded values:
1. NON-REUSABLE: The industry name "cleantech" is hardcoded directly in the query, making it non-reusable for other industries.
2. SECURITY RISK: Directly embedding values in queries is a security risk prone to injection attacks.
3. MAINTENANCE NIGHTMARE: Each change requires modifying the query itself.

The correct approach:
1. Uses ?industry_name as a variable, not a hardcoded value
2. Uses FILTER with a parameter placeholder (%s) 
3. Safely injects the parameter with Literal().n3() to prevent injection attacks:
   `results = list(g.query(query % Literal(industry_name).n3()))`

This approach is:
- Reusable (works with any industry)
- Secure (prevents SPARQL injection)
- Follows best practices for parameterized queries

IMPLEMENTATION RULE: NEVER hardcode values directly in SPARQL queries that should be parameterized!"""

    # Add the parameterization feedback to chat history
    chat_history.append(HumanMessage(content=parameterization_feedback))

    print("Welcome to the SPARQL Query Terminal!")
    print("Enter your natural language queries, and they'll be converted to SPARQL.")
    print("Type 'exit' to quit.")
    print("\n" + "=" * 80 + "\n")

    print("Previous feedback has been added to help the LLM improve its responses.")
    print("\n" + "=" * 80 + "\n")

    while True:
        try:
            # Get user input
            user_query = input("\nEnter your query: ")

            # Check if user wants to exit
            if user_query.lower() in ["exit", "quit", "q"]:
                print("Exiting. Goodbye!")
                break

            print("\n" + "=" * 80 + "\n")
            print(f"QUERY: {user_query}")
            print("\n" + "=" * 80 + "\n")

            # Process the query while maintaining chat history
            result = process_query(user_query)

            # Print the result
            print("\nRESULT:")
            print("=" * 80)
            print(result)
            print("=" * 80)

        except KeyboardInterrupt:
            print("\nExiting. Goodbye!")
            break
        except Exception as e:
            print(f"Error: {str(e)}")

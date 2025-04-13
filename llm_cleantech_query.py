from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from rdflib import Graph, Namespace, Literal
import json
import os
import re
from collections import defaultdict

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


# Direct SPARQL query for cleantech funding analysis - avoiding LLM issues
def get_cleantech_funding_data():
    print("Running direct SPARQL query for cleantech funding data...")
    query = """
    PREFIX ex: <http://example.org/ontology#>
    PREFIX res: <http://example.org/resource/>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT ?company_name ?date ?amount ?phase
    WHERE {
        ?company a ex:Startup ;
                ex:name ?company_name ;
                ex:hasIndustry ?industry .
        ?industry ex:name "cleantech" .
        ?company ex:hasFunding ?funding .
        OPTIONAL { ?funding ex:round_date ?date }
        OPTIONAL { ?funding ex:amount ?amount }
        OPTIONAL { ?funding ex:phase ?phase }
    }
    ORDER BY ?date
    """

    results = list(graph.query(query))
    print(f"Found {len(results)} funding rounds for cleantech companies")

    # Analyze the results
    funding_by_year = defaultdict(
        lambda: {"total": 0, "count": 0, "companies": set(), "phases": defaultdict(int)}
    )

    for row in results:
        if row.date:
            try:
                year = int(str(row.date)[:4])
                company = str(row.company_name)
                funding_by_year[year]["companies"].add(company)
                funding_by_year[year]["count"] += 1

                if row.phase:
                    phase = str(row.phase)
                    funding_by_year[year]["phases"][phase] += 1

                if row.amount:
                    amount = float(row.amount)
                    funding_by_year[year]["total"] += amount
            except (ValueError, TypeError):
                pass

    # Format the data for report
    report = {
        "overview": {
            "total_companies": len(set(str(row.company_name) for row in results)),
            "total_funding_rounds": len(results),
            "total_funding": sum(float(row.amount) for row in results if row.amount),
        },
        "yearly_data": {},
        "growth_rates": {},
        "insights": [],
    }

    years = sorted(funding_by_year.keys())
    for year in years:
        data = funding_by_year[year]
        report["yearly_data"][str(year)] = {
            "total_funding": data["total"],
            "number_of_rounds": data["count"],
            "number_of_companies": len(data["companies"]),
            "average_round_size": data["total"] / data["count"]
            if data["count"] > 0
            else 0,
            "phases": dict(data["phases"]),
        }

    # Calculate growth rates
    if len(years) > 1:
        for i in range(1, len(years)):
            prev_year = years[i - 1]
            curr_year = years[i]

            prev_funding = funding_by_year[prev_year]["total"]
            curr_funding = funding_by_year[curr_year]["total"]

            prev_rounds = funding_by_year[prev_year]["count"]
            curr_rounds = funding_by_year[curr_year]["count"]

            if prev_funding > 0:
                funding_growth = ((curr_funding - prev_funding) / prev_funding) * 100
            else:
                funding_growth = float("inf")  # Infinite growth from zero

            if prev_rounds > 0:
                rounds_growth = ((curr_rounds - prev_rounds) / prev_rounds) * 100
            else:
                rounds_growth = float("inf")  # Infinite growth from zero

            report["growth_rates"][str(curr_year)] = {
                "funding_growth": funding_growth,
                "rounds_growth": rounds_growth,
            }

    # Generate basic insights
    if len(years) >= 3:
        recent_years = years[-3:]
        recent_funding = [funding_by_year[y]["total"] for y in recent_years]
        recent_rounds = [funding_by_year[y]["count"] for y in recent_years]

        # Funding trend
        if recent_funding[0] < recent_funding[1] < recent_funding[2]:
            report["insights"].append(
                "Cleantech funding has been steadily increasing in recent years"
            )
        elif recent_funding[0] > recent_funding[1] > recent_funding[2]:
            report["insights"].append(
                "Cleantech funding has been declining in recent years"
            )

        # Round size trend
        recent_avg_size = [
            funding_by_year[y]["total"] / funding_by_year[y]["count"]
            if funding_by_year[y]["count"] > 0
            else 0
            for y in recent_years
        ]

        if recent_avg_size[0] < recent_avg_size[1] < recent_avg_size[2]:
            report["insights"].append(
                "Average round sizes are increasing, indicating maturing sector"
            )
        elif recent_avg_size[0] > recent_avg_size[1] > recent_avg_size[2]:
            report["insights"].append(
                "Average round sizes are decreasing, possibly indicating more early-stage activity"
            )

    # Add additional data: top funding phases overall
    phases = defaultdict(int)
    for row in results:
        if row.phase:
            phase = str(row.phase)
            phases[phase] += 1

    report["phase_distribution"] = dict(phases)

    # Return the cleantech data report
    return report


# Initialize chat history
system_prompt = """You are an expert in analyzing startup funding data, especially for cleantech companies.
You've been provided with detailed data about cleantech funding in Switzerland.
Please provide insights and analysis based on this data.
Focus on funding trends, growth rates, and phases of investment.
"""

chat_history = [SystemMessage(content=system_prompt)]


def analyze_cleantech():
    """Analyze cleantech funding data and provide insights"""
    # Get the cleantech funding data through direct SPARQL
    cleantech_data = get_cleantech_funding_data()

    # Format the analysis prompt
    analysis_prompt = f"""I've analyzed cleantech funding data and obtained the following results:

```
{json.dumps(cleantech_data, indent=2)}
```

Please provide a comprehensive analysis of the cleantech industry based on this data, including:

1. Overall funding trends and growth patterns
2. Changes in funding rounds and their sizes over time
3. Insights about the maturity of the cleantech sector
4. Observations about funding phases and what they indicate
5. Key takeaways about the state of cleantech investment

Your analysis should be data-driven and insightful, focusing on what the numbers tell us about the industry's trajectory."""

    # Send to LLM for analysis
    chat_history.append(HumanMessage(content=analysis_prompt))
    analysis_response = model.invoke(chat_history)
    analysis_content = analysis_response.content
    chat_history.append(AIMessage(content=analysis_content))

    # Return the formatted response
    return {"cleantech_data": cleantech_data, "analysis": analysis_content}


# Run the analysis when script is executed
if __name__ == "__main__":
    print("Analyzing cleantech industry funding...")
    analysis = analyze_cleantech()
    print("\nCLEANTECH INDUSTRY ANALYSIS:")
    print("=" * 80)
    print(analysis["analysis"])
    print("=" * 80)

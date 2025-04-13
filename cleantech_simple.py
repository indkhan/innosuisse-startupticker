from rdflib import Graph, Namespace, Literal
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np

# Initialize RDF graph
g = Graph()
g.parse("startups_graph.ttl", format="turtle")

# Define namespaces
EX = Namespace("http://example.org/ontology#")
RES = Namespace("http://example.org/resource/")

# Query for cleantech companies and their funding
print("\nAnalyzing cleantech companies with funding rounds:")
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

results = list(g.query(query))
print(f"Found {len(results)} funding rounds for cleantech companies")

# Analyze funding by year
funding_by_year = defaultdict(lambda: {"total": 0, "count": 0, "companies": set()})

for row in results:
    if row.date:
        try:
            year = int(str(row.date)[:4])
            company = str(row.company_name)
            funding_by_year[year]["companies"].add(company)
            funding_by_year[year]["count"] += 1

            if row.amount:
                amount = float(row.amount)
                funding_by_year[year]["total"] += amount
        except (ValueError, TypeError):
            pass

# Print results
print("\nCleantech Funding by Year:")
print("Year | Total Funding (CHF) | # Rounds | # Companies")
print("-" * 60)

years = sorted(funding_by_year.keys())
for year in years:
    data = funding_by_year[year]
    total = data["total"]
    count = data["count"]
    companies = len(data["companies"])
    print(f"{year} | {total:,.2f} | {count} | {companies}")

# Create a simple visualization of the data in text mode
print("\nFunding Amount Trend:")
for year in years:
    amount = funding_by_year[year]["total"]
    # Scale to millions and create a bar of * characters
    bar_length = int(amount / 10000000)  # 1 * = 10M CHF
    print(f"{year}: {'*' * bar_length} ({amount / 1000000:.1f}M CHF)")

print("\nNumber of Funding Rounds Trend:")
for year in years:
    count = funding_by_year[year]["count"]
    print(f"{year}: {'*' * count}")

# Calculate growth rates
if len(years) > 1:
    print("\nYear-over-Year Growth Rates:")
    print("Year | Funding Growth | Rounds Growth")
    print("-" * 45)

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

        print(f"{curr_year} | {funding_growth:+.1f}% | {rounds_growth:+.1f}%")

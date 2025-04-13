from rdflib import Graph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import XSD
from datetime import datetime, timedelta

# Load the RDF graph
print("Loading graph...")
g = Graph()
g.parse("startups_graph.ttl", format="turtle")
print("Graph loaded successfully")

# Define namespaces
ex = Namespace("http://example.org/ontology#")

# Calculate date range for last 5 years
current_year = datetime.now().year
start_year = current_year - 5

print(f"\nTech Sector Analysis ({start_year}-{current_year})")
print("=" * 80)

# 1. Industry Distribution
print("\n1. Industry Distribution in Tech Sector:")
query_industry = """
    SELECT ?industry_name (COUNT(DISTINCT ?startup) as ?count)
    WHERE {
        ?startup a ex:Startup ;
                ex:hasIndustry ?industry .
        ?industry ex:name ?industry_name .
        FILTER (STRSTARTS(?industry_name, "ICT") || ?industry_name = "biotech" || 
                ?industry_name = "medtech" || ?industry_name = "healthcare IT" ||
                ?industry_name = "micro/nano" || ?industry_name = "cleantech")
    }
    GROUP BY ?industry_name
    ORDER BY DESC(?count)
"""

try:
    results = g.query(query_industry)
    print("\nNumber of startups by industry:")
    for row in results:
        count = int(row.count.toPython())
        print(f"- {row.industry_name}: {count} startups")
except Exception as e:
    print(f"Error in industry distribution query: {e}")

# 2. Funding Trends
print("\n2. Funding Trends by Year:")
query_funding = """
    SELECT ?year (COUNT(DISTINCT ?funding) as ?funding_count) 
                 (SUM(?amount) as ?total_amount)
    WHERE {
        ?startup a ex:Startup ;
                ex:hasIndustry ?industry ;
                ex:hasFunding ?funding .
        ?industry ex:name ?industry_name .
        ?funding ex:amount ?amount ;
                ex:date ?funding_date .
        BIND (YEAR(?funding_date) as ?year)
        FILTER (?year >= %d && ?year <= %d)
        FILTER (STRSTARTS(?industry_name, "ICT") || ?industry_name = "biotech" || 
                ?industry_name = "medtech" || ?industry_name = "healthcare IT" ||
                ?industry_name = "micro/nano" || ?industry_name = "cleantech")
    }
    GROUP BY ?year
    ORDER BY ?year
""" % (start_year, current_year)

try:
    print("\nYear | Number of Funding Events | Total Amount (CHF)")
    print("-" * 50)
    results = g.query(query_funding)
    for row in results:
        year = int(row.year.toPython())
        count = int(row.funding_count.toPython())
        amount = float(row.total_amount.toPython())
        print(f"{year} | {count} | {amount:,.2f}")
except Exception as e:
    print(f"Error in funding trends query: {e}")

# 3. Funding Stages Distribution
print("\n3. Funding Stage Distribution:")
query_stages = """
    SELECT ?phase (COUNT(DISTINCT ?funding) as ?count)
    WHERE {
        ?startup a ex:Startup ;
                ex:hasIndustry ?industry ;
                ex:hasFunding ?funding .
        ?industry ex:name ?industry_name .
        ?funding ex:phase ?phase .
        FILTER (STRSTARTS(?industry_name, "ICT") || ?industry_name = "biotech" || 
                ?industry_name = "medtech" || ?industry_name = "healthcare IT" ||
                ?industry_name = "micro/nano" || ?industry_name = "cleantech")
    }
    GROUP BY ?phase
    ORDER BY DESC(?count)
"""

try:
    print("\nFunding stages distribution:")
    results = g.query(query_stages)
    for row in results:
        count = int(row.count.toPython())
        print(f"- {row.phase}: {count} funding events")
except Exception as e:
    print(f"Error in funding stages query: {e}")

# 4. Top Funded Companies
print("\n4. Top 10 Funded Companies:")
query_top_funded = """
    SELECT ?name (SUM(?amount) as ?total_funding)
    WHERE {
        ?startup a ex:Startup ;
                ex:name ?name ;
                ex:hasIndustry ?industry ;
                ex:hasFunding ?funding .
        ?industry ex:name ?industry_name .
        ?funding ex:amount ?amount .
        FILTER (STRSTARTS(?industry_name, "ICT") || ?industry_name = "biotech" || 
                ?industry_name = "medtech" || ?industry_name = "healthcare IT" ||
                ?industry_name = "micro/nano" || ?industry_name = "cleantech")
    }
    GROUP BY ?name
    ORDER BY DESC(?total_funding)
    LIMIT 10
"""

try:
    print("\nCompany | Total Funding (CHF)")
    print("-" * 40)
    results = g.query(query_top_funded)
    for row in results:
        amount = float(row.total_funding.toPython())
        print(f"{row.name} | {amount:,.2f}")
except Exception as e:
    print(f"Error in top funded companies query: {e}")

# 5. Geographic Distribution
print("\n5. Geographic Distribution of Tech Startups:")
query_location = """
    SELECT ?location (COUNT(DISTINCT ?startup) as ?count)
    WHERE {
        ?startup a ex:Startup ;
                ex:hasIndustry ?industry ;
                ex:hasLocation ?loc .
        ?industry ex:name ?industry_name .
        ?loc ex:name ?location .
        FILTER (STRSTARTS(?industry_name, "ICT") || ?industry_name = "biotech" || 
                ?industry_name = "medtech" || ?industry_name = "healthcare IT" ||
                ?industry_name = "micro/nano" || ?industry_name = "cleantech")
    }
    GROUP BY ?location
    ORDER BY DESC(?count)
"""

try:
    print("\nLocation | Number of Startups")
    print("-" * 40)
    results = g.query(query_location)
    for row in results:
        count = int(row.count.toPython())
        print(f"{row.location} | {count}")
except Exception as e:
    print(f"Error in geographic distribution query: {e}") 
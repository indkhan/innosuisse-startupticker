from rdflib import Graph, Namespace, XSD
from rdflib.namespace import RDF

# Load the RDF graph
print("Loading RDF graph...")
graph = Graph()
graph.parse("startups_graph.ttl", format="turtle")
print(f"Graph loaded. Total triples: {len(graph)}")

# Print some sample founding dates to see their format
print("\nSample founding dates in the graph:")
dates_query = """
PREFIX ex: <http://example.org/ontology#>
SELECT ?name ?date
WHERE {
    ?startup a ex:Startup .
    ?startup ex:name ?name .
    ?startup ex:foun_date ?date .
}
LIMIT 5
"""
dates_results = graph.query(dates_query)
for row in dates_results:
    print(f"Company: {row[0]}, Date: {row[1]}")

# Define namespaces
EX = Namespace("http://example.org/ontology#")
RES = Namespace("http://example.org/resource/")
graph.bind("ex", EX)
graph.bind("res", RES)

# Query for companies founded after 2022
query = """
PREFIX ex: <http://example.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?startup ?name ?founding_date ?industry_name ?canton 
       ?funding_round ?funding_date ?funding_amount ?funding_currency
       ?investor_name ?investor_type
WHERE {
    ?startup a ex:Startup .
    ?startup ex:name ?name .
    ?startup ex:foun_date ?founding_date .
    FILTER (xsd:integer(?founding_date) >= 2022)
    
    # Optional industry information
    OPTIONAL {
        ?startup ex:hasIndustry ?industry .
        ?industry ex:name ?industry_name .
    }
    
    # Optional location information
    OPTIONAL {
        ?startup ex:hasLocation ?canton_uri .
        ?canton_uri ex:name ?canton .
    }
    
    # Optional funding information
    OPTIONAL {
        ?startup ex:hasFunding ?funding_round .
        ?funding_round ex:date ?funding_date .
        ?funding_round ex:amount ?funding_amount .
        ?funding_round ex:currency ?funding_currency .
        
        # Optional investor information
        OPTIONAL {
            ?funding_round ex:hasInvestor ?investor .
            ?investor ex:name ?investor_name .
            ?investor ex:type ?investor_type .
        }
    }
}
ORDER BY DESC(?founding_date)
"""

# Execute the query
print("\nCompanies founded after 2022:")
results = graph.query(query)
for row in results:
    startup, name, founding_date, industry, canton, funding_round, funding_date, funding_amount, funding_currency, investor_name, investor_type = row
    
    print(f"\nCompany: {name}")
    print(f"Founded: {founding_date}")
    if industry:
        print(f"Industry: {industry}")
    if canton:
        print(f"Canton: {canton}")
    
    # Print funding information if available
    if funding_round:
        print("\nFunding Information:")
        if funding_date:
            print(f"Date: {funding_date}")
        if funding_amount:
            print(f"Amount: {funding_amount} {funding_currency}")
        if investor_name:
            print(f"Investor: {investor_name} ({investor_type})")
    
    print("-" * 60)

print(f"\nTotal companies founded after 2022: {len(list(results))}") 
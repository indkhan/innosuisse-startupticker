from rdflib import Graph, Namespace, RDF, XSD

# Load the RDF graph
print("Loading RDF graph...")
graph = Graph()
graph.parse('startups_graph.ttl', format='turtle')

# Define namespaces
EX = Namespace("http://example.org/ontology#")
RES = Namespace("http://example.org/resource/")

# Query to check company-funding relationships
print("\nChecking Company-Funding Relationships:")
query = """
SELECT ?company ?company_name ?funding_round ?funding_date ?amount ?currency
WHERE {
    ?company a ex:Startup .
    ?company ex:name ?company_name .
    ?company ex:hasFunding ?funding_round .
    OPTIONAL { ?funding_round ex:date ?funding_date }
    OPTIONAL { ?funding_round ex:amount ?amount }
    OPTIONAL { ?funding_round ex:currency ?currency }
}
"""

print("\nCompany-Funding Relationships:")
for row in graph.query(query, initNs={'ex': EX}):
    print(f"\nCompany: {row.company_name}")
    print(f"Company URI: {row.company}")
    print(f"Funding Round URI: {row.funding_round}")
    if row.funding_date:
        print(f"Funding Date: {row.funding_date}")
    if row.amount:
        print(f"Amount: {row.amount}")
    if row.currency:
        print(f"Currency: {row.currency}")
    print("-" * 50)

# Query to check funding-investor relationships
print("\nChecking Funding-Investor Relationships:")
investor_query = """
SELECT ?company_name ?funding_round ?investor_name ?investor_type
WHERE {
    ?company a ex:Startup .
    ?company ex:name ?company_name .
    ?company ex:hasFunding ?funding_round .
    ?funding_round ex:hasInvestor ?investor_uri .
    ?investor_uri ex:name ?investor_name .
    OPTIONAL { ?investor_uri ex:type ?investor_type }
}
"""

print("\nFunding-Investor Relationships:")
for row in graph.query(investor_query, initNs={'ex': EX}):
    print(f"\nCompany: {row.company_name}")
    print(f"Funding Round URI: {row.funding_round}")
    print(f"Investor: {row.investor_name}")
    if row.investor_type:
        print(f"Investor Type: {row.investor_type}")
    print("-" * 50)

# Query to count relationships
print("\nCounting Relationships:")
count_query = """
SELECT (COUNT(DISTINCT ?company) as ?company_count)
       (COUNT(DISTINCT ?funding) as ?funding_count)
       (COUNT(DISTINCT ?investor) as ?investor_count)
WHERE {
    ?company a ex:Startup .
    OPTIONAL { ?company ex:hasFunding ?funding }
    OPTIONAL { ?funding ex:hasInvestor ?investor }
}
"""

results = graph.query(count_query, initNs={'ex': EX})
for row in results:
    print(f"Total Companies: {row.company_count}")
    print(f"Total Funding Rounds: {row.funding_count}")
    print(f"Total Investors: {row.investor_count}") 
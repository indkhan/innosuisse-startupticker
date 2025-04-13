from rdflib import Graph, Namespace, RDF, XSD

# Load the RDF graph
print("Loading RDF graph...")
graph = Graph()
graph.parse('startups_graph.ttl', format='turtle')

# Define namespaces
EX = Namespace("http://example.org/ontology#")
RES = Namespace("http://example.org/resource/")

# Query 1: Show basic company information
print("\nExample 1: Basic Company Information")
query1 = """
SELECT ?company ?name ?founding_year ?industry ?canton
WHERE {
    ?company a ex:Startup .
    ?company ex:name ?name .
    OPTIONAL { ?company ex:foun_date ?founding_year }
    OPTIONAL { 
        ?company ex:hasIndustry ?industry_uri .
        ?industry_uri ex:name ?industry
    }
    OPTIONAL {
        ?company ex:hasLocation ?canton_uri .
        ?canton_uri ex:name ?canton
    }
}
LIMIT 3
"""

print("\nSample Companies:")
for row in graph.query(query1, initNs={'ex': EX}):
    print(f"\nCompany: {row.name}")
    if row.founding_year:
        print(f"Founded: {row.founding_year}")
    if row.industry:
        print(f"Industry: {row.industry}")
    if row.canton:
        print(f"Canton: {row.canton}")

# Query 2: Show funding information
print("\nExample 2: Funding Information")
query2 = """
SELECT ?company ?name ?funding_date ?amount ?currency ?investor ?investor_type
WHERE {
    ?company a ex:Startup .
    ?company ex:name ?name .
    ?company ex:hasFunding ?funding_round .
    OPTIONAL { ?funding_round ex:date ?funding_date }
    OPTIONAL { ?funding_round ex:amount ?amount }
    OPTIONAL { ?funding_round ex:currency ?currency }
    OPTIONAL {
        ?funding_round ex:hasInvestor ?investor_uri .
        ?investor_uri ex:name ?investor
        OPTIONAL { ?investor_uri ex:type ?investor_type }
    }
}
LIMIT 3
"""

print("\nSample Funding Rounds:")
for row in graph.query(query2, initNs={'ex': EX}):
    print(f"\nCompany: {row.name}")
    if row.funding_date:
        print(f"Funding Date: {row.funding_date}")
    if row.amount:
        print(f"Amount: {row.amount}")
    if row.currency:
        print(f"Currency: {row.currency}")
    if row.investor:
        print(f"Investor: {row.investor}")
        if row.investor_type:
            print(f"Investor Type: {row.investor_type}")

# Query 3: Show the actual RDF triples for one company
print("\nExample 3: Raw RDF Triples for a Company")
query3 = """
SELECT ?subject ?predicate ?object
WHERE {
    ?subject a ex:Startup .
    ?subject ex:name ?name .
    ?subject ?predicate ?object .
}
LIMIT 10
"""

print("\nSample RDF Triples:")
for row in graph.query(query3, initNs={'ex': EX}):
    print(f"{row.subject} {row.predicate} {row.object}") 
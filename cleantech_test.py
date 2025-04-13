from rdflib import Graph, Namespace

# Initialize RDF graph
g = Graph()
g.parse("startups_graph.ttl", format="turtle")

# Define namespaces
EX = Namespace("http://example.org/ontology#")
RES = Namespace("http://example.org/resource/")

# Test a basic query for cleantech companies with funding data
print("\nQuerying cleantech companies with funding:")
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
LIMIT 20
"""

results = g.query(query)
print("\nCleantech companies with funding data:")
for row in results:
    print(
        f"Company: {row.company_name}, Date: {row.date}, Amount: {row.amount}, Phase: {row.phase}"
    )

# Check the location structure used in the data
print("\nChecking location structure:")
location_query = """
PREFIX ex: <http://example.org/ontology#>
PREFIX res: <http://example.org/resource/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?predicate (COUNT(?predicate) as ?count)
WHERE {
    ?company a ex:Startup .
    ?company ?predicate ?location .
    FILTER(CONTAINS(STR(?predicate), "locat"))
}
GROUP BY ?predicate
"""

results = g.query(location_query)
print("\nLocation predicates used in the data:")
for row in results:
    print(f"Predicate: {row.predicate}, Count: {row.count}")

# Try a query with the correct location structure
print("\nQuerying cleantech companies with location and funding:")
full_query = """
PREFIX ex: <http://example.org/ontology#>
PREFIX res: <http://example.org/resource/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?company_name ?date ?amount ?phase 
WHERE {
    ?company a ex:Startup ;
            ex:name ?company_name ;
            ex:hasIndustry ?industry .
    ?industry ex:name "cleantech" .
    
    # Funding data (required)
    ?company ex:hasFunding ?funding .
    OPTIONAL { ?funding ex:round_date ?date }
    OPTIONAL { ?funding ex:amount ?amount }
    OPTIONAL { ?funding ex:phase ?phase }
    
    # Optional location info
    OPTIONAL {
        ?company ex:hasLocation ?location .
        ?location ex:name ?location_name .
    }
}
ORDER BY ?date
LIMIT 20
"""

results = g.query(full_query)
print("\nCleantech companies with location and funding data:")
count = 0
for row in results:
    count += 1
    print(
        f"Company: {row.company_name}, Date: {row.date}, Amount: {row.amount}, Phase: {row.phase}"
    )

print(f"\nTotal results: {count}")

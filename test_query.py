from rdflib import Graph, Namespace

# Initialize RDF graph
g = Graph()
g.parse("startups_graph.ttl", format="turtle")

# Define namespaces
EX = Namespace("http://example.org/ontology#")
RES = Namespace("http://example.org/resource/")

# Test a query specifically for round_date
print("\nRunning healthcare IT query with round_date:")
query = """
PREFIX ex: <http://example.org/ontology#>
PREFIX res: <http://example.org/resource/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?company_name ?date ?amount ?phase
WHERE {
    ?company a ex:Startup ;
            ex:name ?company_name ;
            ex:hasIndustry ?industry .
    ?industry ex:name "healthcare IT" .
    OPTIONAL {
        ?company ex:hasFunding ?funding .
        OPTIONAL { ?funding ex:round_date ?date }
        OPTIONAL { ?funding ex:amount ?amount }
        OPTIONAL { ?funding ex:phase ?phase }
    }
}
ORDER BY ?date
LIMIT 20
"""

results = g.query(query)
print("\nResults with round_date:")
for row in results:
    print(
        f"Company: {row.company_name}, Date: {row.date}, Amount: {row.amount}, Phase: {row.phase}"
    )

# Check companies that have round_date values
print("\nChecking companies with valid funding dates:")
query_dates = """
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
    ?funding ex:round_date ?date .
    OPTIONAL { ?funding ex:amount ?amount }
    OPTIONAL { ?funding ex:phase ?phase }
}
ORDER BY ?date
LIMIT 10
"""

results = g.query(query_dates)
print("\nCompanies with funding dates:")
for row in results:
    print(
        f"Company: {row.company_name}, Date: {row.date}, Amount: {row.amount}, Phase: {row.phase}"
    )

from rdflib import Graph, Namespace

# Initialize RDF graph
g = Graph()
g.parse("startups_graph.ttl", format="turtle")

# Define namespaces
EX = Namespace("http://example.org/ontology#")
RES = Namespace("http://example.org/resource/")

# Find all industry names that might be related to healthcare
print("\nSearching for healthcare-related industries:")
healthcare_related = []
for s, p, o in g.triples((None, EX.name, None)):
    if "industry" in str(s).lower():
        name = str(o)
        if (
            "health" in name.lower()
            or "medtech" in name.lower()
            or "life" in name.lower()
            or "bio" in name.lower()
        ):
            healthcare_related.append(name)
            print(f"Found healthcare-related industry: {name}")

# Try querying with 'healthcare IT'
print("\nQuerying for 'healthcare IT' companies:")
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
        OPTIONAL { ?funding ex:date ?date }
        OPTIONAL { ?funding ex:amount ?amount }
        OPTIONAL { ?funding ex:phase ?phase }
    }
}
ORDER BY ?date
"""

results = g.query(query)
for row in results:
    print(f"Company: {row.company_name}")

# Try querying with 'medtech'
print("\nQuerying for 'medtech' companies:")
query = """
PREFIX ex: <http://example.org/ontology#>
PREFIX res: <http://example.org/resource/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?company_name ?date ?amount ?phase
WHERE {
    ?company a ex:Startup ;
            ex:name ?company_name ;
            ex:hasIndustry ?industry .
    ?industry ex:name "medtech" .
    OPTIONAL {
        ?company ex:hasFunding ?funding .
        OPTIONAL { ?funding ex:date ?date }
        OPTIONAL { ?funding ex:amount ?amount }
        OPTIONAL { ?funding ex:phase ?phase }
    }
}
ORDER BY ?date
LIMIT 5
"""

results = g.query(query)
for row in results:
    print(f"Company: {row.company_name}")

from rdflib import Graph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import XSD

# Load the RDF graph
print("Loading graph...")
g = Graph()
g.parse("startups_graph.ttl", format="turtle")
print("Graph loaded successfully")

# Define namespaces
ex = Namespace("http://example.org/ontology#")

# Query for cleantech startups with complete data
query = """
    SELECT DISTINCT ?name ?founding_date ?location ?highlights ?amount ?type ?phase
    WHERE {
        ?startup a ex:Startup ;
                ex:name ?name ;
                ex:hasIndustry ?industry ;
                ex:foun_date ?founding_date ;
                ex:highlights ?highlights ;
                ex:hasLocation ?loc ;
                ex:hasFunding ?funding .
        
        ?industry ex:name "cleantech" .
        ?loc ex:name ?location .
        ?funding ex:amount ?amount ;
                ex:type ?type ;
                ex:phase ?phase .
    }
    ORDER BY ?name
"""

print("\nCleantech Startups with Complete Data:")
print("Note: These companies have all fields filled (name, founding date, location, highlights, and funding information)")
print("-" * 80)

results = g.query(query)
current_company = None

for row in results:
    # Print company info only when we switch to a new company
    if current_company != row.name:
        if current_company is not None:
            print("-" * 40)
        current_company = row.name
        print(f"\nCompany: {row.name}")
        print(f"Founded: {row.founding_date}")
        print(f"Location: {row.location}")
        print(f"Highlights: {row.highlights}")
    
    # Print funding info
    funding_info = [
        f"Amount: {row.amount}",
        f"Type: {row.type}",
        f"Phase: {row.phase}"
    ]
    print(" | ".join(funding_info)) 
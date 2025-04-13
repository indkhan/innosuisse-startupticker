from rdflib import Graph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import XSD

# Load the RDF graph
print("Loading graph...")
g = Graph()
g.parse("startups_graph.ttl", format="turtle")
print("Graph loaded successfully")

# Define namespaces
ex = Namespace("http://example.org/ontology#")

# Query for all information about cleantech startups
query = """
    SELECT DISTINCT ?name ?founding_date ?location ?highlights ?amount ?type ?phase
    WHERE {
        ?startup a ex:Startup ;
                ex:name ?name ;
                ex:hasIndustry ?industry .
        ?industry ex:name "cleantech" .
        
        OPTIONAL { ?startup ex:foun_date ?founding_date }
        OPTIONAL { 
            ?startup ex:hasLocation ?loc .
            ?loc ex:name ?location 
        }
        OPTIONAL { ?startup ex:highlights ?highlights }
        OPTIONAL { 
            ?startup ex:hasFunding ?funding .
            OPTIONAL { ?funding ex:amount ?amount }
            OPTIONAL { ?funding ex:type ?type }
            OPTIONAL { ?funding ex:phase ?phase }
        }
    }
    ORDER BY ?name ?amount
"""

print("\nCleantech Startups Information:")
print("Note: Only company names are guaranteed to be present. Other fields may be empty.")
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
        
        if row.founding_date:
            print(f"Founded: {row.founding_date}")
        
        if row.location:
            print(f"Location: {row.location}")
        
        if row.highlights:
            print(f"Highlights: {row.highlights}")
    
    # Print funding info if available
    if any([row.amount, row.type, row.phase]):
        funding_info = []
        if row.amount:
            funding_info.append(f"Amount: {row.amount}")
        if row.type:
            funding_info.append(f"Type: {row.type}")
        if row.phase:
            funding_info.append(f"Phase: {row.phase}")
        if funding_info:
            print(" | ".join(funding_info))


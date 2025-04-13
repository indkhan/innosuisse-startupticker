from rdflib import Graph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import XSD

# Load the RDF graph
print("Loading graph...")
g = Graph()
g.parse("startups_graph.ttl", format="turtle")
print("Graph loaded successfully")

# Define namespaces
ex = Namespace("http://example.org/ontology#")

# First, get all cleantech companies
query = """
    SELECT DISTINCT ?name
    WHERE {
        ?startup a ex:Startup ;
                ex:name ?name ;
                ex:hasIndustry ?industry .
        ?industry ex:name "cleantech" .
    }
"""

print("\nCleantech Startups with Multiple Funding Events:")
print("-" * 80)

results = g.query(query)
for row in results:
    company_name = str(row.name)
    
    # For each company, get their funding events
    funding_query = """
        SELECT ?amount ?type ?phase
        WHERE {
            ?startup a ex:Startup ;
                    ex:name ?name ;
                    ex:hasFunding ?funding .
            ?funding ex:amount ?amount ;
                    ex:type ?type ;
                    ex:phase ?phase .
        }
        VALUES ?name { "%s" }
    """ % company_name
    
    funding_results = list(g.query(funding_query))
    
    # Only show companies with multiple funding events
    if len(funding_results) > 1:
        # Get company details
        details_query = """
            SELECT ?founding_date ?location ?highlights
            WHERE {
                ?startup a ex:Startup ;
                        ex:name ?name ;
                        ex:foun_date ?founding_date ;
                        ex:hasLocation ?loc ;
                        ex:highlights ?highlights .
                ?loc ex:name ?location .
            }
            VALUES ?name { "%s" }
        """ % company_name
        
        details = list(g.query(details_query))
        if details:
            detail = details[0]
            print(f"\nCompany: {company_name}")
            print(f"Founded: {detail.founding_date}")
            print(f"Location: {detail.location}")
            print(f"Highlights: {detail.highlights}")
            print(f"Total Funding Events: {len(funding_results)}")
            
            print("\nFunding Events:")
            for i, funding in enumerate(funding_results, 1):
                print(f"Event {i}:")
                print(f"  Amount: {funding.amount}")
                print(f"  Type: {funding.type}")
                print(f"  Phase: {funding.phase}")
            
            print("-" * 40) 
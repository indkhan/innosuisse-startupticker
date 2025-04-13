from rdflib import Graph, Namespace
from collections import defaultdict

# Initialize RDF graph
g = Graph()
g.parse("startups_graph.ttl", format="turtle")

# Define namespaces
EX = Namespace("http://example.org/ontology#")
RES = Namespace("http://example.org/resource/")

# Check available properties for funding events
print("\nChecking properties available for funding events:")
properties = defaultdict(int)

# First get some funding events
funding_events = []
for s, p, o in g.triples((None, EX.hasFunding, None)):
    funding_events.append(o)
    if len(funding_events) >= 10:
        break

print(f"Found {len(funding_events)} funding events to analyze")

# Check what properties these funding events have
for event in funding_events:
    for s, p, o in g.triples((event, None, None)):
        prop_name = str(p).split("#")[-1]
        properties[prop_name] += 1
        # Print some sample values
        if len(properties) <= 10:
            print(f"Property: {prop_name}, Value: {o}")

print("\nProperty counts:")
for prop, count in sorted(properties.items(), key=lambda x: x[1], reverse=True):
    print(f"- {prop}: {count} occurrences")

# Test a query with round_date instead of date
print("\nTesting query with round_date instead of date:")
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
    OPTIONAL {
        ?company ex:hasFunding ?funding .
        OPTIONAL { ?funding ex:round_date ?date }
        OPTIONAL { ?funding ex:amount ?amount }
        OPTIONAL { ?funding ex:phase ?phase }
    }
}
ORDER BY ?date
LIMIT 10
"""

results = g.query(query)
print("\nResults with round_date:")
for row in results:
    print(
        f"Company: {row.company_name}, Date: {row.date}, Amount: {row.amount}, Phase: {row.phase}"
    )

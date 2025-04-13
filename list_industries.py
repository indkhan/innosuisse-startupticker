from rdflib import Graph, Namespace

# Initialize RDF graph
graph = Graph()
graph.parse("startups_graph.ttl", format="turtle")

# Define namespaces
EX = Namespace("http://example.org/ontology#")
RES = Namespace("http://example.org/resource/")

# Find all industry names to see how they're stored
print("\nAll industry names in the graph:")
industry_names = set()
for s, p, o in graph.triples((None, EX.name, None)):
    if "industry" in str(s).lower():
        industry_names.add(str(o))
print("\nFound industry names:", sorted(industry_names))

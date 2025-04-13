from rdflib import Graph, Namespace

# Initialize RDF graph
graph = Graph()
graph.parse('startups_graph.ttl', format='turtle')

# Define namespaces
EX = Namespace("http://example.org/ontology#")
RES = Namespace("http://example.org/resource/")

print("Looking for cleantech companies...")

# First, let's find all industry names to see how they're stored
print("\nAll industry names in the graph:")
industry_names = set()
for s, p, o in graph.triples((None, EX.name, None)):
    if 'industry' in str(s).lower():
        industry_names.add(str(o))
print("\nFound industry names:", sorted(industry_names))

# Now let's find startups with cleantech industry
print("\nSearching for cleantech companies...")
for s, p, o in graph.triples((None, EX.hasIndustry, None)):
    # Get the industry name
    for _, _, name in graph.triples((o, EX.name, None)):
        if 'clean' in str(name).lower():
            print(f"\nFound cleantech company:")
            print(f"Startup: {s}")
            print(f"Industry: {name}")
            # Get the startup name
            for _, _, startup_name in graph.triples((s, EX.name, None)):
                print(f"Company name: {startup_name}") 
from rdflib import Graph
import sys

print(f"Python version: {sys.version}")

# First test with small file
print("\nTesting with small file...")
g_test = Graph()
try:
    g_test.parse("test.ttl", format="turtle")
    print("Small test file loaded successfully")
    print(f"Number of triples in test graph: {len(g_test)}")
except Exception as e:
    print(f"Error loading test file: {e}")
    sys.exit(1)

# Now try the main graph
print("\nAttempting to load main graph...")
g = Graph()
try:
    g.parse("startups_graph.ttl", format="turtle")
    print("Main graph loaded successfully")
    print(f"Number of triples in main graph: {len(g)}")
except Exception as e:
    print(f"Error loading main graph: {e}")
    sys.exit(1)

print("\nTest completed") 
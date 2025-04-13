from rdflib import Graph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import XSD
from datetime import datetime, timedelta
import sys
import os

# Print environment info
print(f"Python version: {sys.version}")
try:
    import rdflib
    print(f"RDFLib version: {rdflib.__version__}")
except Exception as e:
    print(f"Error getting RDFLib version: {e}")

# Check if file exists and its size
ttl_file = "startups_graph.ttl"
if os.path.exists(ttl_file):
    print(f"\nFile exists: {ttl_file}")
    print(f"File size: {os.path.getsize(ttl_file)} bytes")
else:
    print(f"\nFile not found: {ttl_file}")
    sys.exit(1)

# Load the RDF graph in chunks
print("\nAttempting to load graph...")
g = Graph()

try:
    # Try to read first few lines of the file to verify it's readable
    with open(ttl_file, 'r', encoding='utf-8') as f:
        first_lines = [next(f) for _ in range(5)]
        print("\nFirst few lines of the file:")
        for line in first_lines:
            print(line.strip())
except Exception as e:
    print(f"Error reading file: {e}")
    sys.exit(1)

try:
    g.parse(ttl_file, format="turtle")
    print("\nGraph loaded successfully")
    print(f"Number of triples in graph: {len(g)}")
except Exception as e:
    print(f"Error loading graph: {e}")
    print("\nTrying alternative parsing method...")
    try:
        # Try alternative parsing method
        g_alt = Graph()
        with open(ttl_file, 'r', encoding='utf-8') as f:
            content = f.read()
        g_alt.parse(data=content, format="turtle")
        g = g_alt
        print("Graph loaded successfully using alternative method")
        print(f"Number of triples in graph: {len(g)}")
    except Exception as e2:
        print(f"Alternative parsing also failed: {e2}")
        sys.exit(1)

# Define namespaces
ex = Namespace("http://example.org/ontology#")

# Test simple query first
print("\nTesting simple query...")
test_query = """
    SELECT (COUNT(?s) as ?count)
    WHERE {
        ?s a ex:Startup .
    }
"""

try:
    results = g.query(test_query)
    for row in results:
        print(f"Total number of startups: {row.count}")
except Exception as e:
    print(f"Error in test query: {e}")
    sys.exit(1)

# If we get here, basic querying works. Now try the industry distribution
print("\n1. Industry Distribution:")
query_industry = """
    SELECT ?industry_name (COUNT(DISTINCT ?startup) as ?count)
    WHERE {
        ?startup a ex:Startup ;
                ex:hasIndustry ?industry .
        ?industry ex:name ?industry_name .
    }
    GROUP BY ?industry_name
    ORDER BY DESC(?count)
"""

try:
    results = g.query(query_industry)
    print("\nNumber of startups by industry:")
    for row in results:
        try:
            count = int(row.count.toPython())
            industry = str(row.industry_name)
            print(f"- {industry}: {count} startups")
        except Exception as e:
            print(f"Error processing row: {e}")
            print(f"Raw row data: {row}")
except Exception as e:
    print(f"Error in industry distribution query: {e}")

print("\nScript completed successfully") 
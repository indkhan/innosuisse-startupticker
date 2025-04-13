from rdflib import Graph, Namespace, XSD

# Load the RDF graph from your Turtle file
graph = Graph()
graph.parse("startups_graph.ttl", format="turtle")

# Define your namespace based on your ontology IRI
# (Adjust the IRI to match your actual ontology IRI)
EX = Namespace("http://example.org/ontology#")
graph.bind("ex", EX)

# Debug: Print all unique predicates in the graph
print("\nDebug: All unique predicates in the graph:")
predicates = set()
for s, p, o in graph.triples((None, None, None)):
    predicates.add(p)
for pred in sorted(predicates):
    print(f"Predicate: {pred}")

# Debug: Print a sample of data for one startup to see its structure
print("\nDebug: Sample data for one startup:")
sample_startup = None
for s, p, o in graph.triples((None, None, None)):
    if str(p) == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type" and str(o) == "http://example.org/ontology#Startup":
        sample_startup = s
        break

if sample_startup:
    print(f"\nProperties for startup {sample_startup}:")
    for s, p, o in graph.triples((sample_startup, None, None)):
        print(f"Predicate: {p}")
        print(f"Object: {o}")
        print("---")

# First, let's check what funding data exists
print("\nChecking funding data in the graph...")
funding_query = """PREFIX ex: <http://example.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?funding_event ?amount ?startup
WHERE {
  ?funding_event a ex:FundingEvent .
  ?funding_event ex:amount ?amount .
  ?funding_event ex:hasStartup ?startup .
}
ORDER BY DESC(xsd:decimal(?amount))"""

funding_results = graph.query(funding_query)
funding_count = len(list(funding_results))

if funding_count == 0:
    print("No funding events found in the graph.")
    print("\nLet's check what predicates exist in the graph:")
    predicates = set()
    for s, p, o in graph.triples((None, None, None)):
        predicates.add(p)
    print("\nAll predicates in the graph:")
    for pred in sorted(predicates):
        print(f"Predicate: {pred}")
else:
    print(f"\nFound {funding_count} funding events. Here are the top 10 by amount:")
    for row in list(funding_results)[:10]:
        funding_event, amount, startup = row
        print(f"Startup: {startup}")
        print(f"Amount: {float(amount):,.2f} CHF")
        print("-" * 40)

# Define a SPARQL query that uses the ontology:
sparql_query = """PREFIX ex: <http://example.org/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?startup ?name ?foun_date ?industry ?city ?canton
WHERE {
  ?startup a ex:Startup .
  ?startup ex:foun_date ?foun_date .
  FILTER (xsd:date(?foun_date) >= "2008-01-01"^^xsd:date)
  
  OPTIONAL { ?startup ex:name ?name }
  OPTIONAL { 
    ?startup ex:hasIndustry ?industry_uri .
    ?industry_uri a ex:Industry .
    BIND(?industry_uri AS ?industry)
  }
  OPTIONAL {
    ?startup ex:hasLocation ?canton_uri .
    ?canton_uri a ex:Canton .
    ?canton_uri ex:name ?canton .
    OPTIONAL {
      ?canton_uri ex:hasCity ?city_uri .
      ?city_uri ex:name ?city
    }
  }
}
ORDER BY DESC(?foun_date)"""

# Execute the SPARQL query on the RDF graph
results = graph.query(sparql_query)

# Process and print the query results
print("\nStartups founded after 2008:")
for row in results:
    startup, name, foun_date, industry, city, canton = row
    print(f"Startup URI: {startup}")
    if name:
        print(f"Name: {name}")
    print(f"Founded On: {foun_date}")
    if industry:
        print(f"Industry: {industry}")
    if canton:
        print(f"Canton: {canton}")
    if city:
        print(f"City: {city}")
    print("-" * 40)

# Print summary
print(f"\nTotal startups founded after 2008: {len(list(results))}")

from rdflib import Graph, Namespace

# Initialize RDF graph
g = Graph()
g.parse("startups_graph.ttl", format="turtle")

# Define namespaces
EX = Namespace("http://example.org/ontology#")
RES = Namespace("http://example.org/resource/")

# Test a query for healthcare IT companies with funding data
print("\nQuerying healthcare IT companies:")
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
    ?company ex:hasFunding ?funding .
    OPTIONAL { ?funding ex:round_date ?date }
    OPTIONAL { ?funding ex:amount ?amount }
    OPTIONAL { ?funding ex:phase ?phase }
}
ORDER BY ?date
LIMIT 20
"""

results = g.query(query)
print("\nHealthcare IT companies with funding data:")
for row in results:
    print(
        f"Company: {row.company_name}, Date: {row.date}, Amount: {row.amount}, Phase: {row.phase}"
    )

# Count companies by industry
print("\nCounting companies by industry:")
count_query = """
PREFIX ex: <http://example.org/ontology#>
PREFIX res: <http://example.org/resource/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?industry_name (COUNT(DISTINCT ?company) as ?count)
WHERE {
    ?company a ex:Startup ;
            ex:hasIndustry ?industry .
    ?industry ex:name ?industry_name .
}
GROUP BY ?industry_name
ORDER BY DESC(?count)
"""

results = g.query(count_query)
print("\nCompany counts by industry:")
for row in results:
    print(f"Industry: {row.industry_name}, Company Count: {row.count}")

# Count funding events by industry
print("\nCounting funding events by industry:")
funding_query = """
PREFIX ex: <http://example.org/ontology#>
PREFIX res: <http://example.org/resource/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?industry_name (COUNT(?funding) as ?funding_count) (SUM(?amount) as ?total_funding)
WHERE {
    ?company a ex:Startup ;
            ex:hasIndustry ?industry ;
            ex:hasFunding ?funding .
    ?industry ex:name ?industry_name .
    OPTIONAL { ?funding ex:amount ?amount }
}
GROUP BY ?industry_name
ORDER BY DESC(?total_funding)
"""

results = g.query(funding_query)
print("\nFunding by industry:")
for row in results:
    total_funding = float(row.total_funding) if row.total_funding else 0
    print(
        f"Industry: {row.industry_name}, Funding Events: {row.funding_count}, Total Funding: {total_funding:,.2f} CHF"
    )

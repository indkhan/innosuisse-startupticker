from rdflib import Graph, Namespace
import os

# Initialize RDF graph
graph = Graph()
graph.parse('startups_graph.ttl', format='turtle')

# Define namespaces
EX = Namespace("http://example.org/ontology#")
RES = Namespace("http://example.org/resource/")

def execute_sparql(query):
    """Execute SPARQL query and return results"""
    try:
        results = graph.query(query)
        # Convert results to a list of dictionaries
        result_list = []
        for row in results:
            # Handle different types of results (single variables, multiple variables)
            if len(row) == 1:
                result_list.append({"result": str(row[0])})
            else:
                result_dict = {}
                for i, var in enumerate(results.vars):
                    result_dict[str(var)] = str(row[i])
                result_list.append(result_dict)
        return result_list
    except Exception as e:
        return f"Error executing SPARQL query: {str(e)}"

if __name__ == "__main__":
    # SPARQL query to find cleantech companies
    cleantech_query = """
    PREFIX ex: <http://example.org/ontology#>
    PREFIX res: <http://example.org/resource/>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT ?startup ?name WHERE {
      ?startup rdf:type ex:Startup .
      ?startup ex:name ?name .
      ?startup ex:hasIndustry ?industry .
      ?industry ex:name "cleantech" .
    }
    """
    
    print("Finding companies in the cleantech industry...")
    print("\n" + "="*80 + "\n")
    
    # Execute the query
    results = execute_sparql(cleantech_query)
    
    # Print results
    if isinstance(results, list):
        if not results:
            print("No cleantech companies found.")
        else:
            print(f"Found {len(results)} cleantech companies:")
            for result in results:
                print(f"Company: {result.get('name', 'N/A')}")
    else:
        print(f"Error: {results}") 
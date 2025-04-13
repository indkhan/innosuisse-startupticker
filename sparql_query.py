from rdflib import Graph
import sys

def run_sparql_query(ttl_file, query):
    """
    Run a SPARQL query on a TTL file and return the results.
    
    Args:
        ttl_file (str): Path to the TTL file
        query (str): SPARQL query to execute
    
    Returns:
        list: Query results
    """
    # Load the RDF graph from the TTL file
    g = Graph()
    g.parse(ttl_file, format="turtle")
    
    # Execute the query
    results = g.query(query)
    
    # Return the results
    return results

def main():
    if len(sys.argv) != 3:
        print("Usage: python sparql_query.py <ttl_file> <query_file>")
        print("Example: python sparql_query.py startups_graph.ttl query.sparql")
        sys.exit(1)
    
    ttl_file = sys.argv[1]
    query_file = sys.argv[2]
    
    try:
        # Read the SPARQL query from the file
        with open(query_file, 'r') as f:
            query = f.read()
        
        # Run the query
        results = run_sparql_query(ttl_file, query)
        
        # Print the results
        print("\nQuery Results:")
        print("-------------")
        for row in results:
            print(row)
            
    except FileNotFoundError:
        print(f"Error: Could not find file {ttl_file} or {query_file}")
    except Exception as e:
        print(f"Error executing query: {str(e)}")

if __name__ == "__main__":
    main() 
from industry_trends import analyze_industry_trends
from rdflib import Graph

def main():
    print("Loading RDF graph...")
    g = Graph()
    g.parse("startups_graph.ttl", format="turtle")
    print("Graph loaded successfully!")
    
    # Analyze cleantech industry trends
    analyze_industry_trends(g, "cleantech")

if __name__ == "__main__":
    main() 
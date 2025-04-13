from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, XSD
import json

# Load environment variables
load_dotenv()

# Initialize Gemini
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-001",
    temperature=0,
)

# Define namespaces
EX = Namespace("http://example.org/ontology#")
RES = Namespace("http://example.org/resource/")

# Load the RDF graph
def load_graph():
    g = Graph()
    g.parse("startups_graph.ttl", format="turtle")
    return g

# System prompt that explains the ontology and data structure
SYSTEM_PROMPT = """
You are a startup data analyst that can convert natural language queries into SPARQL queries and analyze the results.

Ontology Structure:
- Classes:
  * ex:Startup - Represents companies
  * ex:Industry - Represents industry classifications
  * ex:FundingEvent - Represents funding rounds
  * ex:Investor - Represents investors
  * ex:Location - Represents locations (canton/city)

- Properties:
  * ex:name - Name of entity
  * ex:hasIndustry - Links startup to industry
  * ex:hasLocation - Links startup to location
  * ex:hasFunding - Links startup to funding events
  * ex:amount - Funding amount
  * ex:phase - Funding stage (Seed, Early Stage, Later Stage)
  * ex:round_date - Date of funding round
  * ex:investor - Links funding to investors

Important Notes:
1. Only company name is guaranteed to exist, all other fields can be null
2. Use OPTIONAL patterns in SPARQL for non-required fields
3. Handle missing values gracefully in analysis
4. Amounts are in CHF
5. Dates are in YYYY-MM-DD format

Your task is to:
1. Convert the user's natural language query into a SPARQL query
2. Execute the query on the RDF graph
3. Analyze the results
4. Present findings in a clear, structured way

Example Query:
User: "Show me the top 5 funded companies in biotech"
SPARQL: 
SELECT ?company_name (SUM(?amount) as ?total_funding)
WHERE {
    ?company a ex:Startup ;
            ex:name ?company_name ;
            ex:hasIndustry ?industry .
    ?industry ex:name "biotech" .
    OPTIONAL {
        ?company ex:hasFunding ?funding .
        ?funding ex:amount ?amount .
    }
}
GROUP BY ?company_name
ORDER BY DESC(?total_funding)
LIMIT 5
"""

# Create the prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{query}"),
])

def execute_sparql(g, query):
    """Execute a SPARQL query and return results as JSON"""
    try:
        results = list(g.query(query))
        return json.dumps([dict(row) for row in results], default=str)
    except Exception as e:
        return f"Error executing query: {str(e)}"

def analyze_startup_data(query):
    """Main function to analyze startup data based on natural language query"""
    # Load the graph
    g = load_graph()
    
    # Create the chain
    chain = prompt | llm
    
    # Get the SPARQL query from the LLM
    result = chain.invoke({"query": query})
    
    # Extract SPARQL query from the response
    # (This is a simplified version - in practice you'd need more robust parsing)
    sparql_query = result.content.split("SPARQL:")[1].strip()
    
    # Execute the query
    query_results = execute_sparql(g, sparql_query)
    
    # Get analysis from LLM
    analysis_prompt = f"""
    Here are the results from the SPARQL query:
    {query_results}
    
    Please analyze these results and provide insights based on the original query:
    {query}
    """
    
    analysis = chain.invoke({"query": analysis_prompt})
    
    return {
        "sparql_query": sparql_query,
        "results": query_results,
        "analysis": analysis.content
    }

if __name__ == "__main__":
    # Example usage
    query = "Show me the funding trends in cleantech over the last 5 years"
    result = analyze_startup_data(query)
    
    print("\nSPARQL Query:")
    print(result["sparql_query"])
    print("\nResults:")
    print(result["results"])
    print("\nAnalysis:")
    print(result["analysis"]) 
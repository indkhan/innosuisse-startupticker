from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from rdflib import Graph, Namespace
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

# Load the RDF graph
def load_graph():
    g = Graph()
    g.parse("startups_graph.ttl", format="turtle")
    return g

# System prompt that explains the ontology and data structure
SYSTEM_PROMPT = """
You are a startup data analyst that can convert natural language queries into SPARQL queries and analyze the results.

Ontology Overview:
The RDF graph uses two main namespaces:
EX (http://example.org/ontology#) - for ontology terms
RES (http://example.org/resource/) - for resource instances

Core Classes:
Startup - Represents companies
Industry - Represents industry classifications
FundingEvent - Represents funding rounds
Investor - Represents investors
Canton - Represents Swiss regions
City - Represents cities

Data Properties and Relationships:
Startup Properties:
Required:
name (string) - Company name
Optional:
foun_date (integer) - Founding year
highlights (string) - Company description
hasIndustry - Links to industry classification
hasLocation - Links to location (canton/city)

Industry Properties:
name (string) - Name of the industry

Location Properties:
name (string) - Name of the location
partOf - Links city to canton (for city instances)

Funding Event Properties:
phase (string) - Funding stage/phase
type (string) - Type of funding
amount (decimal) - Funding amount in CHF
valuation (decimal) - Company valuation
round_date (date) - Date of funding round (YYYY-MM-DD)
investor - Links to investor

Investor Properties:
name (string) - Name of the investor

Data Types Used:
xsd:integer - For founding year
xsd:date - For funding round dates
xsd:decimal - For amounts and valuations
xsd:string - For names, descriptions, and other text fields

Key Relationships:
Startup → Industry (many-to-one)
Startup → Location (many-to-one)
Startup → FundingEvent (one-to-many)
FundingEvent → Investor (many-to-many)
City → Canton (many-to-one)

Important Notes:
1. Only company name is guaranteed to exist, all other fields can be null
2. Use OPTIONAL patterns in SPARQL for non-required fields
3. Handle missing values gracefully in analysis
4. Dates for the founding of a company are stored as an integer eg: 2022
5. Dates for the funding round are stored in XSD.date format (YYYY-MM-DD)
6. The graph is stored in a file called startups_graph.ttl
7. The dataset for the graph is in csv files companies.csv and deals.csv

Example Queries and SPARQL:

1. Natural Language: "Show me all startups founded in 2022"
SPARQL:
PREFIX ex: <http://example.org/ontology#>
SELECT ?startup ?name ?industry_name
WHERE {{
    ?startup a ex:Startup .
    ?startup ex:name ?name .
    ?startup ex:foun_date 2022 .
    OPTIONAL {{
        ?startup ex:hasIndustry ?industry .
        ?industry ex:name ?industry_name .
    }}
}}

2. Natural Language: "What are the trends in the cleantech industry?"
SPARQL:
PREFIX ex: <http://example.org/ontology#>
SELECT ?company_name ?date ?amount ?phase
WHERE {{
    ?company a ex:Startup ;
            ex:name ?company_name ;
            ex:hasIndustry ?industry .
    ?industry ex:name "cleantech" .
    OPTIONAL {{
        ?company ex:hasFunding ?funding .
        OPTIONAL {{ ?funding ex:round_date ?date }}
        OPTIONAL {{ ?funding ex:amount ?amount }}
        OPTIONAL {{ ?funding ex:phase ?phase }}
    }}
}}
ORDER BY ?date

3. Natural Language: "Show me the top funded companies in biotech"
SPARQL:
PREFIX ex: <http://example.org/ontology#>
SELECT ?name (SUM(?amount) as ?total_funding)
WHERE {{
    ?startup a ex:Startup ;
            ex:name ?name ;
            ex:hasIndustry ?industry .
    ?industry ex:name "biotech" .
    OPTIONAL {{
        ?startup ex:hasFunding ?funding .
        OPTIONAL {{ ?funding ex:amount ?amount }}
    }}
}}
GROUP BY ?name
ORDER BY DESC(?total_funding)
LIMIT 10

4. Natural Language: "Compare the performance of these companies: CUTISS AG, Augment IT, Cortex"
SPARQL:
PREFIX ex: <http://example.org/ontology#>
SELECT ?name ?industry_name ?location_name 
       (COUNT(?funding) as ?funding_rounds) (SUM(?amount) as ?total_funding)
WHERE {{
    ?startup a ex:Startup .
    ?startup ex:name ?name .
    OPTIONAL {{
        ?startup ex:hasIndustry ?industry .
        ?industry ex:name ?industry_name .
    }}
    OPTIONAL {{
        ?startup ex:hasLocation ?location .
        ?location ex:name ?location_name .
    }}
    OPTIONAL {{
        ?startup ex:hasFunding ?funding .
        OPTIONAL {{ ?funding ex:amount ?amount }}
    }}
    FILTER (?name IN ("CUTISS AG", "Augment IT", "Cortex"))
}}
GROUP BY ?name ?industry_name ?location_name

5. Natural Language: "Show me funding trends in cleantech over the last 5 years"
SPARQL:
PREFIX ex: <http://example.org/ontology#>
SELECT ?year (COUNT(?funding) as ?rounds) (SUM(?amount) as ?total_funding)
WHERE {{
    ?startup a ex:Startup ;
            ex:hasIndustry ?industry ;
            ex:hasFunding ?funding .
    ?industry ex:name "cleantech" .
    ?funding ex:round_date ?date ;
            ex:amount ?amount .
    BIND (SUBSTR(?date, 1, 4) as ?year)
    FILTER (?year >= "2019")
}}
GROUP BY ?year
ORDER BY ?year

Your task is to:
1. Convert the user's natural language query into a SPARQL query following these examples
2. Execute the query on the RDF graph
3. Analyze the results
4. Present findings in a clear, structured way

When responding, always format your SPARQL query like this:
SPARQL:
[your query here]
"""

# Create the prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{query}"),
])

def execute_sparql(g, query):
    """Execute a SPARQL query and return results as JSON"""
    try:
        results = g.query(query)
        # Convert results to a list of dictionaries
        json_results = []
        for row in results:
            row_dict = {}
            for var in row:
                # Get the variable name without the '?' prefix
                var_name = str(var).lstrip('?')
                # Get the value and convert it to a Python type
                value = row[var]
                if value is not None:
                    try:
                        # Convert RDF literals to Python types
                        if hasattr(value, 'toPython'):
                            value = value.toPython()
                        row_dict[var_name] = value
                    except Exception as e:
                        # If conversion fails, use string representation
                        row_dict[var_name] = str(value)
            json_results.append(row_dict)
        return json.dumps(json_results, default=str)
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
    
    # Debug: Print the raw response
    print("\nRaw LLM Response:")
    print(result.content)
    
    # Extract and clean SPARQL query from the response
    try:
        # Find the SPARQL query in the response
        if "SPARQL:" in result.content:
            query_part = result.content.split("SPARQL:")[1]
        else:
            query_part = result.content
        
        # Remove markdown formatting and backticks
        query_part = query_part.replace("```sparql", "").replace("```", "")
        query_part = query_part.strip()
        
        # Extract the actual query (everything after PREFIX)
        if "PREFIX" in query_part:
            query_part = query_part[query_part.find("PREFIX"):]
        
        sparql_query = query_part
        
    except Exception as e:
        print(f"Error extracting SPARQL query: {e}")
        print("Please make sure your query is clear and specific")
        return None
    
    # Debug: Print the cleaned query
    print("\nCleaned SPARQL Query:")
    print(sparql_query)
    
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

<<<<<<< HEAD
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
=======
print(result.content)
>>>>>>> 4b3fd859dd1450880c5c96794ac66fcab4d04571

from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from rdflib import Graph, Namespace
import json
import os

load_dotenv()

# Initialize RDF graph
graph = Graph()
graph.parse('startups_graph.ttl', format='turtle')

# Define namespaces
EX = Namespace("http://example.org/ontology#")
RES = Namespace("http://example.org/resource/")

# Initialize LLM
model = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)

# Create system message for SPARQL generation
system_prompt = """You are an expert in converting natural language queries to SPARQL queries for an RDF graph.
The graph uses the following ontology structure:

Namespaces:
- EX (http://example.org/ontology#) - for ontology terms
- RES (http://example.org/resource/) - for resource instances

Core Classes:
- Startup - Represents companies
- Industry - Represents industry classifications
- FundingEvent - Represents funding rounds
- Investor - Represents investors
- Canton - Represents Swiss regions
- City - Represents cities

Important Relationships:
- Startup hasFunding FundingEvent
- FundingEvent amount (in CHF)
- FundingEvent type (funding type)
- FundingEvent phase (funding phase)
- FundingEvent investor Investor

SPARQL Query Guidelines:
1. For aggregations (SUM, COUNT, etc.), use GROUP BY and HAVING clauses
2. Put aggregations in the SELECT clause, not in BIND
3. Use HAVING for filtering on aggregated values
4. Always include proper PREFIX declarations
5. When selecting multiple variables, make sure to bind them properly in the SELECT clause

When given a natural language query:
1. Convert it to a SPARQL query following these guidelines
2. Execute the query
3. Return both the raw data and analysis if needed

Remember that funding amounts are stored in actual CHF (not millions). For example, 50 million CHF would be stored as 50000000."""

# Initialize chat history with previous prompts and responses
chat_history = [SystemMessage(content=system_prompt)]

# Add previous feedback about cleantech query - this helps the model remember
industry_feedback = """The SPARQL query for finding cleantech companies needs to be fixed. 

In our RDF graph, industry names are stored exactly as "cleantech" (lowercase, case-sensitive). When querying for industries, we need to:

1. Find ?startup entities that have a hasIndustry relationship to an industry entity
2. Check that the industry entity has a name "cleantech" (exact match with lowercase)
3. Return the startup's name for better readability

Here's how the query structure should look:

```sparql
PREFIX ex: <http://example.org/ontology#>
PREFIX res: <http://example.org/resource/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?startup ?name WHERE {
  ?startup rdf:type ex:Startup .
  ?startup ex:name ?name .
  ?startup ex:hasIndustry ?industry .
  ?industry ex:name "cleantech" .
}
```

Please correct your query using this structure to find all companies in the cleantech industry. Remember that string literals in SPARQL are case-sensitive, and in our dataset "cleantech" is stored in lowercase.
"""

# Add previous feedback about funding query
funding_feedback = """Your SPARQL query for cleantech companies with high funding didn't return the correct results due to several issues:

1. You used the incorrect predicate `ex:isInIndustry` to connect startups to industries. The correct predicate is `ex:hasIndustry`.

2. Remember that industry names in our graph are stored as "cleantech" (lowercase, case-sensitive).

3. You should select both the startup name and funding amount to provide more useful results.

4. It's helpful to order the results by funding amount in descending order to see the highest funded companies first.

Here's the correct query structure:

```sparql
PREFIX ex: <http://example.org/ontology#>
PREFIX res: <http://example.org/resource/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?startup ?startupName ?amount WHERE {
  ?startup rdf:type ex:Startup .
  ?startup ex:name ?startupName .
  ?startup ex:hasIndustry ?industry .
  ?industry ex:name "cleantech" .
  ?startup ex:hasFunding ?funding .
  ?funding ex:amount ?amount .
  FILTER(?amount > 5000000)
}
ORDER BY DESC(?amount)
```

Please try again with these corrections to find cleantech companies with funding over 5 million CHF.
"""

# Add the previous feedback to chat history
chat_history.append(HumanMessage(content=industry_feedback))
chat_history.append(AIMessage(content="I'll correct my query based on your feedback."))
chat_history.append(HumanMessage(content=funding_feedback))
chat_history.append(AIMessage(content="Thank you for the feedback. I'll make those corrections."))

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

def analyze_results(data, query_context):
    """Analyze the query results based on the query context"""
    if not isinstance(data, list):
        return data  # Return error message if query failed
    
    analysis = {
        "total_results": len(data),
        "summary": "Query executed successfully",
        "data": data[:10]  # Only show first 10 results to keep output manageable
    }
    
    return analysis

def process_query(user_query):
    """Process a natural language query through the agent"""
    # Add user query to chat history
    chat_history.append(HumanMessage(content=user_query))
    
    # Get SPARQL query from LLM
    response = model.invoke(chat_history)
    response_content = response.content
    chat_history.append(AIMessage(content=response_content))
    
    # Extract SPARQL query from response
    try:
        sparql_query = None
        if "```sparql" in response_content:
            sparql_query = response_content.split("```sparql")[1].split("```")[0].strip()
        elif "```" in response_content:
            sparql_query = response_content.split("```")[1].split("```")[0].strip()
        else:
            sparql_query = response_content
            
        print(f"Extracted SPARQL Query:\n{sparql_query}")
        
        # Execute query
        results = execute_sparql(sparql_query)
        
        # Analyze results
        analysis = analyze_results(results, user_query)
        
        # Format response
        response = {
            "query": sparql_query,
            "results": analysis
        }
        
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error processing query: {str(e)}"

if __name__ == "__main__":
    # Query for all available company information
    info_query = """Create a SPARQL query that returns all available information for companies in our database.
Note that only the company name is guaranteed to be present - other fields might be missing for some companies.
Your query should handle this gracefully using OPTIONAL patterns for non-guaranteed fields.
Include information about industry, funding, location, founding date, and any other available attributes."""

    print("QUERY: All available information for companies")
    print("\n" + "="*80 + "\n")
    
    company_info_result = process_query(info_query)
    print(company_info_result) 
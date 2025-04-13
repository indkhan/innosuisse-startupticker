from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, XSD
import statistics

# Define namespaces
EX = Namespace("http://example.org/ontology#")
RES = Namespace("http://example.org/resource/")

def get_market_metrics(g):
    """Get overall market metrics"""
    query = """
    SELECT ?company_name ?industry_name (SUM(?amount) as ?total_funding) 
           (COUNT(?funding) as ?funding_rounds)
    WHERE {
        ?company a ex:Startup ;
                ex:name ?company_name .
        OPTIONAL {
            ?company ex:hasIndustry ?industry .
            ?industry ex:name ?industry_name .
        }
        OPTIONAL {
            ?company ex:hasFunding ?funding .
            OPTIONAL { ?funding ex:amount ?amount }
        }
    }
    GROUP BY ?company_name ?industry_name
    """
    
    results = list(g.query(query))
    
    # Calculate market metrics
    fundings = []
    rounds = []
    industries = {}
    
    for row in results:
        if row.total_funding:
            fundings.append(float(row.total_funding))
        rounds.append(int(row.funding_rounds))
        
        # Track industry distribution
        industry = str(row.industry_name) if row.industry_name else "Unknown"
        if industry not in industries:
            industries[industry] = 0
        industries[industry] += 1
    
    return {
        'total_companies': len(results),
        'avg_funding': statistics.mean(fundings) if fundings else 0,
        'median_funding': statistics.median(fundings) if fundings else 0,
        'avg_rounds': statistics.mean(rounds) if rounds else 0,
        'industry_distribution': industries
    }

def analyze_portfolio(companies):
    print("Loading RDF graph...")
    g = Graph()
    g.parse("startups_graph.ttl", format="turtle")
    print("Graph loaded successfully!")
    
    print("\nPortfolio Analysis")
    print("=" * 80)
    
    # Get market metrics
    market = get_market_metrics(g)
    
    # Portfolio metrics
    portfolio_fundings = []
    portfolio_rounds = []
    portfolio_industries = {}
    portfolio_locations = {}
    
    for company_name in companies:
        print(f"\nAnalyzing {company_name}:")
        print("-" * 50)
        
        # Get company details
        query = """
        SELECT ?industry_name ?location_name (COUNT(?funding) as ?funding_rounds) 
                (SUM(?amount) as ?total_funding)
        WHERE {
            ?company a ex:Startup ;
                    ex:name ?company_name .
            OPTIONAL {
                ?company ex:hasIndustry ?industry .
                ?industry ex:name ?industry_name .
            }
            OPTIONAL {
                ?company ex:hasLocation ?location .
                ?location ex:name ?location_name .
            }
            OPTIONAL {
                ?company ex:hasFunding ?funding .
                OPTIONAL { ?funding ex:amount ?amount }
            }
            FILTER(?company_name = %s)
        }
        GROUP BY ?industry_name ?location_name
        """
        
        results = list(g.query(query % Literal(company_name).n3()))
        if not results:
            print(f"Company {company_name} not found in the database")
            continue
            
        details = results[0]
        industry = str(details.industry_name) if details.industry_name else "Unknown"
        location = str(details.location_name) if details.location_name else "Unknown"
        total_funding = float(details.total_funding) if details.total_funding else 0
        funding_rounds = int(details.funding_rounds)
        
        # Update portfolio metrics
        portfolio_fundings.append(total_funding)
        portfolio_rounds.append(funding_rounds)
        
        if industry not in portfolio_industries:
            portfolio_industries[industry] = 0
        portfolio_industries[industry] += 1
        
        if location not in portfolio_locations:
            portfolio_locations[location] = 0
        portfolio_locations[location] += 1
        
        print(f"Industry: {industry}")
        print(f"Location: {location}")
        print(f"Total Funding: {total_funding:,.2f} CHF")
        print(f"Number of Funding Rounds: {funding_rounds}")
    
    # Portfolio Summary
    print("\nPortfolio Summary")
    print("=" * 50)
    print(f"Total Companies: {len(companies)}")
    print(f"Average Funding per Company: {statistics.mean(portfolio_fundings):,.2f} CHF")
    print(f"Median Funding per Company: {statistics.median(portfolio_fundings):,.2f} CHF")
    print(f"Average Funding Rounds per Company: {statistics.mean(portfolio_rounds):.1f}")
    
    # Industry Distribution
    print("\nIndustry Distribution:")
    for industry, count in portfolio_industries.items():
        market_share = (count / market['industry_distribution'].get(industry, 1)) * 100
        print(f"- {industry}: {count} companies ({market_share:.1f}% of market)")
    
    # Location Distribution
    print("\nGeographic Distribution:")
    for location, count in portfolio_locations.items():
        print(f"- {location}: {count} companies")
    
    # Market Comparison
    print("\nMarket Comparison")
    print("=" * 50)
    print(f"Portfolio vs Market Average Funding: {statistics.mean(portfolio_fundings)/market['avg_funding']*100:.1f}%")
    print(f"Portfolio vs Market Median Funding: {statistics.median(portfolio_fundings)/market['median_funding']*100:.1f}%")
    print(f"Portfolio vs Market Average Rounds: {statistics.mean(portfolio_rounds)/market['avg_rounds']*100:.1f}%")
    
    # Risk Analysis
    print("\nRisk Analysis")
    print("=" * 50)
    print(f"Industry Concentration: {len(portfolio_industries)} different industries")
    print(f"Geographic Concentration: {len(portfolio_locations)} different locations")
    print(f"Funding Stage Distribution:")
    for company in companies:
        query = """
        SELECT ?phase
        WHERE {
            ?company a ex:Startup ;
                    ex:name ?company_name ;
                    ex:hasFunding ?funding .
            OPTIONAL { ?funding ex:phase ?phase }
            FILTER(?company_name = %s)
        }
        """
        results = list(g.query(query % Literal(company).n3()))
        phases = [str(r.phase) for r in results if r.phase]
        print(f"- {company}: {', '.join(phases) if phases else 'No funding rounds'}")

if __name__ == "__main__":
    portfolio = ["CUTISS AG", "Augment IT", "Cortex"]
    analyze_portfolio(portfolio) 
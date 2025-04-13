from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, XSD
from datetime import datetime
import statistics

# Define namespaces
EX = Namespace("http://example.org/ontology#")
RES = Namespace("http://example.org/resource/")

def get_company_details(g, company_name):
    """Get basic details and metrics for a company"""
    query = """
    SELECT DISTINCT ?industry_name ?location_name (COUNT(?funding) as ?funding_rounds) 
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
    return results[0] if results else None

def get_sector_metrics(g, industry_name):
    """Get metrics for an entire sector"""
    query = """
    SELECT ?company_name (SUM(?amount) as ?total_funding) (COUNT(?funding) as ?funding_rounds)
    WHERE {
        ?company a ex:Startup ;
                ex:name ?company_name ;
                ex:hasIndustry ?industry .
        ?industry ex:name ?industry_name .
        OPTIONAL {
            ?company ex:hasFunding ?funding .
            OPTIONAL { ?funding ex:amount ?amount }
        }
        FILTER(?industry_name = %s)
    }
    GROUP BY ?company_name
    """
    
    results = list(g.query(query % Literal(industry_name).n3()))
    
    # Calculate sector metrics
    fundings = []
    rounds = []
    for row in results:
        if row.total_funding:
            fundings.append(float(row.total_funding))
        rounds.append(int(row.funding_rounds))
    
    return {
        'companies': len(results),
        'avg_funding': statistics.mean(fundings) if fundings else 0,
        'median_funding': statistics.median(fundings) if fundings else 0,
        'avg_rounds': statistics.mean(rounds) if rounds else 0,
        'total_sector_funding': sum(fundings)
    }

def get_funding_history(g, company_name):
    """Get detailed funding history for a company"""
    query = """
    SELECT ?date ?phase ?amount
    WHERE {
        ?company a ex:Startup ;
                ex:name ?company_name ;
                ex:hasFunding ?funding .
        OPTIONAL { ?funding ex:round_date ?date }
        OPTIONAL { ?funding ex:phase ?phase }
        OPTIONAL { ?funding ex:amount ?amount }
        FILTER(?company_name = %s)
    }
    ORDER BY ?date
    """
    
    return list(g.query(query % Literal(company_name).n3()))

def analyze_companies(companies):
    print("Loading RDF graph...")
    g = Graph()
    g.parse("startups_graph.ttl", format="turtle")
    print("Graph loaded successfully!")
    
    print("\nCompany Analysis")
    print("=" * 80)
    
    for company_name in companies:
        print(f"\nAnalyzing {company_name}:")
        print("-" * 50)
        
        # Get company details
        details = get_company_details(g, company_name)
        if not details:
            print(f"Company {company_name} not found in the database")
            continue
            
        industry = str(details.industry_name) if details.industry_name else None
        location = str(details.location_name) if details.location_name else "Unknown"
        total_funding = float(details.total_funding) if details.total_funding else 0
        funding_rounds = int(details.funding_rounds)
        
        if industry:
            print(f"Industry: {industry}")
        else:
            print("Industry: No defined sector for this company")
            
        print(f"Location: {location}")
        print(f"Total Funding: {total_funding:,.2f} CHF")
        print(f"Number of Funding Rounds: {funding_rounds}")
        
        # Get sector metrics only if industry is defined
        if industry:
            sector = get_sector_metrics(g, industry)
            print(f"\nSector Comparison ({industry}):")
            print(f"- Total companies in sector: {sector['companies']}")
            print(f"- Sector average funding: {sector['avg_funding']:,.2f} CHF")
            print(f"- Sector median funding: {sector['median_funding']:,.2f} CHF")
            print(f"- Sector average funding rounds: {sector['avg_rounds']:.1f}")
            
            # Calculate percentiles
            if total_funding > 0:
                funding_percentile = (total_funding / sector['avg_funding']) * 100
                print(f"- Company funding compared to sector average: {funding_percentile:.1f}%")
            
            rounds_percentile = (funding_rounds / sector['avg_rounds']) * 100
            print(f"- Company funding rounds compared to sector average: {rounds_percentile:.1f}%")
            
            market_share = (total_funding / sector['total_sector_funding']) * 100
            print(f"- Share of total sector funding: {market_share:.2f}%")
        
        # Get funding history
        print("\nFunding History:")
        funding_history = get_funding_history(g, company_name)
        for event in funding_history:
            date = str(event.date) if event.date else "Unknown date"
            phase = str(event.phase) if event.phase else "Unknown phase"
            amount = f"{float(event.amount):,.2f} CHF" if event.amount else "Confidential"
            print(f"- {date}: {phase} - {amount}")
        
        print("\n" + "=" * 50)

if __name__ == "__main__":
    companies = ["CUTISS AG", "Augment IT", "Cortex"]
    analyze_companies(companies) 
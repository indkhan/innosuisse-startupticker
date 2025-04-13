from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF
import random

# Define namespaces
EX = Namespace("http://example.org/ontology#")
RES = Namespace("http://example.org/resource/")

def analyze_portfolio(g, companies):
    print("\nPortfolio Analysis")
    print("=" * 80)
    
    for company_name in companies:
        print(f"\nAnalyzing {company_name}:")
        print("-" * 50)
        
        # Find the company URI
        company_uri = None
        for s in g.subjects(EX.name, Literal(company_name)):
            company_uri = s
            break
            
        if not company_uri:
            print(f"Company {company_name} not found in the graph")
            continue
            
        # Get basic information
        industry = g.value(company_uri, EX.hasIndustry)
        if industry:
            industry_name = g.value(industry, EX.name)
            print(f"Industry: {industry_name}")
            
        location = g.value(company_uri, EX.hasLocation)
        if location:
            location_name = g.value(location, EX.name)
            print(f"Location: {location_name}")
            
        # Get funding information
        funding_events = list(g.objects(company_uri, EX.hasFunding))
        print(f"\nFunding History ({len(funding_events)} events):")
        
        total_funding = 0
        for funding in funding_events:
            amount = g.value(funding, EX.amount)
            if amount:
                amount_value = float(amount.toPython())
                total_funding += amount_value
                
            phase = g.value(funding, EX.phase)
            date = g.value(funding, EX.round_date)
            
            print(f"  - Phase: {phase if phase else 'Unknown'}")
            print(f"    Date: {date if date else 'Unknown'}")
            print(f"    Amount: {amount_value:,.2f} CHF" if amount else "    Amount: Confidential")
            
            # Get investors
            investors = list(g.objects(funding, EX.investor))
            if investors:
                print("    Investors:")
                for investor in investors:
                    investor_name = g.value(investor, EX.name)
                    print(f"      - {investor_name}")
            
        print(f"\nTotal Funding: {total_funding:,.2f} CHF")
        
        # Get valuation if available
        latest_funding = funding_events[-1] if funding_events else None
        if latest_funding:
            valuation = g.value(latest_funding, EX.valuation)
            if valuation:
                print(f"Latest Valuation: {float(valuation.toPython()):,.2f} CHF")
        
        print("\n" + "=" * 50)

def load_and_verify_graph():
    print("Loading RDF graph...")
    g = Graph()
    
    try:
        # Load the graph
        g.parse("startups_graph.ttl", format="turtle")
        print(f"Graph loaded successfully! Total triples: {len(g)}")
        
        # Print some basic statistics
        print("\nBasic Statistics:")
        print("-" * 50)
        
        # Count startups
        startups = list(g.subjects(RDF.type, EX.Startup))
        print(f"Number of startups: {len(startups)}")
        
        # Count industries
        industries = list(g.subjects(RDF.type, EX.Industry))
        print(f"Number of industries: {len(industries)}")
        
        # Count funding events
        funding_events = list(g.subjects(RDF.type, EX.FundingEvent))
        print(f"Number of funding events: {len(funding_events)}")
        
        # Count investors
        investors = list(g.subjects(RDF.type, EX.Investor))
        print(f"Number of investors: {len(investors)}")
        
        # Select 5 random companies for portfolio analysis
        random_companies = random.sample([str(g.value(s, EX.name)) for s in startups], 5)
        print("\nSelected companies for portfolio analysis:")
        for company in random_companies:
            print(f"- {company}")
            
        analyze_portfolio(g, random_companies)
            
    except Exception as e:
        print(f"Error loading graph: {e}")

if __name__ == "__main__":
    load_and_verify_graph() 
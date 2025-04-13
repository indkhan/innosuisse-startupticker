from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, XSD
from datetime import datetime
import statistics
from collections import defaultdict

# Define namespaces
EX = Namespace("http://example.org/ontology#")
RES = Namespace("http://example.org/resource/")

def analyze_industry_trends(g, industry_name):
    """Analyze trends in a specific industry"""
    print(f"\nAnalyzing trends in {industry_name} industry")
    print("=" * 80)
    
    # Get all companies in the industry with their funding history
    query = """
    SELECT ?company_name ?date ?amount ?phase
    WHERE {
        ?company a ex:Startup ;
                ex:name ?company_name ;
                ex:hasIndustry ?industry .
        ?industry ex:name ?industry_name .
        OPTIONAL {
            ?company ex:hasFunding ?funding .
            OPTIONAL { ?funding ex:round_date ?date }
            OPTIONAL { ?funding ex:amount ?amount }
            OPTIONAL { ?funding ex:phase ?phase }
        }
        FILTER(?industry_name = %s)
    }
    ORDER BY ?date
    """
    
    results = list(g.query(query % Literal(industry_name).n3()))
    
    if not results:
        print(f"No data found for {industry_name} industry")
        return
    
    # Organize data by year
    yearly_data = defaultdict(lambda: {
        'total_funding': 0,
        'rounds': 0,
        'companies': set(),
        'phases': defaultdict(int)
    })
    
    for row in results:
        if row.date:
            year = int(str(row.date)[:4])
            if row.amount:
                yearly_data[year]['total_funding'] += float(row.amount)
            yearly_data[year]['rounds'] += 1
            yearly_data[year]['companies'].add(str(row.company_name))
            if row.phase:
                yearly_data[year]['phases'][str(row.phase)] += 1
    
    # Calculate growth metrics
    years = sorted(yearly_data.keys())
    if len(years) < 2:
        print("Insufficient data for trend analysis")
        return
    
    # Print yearly trends
    print("\nYearly Trends:")
    print("-" * 50)
    for year in years:
        data = yearly_data[year]
        print(f"\n{year}:")
        print(f"  Total Funding: {data['total_funding']:,.2f} CHF")
        print(f"  Number of Funding Rounds: {data['rounds']}")
        print(f"  Number of Companies Funded: {len(data['companies'])}")
        print(f"  Average Round Size: {data['total_funding']/data['rounds']:,.2f} CHF" if data['rounds'] > 0 else "  No funding rounds")
        
        if data['phases']:
            print("  Funding Stages:")
            for phase, count in data['phases'].items():
                print(f"    - {phase}: {count} rounds")
    
    # Calculate growth rates
    print("\nGrowth Analysis:")
    print("-" * 50)
    funding_growth = []
    rounds_growth = []
    companies_growth = []
    
    for i in range(1, len(years)):
        prev_year = years[i-1]
        curr_year = years[i]
        
        prev_funding = yearly_data[prev_year]['total_funding']
        curr_funding = yearly_data[curr_year]['total_funding']
        if prev_funding > 0:
            funding_growth.append((curr_funding - prev_funding) / prev_funding * 100)
        
        prev_rounds = yearly_data[prev_year]['rounds']
        curr_rounds = yearly_data[curr_year]['rounds']
        if prev_rounds > 0:
            rounds_growth.append((curr_rounds - prev_rounds) / prev_rounds * 100)
        
        prev_companies = len(yearly_data[prev_year]['companies'])
        curr_companies = len(yearly_data[curr_year]['companies'])
        if prev_companies > 0:
            companies_growth.append((curr_companies - prev_companies) / prev_companies * 100)
    
    if funding_growth:
        print(f"Average Annual Funding Growth: {statistics.mean(funding_growth):.1f}%")
        print(f"Median Annual Funding Growth: {statistics.median(funding_growth):.1f}%")
    
    if rounds_growth:
        print(f"Average Annual Growth in Funding Rounds: {statistics.mean(rounds_growth):.1f}%")
        print(f"Median Annual Growth in Funding Rounds: {statistics.median(rounds_growth):.1f}%")
    
    if companies_growth:
        print(f"Average Annual Growth in Funded Companies: {statistics.mean(companies_growth):.1f}%")
        print(f"Median Annual Growth in Funded Companies: {statistics.median(companies_growth):.1f}%")
    
    # Analyze funding stage trends
    print("\nFunding Stage Evolution:")
    print("-" * 50)
    stage_trends = defaultdict(list)
    for year in years:
        for phase, count in yearly_data[year]['phases'].items():
            stage_trends[phase].append((year, count))
    
    for phase, trend in stage_trends.items():
        print(f"\n{phase} Stage:")
        for year, count in trend:
            print(f"  {year}: {count} rounds")
    
    # Calculate market maturity indicators
    print("\nMarket Maturity Indicators:")
    print("-" * 50)
    latest_year = max(years)
    latest_data = yearly_data[latest_year]
    
    if latest_data['rounds'] > 0:
        avg_round_size = latest_data['total_funding'] / latest_data['rounds']
        print(f"Average Round Size in {latest_year}: {avg_round_size:,.2f} CHF")
        
        # Calculate concentration ratio (top 3 rounds / total funding)
        if len(latest_data['companies']) >= 3:
            print("Market Concentration: Top 3 companies' share of funding")
    
    # Predict future trends
    print("\nTrend Analysis:")
    print("-" * 50)
    if len(years) >= 3:
        recent_years = years[-3:]
        recent_funding = [yearly_data[y]['total_funding'] for y in recent_years]
        recent_rounds = [yearly_data[y]['rounds'] for y in recent_years]
        
        funding_trend = "increasing" if recent_funding[-1] > recent_funding[0] else "decreasing"
        rounds_trend = "increasing" if recent_rounds[-1] > recent_rounds[0] else "decreasing"
        
        print(f"Recent funding trend: {funding_trend}")
        print(f"Recent rounds trend: {rounds_trend}")
        
        # Check for acceleration/deceleration
        if len(recent_funding) >= 2:
            growth_rate_1 = (recent_funding[1] - recent_funding[0]) / recent_funding[0]
            growth_rate_2 = (recent_funding[2] - recent_funding[1]) / recent_funding[1]
            acceleration = "accelerating" if growth_rate_2 > growth_rate_1 else "decelerating"
            print(f"Growth is {acceleration}")

def main():
    print("Loading RDF graph...")
    g = Graph()
    g.parse("startups_graph.ttl", format="turtle")
    print("Graph loaded successfully!")
    
    # Analyze cleantech industry trends
    analyze_industry_trends(g, "cleantech")
    
    # You can analyze other industries by uncommenting these lines:
    # analyze_industry_trends(g, "biotech")
    # analyze_industry_trends(g, "ICT")
    # analyze_industry_trends(g, "medtech")

if __name__ == "__main__":
    main() 
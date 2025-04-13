import pandas as pd
from rdflib import Graph, Namespace, Literal, BNode, RDF, XSD
import re
from datetime import datetime

def clean_text(text):
    if pd.isna(text):
        return None
    return str(text).strip()

def uri_safe(text):
    if not text:
        return None
    return re.sub(r'[^a-zA-Z0-9_-]', '_', str(text))

def convert_date(date_str):
    try:
        # Try different date formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
            try:
                date_obj = datetime.strptime(str(date_str), fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        return None
    except (ValueError, TypeError):
        return None

# Create a new RDF graph
graph = Graph()

# Define namespaces
EX = Namespace("http://example.org/ontology#")
RES = Namespace("http://example.org/resource/")

# Bind namespaces to prefixes for prettier output
graph.bind("ex", EX)
graph.bind("res", RES)

# Load CSV files
print("Loading CSV files...")
companies_df = pd.read_csv('companies.csv')
deals_df = pd.read_csv('deals.csv')
print(f"Loaded {len(companies_df)} companies and {len(deals_df)} deals from CSV files")

# Process company information
print("Processing company information...")
for index, row in companies_df.iterrows():
    # Get the company name (required)
    startup_name = clean_text(row['Title'])
    if not startup_name:
        continue
    
    # Create company URI and add basic information
    startup_uri = RES[uri_safe(startup_name)]
    graph.add((startup_uri, RDF.type, EX.Startup))
    graph.add((startup_uri, EX.name, Literal(startup_name)))
    
    # Add founding date (optional)
    if not pd.isna(row['Year']):
        try:
            year = int(row['Year'])
            graph.add((startup_uri, EX.foun_date, Literal(year, datatype=XSD.integer)))
        except ValueError:
            pass
    
    # Add highlights (optional)
    if not pd.isna(row['Highlights']):
        highlights = clean_text(row['Highlights'])
        graph.add((startup_uri, EX.highlights, Literal(highlights)))
    
    # Add industry (optional)
    if not pd.isna(row['Industry']):
        industry = clean_text(row['Industry'])
        industry_uri = RES[f"industry-{uri_safe(industry)}"]
        graph.add((industry_uri, RDF.type, EX.Industry))
        graph.add((industry_uri, EX.name, Literal(industry)))
        graph.add((startup_uri, EX.hasIndustry, industry_uri))
    
    # Add location hierarchy (optional)
    if not pd.isna(row['Canton']):
        canton = clean_text(row['Canton'])
        canton_uri = RES[f"canton-{uri_safe(canton)}"]
        graph.add((canton_uri, RDF.type, EX.Canton))
        graph.add((canton_uri, EX.name, Literal(canton)))
        graph.add((startup_uri, EX.hasLocation, canton_uri))
        
        # Add city if available (optional)
        if not pd.isna(row['City']):
            city = clean_text(row['City'])
            city_uri = RES[f"city-{uri_safe(city)}"]
            graph.add((city_uri, RDF.type, EX.City))
            graph.add((city_uri, EX.name, Literal(city)))
            graph.add((city_uri, EX.partOf, canton_uri))
            graph.add((startup_uri, EX.hasLocation, city_uri))

# Process funding rounds
print("Processing funding rounds...")
for index, row in deals_df.iterrows():
    # Get the company name (required to link the deal)
    startup_name = clean_text(row['Company'])
    if not startup_name:
        continue
        
    startup_uri = RES[uri_safe(startup_name)]
    
    # Create a new funding round
    funding_round = BNode()
    graph.add((funding_round, RDF.type, EX.FundingEvent))
    graph.add((startup_uri, EX.hasFunding, funding_round))
    
    # Add funding phase (optional)
    if not pd.isna(row['Phase']):
        phase = clean_text(row['Phase'])
        graph.add((funding_round, EX.phase, Literal(phase)))
    
    # Add funding type (optional)
    if not pd.isna(row['Type']):
        funding_type = clean_text(row['Type'])
        graph.add((funding_round, EX.type, Literal(funding_type)))
    
    # Add funding amount (optional)
    if not pd.isna(row['Amount']):
        try:
            # Handle confidential amounts
            is_confidential = str(row['Amount confidential']).strip().lower() == 'yes'
            if not is_confidential:
                # Clean and convert the amount
                amount_str = str(row['Amount']).strip()
                # Remove any currency symbols, commas, and spaces
                amount_str = re.sub(r'[^\d.]', '', amount_str)
                if amount_str:
                    amount = float(amount_str)
                    # Convert to actual amount (assuming input is in millions)
                    amount = amount * 1000000
                    graph.add((funding_round, EX.amount, Literal(amount, datatype=XSD.decimal)))
                    print(f"Converted amount for {startup_name}: {amount:,.2f} CHF")
        except (ValueError, TypeError) as e:
            print(f"Warning: Could not convert amount for {startup_name}: {e}")
    
    # Add valuation (optional)
    if not pd.isna(row['Valuation']):
        try:
            valuation = float(str(row['Valuation']).replace(',', ''))
            graph.add((funding_round, EX.valuation, Literal(valuation, datatype=XSD.decimal)))
        except ValueError:
            pass
    
    # Add funding date (optional)
    if not pd.isna(row['Date of the funding round']):
        funding_date = convert_date(row['Date of the funding round'])
        if funding_date:
            graph.add((funding_round, EX.round_date, Literal(funding_date, datatype=XSD.date)))
    
    # Add investor information (optional)
    if not pd.isna(row['Investors']) and row['Investors'] != 'n.a.':
        investor_name = clean_text(row['Investors'])
        investor_uri = RES[f"investor-{uri_safe(investor_name)}"]
        graph.add((investor_uri, RDF.type, EX.Investor))
        graph.add((investor_uri, EX.name, Literal(investor_name)))
        graph.add((funding_round, EX.investor, investor_uri))

# Save the graph
print("Saving RDF graph...")
graph.serialize('startups_graph.ttl', format='turtle')
print(f"RDF conversion complete! Total triples: {len(graph)}") 
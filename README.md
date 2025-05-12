# SwissInsight: AI-Driven Startup Analytics Platform

A powerful, intuitive platform that transforms Swiss startup data into actionable insights through natural language interactions.


## 🚀 Overview

SwissInsight is a sophisticated yet user-friendly platform built specifically for Switzerland's startup ecosystem. It unlocks the valuable Startupticker database by enabling non-technical users to query and analyze Swiss startup funding data using simple natural language questions. The system automatically transforms user questions into complex SPARQL queries, performs semantic analysis, and presents the results through interactive visualizations.

## 🛠️ Technical Implementation

SwissInsight leverages several advanced technologies:

- **Knowledge Graph**: Swiss startup data transformed into a semantic RDF graph
- **LLM Integration**: Google Gemini for natural language understanding and query generation
- **SPARQL Engine**: Powerful query language for precise data retrieval
- **Streamlit Framework**: Interactive web interface with visualization capabilities
- **SOGC Integration**: Web scraping capabilities to retrieve official registry data


## 📊 Data Sources

The platform integrates multiple data sources:
- **Startupticker Database**: 5,213 Swiss startups and 3,902 funding deals
- **Crunchbase**: Additional company and investment data
- **SOGC**: Official Swiss company registry information

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Google API key for Gemini

### Quick Start
1. Clone the repository
```
git clone https://github.com/indkhan/innosuisse-startupticker
cd innosuisse-startupticker
```

2. Install dependencies
```
pip install -r requirements.txt
```

3. Set up your API key
```
echo "GOOGLE_API_KEY=your_key_here" > .env
```

4. Launch the application
```
streamlit run app.py
```

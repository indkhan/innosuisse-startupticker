# INNOSUISSE & STARTUPTICKER
# Empowering Swiss start-ups and investors with AI-driven data insights

Startupticker has a large, reliable data set on Swiss startups. This data is only used for reports and is otherwise not available. We see huge untapped potential in making this data available to start-ups, investors and support organisations. It would be ideal for creating more transparency in the ecosystem. There is also great potential for semantic search.

* Use case 1: Recognising trends
Recognising trends with semantic search: Investors and startups want to know how a sector or vertical has developed, for example to recognise whether there are signs of a recovery in investments or whether rising valuations or a wave of startups looking for investors can be expected

* Use case 2: Benchmarking
Investors and support organisations want to know whether the startups in their portfolio are performing better or worse than average. As all other content by Startupticker, the analyses will be offered for free.

## Expected Outcome:

There are two possibilities: 
Recognising trends with semantic search 
Ontology instead of standard classification for the three data sets
Step 1: create a model to organise descriptors/tags 
Step 2: develop algorithms able to hat capture them 

Benchmarking
Dashboard on the Startupticker website for users to perform simple analyses

Format: 
* Presentation with slides and short live demo if possible
Key elements:
* Concept, functionality, examples, description of the necessary work up to the finished product
Requirements:
* The prototype is far more relevant than the presentation itself


## Data:
The Startupticker database includes data of more than 5000 Swiss start-ups. The datasets include Founding year, sector, canton, website. In addition, we have a comprehensive database of transactions since 2012 which includes funding rounds, acquisitions and liquidations.
We will provide the database in an excel file.



## The Pitch:
[SwissHacksStartuptickerPitch.pdf](https://github.com/user-attachments/files/19607111/SwissHacksStartuptickerPitch.pdf)

## Deep Dive Slides:

[SwissHacksStartuptickerV3.pdf](https://github.com/user-attachments/files/19549003/SwissHacksStartuptickerV3.pdf)

## Further Information:

Add further information

## Resources:

### Startupticker

[Data-startupticker.xlsx](https://github.com/user-attachments/files/19537050/Data-startupticker.xlsx)
 contains the database from startupticker and a short description about the fields. There are 5213 companies and 3902 deals. 

### Crunchbase

[Data-crunchbase.xlsx](https://github.com/user-attachments/files/19537056/Data-crunchbase.xlsx)
 contains a selection of the database from crunchbase and a short description about the fields. There are 10'000 organizations and 10'956 funding rounds. You find a full data dictionary here: [full_data_dictionary_crunchbase.pdf](https://github.com/user-attachments/files/19537062/full_data_dictionary_crunchbase.pdf).

For more information about the data, turn to the crunchbase documentation: https://data.crunchbase.com/docs/getting-started. 

### Swiss Official Gazette of Commerce

The Swiss Official Gazette of Commerce (SOGC) is a public database containing information about legal form, ownership and management of the companies and legal entities registered there. It can be accessed here: https://www.shab.ch/#!/search/publications. This database can be useful for information such as the names of the founders, citizenships of the founders and official liquidations, current residence address and changes to the corporate structure of companies. 

Due to a change of the database on the 02. September 2018, the archive has to be visited for information prior to this date. This can be accessed here: https://www.shab.ch/#!/search/archive.

Here you find more information about how to use it: [How to use the SOGC.pdf](https://github.com/user-attachments/files/19537068/How.to.use.the.SOGC.pdf).

## Judging Criteria:

* Visual design (10%)
The design must make it possible for non-experts to use the interface. 
* Feasibility (40%) 
As Startupticker is a small organisation with very limited resources, it is important that the solution does not require large resources for implementation or operation. ..
* Reachability (50%)
The closer the solution is to a usable product, the better.


## Point of Contact:

* Stefan Kyora, Editor in Chief, Startupticker
* Ritah Nyakato, Duty Editor, Startupticker
* Benjamin Klavins, Data Analyst, Startupticker


## Price - the winning team members will each receive:

Introduction to the Swiss start-up ecosystem and hands-on tips if winner is interested in starting a company or working with a start-up.

# Swiss Startup Funding Analysis

A Streamlit-based web application that lets you query Swiss startup funding data using natural language. The application converts natural language queries into SPARQL and provides analysis of the results.

## Features

- Natural language interface for querying startup funding data
- Interactive Streamlit UI with analysis visualizations
- SPARQL query generation using LLM (Google Gemini)
- Support for industry-specific queries and trend analysis
- Detailed funding analysis with insights

## Setup

### Prerequisites

- Python 3.8 or higher
- A Google API key for Gemini

### Installation

1. Clone the repository:
```
git clone <repository-url>
cd <repository-folder>
```

2. Install the required dependencies:
```
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory and add your Google API key:
```
GOOGLE_API_KEY=your_google_api_key_here
```

### Running the Application

1. Start the Streamlit application:
```
streamlit run app.py
```

2. Open your browser and navigate to the URL displayed in the terminal (typically http://localhost:8501)

## Example Queries

- "Show funding trends in the cleantech industry"
- "What are the top medtech companies by funding amount?"
- "Compare funding between biotech and ICT industries"
- "How has funding in healthcare IT changed over time?"
- "Which cantons have the most startups?"

## Available Industries

The database includes the following industries:
- cleantech
- biotech
- medtech
- healthcare IT
- ICT
- ICT (fintech)
- micro / nano
- Life-Sciences

## Project Structure

- `app.py` - Streamlit frontend application
- `llm.py` - Core logic for processing queries and generating SPARQL
- `startups_graph.ttl` - RDF graph containing the startup data
- `requirements.txt` - Dependencies list

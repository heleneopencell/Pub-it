# Pub-it

A Python application that tracks your community's latest papers, collaborations and spots the most cited.

## Features

- Tracks publications from specified researchers using their ORCID IDs, name and affiliation
- Fetches citation counts from Google Scholar

## Project Structure

```
.
├── data/
│   ├── researchers.csv    # List of researchers and their ORCID IDs
│   └── publications.csv   # Tracked publications with citation counts
├── podcasts/             # Generated audio podcasts
├── src/
│   ├── pubmed_tracker.py     # Tracks new publications
│   ├── scholar_citations.py  # Fetches citation counts
│   └── paper_to_podcast.py   # Generates podcasts
└── requirements.txt      # Python dependencies
```

## Setup

1. Create and activate a Python virtual environment:
```bash
python -m venv pub_it_env
source pub_it_env/bin/activate  # On Windows: pub_it_env\Scripts\activate
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Install ffmpeg (required for audio processing):
```bash
# On macOS with Homebrew:
brew install ffmpeg

# On Ubuntu/Debian:
sudo apt-get install ffmpeg

# On Windows with Chocolatey:
choco install ffmpeg
```

4. Configure `data/researchers.csv` with researcher information:
```csv
name,orcid
Jenny Molloy,0000-0003-3477-8462
```

## Usage

The application consists of three main scripts that work together:

1. Track new publications:
```bash
python src/pubmed_tracker.py
```
This script:
- Reads researcher information from `data/researchers.csv`
- Searches PubMed for publications from the previous month
- Saves results to `data/publications.csv`

2. Update citation counts:
```bash
python src/scholar_citations.py
```
This script:
- Reads publications from `data/publications.csv`
- Fetches citation counts from Google Scholar
- Updates and sorts publications by citation count

3. Generate podcasts:
```bash
python src/paper_to_podcast.py
```
This script:
- Uses Illuminate.ai to convert papers into audio podcasts
- Downloads podcasts to the `podcasts` directory
- Automatically trims the first 5 seconds from each podcast

## Output

- `data/publications.csv`: Contains publication details including:
  - Title
  - Authors (all authors and our tracked authors)
  - Journal
  - DOI
  - Publication date
  - PMID
  - Citation count

- `podcasts/`: Contains generated MP3 files named after the paper titles

## Requirements

- Python 3.8+
- Chrome browser installed
- ffmpeg (for audio processing)
- Illuminate.ai account credentials
- Internet connection

## Dependencies

- selenium: Web automation
- undetected-chromedriver: Browser automation
- pandas: Data handling
- pydub: Audio processing
- beautifulsoup4: HTML parsing
- requests: HTTP requests 
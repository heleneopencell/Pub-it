#!/usr/bin/env python3

import pandas as pd
import requests
import os
import re
import time
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import datetime

REQUEST_DELAY = 1  # Delay between requests in seconds

PUBMED_TXT_URL = "https://pubmed.ncbi.nlm.nih.gov/{}/?format=pubmed"

# Helper to extract metadata from pubmed text format
def fetch_pubmed_text_metadata(pmid, researcher_name, researcher_orcid):
    url = PUBMED_TXT_URL.format(pmid)
    response = requests.get(url)
    text = response.text

    title = re.search(r'TI  - (.+)', text)
    title = title.group(1).strip() if title else ''

    # Improved author extraction
    authors = []
    current_author = None
    for line in text.splitlines():
        if line.startswith('FAU - '):
            if current_author:
                authors.append(current_author)
            current_author = {'name': line.replace('FAU - ', '').strip(), 'orcid': '', 'affiliation': ''}
        elif line.startswith('AUID- ORCID:') and current_author:
            current_author['orcid'] = line.replace('AUID- ORCID:', '').replace('ORCID:', '').strip()
        elif line.startswith('AD  -') and current_author:
            affil = line.replace('AD  -', '').strip()
            if current_author['affiliation']:
                current_author['affiliation'] += ' ' + affil
            else:
                current_author['affiliation'] = affil
    if current_author:
        authors.append(current_author)

    # Convert authors to a readable string (or keep as JSON if preferred)
    authors_str = '; '.join([
        f"{a['name']} (ORCID: {a['orcid']}) [{a['affiliation']}]" if a['orcid'] else f"{a['name']} [{a['affiliation']}]"
        for a in authors
    ])

    journal = re.search(r'TA  - (.+)', text)
    journal = journal.group(1).strip() if journal else ''

    doi = re.search(r'LID - (10\.\S+) \[doi\]', text)
    doi = doi.group(1).strip() if doi else ''
    doi_link = f"https://doi.org/{doi}" if doi else ''

    # Publication date: try pmc-release, then pubmed
    pub_date = re.search(r'PHST- (\d{4}/\d{2}/\d{2}) \d{2}:\d{2} \[pmc-release\]', text)
    if pub_date:
        pub_date = pub_date.group(1).replace('/', '-')
    else:
        pub_date = re.search(r'PHST- (\d{4}/\d{2}/\d{2}) \d{2}:\d{2} \[pubmed\]', text)
        pub_date = pub_date.group(1).replace('/', '-') if pub_date else ''

    return {
        'researcher_name': researcher_name,
        'researcher_orcid': researcher_orcid,
        'title': title,
        'authors': authors_str,
        'journal': journal,
        'doi': doi_link,
        'publication_date': pub_date,
        'pmid': pmid
    }

def get_pmids_by_orcid(orcid):
    query = f'{orcid}[Author - Identifier]'
    encoded_query = quote_plus(query)
    base_url = f"https://pubmed.ncbi.nlm.nih.gov/?term={encoded_query}"
    pmids = []
    page = 1
    while True:
        url = f"{base_url}&page={page}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        new_pmids = [span.text.strip() for span in soup.find_all('span', class_='docsum-pmid')]
        if not new_pmids:
            break
        pmids.extend(new_pmids)
        next_button = soup.find('button', class_='load-button next-page')
        if not next_button:
            break
        page += 1
        time.sleep(REQUEST_DELAY)
    return pmids

def get_pmids_by_name_and_affiliation(name, university):
    query = f'({name}[Author]) AND ({university}[Affiliation])'
    encoded_query = quote_plus(query)
    base_url = f"https://pubmed.ncbi.nlm.nih.gov/?term={encoded_query}"
    pmids = []
    page = 1
    while True:
        url = f"{base_url}&page={page}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        new_pmids = [span.text.strip() for span in soup.find_all('span', class_='docsum-pmid')]
        if not new_pmids:
            break
        pmids.extend(new_pmids)
        next_button = soup.find('button', class_='load-button next-page')
        if not next_button:
            break
        page += 1
        time.sleep(REQUEST_DELAY)
    return pmids

def save_publications_to_csv(orcid, publications):
    os.makedirs('data/publications', exist_ok=True)
    df = pd.DataFrame(publications)
    
    # Add citations column if it doesn't exist and initialize to 0
    if 'citations' not in df.columns:
        df['citations'] = 0
    
    # Convert publication_date to datetime for sorting (ignore errors for missing/invalid dates)
    if 'publication_date' in df.columns:
        df['publication_date'] = pd.to_datetime(df['publication_date'], errors='coerce')
        df = df.sort_values(by='publication_date', ascending=False)
    
    # Specify the desired column order, with citations before authors
    column_order = [
        'researcher_name',
        'researcher_orcid',
        'title',
        'journal',
        'doi',
        'publication_date',
        'pmid',
        'citations',  # Add citations before authors
        'authors'     # authors last
    ]
    column_order = [col for col in column_order if col in df.columns]
    df = df[column_order]
    
    # If the file already exists, merge with existing data preserving citation counts
    csv_path = f'data/publications/{orcid}.csv'
    if os.path.exists(csv_path):
        existing_df = pd.read_csv(csv_path)
        if 'citations' in existing_df.columns:
            # Create a mapping of DOIs to citation counts from existing data
            citation_map = dict(zip(existing_df['doi'], existing_df['citations']))
            # Update citations in new data where DOI matches
            df['citations'] = df['doi'].map(citation_map).fillna(0).astype(int)
    
    df.to_csv(csv_path, index=False)

def main():
    researchers_df = pd.read_csv('data/researchers.csv')
    today = pd.Timestamp.today().normalize()
    updated = False
    for idx, row in researchers_df.iterrows():
        last_search = row.get('last_pubmed_search', None)
        if pd.isna(last_search) or not last_search:
            needs_search = True
        else:
            try:
                last_search_date = pd.to_datetime(last_search, errors='coerce')
                needs_search = (today - last_search_date) > pd.Timedelta(days=30)
            except Exception:
                needs_search = True
        if not needs_search:
            print(f"Skipping {row['name']} ({row['orcid']}): searched within last month.")
            continue
        researcher_name = row['name']
        researcher_orcid = row['orcid']
        print(f"Processing: {researcher_name} ({researcher_orcid})")
        pmids_orcid = get_pmids_by_orcid(researcher_orcid)
        print(f"  ORCID search found {len(pmids_orcid)} PMIDs")
        pmids_name_affil = get_pmids_by_name_and_affiliation(researcher_name, row['university'])
        print(f"  Name+Affiliation search found {len(pmids_name_affil)} PMIDs")
        all_pmids = set(pmids_orcid) | set(pmids_name_affil)
        print(f"  Combined unique PMIDs: {len(all_pmids)}")
        publications = []
        seen_pmids = set()
        seen_titles = set()
        for pmid in all_pmids:
            if pmid in seen_pmids:
                continue
            pub = fetch_pubmed_text_metadata(pmid, researcher_name, researcher_orcid)
            if pub['pmid']:
                if pub['pmid'] in seen_pmids:
                    continue
                seen_pmids.add(pub['pmid'])
            else:
                title_key = pub['title'].strip().lower() if pub['title'] else pmid
                if title_key in seen_titles:
                    continue
                seen_titles.add(title_key)
            publications.append(pub)
            time.sleep(REQUEST_DELAY)
        print(f"  Publications to save: {len(publications)}")
        save_publications_to_csv(researcher_orcid, publications)
        print(f"Saved {len(publications)} publications for {researcher_orcid}")
        # Update last_pubmed_search to today
        researchers_df.at[idx, 'last_pubmed_search'] = today.strftime('%Y-%m-%d')
        updated = True
    if updated:
        researchers_df.to_csv('data/researchers.csv', index=False)
        print("Updated last_pubmed_search for processed researchers.")

if __name__ == "__main__":
    main() 
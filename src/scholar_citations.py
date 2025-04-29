#!/usr/bin/env python3

import os
import json
import time
import pandas as pd
from datetime import datetime, timezone
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import quote
import logging
import random
import undetected_chromedriver as uc
import glob

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Constants for human-like behavior
MIN_PAGE_VIEW_TIME = 5
MAX_PAGE_VIEW_TIME = 10
MIN_TYPING_DELAY = 0.1
MAX_TYPING_DELAY = 0.3

class ScholarCitationFetcher:
    def __init__(self):
        """Initialize the Chrome driver with undetected-chromedriver."""
        options = uc.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--disable-notifications')
        self.driver = uc.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 20)
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure browser is closed when done."""
        self.driver.quit()
    
    def simulate_typing(self, element, text):
        """Simulate human typing behavior."""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(MIN_TYPING_DELAY, MAX_TYPING_DELAY))
    
    def get_citation_count(self, doi):
        """Get citation count for a paper using its DOI."""
        try:
            # Clean DOI
            clean_doi = doi.replace('https://doi.org/', '').strip()
            
            # Navigate to Google Scholar
            self.driver.get('https://scholar.google.com')
            
            # Wait for and find the search box
            search_box = self.wait.until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            
            # Clear any existing text and simulate typing
            search_box.clear()
            self.simulate_typing(search_box, clean_doi)
            
            # Submit search
            search_box.submit()
            
            # Random wait to simulate reading
            time.sleep(random.uniform(MIN_PAGE_VIEW_TIME, MAX_PAGE_VIEW_TIME))
            
            try:
                # Look for citation count in various formats
                citation_elements = self.driver.find_elements(
                    By.XPATH,
                    "//a[contains(text(), 'Cited by')]"
                )
                
                for element in citation_elements:
                    text = element.text
                    if 'Cited by' in text:
                        try:
                            return int(''.join(filter(str.isdigit, text)))
                        except ValueError:
                            continue
                
                return 0
                
            except NoSuchElementException:
                logging.info(f"No citations found for DOI: {doi}")
                return 0
                
        except TimeoutException:
            logging.error(f"Timeout while processing DOI: {doi}")
            return None
        except Exception as e:
            logging.error(f"Error processing DOI {doi}: {str(e)}")
            return None

def update_citations():
    """Update citation counts in all publication CSVs in the publications directory if not updated in the last 30 days."""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        publications_dir = os.path.join(project_root, "data", "publications")
        researchers_file = os.path.join(project_root, "data", "researchers.csv")
        all_files = glob.glob(os.path.join(publications_dir, "*.csv"))
        logging.info(f"Processing {len(all_files)} publication files")
        now = datetime.now(timezone.utc)

        # Load researchers data
        researchers_df = pd.read_csv(researchers_file)
        if 'last_scholar_citation_search' not in researchers_df.columns:
            researchers_df['last_scholar_citation_search'] = None
            researchers_df.to_csv(researchers_file, index=False)
        
        with ScholarCitationFetcher() as fetcher:
            for file in all_files:
                try:
                    fname = os.path.basename(file)
                    orcid = fname.replace('.csv', '')
                    
                    # Get last update date from researchers.csv
                    researcher_row = researchers_df[researchers_df['orcid'] == orcid]
                    if researcher_row.empty:
                        logging.warning(f"Researcher with ORCID {orcid} not found in researchers.csv")
                        continue
                        
                    last_update_str = researcher_row['last_scholar_citation_search'].iloc[0]
                    
                    try:
                        # Parse the date string if it exists
                        if pd.notna(last_update_str):
                            last_update = datetime.strptime(last_update_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                            if (now - last_update).days < 30:
                                logging.info(f"Skipping {file}: citations updated less than 30 days ago")
                                continue
                    except (ValueError, TypeError) as e:
                        logging.warning(f"Invalid date format for {orcid}: {str(e)}")
                        last_update = None
                    
                    df = pd.read_csv(file)
                    if 'citations' not in df.columns:
                        df['citations'] = 0
                        
                    citations_updated = False
                    citations_checked = False
                    
                    for idx, row in df.iterrows():
                        try:
                            if pd.isna(row['doi']) or not row['doi']:
                                logging.warning(f"Skipping row {idx} in {file}: No DOI available")
                                continue
                                
                            logging.info(f"Processing {row['doi']} in {file}")
                            citations = fetcher.get_citation_count(row['doi'])
                            citations_checked = True
                            
                            if citations is not None and citations > 0:
                                current_citations = int(row.get('citations', 0))
                                if citations > current_citations:
                                    df.at[idx, 'citations'] = citations
                                    citations_updated = True
                                    logging.info(f"Updated citations from {current_citations} to {citations} for DOI: {row['doi']} in {file}")
                                    df.to_csv(file, index=False)
                                else:
                                    logging.info(f"Keeping existing citation count of {current_citations} for DOI: {row['doi']} in {file}")
                            else:
                                logging.info(f"No valid citation count found for DOI: {row['doi']} in {file}, keeping existing count")
                        except Exception as e:
                            logging.error(f"Error processing row {idx} in {file}: {str(e)}")
                            continue
                    
                    if citations_updated:
                        df = df.sort_values('citations', ascending=False)
                        df.to_csv(file, index=False)
                        
                    if citations_checked:
                        # Update researcher's last_scholar_citation_search
                        researchers_df.loc[researchers_df['orcid'] == orcid, 'last_scholar_citation_search'] = now.strftime("%Y-%m-%d")
                        researchers_df.to_csv(researchers_file, index=False)
                        logging.info(f"Updated last_scholar_citation_search for researcher {orcid}")
                        
                except Exception as e:
                    logging.error(f"Error processing file {file}: {str(e)}")
                    continue
                    
            logging.info("Completed updating citations for all files")
            
    except Exception as e:
        logging.error(f"Error processing publications: {str(e)}")

if __name__ == "__main__":
    update_citations() 
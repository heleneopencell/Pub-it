from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
import pandas as pd
from typing import List, Dict
import logging

__all__ = ['router']
router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/publications", response_model=List[Dict])
async def get_publications():
    """Get all publications from CSV files."""
    try:
        # Get absolute path to publications directory
        publications_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "publications")
        logger.info(f"Looking for publications in directory: {publications_dir}")
        publications_dict = {}  # Use DOI as key to merge duplicate publications
        
        # Ensure directory exists
        if not os.path.exists(publications_dir):
            logger.warning(f"Publications directory does not exist: {publications_dir}")
            return []
            
        # Read all CSV files in the publications directory
        for filename in os.listdir(publications_dir):
            if filename.endswith('.csv') and not filename.startswith('.'):
                file_path = os.path.join(publications_dir, filename)
                logger.info(f"Reading file: {file_path}")
                try:
                    df = pd.read_csv(file_path)
                    if not df.empty:
                        # Get researcher name and ORCID from filename
                        researcher_orcid = filename.split('.')[0]
                        researcher_name = df['researcher_name'].iloc[0] if 'researcher_name' in df.columns else None
                        
                        for _, row in df.iterrows():
                            doi = row.get('doi', '')
                            if doi not in publications_dict:
                                # Create new publication entry
                                publications_dict[doi] = {
                                    'title': row.get('title', ''),
                                    'journal': row.get('journal', ''),
                                    'doi': doi,
                                    'publication_date': row.get('publication_date', ''),
                                    'citations': row.get('citations', 0),
                                    'authors': [],
                                    'researcher_names': set()  # Use set to avoid duplicates
                                }
                            
                            # Add researcher to the publication's authors if not already present
                            if researcher_name and researcher_name not in publications_dict[doi]['researcher_names']:
                                publications_dict[doi]['researcher_names'].add(researcher_name)
                                publications_dict[doi]['authors'].append(researcher_name)
                        
                        logger.info(f"Processed publications for researcher: {researcher_name} ({researcher_orcid})")
                    else:
                        logger.warning(f"Empty dataframe in file: {filename}")
                except Exception as e:
                    logger.error(f"Error reading file {filename}: {str(e)}")
                    continue
        
        # Convert dictionary to list and sort by citations
        all_publications = list(publications_dict.values())
        all_publications.sort(key=lambda x: x.get('citations', 0), reverse=True)
        
        # Remove the set of researcher names from the final output
        for pub in all_publications:
            pub.pop('researcher_names', None)
            
        logger.info(f"Total unique publications found: {len(all_publications)}")
        return all_publications
        
    except Exception as e:
        logger.error(f"Error in get_publications: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/publications/{orcid}/download")
async def download_publications(orcid: str):
    """Download publications CSV for a specific researcher."""
    try:
        # Get absolute path to publications file
        file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "publications", f"{orcid}.csv")
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Publications not found")
            
        return FileResponse(
            file_path,
            media_type="text/csv",
            filename=f"publications_{orcid}.csv"
        )
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e)) 
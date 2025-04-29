from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
import pandas as pd
from typing import List, Dict

__all__ = ['router']
router = APIRouter(prefix="/api")

@router.get("/researchers", response_model=Dict)
async def get_researchers():
    """Get all researchers from CSV files."""
    try:
        researchers_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "researchers.csv")
        
        # Ensure file exists
        if not os.path.exists(researchers_file):
            return {"researchers": []}
            
        # Read researchers data
        df = pd.read_csv(researchers_file)
        
        # Add last_scholar_citation_search column if it doesn't exist
        if 'last_scholar_citation_search' not in df.columns:
            df['last_scholar_citation_search'] = None
            df.to_csv(researchers_file, index=False)
            
        researchers = df.to_dict('records')
        return {"researchers": researchers}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/researchers")
async def add_researcher(researcher: Dict):
    """Add a new researcher."""
    try:
        researchers_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "researchers.csv")
        
        # Extract only the fields we want
        new_researcher = {
            'name': researcher.get('name', ''),
            'orcid': researcher.get('orcid', ''),
            'department': researcher.get('department', ''),
            'university': researcher.get('university', ''),
            'last_pubmed_search': None,
            'last_scholar_citation_search': None
        }
        
        # Create new DataFrame with the researcher data
        new_researcher_df = pd.DataFrame([new_researcher])
        
        # If file exists, append to it
        if os.path.exists(researchers_file):
            existing_df = pd.read_csv(researchers_file)
            # Add last_scholar_citation_search column if it doesn't exist
            if 'last_scholar_citation_search' not in existing_df.columns:
                existing_df['last_scholar_citation_search'] = None
            updated_df = pd.concat([existing_df, new_researcher_df], ignore_index=True)
        else:
            updated_df = new_researcher_df
            
        # Save to CSV
        updated_df.to_csv(researchers_file, index=False)
        return {"message": "Researcher added successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/researchers/{name}/{orcid}")
async def delete_researcher(name: str, orcid: str):
    """Delete a researcher by name and ORCID."""
    try:
        researchers_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "researchers.csv")
        
        if not os.path.exists(researchers_file):
            raise HTTPException(status_code=404, detail="No researchers found")
            
        # Read existing data
        df = pd.read_csv(researchers_file)
        
        # Filter out the researcher to delete
        updated_df = df[~((df['name'] == name) & (df['orcid'] == orcid))]
        
        if len(updated_df) == len(df):
            raise HTTPException(status_code=404, detail="Researcher not found")
            
        # Save updated data
        updated_df.to_csv(researchers_file, index=False)
        return {"message": "Researcher deleted successfully"}
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/researchers/{orcid}")
async def update_researcher(orcid: str, researcher: Dict):
    """Update a researcher by ORCID."""
    try:
        researchers_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "researchers.csv")
        
        if not os.path.exists(researchers_file):
            raise HTTPException(status_code=404, detail="No researchers found")
            
        # Read existing data
        df = pd.read_csv(researchers_file)
        
        # Find the researcher to update
        if not df['orcid'].eq(orcid).any():
            raise HTTPException(status_code=404, detail="Researcher not found")
            
        # Update the researcher data
        df.loc[df['orcid'] == orcid, ['name', 'department', 'university']] = [
            researcher.get('name', ''),
            researcher.get('department', ''),
            researcher.get('university', '')
        ]
        
        # Save updated data
        df.to_csv(researchers_file, index=False)
        return {"message": "Researcher updated successfully"}
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e)) 
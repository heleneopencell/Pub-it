from fastapi import APIRouter, HTTPException
import subprocess
import sys
import os

__all__ = ['router']
router = APIRouter(prefix="/api/scripts")

@router.post("/{script_name}")
async def run_script(script_name: str):
    """Run a Python script."""
    try:
        # Get the project root directory (two levels up from this file)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        # Map script names to actual script files
        script_map = {
            'pubmed_tracker.py': os.path.join(project_root, 'src', 'pubmed_tracker.py'),
            'scholar_citations.py': os.path.join(project_root, 'src', 'scholar_citations.py')
        }
        
        if script_name not in script_map:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid script name. Allowed scripts: {list(script_map.keys())}"
            )
            
        script_path = script_map[script_name]
        if not os.path.exists(script_path):
            raise HTTPException(
                status_code=404,
                detail=f"Script file not found: {script_path}"
            )
            
        # Run the script using the current Python interpreter
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            cwd=project_root  # Run from project root directory
        )
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Script failed: {result.stderr}"
            )
            
        return {"message": "Script executed successfully"}
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pubmed")
async def run_pubmed_tracker():
    """Run the PubMed tracker script"""
    return await run_script("pubmed_tracker.py")

@router.post("/citations")
async def run_scholar_citations():
    """Run the Scholar citations script"""
    return await run_script("scholar_citations.py")

@router.post("/podcast")
async def run_paper_to_podcast():
    """Run the paper to podcast script"""
    return await run_script("paper_to_podcast.py") 
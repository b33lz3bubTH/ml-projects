from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from pathlib import Path
from app.core.config import settings
from app.core.index import create_index_from_directory
from app.core.utils import logger

router = APIRouter()


@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload PDF files for ingestion and indexing."""
    data_path = Path(settings.DATA_DIR)
    data_path.mkdir(parents=True, exist_ok=True)
    
    indexed_files = []
    
    for file in files:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail=f"{file.filename} is not a PDF file")
        
        file_path = data_path / file.filename
        try:
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            indexed_files.append(file.filename)
            logger.info(f"Saved file: {file.filename}")
        except Exception as e:
            logger.error(f"Error saving file {file.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Error saving file {file.filename}: {str(e)}")
    
    try:
        logger.info("Creating index from uploaded files...")
        create_index_from_directory()
        logger.info("Indexing completed successfully")
    except Exception as e:
        logger.error(f"Error during indexing: {e}")
        raise HTTPException(status_code=500, detail=f"Error during indexing: {str(e)}")
    
    return {
        "status": "success",
        "files_indexed": indexed_files
    }


"""
API router for document management
"""
import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Dict, Any
import logging

from core.config.storage_config import StorageConfig
from core.storage.document_processor import process_document
from api.main import vector_store

logger = logging.getLogger(__name__)
router = APIRouter()

# Get all documents
@router.get("/")
async def get_documents():
    """Get a list of all available documents"""
    try:
        documents = []
        
        # Check if uploads directory exists
        if not os.path.exists(StorageConfig.UPLOADS_DIR):
            os.makedirs(StorageConfig.UPLOADS_DIR, exist_ok=True)
            
        # List all files in the uploads directory
        for filename in os.listdir(StorageConfig.UPLOADS_DIR):
            file_path = os.path.join(StorageConfig.UPLOADS_DIR, filename)
            
            # Skip directories
            if os.path.isdir(file_path):
                continue
                
            # Get file info
            file_size = os.path.getsize(file_path)
            file_extension = os.path.splitext(filename)[1].lower()
            
            # Add to list
            documents.append({
                "filename": filename,
                "size_bytes": file_size,
                "extension": file_extension
            })
            
        return {"documents": documents}
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Upload a document
@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document and add it to the vector store"""
    try:
        # Check file extension
        filename = file.filename
        file_extension = os.path.splitext(filename)[1].lower()
        
        if file_extension not in StorageConfig.SUPPORTED_FILE_TYPES:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Supported types: {', '.join(StorageConfig.SUPPORTED_FILE_TYPES)}"
            )
        
        # Create file path
        file_path = os.path.join(StorageConfig.UPLOADS_DIR, filename)
        
        # Save the uploaded file
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
            
        # Process the document and add to vector store
        document_info = process_document(file_path, vector_store)
        
        return {
            "status": "success",
            "message": f"File uploaded: {filename}",
            "document": document_info
        }
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Delete a document
@router.delete("/{filename}")
async def delete_document(filename: str):
    """Delete a document"""
    try:
        # Check if file exists
        file_path = os.path.join(StorageConfig.UPLOADS_DIR, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {filename}")
            
        # Delete the file
        os.remove(file_path)
        
        return {
            "status": "success",
            "message": f"File deleted: {filename}"
        }
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
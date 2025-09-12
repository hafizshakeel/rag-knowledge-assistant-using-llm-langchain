"""
API router for session management
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from api.main import chat_model

logger = logging.getLogger(__name__)
router = APIRouter()

# Request models
class LoadSessionRequest(BaseModel):
    session_id: str

# Get all sessions
@router.get("/")
async def get_sessions():
    """Get a list of all available sessions"""
    try:
        sessions = chat_model.get_all_sessions()
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Error getting sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Create a new session
@router.post("/new")
async def create_session():
    """Create a new session"""
    try:
        session_id = chat_model.create_new_session()
        if not session_id:
            raise HTTPException(status_code=500, detail="Failed to create new session")
            
        return {"session_id": session_id}
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Load a session
@router.post("/load")
async def load_session(request: LoadSessionRequest):
    """Load an existing session"""
    try:
        success = chat_model.load_session(request.session_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Session not found: {request.session_id}")
            
        return {
            "status": "success",
            "message": f"Session loaded: {request.session_id}"
        }
    except Exception as e:
        logger.error(f"Error loading session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Delete a session
@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    try:
        success = chat_model.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
            
        return {
            "status": "success",
            "message": f"Session deleted: {session_id}"
        }
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Delete all sessions
@router.delete("/")
async def clear_all_sessions():
    """Delete all sessions"""
    try:
        success = chat_model.clear_all_sessions()
        if not success:
            raise HTTPException(status_code=500, detail="Failed to clear sessions")
            
        return {
            "status": "success",
            "message": "All sessions cleared"
        }
    except Exception as e:
        logger.error(f"Error clearing sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
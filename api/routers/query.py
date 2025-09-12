"""
API router for handling query processing
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

# Import the LLM service (will be provided through dependency injection)
from api.main import chat_model

router = APIRouter()

# Request models
class QueryRequest(BaseModel):
    question: str

# Response models
class QueryResponse(BaseModel):
    response: str
    has_sensitive_data: bool = False
    sources: Optional[List[str]] = None

# Process a query
@router.post("/", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a user query and return a response"""
    try:
        # Call the LLM service to get a response
        response, has_sensitive_data = chat_model.get_response(request.question)
        
        # Return the response
        return {
            "response": response,
            "has_sensitive_data": has_sensitive_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
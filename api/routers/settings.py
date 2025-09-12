"""
API router for managing application settings
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from core.config.enums import AnswerMode, ModelProvider, EmbeddingProvider, MemoryMode

# Import the LLM service (will be provided through dependency injection)
from api.main import settings, vector_store, chat_model

router = APIRouter()

# Request models
class AnswerModeRequest(BaseModel):
    mode: str
    
class ModelProviderRequest(BaseModel):
    provider: str
    
class EmbeddingProviderRequest(BaseModel):
    provider: str
    
class MemoryModeRequest(BaseModel):
    mode: str
    
class PrivacyFilterRequest(BaseModel):
    enable: bool
    
class APIKeysRequest(BaseModel):
    openai: Optional[str] = None
    anthropic: Optional[str] = None
    groq: Optional[str] = None
    serper: Optional[str] = None
    tavily: Optional[str] = None

# Get all settings
@router.get("/")
async def get_settings():
    """Get current application settings"""
    return settings

# Update answer mode
@router.post("/answer_mode")
async def update_answer_mode(request: AnswerModeRequest):
    """Update the answer mode"""
    try:
        # Validate mode
        if request.mode not in [mode.value for mode in AnswerMode]:
            raise HTTPException(status_code=400, detail=f"Invalid answer mode: {request.mode}")
            
        # Update settings
        settings["answer_mode"] = request.mode
        
        # Update chat model
        chat_model.change_answer_mode(request.mode)
        
        return {"status": "success", "answer_mode": request.mode}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Update model provider
@router.post("/model_provider")
async def update_model_provider(request: ModelProviderRequest):
    """Update the model provider"""
    try:
        # Validate provider
        if request.provider not in [provider.value for provider in ModelProvider]:
            raise HTTPException(status_code=400, detail=f"Invalid model provider: {request.provider}")
            
        # Update settings
        settings["model_provider"] = request.provider
        
        # Update chat model
        chat_model.change_model_provider(request.provider)
        
        return {"status": "success", "model_provider": request.provider}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Update embedding provider
@router.post("/embedding_provider")
async def update_embedding_provider(request: EmbeddingProviderRequest):
    """Update the embedding provider"""
    try:
        # Validate provider
        if request.provider not in [provider.value for provider in EmbeddingProvider]:
            raise HTTPException(status_code=400, detail=f"Invalid embedding provider: {request.provider}")
            
        # Update settings
        settings["embedding_provider"] = request.provider
        
        # Update vector store
        vector_store.change_embedding_provider(request.provider)
        
        return {"status": "success", "embedding_provider": request.provider}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Update memory mode
@router.post("/memory_mode")
async def update_memory_mode(request: MemoryModeRequest):
    """Update the memory mode"""
    try:
        # Validate mode
        if request.mode not in [mode.value for mode in MemoryMode]:
            raise HTTPException(status_code=400, detail=f"Invalid memory mode: {request.mode}")
            
        # Update settings
        settings["memory_mode"] = request.mode
        
        # Update chat model and get session ID if switching to persistent
        success = chat_model.change_memory_mode(request.mode)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update memory mode")
            
        response = {"status": "success", "memory_mode": request.mode}
        
        # Include session ID if available
        if request.mode == MemoryMode.PERSISTENT.value and chat_model.session_id:
            response["session_id"] = chat_model.session_id
            
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Update privacy filter
@router.post("/privacy_filter")
async def update_privacy_filter(request: PrivacyFilterRequest):
    """Enable or disable the privacy filter"""
    try:
        # Update settings
        settings["privacy_filter"] = request.enable
        
        # Update chat model
        chat_model.toggle_privacy_filter(request.enable)
        
        return {"status": "success", "privacy_filter": request.enable}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Update API keys
@router.post("/api_keys")
async def update_api_keys(request: APIKeysRequest):
    """Update API keys"""
    try:
        # Update environment variables (these will be used the next time LLMs are initialized)
        import os
        
        if request.openai:
            os.environ["OPENAI_API_KEY"] = request.openai
            
        if request.anthropic:
            os.environ["ANTHROPIC_API_KEY"] = request.anthropic
            
        if request.groq:
            os.environ["GROQ_API_KEY"] = request.groq
            
        if request.serper:
            os.environ["SERPER_API_KEY"] = request.serper
            
        if request.tavily:
            os.environ["TAVILY_API_KEY"] = request.tavily
        
        return {"status": "success", "message": "API keys updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
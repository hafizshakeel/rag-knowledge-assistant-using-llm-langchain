"""
Main FastAPI application file
"""
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/app.log")
    ]
)

# Import configurations
from core.config import (
    AppConfig, ModelConfig, EmbeddingConfig, StorageConfig,
    ModelProvider, EmbeddingProvider, AnswerMode, MemoryMode
)

# Import components
from core.vector_store.chroma_store import VectorStore
from core.llm.llm_service import LLM

# Create logger
logger = logging.getLogger(__name__)

# Initialize vector store
vector_store = VectorStore(
    path=StorageConfig.DATA_DIR,
    embedding_provider=EmbeddingConfig.DEFAULT_EMBEDDING_PROVIDER
)

# Initialize LLM service
chat_model = LLM(
    vector_store=vector_store,
    model_provider=ModelConfig.DEFAULT_MODEL_PROVIDER,
    answer_mode=AnswerMode.RAG,
    memory_mode=MemoryMode.TRANSIENT
)

# Current settings (global state)
settings = {
    "answer_mode": AnswerMode.RAG.value,
    "model_provider": ModelConfig.DEFAULT_MODEL_PROVIDER.value,
    "embedding_provider": EmbeddingConfig.DEFAULT_EMBEDDING_PROVIDER.value,
    "memory_mode": MemoryMode.TRANSIENT.value,
    "privacy_filter": AppConfig.ENABLE_PRIVACY_FILTER,
    "session_id": None
}

# Create FastAPI app
app = FastAPI(
    title=AppConfig.APP_NAME,
    version=AppConfig.APP_VERSION,
    description="Advanced RAG API with multiple LLM providers and memory management"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",  # Streamlit local development
        "https://yourdomain.com",  # Replace with your production domain
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# Import and include API router
from api.routers import api_router
app.include_router(api_router, prefix="/api")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Check if the API is running"""
    return {
        "status": "healthy",
        "version": AppConfig.APP_VERSION
    }

# Root endpoint
@app.get("/")
async def root():
    """API root with information"""
    return {
        "app": AppConfig.APP_NAME,
        "version": AppConfig.APP_VERSION,
        "api_docs": "/docs",
        "health": "/health"
    }

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8080, reload=True)
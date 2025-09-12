import os
import logging
import requests
from typing import List, Optional
import shutil

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma

from core.config.embedding_config import EmbeddingConfig
from core.config.model_config import ModelConfig
from core.config.enums import EmbeddingProvider

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, path, embedding_provider=EmbeddingConfig.DEFAULT_EMBEDDING_PROVIDER):
        self.path = path
        self.embedding_provider = embedding_provider
        self.embeddings = self._initialize_embeddings()
        self.vector_store = self._initialize_db()

    def _initialize_embeddings(self):
        """Initialize embeddings based on the provider with fallback support"""
        try:
            if self.embedding_provider == EmbeddingProvider.HUGGINGFACE:
                logger.info(f"Initializing HuggingFace embeddings with model: {EmbeddingConfig.DEFAULT_HF_EMBEDDING_MODEL}")
                try:
                    return HuggingFaceEmbeddings(
                        model_name=EmbeddingConfig.DEFAULT_HF_EMBEDDING_MODEL
                    )
                except Exception as e:
                    logger.error(f"Failed to initialize HuggingFace embeddings: {str(e)}")
                    logger.info("Falling back to Ollama embeddings")
                    self.embedding_provider = EmbeddingProvider.OLLAMA
                    return self._initialize_ollama_embeddings()
            else:
                return self._initialize_ollama_embeddings()
        except Exception as e:
            logger.error(f"Error initializing embeddings: {str(e)}")
            raise

    def _initialize_ollama_embeddings(self):
        """Initialize Ollama embeddings with connectivity check"""
        logger.info(f"Initializing Ollama embeddings with model: {EmbeddingConfig.DEFAULT_OLLAMA_EMBEDDING_MODEL}")
        # Check if Ollama is running
        try:
            response = requests.get(f"{ModelConfig.OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                return OllamaEmbeddings(
                    model=EmbeddingConfig.DEFAULT_OLLAMA_EMBEDDING_MODEL,
                    base_url=ModelConfig.OLLAMA_BASE_URL
                )
            else:
                raise ConnectionError(f"Ollama server returned status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to connect to Ollama server: {str(e)}")
            # If Ollama fails and we were already trying to use it as a fallback,
            # use a dummy embedding as last resort
            if self.embedding_provider == EmbeddingProvider.OLLAMA:
                logger.warning("Using fallback basic embeddings. RAG functionality will be limited.")
                return self._get_fallback_embeddings()
            # If we were trying HuggingFace first and Ollama fallback fails, try to use HuggingFace offline
            return self._get_fallback_embeddings()

    def _get_fallback_embeddings(self):
        """Create a very basic fallback embedding for offline use"""
        from langchain.embeddings.base import Embeddings
        
        class FallbackEmbeddings(Embeddings):
            def embed_documents(self, texts):
                # Create 384-dimension embeddings to match the expected dimension
                return [[hash(text) % 1000 / 1000] * 384 for text in texts]
            
            def embed_query(self, text):
                return [hash(text) % 1000 / 1000] * 384
        
        return FallbackEmbeddings()

    def _initialize_db(self):
        """Initialize ChromaDB with the chosen embeddings"""
        try:
            if not os.path.exists(self.path):
                os.makedirs(self.path, exist_ok=True)
                logger.info(f"Created vector store directory: {self.path}")
                
            try:
                # Try to load existing DB
                return Chroma(
                    persist_directory=self.path,
                    embedding_function=self.embeddings
                )
            except Exception as e:
                if "dimension" in str(e).lower():
                    # Handle dimension mismatch error by recreating the vector store
                    logger.warning(f"Dimension mismatch detected: {str(e)}")
                    logger.info("Recreating vector store with new embedding model...")
                    
                    # Backup the old vector store
                    backup_path = f"{self.path}_backup"
                    if os.path.exists(self.path):
                        if os.path.exists(backup_path):
                            shutil.rmtree(backup_path)
                        shutil.copytree(self.path, backup_path)
                        logger.info(f"Backed up existing vector store to {backup_path}")
                        
                        # Remove the old vector store
                        shutil.rmtree(self.path)
                        os.makedirs(self.path, exist_ok=True)
                        logger.info("Removed old vector store and created new directory")
                    
                    # Create new vector store with current embeddings
                    return Chroma(
                        persist_directory=self.path,
                        embedding_function=self.embeddings
                    )
                else:
                    # If it's not a dimension issue, re-raise the exception
                    raise
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {str(e)}")
            raise

    def add_documents(self, documents):
        try:
            self.vector_store.add_documents(documents)
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            if "dimension" in str(e).lower():
                # If dimension error occurs during document addition, recreate the vector store
                logger.warning("Dimension mismatch during document addition. Recreating vector store...")
                self.vector_store = self._initialize_db()
                # Try adding documents again
                self.vector_store.add_documents(documents)
            else:
                # If it's not a dimension error, re-raise
                raise
        
    def _enhance_query_with_history(self, query: str, chat_history: Optional[List] = None) -> str:
        """
        Enhance the current query with relevant context from conversation history
        """
        if not chat_history or len(chat_history) == 0:
            return query
            
        # Extract last 2-3 exchanges for context
        recent_history = chat_history[-6:]  # Last 3 exchanges (user+assistant pairs)
        
        # Build context string
        history_context = "Previous conversation:\n"
        for msg in recent_history:
            role = "User" if msg.type == "human" else "Assistant"
            history_context += f"{role}: {msg.content}\n"
        
        # Combine with current query
        enhanced_query = f"{history_context}\nCurrent question: {query}"
        return enhanced_query

    def similarity_search(self, query, k=3, chat_history=None):
        # Combine current query with relevant history
        enhanced_query = self._enhance_query_with_history(query, chat_history)
        return self.vector_store.similarity_search(enhanced_query, k=k)
        
    def change_embedding_provider(self, provider: EmbeddingProvider):
        """Change the embedding provider at runtime"""
        try:
            self.embedding_provider = provider
            self.embeddings = self._initialize_embeddings()
            self.vector_store = self._initialize_db()
            logger.info(f"Changed embedding provider to: {provider}")
            return True
        except Exception as e:
            logger.error(f"Error changing embedding provider: {str(e)}")
            return False
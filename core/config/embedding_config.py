"""
Embedding-specific configuration settings
"""
from core.config.enums import EmbeddingProvider

class EmbeddingConfig:
    # Default embedding provider
    DEFAULT_EMBEDDING_PROVIDER = EmbeddingProvider.HUGGINGFACE
    
    # HuggingFace Configuration
    DEFAULT_HF_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Ollama Configuration
    DEFAULT_OLLAMA_EMBEDDING_MODEL = "all-minilm"
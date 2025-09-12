"""
Enums for configuration settings
"""
from enum import Enum

class ModelProvider(Enum):
    """LLM provider options"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    OLLAMA = "ollama"

class EmbeddingProvider(Enum):
    """Embedding provider options"""
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"

class AnswerMode(Enum):
    """Answer mode options"""
    DEFAULT = "default"  # Uses model's knowledge
    RAG = "rag"  # Uses document search
    WEB_SEARCH = "web_search"  # Uses web search

class MemoryMode(Enum):
    """Memory mode options"""
    TRANSIENT = "transient"  # Only remembers recent messages
    PERSISTENT = "persistent"  # Stores conversations in database
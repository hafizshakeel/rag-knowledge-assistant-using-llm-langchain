"""
Model-specific configuration settings
"""
import os
from dotenv import load_dotenv
from core.config.enums import ModelProvider

# Load environment variables
load_dotenv()

class ModelConfig:
    # Default model provider
    DEFAULT_MODEL_PROVIDER = ModelProvider.GROQ
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DEFAULT_OPENAI_MODEL = "gpt-3.5-turbo"
    OPENAI_TEMPERATURE = 0.7
    OPENAI_MAX_TOKENS = 2048
    OPENAI_REQUEST_TIMEOUT = 60
    
    # Anthropic Configuration
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    DEFAULT_ANTHROPIC_MODEL = "claude-3-haiku-20240307"
    ANTHROPIC_TEMPERATURE = 0.7
    ANTHROPIC_MAX_TOKENS = 4096
    
    # Groq Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    DEFAULT_GROQ_MODEL = "openai/gpt-oss-20b" 
    GROQ_TEMPERATURE = 0.2
    GROQ_MAX_TOKENS = 2048
    
    # Ollama Configuration
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    DEFAULT_OLLAMA_MODEL = "llama3"
    OLLAMA_TEMPERATURE = 0.7
    OLLAMA_NUM_CTX = 4096
    OLLAMA_REQUEST_TIMEOUT = 120
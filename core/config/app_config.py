"""
Application-wide configuration settings
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AppConfig:
    # Application metadata
    APP_NAME = "Advanced RAG Assistant"
    APP_VERSION = "1.0.0"
    
    # Storage paths
    VECTOR_DB_PATH = "core/vector_store/vector_db"
    MEMORY_DB_PATH = "core/memory/memory_db"
    
    # Memory settings
    MEMORY_MESSAGE_LIMIT = 10
    
    # Security settings
    ENABLE_PRIVACY_FILTER = True
    
    # Web search settings
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    TAVILY_MAX_RESULTS = 5
    
    # SERPER settings (legacy)
    SERPER_API_KEY = os.getenv("SERPER_API_KEY")
    SERPER_MAX_RESULTS = 5
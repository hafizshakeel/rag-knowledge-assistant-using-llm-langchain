"""
Storage-specific configuration settings
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class StorageConfig:
    # S3 Storage
    AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
    AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
    AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')
    
    # Local storage
    DATA_DIR = "data"
    UPLOADS_DIR = "data/uploads"
    
    # Ensure directories exist
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    
    # Supported file types
    SUPPORTED_FILE_TYPES = [".txt", ".pdf", ".csv", ".md", ".html"]
    
    # Maximum file size in bytes (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
"""
Central logging utility for the RAG application.
Provides consistent logging across all components.
"""
import os
import logging
from logging.handlers import RotatingFileHandler
import sys

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Define log format
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

def setup_logger(name, level=logging.INFO, log_file=None):
    """
    Set up a logger with consistent formatting.
    
    Args:
        name (str): Name of the logger
        level (int): Logging level
        log_file (str, optional): Path to log file. If None, only console logging is used.
        
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers = []
        
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name):
    """
    Get a logger with the given name.
    If it doesn't exist, it will be created with default settings.
    
    Args:
        name (str): Name of the logger
        
    Returns:
        logging.Logger: Logger instance
    """
    return setup_logger(name, log_file=f"logs/app.log")

# Default application logger
app_logger = get_logger("rag_app")
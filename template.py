#!/usr/bin/env python

import os
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("template")

def create_directory_structure(base_dir=None):
    """Create the directory structure for the project"""
    if base_dir:
        os.makedirs(base_dir, exist_ok=True)
        os.chdir(base_dir)
    
    directories = [
        "api/middleware",
        "api/routers",
        "app/components",
        "app/pages",
        "app/utils",
        "core/config",
        "core/llm",
        "core/memory",
        "core/memory/memory_db/sessions",
        "core/security",
        "core/storage",
        "core/utils",
        "core/vector_store",
        "data/uploads",
        "logs",
        "notebook",
        "tests"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        # Add __init__.py for Python package structure
        if not directory.endswith(("uploads", "logs", "sessions", "notebook")):
            init_file = Path(directory) / "__init__.py"
            if not init_file.exists():
                init_file.write_text(f'""" {directory.replace("/", ".")} """\n')
    
    logger.info("Directory structure created successfully")

def create_config_files():
    """Create basic configuration files"""
    env_template = """# API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GROQ_API_KEY=your_groq_key
SERPER_API_KEY=your_serper_key
TAVILY_API_KEY=your_tavily_key

# Ollama Settings
OLLAMA_BASE_URL=http://localhost:11434
"""
    Path(".env.template").write_text(env_template)
    
    setup_py = """from setuptools import setup, find_packages

setup(
    name="rag_app",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "streamlit>=1.27.0",
        "langchain>=0.0.267",
        "chromadb>=0.4.13",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="RAG Application",
)
"""
    Path("setup.py").write_text(setup_py)

    logger.info("Configuration files created successfully")

def main():
    """Main function to initialize the project"""
    parser = argparse.ArgumentParser(description="Initialize project structure")
    parser.add_argument("--dir", help="Base directory for the project", default=None)
    args = parser.parse_args()
    
    try:
        create_directory_structure(args.dir)
        create_config_files()
        
        logger.info("Project initialization completed successfully")
        logger.info("Next steps:")
        logger.info("1. Create a virtual environment: python -m venv venv")
        logger.info("2. Activate the virtual environment")
        logger.info("3. Install dependencies: pip install -r requirements.txt")
        logger.info("4. Create .env file from .env.template and add your API keys")
        logger.info("5. Run the application: python run.py")
        
    except Exception as e:
        logger.error(f"Error initializing project: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())

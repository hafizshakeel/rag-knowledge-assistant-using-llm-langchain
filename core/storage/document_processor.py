"""
Helper functions for loading, processing, and splitting documents for the vector store.
"""
import os
import logging
from typing import List, Dict, Any
from langchain.docstore.document import Document
from langchain_community.document_loaders import TextLoader, PyPDFLoader, CSVLoader, UnstructuredHTMLLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

# Text splitting parameters
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

def split_text(documents: List[Document]) -> List[Document]:
    """Split documents into smaller chunks for better embedding and retrieval"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, 
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = text_splitter.split_documents(documents)
    logger.info(f"Split {len(documents)} documents into {len(chunks)} chunks")
    return chunks

def load_document(file_path: str) -> List[Document]:
    """Load document based on file type"""
    file_extension = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_extension == '.pdf':
            loader = PyPDFLoader(file_path)
        elif file_extension == '.txt':
            loader = TextLoader(file_path, encoding="utf-8")
        elif file_extension == '.csv':
            loader = CSVLoader(file_path)
        elif file_extension == '.md':
            loader = UnstructuredMarkdownLoader(file_path)
        elif file_extension == '.html':
            loader = UnstructuredHTMLLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        documents = loader.load()
        logger.info(f"Loaded {len(documents)} document segments from {file_path}")
        return documents
    except Exception as e:
        logger.error(f"Error loading document {file_path}: {str(e)}")
        raise

def process_document(file_path: str, vector_store=None) -> Dict[str, Any]:
    """
    Process a document file and add it to the vector store
    
    Args:
        file_path: Path to the document file
        vector_store: VectorStore instance to add documents to
    
    Returns:
        Dict with document information
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Get file information
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_extension = os.path.splitext(file_path)[1].lower()
        
        # Load document
        documents = load_document(file_path)
        
        # Split text into chunks
        chunks = split_text(documents)
        
        # Add to vector store if provided
        if vector_store:
            vector_store.add_documents(chunks)
            logger.info(f"Added {len(chunks)} chunks from {file_name} to vector store")
        
        # Return document information
        return {
            "filename": file_name,
            "size_bytes": file_size,
            "extension": file_extension,
            "chunk_count": len(chunks)
        }
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise


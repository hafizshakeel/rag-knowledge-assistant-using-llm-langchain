"""
Memory management service for storing and retrieving conversation history
"""
import os
import json
import uuid
import logging
import datetime
from typing import List, Dict, Any, Optional
from langchain.memory import ConversationBufferMemory
from langchain_chroma import Chroma
from langchain.schema import Document

from core.config.app_config import AppConfig
from core.config.enums import MemoryMode

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self, memory_mode=MemoryMode.TRANSIENT, embedding_function=None):
        self.memory_mode = memory_mode
        self.transient_memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.embedding_function = embedding_function
        
        # Initialize persistent memory if needed
        if self.memory_mode == MemoryMode.PERSISTENT:
            self._init_persistent_memory()
            
        # Directory for session metadata storage
        self.sessions_dir = os.path.join(AppConfig.MEMORY_DB_PATH, "sessions")
        os.makedirs(self.sessions_dir, exist_ok=True)
        
    def _init_persistent_memory(self):
        """Initialize persistent memory storage using ChromaDB"""
        try:
            if not self.embedding_function:
                raise ValueError("Embedding function is required for persistent memory")
                
            os.makedirs(AppConfig.MEMORY_DB_PATH, exist_ok=True)
            
            self.persistent_memory = Chroma(
                persist_directory=AppConfig.MEMORY_DB_PATH,
                embedding_function=self.embedding_function,
                collection_name="chat_history"
            )
            logger.info("Initialized persistent memory storage")
        except Exception as e:
            logger.error(f"Failed to initialize persistent memory: {str(e)}")
            # Fall back to transient memory
            self.memory_mode = MemoryMode.TRANSIENT
            
    def change_memory_mode(self, mode: MemoryMode):
        """Change the memory mode"""
        if mode == self.memory_mode:
            return True
            
        try:
            self.memory_mode = mode
            if mode == MemoryMode.PERSISTENT and not hasattr(self, 'persistent_memory'):
                self._init_persistent_memory()
            logger.info(f"Changed memory mode to {mode}")
            return True
        except Exception as e:
            logger.error(f"Failed to change memory mode: {str(e)}")
            return False
            
    def add_user_message(self, message: str, session_id: str = None):
        """Add a user message to memory"""
        # Always add to transient memory
        self.transient_memory.chat_memory.add_user_message(message)
        
        # Trim transient memory if needed
        self._trim_transient_memory()
        
        # Add to persistent memory if enabled
        if self.memory_mode == MemoryMode.PERSISTENT and session_id:
            self._add_to_persistent_memory("user", message, session_id)
            
    def add_ai_message(self, message: str, session_id: str = None):
        """Add an AI message to memory"""
        # Always add to transient memory
        self.transient_memory.chat_memory.add_ai_message(message)
        
        # Trim transient memory if needed
        self._trim_transient_memory()
        
        # Add to persistent memory if enabled
        if self.memory_mode == MemoryMode.PERSISTENT and session_id:
            self._add_to_persistent_memory("assistant", message, session_id)
            
    def _add_to_persistent_memory(self, role: str, content: str, session_id: str):
        """Add a message to persistent memory"""
        try:
            timestamp = datetime.datetime.now().isoformat()
            
            # Create document for vector store
            doc = Document(
                page_content=content,
                metadata={
                    "role": role,
                    "timestamp": timestamp,
                    "session_id": session_id
                }
            )
            
            # Add to vector store
            self.persistent_memory.add_documents([doc])
            
            # Update session metadata
            self._update_session_metadata(session_id, role, content, timestamp)
            
        except Exception as e:
            logger.error(f"Failed to add message to persistent memory: {str(e)}")
            
    def _update_session_metadata(self, session_id: str, role: str, content: str, timestamp: str):
        """Update session metadata file"""
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        
        # Create or update session file
        try:
            if os.path.exists(session_file):
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
            else:
                # New session
                session_data = {
                    "session_id": session_id,
                    "created_at": timestamp,
                    "updated_at": timestamp,
                    "title": self._extract_title(content) if role == "user" else "New Chat",
                    "messages": []
                }
                
            # Update metadata
            session_data["updated_at"] = timestamp
            
            # Add message to messages list
            session_data["messages"].append({
                "role": role,
                "content": content,
                "timestamp": timestamp
            })
            
            # Set title to first user message if this is the first message
            if len(session_data["messages"]) == 1 and role == "user":
                session_data["title"] = self._extract_title(content)
                
            # Write updated data
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to update session metadata: {str(e)}")
            
    def _extract_title(self, content: str) -> str:
        """Extract a title from the first user message"""
        # Use the first 30 chars or first sentence as title
        title = content.strip().split("\n")[0]
        if len(title) > 30:
            title = title[:27] + "..."
        return title
            
    def _trim_transient_memory(self):
        """Trim transient memory to the configured limit"""
        messages = self.transient_memory.chat_memory.messages
        if len(messages) > AppConfig.MEMORY_MESSAGE_LIMIT:
            # Keep only the last N messages
            self.transient_memory.chat_memory.messages = messages[-AppConfig.MEMORY_MESSAGE_LIMIT:]
            
    def get_chat_history(self) -> List:
        """Get the current chat history from transient memory"""
        return self.transient_memory.chat_memory.messages
        
    def load_session(self, session_id: str) -> bool:
        """Load a session from persistent memory into transient memory"""
        if self.memory_mode != MemoryMode.PERSISTENT:
            logger.warning("Cannot load session in transient memory mode")
            return False
            
        try:
            # Clear transient memory
            self.transient_memory.clear()
            
            # Get session file
            session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
            if not os.path.exists(session_file):
                logger.error(f"Session {session_id} not found")
                return False
                
            # Load session data
            with open(session_file, 'r') as f:
                session_data = json.load(f)
                
            # Add messages to transient memory
            for message in session_data["messages"]:
                if message["role"] == "user":
                    self.transient_memory.chat_memory.add_user_message(message["content"])
                else:
                    self.transient_memory.chat_memory.add_ai_message(message["content"])
                    
            # Trim if needed
            self._trim_transient_memory()
            
            logger.info(f"Loaded session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {str(e)}")
            return False
            
    def create_session(self) -> str:
        """Create a new session and return its ID"""
        session_id = str(uuid.uuid4())
        logger.info(f"Created new session with ID {session_id}")
        return session_id
        
    def get_all_sessions(self) -> List[Dict]:
        """Get a list of all available sessions"""
        sessions = []
        
        try:
            # Get all session files
            for filename in os.listdir(self.sessions_dir):
                if filename.endswith(".json"):
                    with open(os.path.join(self.sessions_dir, filename), 'r') as f:
                        session_data = json.load(f)
                        # Add a summary version to the list
                        sessions.append({
                            "session_id": session_data["session_id"],
                            "title": session_data["title"],
                            "created_at": session_data["created_at"],
                            "updated_at": session_data["updated_at"],
                            "message_count": len(session_data["messages"])
                        })
            
            # Sort by updated_at (newest first)
            sessions.sort(key=lambda s: s["updated_at"], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to get sessions: {str(e)}")
            
        return sessions
        
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        try:
            # Delete session file
            session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
            if os.path.exists(session_file):
                os.remove(session_file)
                
            # Delete from vector store
            if hasattr(self, 'persistent_memory'):
                self.persistent_memory.delete(
                    where={"session_id": session_id}
                )
                
            logger.info(f"Deleted session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {str(e)}")
            return False
            
    def clear_all_sessions(self) -> bool:
        """Delete all sessions"""
        try:
            # Delete all session files
            for filename in os.listdir(self.sessions_dir):
                if filename.endswith(".json"):
                    os.remove(os.path.join(self.sessions_dir, filename))
                    
            # Clear vector store
            if hasattr(self, 'persistent_memory'):
                self.persistent_memory.delete(
                    where={}  # Delete all documents
                )
                
            logger.info("Cleared all sessions")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear sessions: {str(e)}")
            return False
"""
Main Streamlit application for the RAG frontend
"""
import os
import requests
import json
import streamlit as st
from typing import List, Dict, Any, Optional
import time

# API URL
API_URL = "http://localhost:8080/api"

# Set page config
st.set_page_config(
    page_title="Advanced RAG Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    /* Main container */
    .main {
        background-color: #f5f7f9;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #ffffff;
    }
    
    /* User message bubble */
    .user-message {
        background-color: #e6f7ff;
        border-radius: 15px;
        padding: 10px 15px;
        margin: 5px 0;
        box-shadow: 1px 1px 3px rgba(0, 0, 0, 0.1);
        display: inline-block;
        max-width: 80%;
        margin-left: auto;
        margin-right: 0;
        text-align: right;
    }
    
    /* Assistant message bubble */
    .assistant-message {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 10px 15px;
        margin: 5px 0;
        box-shadow: 1px 1px 3px rgba(0, 0, 0, 0.1);
        display: inline-block;
        max-width: 80%;
        margin-right: auto;
        margin-left: 0;
    }
    
    /* Message container */
    .message-container {
        display: flex;
        flex-direction: column;
        width: 100%;
        padding: 5px 0;
    }
    
    /* Typing indicator */
    .typing-indicator {
        display: flex;
        padding: 8px 15px;
        background-color: #ffffff;
        border-radius: 15px;
        margin: 5px 0;
        width: fit-content;
    }
    
    .typing-indicator span {
        height: 8px;
        width: 8px;
        background-color: #9E9E9E;
        border-radius: 50%;
        display: inline-block;
        margin-right: 5px;
        animation: typing 1.3s ease-in-out infinite;
    }
    
    .typing-indicator span:nth-child(2) {
        animation-delay: 0.2s;
    }
    
    .typing-indicator span:nth-child(3) {
        animation-delay: 0.4s;
    }
    
    @keyframes typing {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-5px); }
        100% { transform: translateY(0px); }
    }
    
    /* File upload area */
    .file-upload-container {
        border: 2px dashed #ccc;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        margin: 10px 0;
        background-color: #f9f9f9;
    }
    
    /* Document card */
    .document-card {
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
        background-color: white;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        display: flex;
        align-items: center;
    }
    
    .document-card .icon {
        margin-right: 10px;
        font-size: 24px;
    }
    
    .document-card .details {
        flex-grow: 1;
    }
    
    .document-card .actions {
        display: flex;
    }
    
    /* Settings container */
    .settings-section {
        background-color: white;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    
    /* Status indicator */
    .status-indicator {
        display: inline-block;
        height: 10px;
        width: 10px;
        border-radius: 50%;
        margin-right: 5px;
    }
    
    .status-indicator.success {
        background-color: #4CAF50;
    }
    
    .status-indicator.warning {
        background-color: #FF9800;
    }
    
    .status-indicator.error {
        background-color: #F44336;
    }
    
    /* Source citation */
    .source-citation {
        font-size: 0.8em;
        color: #666;
        font-style: italic;
        border-top: 1px solid #eee;
        padding-top: 5px;
        margin-top: 10px;
    }
    
    /* Security notice */
    .security-notice {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 10px;
        margin: 10px 0;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "api_ready" not in st.session_state:
    st.session_state.api_ready = False
    
if "documents" not in st.session_state:
    st.session_state.documents = []
    
if "settings" not in st.session_state:
    st.session_state.settings = {
        "answer_mode": "rag",
        "model_provider": "groq",
        "embedding_provider": "huggingface",
        "memory_mode": "transient",
        "privacy_filter": True,
        "session_id": None
    }
    
if "typing" not in st.session_state:
    st.session_state.typing = False

# Check API connection
def check_api_connection():
    try:
        response = requests.get("http://localhost:8080/health", timeout=2)
        if response.status_code == 200:
            return True
        return False
    except:
        return False

# Load settings from API
def load_settings():
    try:
        response = requests.get(f"{API_URL}/settings")
        if response.status_code == 200:
            st.session_state.settings = response.json()
            return True
        return False
    except:
        return False

# Load documents from API
def load_documents():
    try:
        response = requests.get(f"{API_URL}/documents")
        if response.status_code == 200:
            st.session_state.documents = response.json().get("documents", [])
            return True
        return False
    except:
        return False

# Send message to API
def send_message(question):
    try:
        response = requests.post(
            f"{API_URL}/query",
            json={"question": question}
        )
        if response.status_code == 200:
            return response.json().get("response"), response.json().get("has_sensitive_data", False)
        return f"Error: {response.json().get('detail', 'Unknown error')}", False
    except Exception as e:
        return f"Error connecting to API: {str(e)}", False

# Update settings in API
def update_setting(setting_type, value):
    endpoint = f"{API_URL}/settings/{setting_type}"
    payload = {}
    
    if setting_type == "answer_mode":
        payload = {"mode": value}
    elif setting_type == "model_provider":
        payload = {"provider": value}
    elif setting_type == "embedding_provider":
        payload = {"provider": value}
    elif setting_type == "memory_mode":
        payload = {"mode": value}
    elif setting_type == "privacy_filter":
        payload = {"enable": value}
    
    try:
        response = requests.post(endpoint, json=payload)
        if response.status_code == 200:
            # Update local settings
            data = response.json()
            if setting_type in st.session_state.settings:
                st.session_state.settings[setting_type] = value
            
            # If session ID is returned, update it
            if "session_id" in data:
                st.session_state.settings["session_id"] = data["session_id"]
                
            return True
        return False
    except:
        return False

# Upload document to API
def upload_document(file):
    try:
        files = {"file": (file.name, file, "application/octet-stream")}
        response = requests.post(f"{API_URL}/documents/upload", files=files)
        if response.status_code == 200:
            # Reload documents
            load_documents()
            return True, response.json().get("message", "File uploaded")
        return False, response.json().get("detail", "Upload failed")
    except Exception as e:
        return False, f"Error uploading file: {str(e)}"

# Delete document from API
def delete_document(filename):
    try:
        response = requests.delete(f"{API_URL}/documents/{filename}")
        if response.status_code == 200:
            # Reload documents
            load_documents()
            return True
        return False
    except:
        return False

# Create new session
def create_new_session():
    try:
        response = requests.post(f"{API_URL}/sessions/new")
        if response.status_code == 200:
            session_id = response.json().get("session_id")
            st.session_state.settings["session_id"] = session_id
            # Clear messages
            st.session_state.messages = []
            return True
        return False
    except:
        return False

# Load existing session
def load_session(session_id):
    try:
        response = requests.post(
            f"{API_URL}/sessions/load",
            json={"session_id": session_id}
        )
        if response.status_code == 200:
            st.session_state.settings["session_id"] = session_id
            # Clear messages (server has the history)
            st.session_state.messages = []
            return True
        return False
    except:
        return False

# Get all sessions
def get_all_sessions():
    try:
        response = requests.get(f"{API_URL}/sessions")
        if response.status_code == 200:
            return response.json().get("sessions", [])
        return []
    except:
        return []

# Delete session
def delete_session(session_id):
    try:
        response = requests.delete(f"{API_URL}/sessions/{session_id}")
        if response.status_code == 200:
            if st.session_state.settings.get("session_id") == session_id:
                st.session_state.settings["session_id"] = None
                st.session_state.messages = []
            return True
        return False
    except:
        return False

# Display messages
def display_messages():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if "has_sensitive_data" in message and message["has_sensitive_data"]:
                st.markdown(f"{message['content']}")
                st.markdown("""
                <div class="security-notice">
                    ⚠️ <b>Privacy Notice:</b> Sensitive information was detected and filtered from your input.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"{message['content']}")

# Main title
st.title("📚 RAG Knowledge Assistant")

# Check API connection and load initial data
if not st.session_state.api_ready:
    with st.spinner("Connecting to API..."):
        if check_api_connection():
            load_settings()
            load_documents()
            st.session_state.api_ready = True
        else:
            st.error("⚠️ Cannot connect to API. Please make sure the backend is running.")
            st.stop()

# Sidebar
with st.sidebar:
    st.header("Settings")
    
    # Answer Mode
    with st.expander("Answer Mode", expanded=True):
        answer_mode = st.radio(
            "How should I answer questions?",
            ["Default", "RAG", "Web Search"],
            index=1,  # Default to RAG
            format_func=lambda x: {
                "Default": "Model Knowledge",
                "RAG": "Document Search",
                "Web Search": "Web Search"
            }[x],
            key="answer_mode_radio"
        )
        
        # Map to API values
        answer_mode_map = {
            "Default": "default",
            "RAG": "rag",
            "Web Search": "web_search"
        }
        
        # Update if changed
        if answer_mode_map[answer_mode] != st.session_state.settings.get("answer_mode"):
            with st.spinner("Updating answer mode..."):
                if update_setting("answer_mode", answer_mode_map[answer_mode]):
                    st.success(f"Answer mode updated to {answer_mode}")
                else:
                    st.error("Failed to update answer mode")
    
    # Model Provider
    with st.expander("Model Provider"):
        model_provider = st.radio(
            "Which AI model should I use?",
            ["OpenAI", "Anthropic", "Groq", "Ollama"],
            index=3,  # Default to Ollama
            format_func=lambda x: {
                "OpenAI": "OpenAI GPT",
                "Anthropic": "Anthropic Claude",
                "Groq": "Groq LLama",
                "Ollama": "Ollama"
            }[x],
            key="model_provider_radio"
        )
        
        # Map to API values
        provider_map = {
            "OpenAI": "openai",
            "Anthropic": "anthropic",
            "Groq": "groq",
            "Ollama": "ollama"
        }
        
        # Update if changed
        if provider_map[model_provider] != st.session_state.settings.get("model_provider"):
            with st.spinner("Updating model provider..."):
                if update_setting("model_provider", provider_map[model_provider]):
                    st.success(f"Model provider updated to {model_provider}")
                else:
                    st.error("Failed to update model provider")
    
    # Embedding Provider
    with st.expander("Embedding Provider"):
        embedding_provider = st.radio(
            "Which embedding model should I use?",
            ["HuggingFace", "Ollama"],
            index=1,  # Default to Ollama
            format_func=lambda x: {
                "HuggingFace": "HuggingFace",
                "Ollama": "Ollama"
            }[x],
            key="embedding_provider_radio"
        )
        
        # Map to API values
        embedding_map = {
            "HuggingFace": "huggingface",
            "Ollama": "ollama"
        }
        
        # Update if changed
        if embedding_map[embedding_provider] != st.session_state.settings.get("embedding_provider"):
            with st.spinner("Updating embedding provider..."):
                if update_setting("embedding_provider", embedding_map[embedding_provider]):
                    st.success(f"Embedding provider updated to {embedding_provider}")
                else:
                    st.error("Failed to update embedding provider")
    
    # Memory Mode
    with st.expander("Memory Mode"):
        memory_mode = st.radio(
            "How should I remember our conversation?",
            ["Transient", "Persistent"],
            index=0,  # Default to Transient
            format_func=lambda x: {
                "Transient": "Short-term Memory",
                "Persistent": "Long-term Storage"
            }[x],
            key="memory_mode_radio"
        )
        
        # Map to API values
        memory_map = {
            "Transient": "transient",
            "Persistent": "persistent"
        }
        
        # Update if changed
        if memory_map[memory_mode] != st.session_state.settings.get("memory_mode"):
            with st.spinner("Updating memory mode..."):
                if update_setting("memory_mode", memory_map[memory_mode]):
                    st.success(f"Memory mode updated to {memory_mode}")
                else:
                    st.error("Failed to update memory mode")
    
    # Privacy Filter
    with st.expander("Privacy Filter"):
        privacy_filter = st.toggle(
            "Enable privacy filter",
            value=st.session_state.settings.get("privacy_filter", True),
            key="privacy_filter_toggle"
        )
        
        # Update if changed
        if privacy_filter != st.session_state.settings.get("privacy_filter"):
            with st.spinner("Updating privacy filter..."):
                if update_setting("privacy_filter", privacy_filter):
                    st.success(f"Privacy filter {'enabled' if privacy_filter else 'disabled'}")
                else:
                    st.error("Failed to update privacy filter")
    
    # Session Management
    with st.expander("Session Management"):
        # New session button
        if st.button("New Chat Session"):
            with st.spinner("Creating new session..."):
                if create_new_session():
                    st.success("New session created")
                else:
                    st.error("Failed to create new session")
        
        # Session list
        if st.session_state.settings.get("memory_mode") == "persistent":
            st.subheader("Available Sessions")
            sessions = get_all_sessions()
            if sessions:
                for session in sessions:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button(f"{session.get('title', 'Untitled')} - {session.get('message_count', 0)} msgs", key=f"session_{session.get('session_id')}"):
                            with st.spinner("Loading session..."):
                                if load_session(session.get("session_id")):
                                    st.success("Session loaded")
                                else:
                                    st.error("Failed to load session")
                    with col2:
                        if st.button("🗑️", key=f"delete_{session.get('session_id')}"):
                            with st.spinner("Deleting session..."):
                                if delete_session(session.get("session_id")):
                                    st.success("Session deleted")
                                else:
                                    st.error("Failed to delete session")
            else:
                st.info("No saved sessions found")
    
    # Document Management
    with st.expander("Document Management", expanded=True):
        st.subheader("Upload Document")
        
        uploaded_file = st.file_uploader("Choose a file", type=["pdf", "txt", "csv", "md", "html"])
        if uploaded_file is not None:
            if st.button("Upload"):
                with st.spinner("Uploading document..."):
                    success, message = upload_document(uploaded_file)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
        
        # Document list
        st.subheader("Available Documents")
        if st.session_state.documents:
            for doc in st.session_state.documents:
                col1, col2 = st.columns([3, 1])
                with col1:
                    # Choose icon based on file extension
                    icon = "📄"
                    if doc.get("extension") == ".pdf":
                        icon = "📑"
                    elif doc.get("extension") == ".csv":
                        icon = "📊"
                    elif doc.get("extension") == ".md":
                        icon = "📝"
                    elif doc.get("extension") == ".html":
                        icon = "🌐"
                    
                    st.markdown(f"{icon} **{doc.get('filename')}** - {doc.get('size_bytes')/1024:.1f} KB")
                with col2:
                    if st.button("🗑️", key=f"delete_doc_{doc.get('filename')}"):
                        with st.spinner("Deleting document..."):
                            if delete_document(doc.get("filename")):
                                st.success("Document deleted")
                            else:
                                st.error("Failed to delete document")
        else:
            st.info("No documents uploaded yet")

# Display active session info
if st.session_state.settings.get("session_id") and st.session_state.settings.get("memory_mode") == "persistent":
    st.info(f"Active Session ID: {st.session_state.settings.get('session_id')}")

# Display messages
display_messages()

# Show typing indicator
if st.session_state.typing:
    st.markdown("""
    <div class="typing-indicator">
        <span></span>
        <span></span>
        <span></span>
    </div>
    """, unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input("Ask a question..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.typing = True
    st.rerun()

# If typing indicator is shown, process the message
if st.session_state.typing:
    # Get last user message
    last_message = st.session_state.messages[-1]["content"]
    
    # Process response
    response, has_sensitive_data = send_message(last_message)
    
    # Add assistant message to chat
    st.session_state.messages.append({
        "role": "assistant", 
        "content": response,
        "has_sensitive_data": has_sensitive_data
    })
    
    # Turn off typing indicator
    st.session_state.typing = False
    st.rerun()
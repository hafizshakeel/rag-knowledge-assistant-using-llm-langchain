import logging
from typing import Dict, List, Optional, Any, Tuple
import os

from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from langchain_community.chat_models import ChatOllama
from langchain_tavily import TavilySearch
from langchain.chains import LLMChain

from core.config.app_config import AppConfig
from core.config.model_config import ModelConfig
from core.config.enums import ModelProvider, AnswerMode, MemoryMode
from core.llm.prompts import DEFAULT_PROMPT, RAG_PROMPT, WEB_SEARCH_PROMPT
from core.security.privacy_filter import PrivacyFilter
from core.memory.memory_manager import MemoryManager


logger = logging.getLogger(__name__)

class LLM:
    def __init__(self, vector_store, 
                 model_provider=ModelConfig.DEFAULT_MODEL_PROVIDER,
                 answer_mode=AnswerMode.RAG,
                 memory_mode=MemoryMode.TRANSIENT):
        
        self.vector_store = vector_store
        self.model_provider = model_provider
        self.answer_mode = answer_mode
        self.memory_mode = memory_mode
        self.session_id = None
        
        # Initialize privacy filter
        self.privacy_filter = PrivacyFilter(enable_filter=AppConfig.ENABLE_PRIVACY_FILTER)
        
        # Initialize memory manager
        self.memory_manager = MemoryManager(
            memory_mode=memory_mode,
            embedding_function=vector_store.embeddings
        )
        
        # Keep legacy memory for compatibility with LangChain
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
        )
        
        # Initialize LLM based on provider
        self.llm = self._initialize_llm()
        
        # Initialize chain based on answer mode
        self._initialize_chain()
        
    def _initialize_llm(self):
        """Initialize the LLM based on the selected provider"""
        try:
            if self.model_provider == ModelProvider.OPENAI:
                if not ModelConfig.OPENAI_API_KEY:
                    raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
                return ChatOpenAI(
                    model=ModelConfig.DEFAULT_OPENAI_MODEL,
                    temperature=ModelConfig.OPENAI_TEMPERATURE,
                    api_key=ModelConfig.OPENAI_API_KEY,
                    max_tokens=ModelConfig.OPENAI_MAX_TOKENS,
                    request_timeout=ModelConfig.OPENAI_REQUEST_TIMEOUT
                )
            elif self.model_provider == ModelProvider.ANTHROPIC:
                if not ModelConfig.ANTHROPIC_API_KEY:
                    raise ValueError("Anthropic API key not found. Please set ANTHROPIC_API_KEY environment variable.")
                return ChatAnthropic(
                    model=ModelConfig.DEFAULT_ANTHROPIC_MODEL,
                    temperature=ModelConfig.ANTHROPIC_TEMPERATURE,
                    api_key=ModelConfig.ANTHROPIC_API_KEY,
                    max_tokens=ModelConfig.ANTHROPIC_MAX_TOKENS
                )
            elif self.model_provider == ModelProvider.GROQ:
                if not ModelConfig.GROQ_API_KEY:
                    raise ValueError("Groq API key not found. Please set GROQ_API_KEY environment variable.")
                return ChatGroq(
                    model=ModelConfig.DEFAULT_GROQ_MODEL,
                    temperature=ModelConfig.GROQ_TEMPERATURE,
                    max_tokens=ModelConfig.GROQ_MAX_TOKENS,
                    api_key=ModelConfig.GROQ_API_KEY
                )
            elif self.model_provider == ModelProvider.OLLAMA:
                try:
                    # Enhanced Ollama setup with better error handling
                    ollama_instance = ChatOllama(
                        model=ModelConfig.DEFAULT_OLLAMA_MODEL,
                        temperature=ModelConfig.OLLAMA_TEMPERATURE,
                        base_url=ModelConfig.OLLAMA_BASE_URL,
                        num_ctx=ModelConfig.OLLAMA_NUM_CTX,
                        request_timeout=ModelConfig.OLLAMA_REQUEST_TIMEOUT
                    )
                    # Verify Ollama is working by doing a simple test
                    test_response = ollama_instance.invoke("Test connection")
                    logger.info(f"Ollama test successful: {test_response.content[:30]}...")
                    return ollama_instance
                except Exception as e:
                    logger.error(f"Ollama initialization failed: {str(e)}")
                    logger.info("Falling back to default model provider (Groq)")
                    self.model_provider = ModelProvider.GROQ
                    return ChatGroq(
                        model=ModelConfig.DEFAULT_GROQ_MODEL,
                        temperature=ModelConfig.GROQ_TEMPERATURE,
                        max_tokens=ModelConfig.GROQ_MAX_TOKENS,
                        api_key=ModelConfig.GROQ_API_KEY
                    )
            else:
                # Default to Groq
                return ChatGroq(
                    model=ModelConfig.DEFAULT_GROQ_MODEL,
                    temperature=ModelConfig.GROQ_TEMPERATURE,
                    max_tokens=ModelConfig.GROQ_MAX_TOKENS,
                    api_key=ModelConfig.GROQ_API_KEY
                )
        except Exception as e:
            logger.error(f"Error initializing LLM: {str(e)}")
            raise
            
    def _initialize_chain(self):
        """Initialize the appropriate chain based on answer mode"""
        if self.answer_mode == AnswerMode.DEFAULT:
            self._initialize_default_chain()
        elif self.answer_mode == AnswerMode.RAG:
            self._initialize_rag_chain()
        elif self.answer_mode == AnswerMode.WEB_SEARCH:
            self._initialize_web_search_chain()
        else:
            # Default to RAG mode
            self._initialize_rag_chain()
            
    def _initialize_default_chain(self):
        """Initialize chain for Default mode - uses model's knowledge"""
        prompt = PromptTemplate(
            template=DEFAULT_PROMPT,
            input_variables=["question"]
        )
        self.chain = LLMChain(
            llm=self.llm,
            prompt=prompt,
            verbose=True
        )
        
    def _initialize_rag_chain(self):
        """Initialize chain for RAG mode - uses vector store"""
        prompt = PromptTemplate(
            template=RAG_PROMPT,
            input_variables=["context", "question"]
        )
        
        self.chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vector_store.vector_store.as_retriever(
                search_kwargs={"k": 4}
            ),
            memory=self.memory,
            combine_docs_chain_kwargs={"prompt": prompt},
            return_source_documents=True,
            verbose=True
        )
        
    def _initialize_web_search_chain(self):
        """Initialize chain for Web Search mode - uses Tavily search API"""
        if not AppConfig.TAVILY_API_KEY:
            logger.warning("Tavily API key not found. Web search functionality will be limited.")
            self._initialize_default_chain()
            return
            
        try:
            # Initialize Tavily search tool
            self.search_tool = TavilySearch(
                api_key=AppConfig.TAVILY_API_KEY,
                max_results=AppConfig.TAVILY_MAX_RESULTS,
                include_raw_content=True,
                include_images=False
            )
            
            # Create a simple chain that uses the search tool
            prompt = PromptTemplate(
                template=WEB_SEARCH_PROMPT,
                input_variables=["question", "search_results"]
            )
            
            self.chain = LLMChain(
                llm=self.llm,
                prompt=prompt,
                verbose=True
            )
            
            logger.info("Tavily search tool initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Tavily search: {str(e)}")
            # Fall back to default mode
            self._initialize_default_chain()
            
    def get_response(self, query: str) -> Tuple[str, bool]:
        """
        Get response based on the current answer mode, with privacy filtering
        Returns the response and whether sensitive info was detected
        """
        try:
            # Apply privacy filter to the query
            filtered_query, has_sensitive_data = self.privacy_filter.filter_text(query)
            
            # Get chat history from memory manager
            chat_history = self.memory_manager.get_chat_history()
            
            # Update LangChain memory for compatibility
            self.memory.chat_memory.messages = chat_history
            
            # Add user message to memory
            self.memory_manager.add_user_message(filtered_query, self.session_id)
            
            # Get response based on answer mode
            if self.answer_mode == AnswerMode.DEFAULT:
                response = self._get_default_response(filtered_query)
            elif self.answer_mode == AnswerMode.RAG:
                response = self._get_rag_response(filtered_query)
            elif self.answer_mode == AnswerMode.WEB_SEARCH:
                response = self._get_web_search_response(filtered_query)
            else:
                # Default to RAG mode
                response = self._get_rag_response(filtered_query)
                
            # Add AI response to memory
            self.memory_manager.add_ai_message(response, self.session_id)
            
            return response, has_sensitive_data
            
        except Exception as e:
            logger.error(f"Error getting response: {str(e)}")
            error_msg = f"I encountered an error processing your request: {str(e)}"
            self.memory_manager.add_ai_message(error_msg, self.session_id)
            return error_msg, False
            
    def _get_default_response(self, query):
        """Get response using model's knowledge"""
        response = self.chain.invoke({"question": query})
        return response["text"]
        
    def _get_rag_response(self, query):
        """Get response using RAG"""
        # Get chat history from memory manager
        chat_history = self.memory_manager.get_chat_history()
        
        # Use the enhanced retrieval with history
        docs = self.vector_store.similarity_search(
            query, 
            k=4, 
            chat_history=chat_history
        )
        
        # Create context from retrieved documents and track sources
        context_parts = []
        sources = []
        
        for doc in docs:
            context_parts.append(doc.page_content)
            # Extract source filename from metadata
            if hasattr(doc, 'metadata') and 'source' in doc.metadata:
                source = doc.metadata['source']
                
                # Skip invalid or placeholder sources
                if not source or source in ['context.txt', 'filename.txt', 'None']:
                    continue
                    
                # Extract just the filename from the path if it's a full path
                if '/' in source or '\\' in source:
                    source = source.replace('\\', '/').split('/')[-1]
                    
                # Add all valid sources to the list
                if source not in sources:
                    sources.append(source)
            
        # Join all context parts
        context = "\n\n".join(context_parts)
        
        # Format the prompt with context and question
        formatted_prompt = RAG_PROMPT.format(
            context=context,
            question=query
        )
        
        # Get response from LLM
        response = self.llm.invoke(formatted_prompt)
        
        # Add source attribution if sources were found
        content = response.content
        
        # First check if the LLM has already added a source citation
        if content.strip().endswith(']') and '[Source' in content[content.rfind('['):]:
            # Remove incorrect source attribution that might have been added by the model
            content = content[:content.rfind('[')].strip()
            
        # Add validated sources to the end of the response
        if sources:
            if len(sources) == 1:
                content += f"\n\n[Source: {sources[0]}]"
            else:
                sources_text = ", ".join(sources)
                content += f"\n\n[Sources: {sources_text}]"
        
        return content
        
    def _get_web_search_response(self, query):
        """Get response using web search with Tavily"""
        try:
            # Perform Tavily web search
            search_results = self.search_tool.invoke(query)
            
            # Format the search results to include URLs for proper attribution
            formatted_results = []
            
            # Check if search_results is a list (as expected in newer versions)
            if isinstance(search_results, list):
                for result in search_results:
                    title = result.get('title', 'No title')
                    content = result.get('content', 'No content')
                    url = result.get('url', 'No URL')
                    
                    # Format without including the URL in the content itself
                    formatted_result = f"Title: {title}\nContent: {content}\n---"
                    formatted_results.append(formatted_result)
            # Check if it's a dictionary (as returned in some versions)
            elif isinstance(search_results, dict) and 'results' in search_results:
                for result in search_results['results']:
                    title = result.get('title', 'No title')
                    content = result.get('content', 'No content')
                    url = result.get('url', 'No URL')
                    
                    # Format without including the URL in the content itself
                    formatted_result = f"Title: {title}\nContent: {content}\n---"
                    formatted_results.append(formatted_result)
            # Handle string format (simple text results)
            elif isinstance(search_results, str):
                formatted_results.append(search_results)
            else:
                raise ValueError(f"Unexpected search results format: {type(search_results)}")
            
            # Join all formatted results
            all_results = "\n\n".join(formatted_results)
            
            # Add specific instruction to avoid mentioning sources in the content
            formatted_prompt = """
You are a helpful AI assistant with access to real-time web search.
I've searched the web for: "{question}" 
Here are the search results:

{search_results}

Based on these search results, please answer the original question: {question}

Instructions:
1. Use information from the search results to provide a comprehensive answer
2. DO NOT cite sources within your answer text - they will be added automatically at the end
3. DO NOT mention URLs, source names, or phrases like "according to..." in your response
4. If the search results don't contain relevant information, say so and provide your best answer
5. Focus on providing factual information only

Answer:
""".format(
                question=query,
                search_results=all_results
            )
            
            # Get response directly from LLM instead of using chain
            response = self.llm.invoke(formatted_prompt)
            result = response.content
            
            # Extract URLs for citation
            urls = []
            
            if isinstance(search_results, list):
                urls = [result.get('url', '') for result in search_results if result.get('url')]
            elif isinstance(search_results, dict) and 'results' in search_results:
                urls = [result.get('url', '') for result in search_results['results'] if result.get('url')]
            
            # Add sources at the end
            if urls:
                # Remove any existing source citations at the end of the response
                if result.strip().endswith(']'):
                    last_bracket = result.rfind('[')
                    if last_bracket > 0 and 'source' in result[last_bracket:].lower():
                        result = result[:last_bracket].strip()
                
                # Add formatted sources block
                sources_text = ", ".join(urls)
                result += f"\n\n[Sources: {sources_text}]"
            
            return result
        except Exception as e:
            logger.error(f"Error in Tavily web search: {str(e)}")
            # Fall back to default mode
            return self._get_default_response(query)
            
    def change_model_provider(self, provider: str or ModelProvider):
        """Change the model provider at runtime"""
        try:
            # Convert string to enum if necessary
            if isinstance(provider, str):
                try:
                    provider = ModelProvider(provider)
                except ValueError:
                    # Try to match the string directly
                    for model_provider in ModelProvider:
                        if model_provider.value == provider:
                            provider = model_provider
                            break
                    else:
                        logger.error(f"Invalid model provider: {provider}")
                        return False
                        
            self.model_provider = provider
            self.llm = self._initialize_llm()
            self._initialize_chain()
            logger.info(f"Changed model provider to: {provider}")
            return True
        except Exception as e:
            logger.error(f"Error changing model provider: {str(e)}")
            return False
            
    def change_answer_mode(self, mode: str or AnswerMode):
        """Change the answer mode at runtime"""
        try:
            # Convert string to enum if necessary
            if isinstance(mode, str):
                try:
                    mode = AnswerMode(mode)
                except ValueError:
                    # Try to match the string directly
                    for answer_mode in AnswerMode:
                        if answer_mode.value == mode:
                            mode = answer_mode
                            break
                    else:
                        logger.error(f"Invalid answer mode: {mode}")
                        return False
                        
            self.answer_mode = mode
            self._initialize_chain()
            logger.info(f"Changed answer mode to: {mode}")
            return True
        except Exception as e:
            logger.error(f"Error changing answer mode: {str(e)}")
            return False
            
    def change_memory_mode(self, mode: MemoryMode):
        """Change the memory mode at runtime"""
        try:
            success = self.memory_manager.change_memory_mode(mode)
            if success:
                self.memory_mode = mode
                logger.info(f"Changed memory mode to: {mode}")
                
                # Create new session if switching to persistent
                if mode == MemoryMode.PERSISTENT and not self.session_id:
                    self.session_id = self.memory_manager.create_session()
                    
            return success
        except Exception as e:
            logger.error(f"Error changing memory mode: {str(e)}")
            return False
            
    def toggle_privacy_filter(self, enable: bool):
        """Enable or disable the privacy filter"""
        try:
            if enable:
                self.privacy_filter.enable()
            else:
                self.privacy_filter.disable()
            logger.info(f"Privacy filter {'enabled' if enable else 'disabled'}")
            return True
        except Exception as e:
            logger.error(f"Error toggling privacy filter: {str(e)}")
            return False
            
    def create_new_session(self):
        """Create a new chat session"""
        try:
            self.session_id = self.memory_manager.create_session()
            # Clear transient memory
            self.memory_manager.transient_memory.clear()
            # Clear LangChain memory
            self.memory.chat_memory.messages = []
            logger.info(f"Created new session with ID: {self.session_id}")
            return self.session_id
        except Exception as e:
            logger.error(f"Error creating new session: {str(e)}")
            return None
            
    def load_session(self, session_id: str):
        """Load an existing chat session"""
        try:
            success = self.memory_manager.load_session(session_id)
            if success:
                self.session_id = session_id
                # Update LangChain memory
                self.memory.chat_memory.messages = self.memory_manager.get_chat_history()
                logger.info(f"Loaded session with ID: {session_id}")
            return success
        except Exception as e:
            logger.error(f"Error loading session: {str(e)}")
            return False
            
    def get_all_sessions(self):
        """Get all available chat sessions"""
        try:
            return self.memory_manager.get_all_sessions()
        except Exception as e:
            logger.error(f"Error getting sessions: {str(e)}")
            return []
            
    def delete_session(self, session_id: str):
        """Delete a chat session"""
        try:
            success = self.memory_manager.delete_session(session_id)
            if success and self.session_id == session_id:
                # Clear current session if it was deleted
                self.session_id = None
                # Clear transient memory
                self.memory_manager.transient_memory.clear()
                # Clear LangChain memory
                self.memory.chat_memory.messages = []
            return success
        except Exception as e:
            logger.error(f"Error deleting session: {str(e)}")
            return False
            
    def clear_all_sessions(self):
        """Delete all chat sessions"""
        try:
            success = self.memory_manager.clear_all_sessions()
            if success:
                # Clear current session
                self.session_id = None
                # Clear transient memory
                self.memory_manager.transient_memory.clear()
                # Clear LangChain memory
                self.memory.chat_memory.messages = []
            return success
        except Exception as e:
            logger.error(f"Error clearing all sessions: {str(e)}")
            return False

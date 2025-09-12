"""
Prompt templates for different answer modes
"""

# Default mode prompt - answers from model's own knowledge
DEFAULT_PROMPT = """
You are a helpful AI assistant. Answer the user's question to the best of your knowledge.

Question: {question}

Answer:
"""

# RAG mode prompt - answers using retrieved documents
RAG_PROMPT = """
You are a helpful AI assistant. Answer the user's question based ONLY on the following context:

Context:
{context}

Question: {question}

Instructions:
1. Use ONLY information from the provided context
2. If the context doesn't contain relevant information, say "I don't have information about that in my knowledge base"
3. Do not use any prior knowledge or make up information
4. Include the source file name at the end of your response in the format: [Source: filename.txt]

Answer:
"""

# Web search mode prompt - answers using web search results
WEB_SEARCH_PROMPT = """
You are a helpful AI assistant with access to real-time web search.
I've searched the web for: "{question}" 
Here are the search results:

{search_results}

Based on these search results, please answer the original question: {question}

Instructions:
1. Use information from the search results to provide a comprehensive answer
2. Cite sources by including the full URLs in your response
3. If the search results don't contain relevant information, say so and provide your best answer
4. Always include the full source URLs at the end of your response in the format: [Sources: https://example.com, https://another-site.com]

Answer:
"""

# System prompt that will be used by default
system_prompt = RAG_PROMPT
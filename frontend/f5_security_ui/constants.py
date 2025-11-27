"""
Configuration constants for F5 API Security UI.
Based on Section 6.1 Environment Variables and FR-2 Configuration Management.
"""

import os

# Default Endpoint Configuration (FR-2.1, FR-2.2, FR-2.3)
DEFAULT_CHAT_ENDPOINT = os.getenv(
    "DEFAULT_CHAT_ENDPOINT",
    "http://llamastack:8321/v1/openai/v1"
)

DEFAULT_MODEL = os.getenv(
    "DEFAULT_MODEL",
    "remote-llm/RedHatAI/Llama-3.2-1B-Instruct-quantized.w8a8"
)

DEFAULT_API_KEY = os.getenv(
    "DEFAULT_API_KEY",
    "dummy-key"
)

LLAMA_STACK_ENDPOINT = os.getenv(
    "LLAMA_STACK_ENDPOINT",
    "http://llamastack:8321"
)

# LLM Configuration (FR-1.3)
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 512
DEFAULT_TOP_P = 0.95

# RAG Configuration (FR-3)
RAG_ENABLED = True
RAG_TOP_K = 5  # Number of relevant documents to retrieve

# Debug Mode (FR-5)
DEBUG_MODE_DEFAULT = False

# Session Configuration (FR-1.4)
MAX_CONVERSATION_HISTORY = 50  # Maximum messages to keep in history

# API Endpoints (Section 4.3)
CHAT_COMPLETIONS_ENDPOINT = "/chat/completions"
MODELS_ENDPOINT = "/models"
RAG_QUERY_ENDPOINT = "/v1/tool_runtime/rag_tool/query"
VECTOR_DBS_ENDPOINT = "/v1/vector_dbs"

# Security Configuration (NFR-8, NFR-9)
# Note: Actual API keys should be loaded from Kubernetes Secrets in production
VALIDATE_SSL = True

# UI Configuration (NFR-16, NFR-18)
PAGE_TITLE = "F5 API Security - AI Chat Interface"
PAGE_ICON = "🔒"
LAYOUT = "wide"

# Performance Configuration (NFR-1, NFR-2)
REQUEST_TIMEOUT = 30  # seconds
VECTOR_SEARCH_TIMEOUT = 5  # seconds

# Supported Models (Section 10)
SUPPORTED_MODELS = [
    "meta-llama/Llama-3.2-3B-Instruct",
    "meta-llama/Llama-3.1-8B-Instruct",
    "meta-llama/Meta-Llama-3-70B-Instruct",
    "remote-llm/RedHatAI/Llama-3.2-1B-Instruct-quantized.w8a8"
]

# Error Messages (NFR-17)
ERROR_MESSAGES = {
    "connection": "Failed to connect to the endpoint. Please check your configuration.",
    "invalid_model": "The selected model is not compatible with the endpoint.",
    "rate_limit": "Rate limit exceeded. Please try again later.",
    "timeout": "Request timed out. The service may be overloaded.",
    "validation": "Invalid input. Please check your message and try again."
}

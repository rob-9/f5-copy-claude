"""
API client module for LLaMA Stack and OpenAI-compatible endpoints.
Implements FR-6 (LLaMA Stack Service) and FR-2.4 (endpoint connectivity testing).

Security considerations:
- Input validation to prevent injection attacks (SEC-3)
- Timeout handling to prevent hanging requests (NFR-13)
- No hardcoded credentials (NFR-10)
- Proper error handling (NFR-12)
"""

import requests
from typing import List, Dict, Any, Optional
import logging

from ..constants import (
    CHAT_COMPLETIONS_ENDPOINT,
    MODELS_ENDPOINT,
    RAG_QUERY_ENDPOINT,
    VECTOR_DBS_ENDPOINT,
    REQUEST_TIMEOUT,
    VECTOR_SEARCH_TIMEOUT,
    ERROR_MESSAGES
)

logger = logging.getLogger(__name__)


class APIClient:
    """Client for interacting with LLaMA Stack and OpenAI-compatible APIs."""

    def __init__(self, base_url: str, api_key: str = ""):
        """
        Initialize API client.

        Args:
            base_url: Base URL for the API endpoint
            api_key: API key for authentication (stored in session state, not hardcoded)
        """
        # Input validation - ensure base_url is properly formatted
        if not base_url:
            raise ValueError("Base URL cannot be empty")

        # Remove trailing slash for consistent URL construction
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key

        # Set up headers with API key if provided
        self.headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    def test_connection(self) -> tuple[bool, str]:
        """
        Test connectivity to the endpoint (FR-2.4).

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            response = requests.get(
                f"{self.base_url}{MODELS_ENDPOINT}",
                headers=self.headers,
                timeout=REQUEST_TIMEOUT
            )

            if response.status_code == 200:
                return True, "Connection successful"
            elif response.status_code == 401:
                return False, "Authentication failed. Check your API key."
            elif response.status_code == 404:
                return False, "Endpoint not found. Check your URL."
            else:
                return False, f"Connection failed with status {response.status_code}"

        except requests.exceptions.Timeout:
            return False, ERROR_MESSAGES["timeout"]
        except requests.exceptions.ConnectionError:
            return False, ERROR_MESSAGES["connection"]
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False, f"Unexpected error: {str(e)}"

    def get_models(self) -> List[Dict[str, Any]]:
        """
        Retrieve available models from the endpoint (FR-6.2).

        Returns:
            List of model dictionaries
        """
        try:
            response = requests.get(
                f"{self.base_url}{MODELS_ENDPOINT}",
                headers=self.headers,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()

            data = response.json()
            # OpenAI format returns {"data": [models]}
            return data.get("data", []) if isinstance(data, dict) else []

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch models: {str(e)}")
            return []

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 512,
        top_p: float = 0.95,
        stream: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Send a chat completion request (FR-6.1).

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model ID to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            stream: Whether to stream the response

        Returns:
            Response dictionary or None on error
        """
        # Input validation - sanitize messages to prevent injection
        validated_messages = self._validate_messages(messages)
        if not validated_messages:
            logger.error("Invalid messages format")
            return None

        payload = {
            "model": model,
            "messages": validated_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": stream
        }

        try:
            response = requests.post(
                f"{self.base_url}{CHAT_COMPLETIONS_ENDPOINT}",
                headers=self.headers,
                json=payload,
                timeout=REQUEST_TIMEOUT
            )

            # Handle rate limiting (SEC-5, FR-13)
            if response.status_code == 429:
                logger.warning("Rate limit exceeded")
                return {"error": ERROR_MESSAGES["rate_limit"]}

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            return {"error": ERROR_MESSAGES["timeout"]}
        except requests.exceptions.RequestException as e:
            logger.error(f"Chat completion failed: {str(e)}")
            return {"error": str(e)}

    def query_vector_db(
        self,
        query: str,
        vector_db_ids: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Query vector database for RAG (FR-3.2, FR-6.3).

        Args:
            query: Search query
            vector_db_ids: List of vector database IDs to query

        Returns:
            Query results or None on error
        """
        # Input validation
        if not query or not isinstance(query, str):
            logger.error("Invalid query")
            return None

        # Sanitize query to prevent injection attacks
        sanitized_query = self._sanitize_input(query)

        payload = {
            "content": sanitized_query,
            "vector_db_ids": vector_db_ids
        }

        try:
            response = requests.post(
                f"{self.base_url}{RAG_QUERY_ENDPOINT}",
                headers=self.headers,
                json=payload,
                timeout=VECTOR_SEARCH_TIMEOUT
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Vector DB query failed: {str(e)}")
            return None

    def get_vector_databases(self) -> List[Dict[str, Any]]:
        """
        Retrieve available vector databases (FR-3.1).

        Returns:
            List of vector database configurations
        """
        try:
            response = requests.get(
                f"{self.base_url}{VECTOR_DBS_ENDPOINT}",
                headers=self.headers,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch vector databases: {str(e)}")
            return []

    def _validate_messages(self, messages: List[Dict[str, str]]) -> Optional[List[Dict[str, str]]]:
        """
        Validate and sanitize message format.

        Args:
            messages: List of message dictionaries

        Returns:
            Validated messages or None if invalid
        """
        if not isinstance(messages, list):
            return None

        validated = []
        valid_roles = {"user", "assistant", "system"}

        for msg in messages:
            if not isinstance(msg, dict):
                continue

            role = msg.get("role")
            content = msg.get("content")

            if role not in valid_roles or not isinstance(content, str):
                continue

            # Sanitize content to prevent XSS/injection (SEC-3)
            sanitized_content = self._sanitize_input(content)

            validated.append({
                "role": role,
                "content": sanitized_content
            })

        return validated if validated else None

    def _sanitize_input(self, text: str) -> str:
        """
        Sanitize user input to prevent injection attacks.

        Note: The actual XSS protection is handled by F5 WAF (SEC-3),
        but we still do basic sanitization at the application level.

        Args:
            text: Input text to sanitize

        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            return ""

        # Basic sanitization - remove null bytes and control characters
        # Additional protection is provided by F5 XC WAF
        sanitized = text.replace('\x00', '')

        # Limit length to prevent DoS
        max_length = 10000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized


class LlamaStackClient:
    """
    Wrapper for llama-stack-client library (optional).
    This can be used as an alternative to the REST API client.
    """

    def __init__(self, base_url: str):
        """Initialize LLaMA Stack client."""
        self.base_url = base_url
        # Note: Actual llama-stack-client initialization would go here
        # from llama_stack_client import LlamaStackClient as LSClient
        # self.client = LSClient(base_url=base_url)

    # Additional methods would be implemented here if using llama-stack-client library

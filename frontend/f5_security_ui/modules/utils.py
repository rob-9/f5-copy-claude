"""
Utility functions for F5 Security UI.
Implements helper functions for RAG, configuration, and UI operations.
"""

import logging
from typing import List, Dict, Any, Optional
import streamlit as st

logger = logging.getLogger(__name__)


def initialize_session_state():
    """
    Initialize Streamlit session state variables (FR-1.4, FR-2).

    This ensures all required session variables exist with default values.
    """
    # Conversation history (FR-1.4)
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Configuration (FR-2)
    if "endpoint_url" not in st.session_state:
        from ..constants import DEFAULT_CHAT_ENDPOINT
        st.session_state.endpoint_url = DEFAULT_CHAT_ENDPOINT

    if "model_id" not in st.session_state:
        from ..constants import DEFAULT_MODEL
        st.session_state.model_id = DEFAULT_MODEL

    if "api_key" not in st.session_state:
        from ..constants import DEFAULT_API_KEY
        st.session_state.api_key = DEFAULT_API_KEY

    # Debug mode (FR-5)
    if "debug_mode" not in st.session_state:
        from ..constants import DEBUG_MODE_DEFAULT
        st.session_state.debug_mode = DEBUG_MODE_DEFAULT

    # RAG configuration (FR-3)
    if "rag_enabled" not in st.session_state:
        st.session_state.rag_enabled = True

    if "selected_vector_dbs" not in st.session_state:
        st.session_state.selected_vector_dbs = []

    if "available_vector_dbs" not in st.session_state:
        st.session_state.available_vector_dbs = []


def format_chat_message(role: str, content: str) -> Dict[str, str]:
    """
    Format a chat message according to OpenAI spec (Section 4.4).

    Args:
        role: Message role (user, assistant, system)
        content: Message content

    Returns:
        Formatted message dictionary
    """
    valid_roles = {"user", "assistant", "system"}
    if role not in valid_roles:
        logger.warning(f"Invalid role '{role}', defaulting to 'user'")
        role = "user"

    return {
        "role": role,
        "content": content
    }


def enhance_prompt_with_rag(
    user_message: str,
    rag_context: Optional[List[Dict[str, Any]]] = None,
    debug_mode: bool = False
) -> str:
    """
    Enhance user prompt with RAG context (FR-3.3).

    Args:
        user_message: Original user message
        rag_context: Retrieved context from vector database
        debug_mode: Whether to include debug information

    Returns:
        Enhanced prompt with context
    """
    if not rag_context or not isinstance(rag_context, list):
        return user_message

    # Build context string from retrieved documents
    context_parts = []
    for idx, doc in enumerate(rag_context, 1):
        if isinstance(doc, dict):
            content = doc.get("content", "")
            if content:
                context_parts.append(f"[Document {idx}]\n{content}")

    if not context_parts:
        return user_message

    context_str = "\n\n".join(context_parts)

    # Construct enhanced prompt
    enhanced_prompt = f"""Based on the following context, please answer the user's question:

Context:
{context_str}

User Question: {user_message}

Please provide a comprehensive answer based on the context provided above."""

    if debug_mode:
        logger.info(f"Enhanced prompt with {len(context_parts)} documents")
        st.sidebar.write(f"**RAG Context:** {len(context_parts)} documents")

    return enhanced_prompt


def truncate_conversation_history(
    messages: List[Dict[str, str]],
    max_messages: int
) -> List[Dict[str, str]]:
    """
    Truncate conversation history to prevent context overflow (FR-1.4).

    Keeps system messages and the most recent user/assistant messages.

    Args:
        messages: List of message dictionaries
        max_messages: Maximum number of messages to keep

    Returns:
        Truncated message list
    """
    if len(messages) <= max_messages:
        return messages

    # Separate system messages from conversation
    system_messages = [m for m in messages if m.get("role") == "system"]
    conversation = [m for m in messages if m.get("role") != "system"]

    # Keep most recent conversation messages
    recent_conversation = conversation[-(max_messages - len(system_messages)):]

    # Combine system messages with recent conversation
    return system_messages + recent_conversation


def validate_model_compatibility(
    model_id: str,
    available_models: List[Dict[str, Any]]
) -> bool:
    """
    Validate that a model is compatible with the endpoint (FR-2.6).

    Args:
        model_id: Model ID to validate
        available_models: List of available models from endpoint

    Returns:
        True if model is compatible, False otherwise
    """
    if not available_models:
        logger.warning("No available models to validate against")
        return False

    # Check if model ID matches any available model
    for model in available_models:
        if isinstance(model, dict):
            if model.get("id") == model_id or model.get("name") == model_id:
                return True

    return False


def display_debug_info(
    rag_query: Optional[str] = None,
    rag_results: Optional[List[Dict[str, Any]]] = None,
    vector_dbs: Optional[List[str]] = None,
    api_response: Optional[Dict[str, Any]] = None
):
    """
    Display debug information in the UI (FR-5).

    Args:
        rag_query: RAG query text
        rag_results: Results from vector database query
        vector_dbs: Selected vector databases
        api_response: Raw API response
    """
    if not st.session_state.get("debug_mode", False):
        return

    with st.expander("🔍 Debug Information", expanded=False):
        if rag_query:
            st.write("**RAG Query:**")
            st.code(rag_query)

        if vector_dbs:
            st.write("**Selected Vector Databases:**")
            st.write(vector_dbs)

        if rag_results:
            st.write("**RAG Results:**")
            st.json(rag_results)

        if api_response:
            st.write("**API Response:**")
            st.json(api_response)


def format_error_message(error: str) -> str:
    """
    Format error messages for user display (NFR-17).

    Args:
        error: Error message

    Returns:
        Formatted error message
    """
    from ..constants import ERROR_MESSAGES

    # Check if error matches known error types
    if "rate limit" in error.lower() or "429" in error:
        return f"⚠️ {ERROR_MESSAGES['rate_limit']}"
    elif "timeout" in error.lower():
        return f"⚠️ {ERROR_MESSAGES['timeout']}"
    elif "connection" in error.lower():
        return f"⚠️ {ERROR_MESSAGES['connection']}"
    elif "authentication" in error.lower() or "401" in error:
        return "⚠️ Authentication failed. Please check your API key."
    else:
        return f"⚠️ Error: {error}"


def save_configuration(
    endpoint_url: str,
    model_id: str,
    api_key: str
) -> bool:
    """
    Save configuration to session state (FR-2).

    Args:
        endpoint_url: API endpoint URL
        model_id: Model ID
        api_key: API key

    Returns:
        True if configuration saved successfully
    """
    try:
        st.session_state.endpoint_url = endpoint_url
        st.session_state.model_id = model_id
        st.session_state.api_key = api_key
        return True
    except Exception as e:
        logger.error(f"Failed to save configuration: {str(e)}")
        return False


def reset_configuration():
    """
    Reset configuration to defaults (FR-2.5).
    """
    from ..constants import (
        DEFAULT_CHAT_ENDPOINT,
        DEFAULT_MODEL,
        DEFAULT_API_KEY
    )

    st.session_state.endpoint_url = DEFAULT_CHAT_ENDPOINT
    st.session_state.model_id = DEFAULT_MODEL
    st.session_state.api_key = DEFAULT_API_KEY


def extract_assistant_message(response: Dict[str, Any]) -> Optional[str]:
    """
    Extract assistant message from API response.

    Args:
        response: API response dictionary

    Returns:
        Assistant message content or None
    """
    try:
        # OpenAI format: response.choices[0].message.content
        if "choices" in response and len(response["choices"]) > 0:
            choice = response["choices"][0]
            if "message" in choice:
                return choice["message"].get("content")
            elif "text" in choice:
                return choice.get("text")

        # Alternative format
        if "message" in response:
            return response["message"].get("content")

        return None

    except Exception as e:
        logger.error(f"Failed to extract message from response: {str(e)}")
        return None

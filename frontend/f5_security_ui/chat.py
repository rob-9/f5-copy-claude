"""
Main chat interface for F5 API Security System.
Implements FR-1 (Chat Interface) and FR-2 (Configuration Management).

Security considerations:
- All user inputs are validated and sanitized
- API keys stored in session state, not logged
- XSS protection delegated to F5 WAF
"""

import streamlit as st
import logging
from typing import List, Dict, Any

from .constants import (
    PAGE_TITLE,
    PAGE_ICON,
    LAYOUT,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TOP_P,
    MAX_CONVERSATION_HISTORY
)
from .modules.api import APIClient
from .modules.utils import (
    initialize_session_state,
    format_chat_message,
    enhance_prompt_with_rag,
    truncate_conversation_history,
    validate_model_compatibility,
    display_debug_info,
    format_error_message,
    save_configuration,
    reset_configuration,
    extract_assistant_message
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def configure_page():
    """Configure Streamlit page settings (NFR-18)."""
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout=LAYOUT
    )


def render_sidebar():
    """
    Render sidebar with configuration options (FR-2).
    """
    with st.sidebar:
        st.title("⚙️ Configuration")

        # Endpoint configuration (FR-2.1, FR-2.2, FR-2.3)
        with st.expander("🔌 Endpoint Settings", expanded=False):
            endpoint_url = st.text_input(
                "XC Endpoint URL",
                value=st.session_state.endpoint_url,
                help="F5 Distributed Cloud endpoint URL"
            )

            model_id = st.text_input(
                "Model ID",
                value=st.session_state.model_id,
                help="LLM model identifier"
            )

            api_key = st.text_input(
                "API Key",
                value=st.session_state.api_key,
                type="password",
                help="Authentication key for the endpoint"
            )

            col1, col2 = st.columns(2)

            with col1:
                # Test connection (FR-2.4)
                if st.button("🔍 Test Connection", use_container_width=True):
                    with st.spinner("Testing connection..."):
                        client = APIClient(endpoint_url, api_key)
                        success, message = client.test_connection()

                        if success:
                            st.success(message)
                            # Save configuration if connection successful
                            save_configuration(endpoint_url, model_id, api_key)
                        else:
                            st.error(message)

            with col2:
                # Reset configuration (FR-2.5)
                if st.button("🔄 Reset", use_container_width=True):
                    reset_configuration()
                    st.rerun()

            # Save configuration
            if st.button("💾 Save Configuration", use_container_width=True):
                save_configuration(endpoint_url, model_id, api_key)
                st.success("Configuration saved!")

        # Model validation (FR-2.6)
        with st.expander("🤖 Model Validation", expanded=False):
            if st.button("Validate Model Compatibility"):
                with st.spinner("Checking model compatibility..."):
                    client = APIClient(
                        st.session_state.endpoint_url,
                        st.session_state.api_key
                    )
                    available_models = client.get_models()

                    if available_models:
                        is_compatible = validate_model_compatibility(
                            st.session_state.model_id,
                            available_models
                        )

                        if is_compatible:
                            st.success("✅ Model is compatible with the endpoint")
                        else:
                            st.warning("⚠️ Model may not be compatible. Available models:")
                            for model in available_models:
                                st.write(f"- {model.get('id', 'Unknown')}")
                    else:
                        st.error("Could not retrieve available models")

        # RAG configuration (FR-3)
        with st.expander("📚 RAG Settings", expanded=False):
            rag_enabled = st.checkbox(
                "Enable RAG",
                value=st.session_state.rag_enabled,
                help="Enable Retrieval-Augmented Generation"
            )
            st.session_state.rag_enabled = rag_enabled

            if rag_enabled:
                # Auto-discover vector databases (FR-3.1)
                if st.button("🔍 Discover Vector Databases"):
                    with st.spinner("Discovering vector databases..."):
                        client = APIClient(
                            st.session_state.endpoint_url,
                            st.session_state.api_key
                        )
                        vector_dbs = client.get_vector_databases()

                        if vector_dbs:
                            st.session_state.available_vector_dbs = vector_dbs
                            st.success(f"Found {len(vector_dbs)} vector database(s)")
                        else:
                            st.info("No vector databases found")

                # Display and select vector databases
                if st.session_state.available_vector_dbs:
                    st.write("**Available Vector Databases:**")
                    for db in st.session_state.available_vector_dbs:
                        db_id = db.get("identifier", "Unknown")
                        st.write(f"- {db_id}")

        # Debug mode (FR-5)
        st.divider()
        debug_mode = st.checkbox(
            "🐛 Debug Mode",
            value=st.session_state.debug_mode,
            help="Show detailed debug information (FR-5)"
        )
        st.session_state.debug_mode = debug_mode

        # Advanced parameters
        with st.expander("🎛️ Advanced Parameters", expanded=False):
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=DEFAULT_TEMPERATURE,
                step=0.1,
                help="Controls randomness in responses"
            )

            max_tokens = st.slider(
                "Max Tokens",
                min_value=64,
                max_value=2048,
                value=DEFAULT_MAX_TOKENS,
                step=64,
                help="Maximum length of response"
            )

            top_p = st.slider(
                "Top P",
                min_value=0.0,
                max_value=1.0,
                value=DEFAULT_TOP_P,
                step=0.05,
                help="Nucleus sampling parameter"
            )

            st.session_state.temperature = temperature
            st.session_state.max_tokens = max_tokens
            st.session_state.top_p = top_p

        # Clear conversation
        st.divider()
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()


def render_chat_interface():
    """
    Render main chat interface (FR-1).
    """
    st.title(f"{PAGE_ICON} F5 API Security - AI Chat")

    # Display conversation history (FR-1.1, FR-1.4)
    for message in st.session_state.messages:
        role = message.get("role", "user")
        content = message.get("content", "")

        with st.chat_message(role):
            st.markdown(content)

    # User input (FR-1.2)
    if prompt := st.chat_input("Ask me anything..."):
        # Add user message to history
        user_message = format_chat_message("user", prompt)
        st.session_state.messages.append(user_message)

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Process and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response_content = process_user_message(prompt)

                if response_content:
                    st.markdown(response_content)

                    # Add assistant response to history
                    assistant_message = format_chat_message("assistant", response_content)
                    st.session_state.messages.append(assistant_message)

                    # Truncate history to prevent overflow (FR-1.4)
                    st.session_state.messages = truncate_conversation_history(
                        st.session_state.messages,
                        MAX_CONVERSATION_HISTORY
                    )
                else:
                    st.error("Failed to get response from the model")


def process_user_message(user_input: str) -> str:
    """
    Process user message and get LLM response.

    Implements:
    - FR-1.3: Stream or display LLM responses
    - FR-3: RAG integration
    - FR-5: Debug mode

    Args:
        user_input: User's message

    Returns:
        Assistant's response
    """
    try:
        # Initialize API client
        client = APIClient(
            st.session_state.endpoint_url,
            st.session_state.api_key
        )

        # Prepare messages
        messages_to_send = st.session_state.messages.copy()

        # RAG enhancement (FR-3)
        rag_results = None
        enhanced_input = user_input

        if st.session_state.rag_enabled and st.session_state.selected_vector_dbs:
            # Query vector database (FR-3.2)
            rag_results = client.query_vector_db(
                user_input,
                st.session_state.selected_vector_dbs
            )

            if rag_results:
                # Enhance prompt with context (FR-3.3)
                enhanced_input = enhance_prompt_with_rag(
                    user_input,
                    rag_results,
                    st.session_state.debug_mode
                )

                # Update the last user message with enhanced prompt
                if messages_to_send and messages_to_send[-1]["role"] == "user":
                    messages_to_send[-1]["content"] = enhanced_input

        # Display debug info (FR-5)
        if st.session_state.debug_mode:
            display_debug_info(
                rag_query=user_input if st.session_state.rag_enabled else None,
                rag_results=rag_results,
                vector_dbs=st.session_state.selected_vector_dbs
            )

        # Send chat completion request (FR-6.1)
        response = client.chat_completion(
            messages=messages_to_send,
            model=st.session_state.model_id,
            temperature=st.session_state.get("temperature", DEFAULT_TEMPERATURE),
            max_tokens=st.session_state.get("max_tokens", DEFAULT_MAX_TOKENS),
            top_p=st.session_state.get("top_p", DEFAULT_TOP_P),
            stream=False
        )

        # Display debug info for API response
        if st.session_state.debug_mode and response:
            display_debug_info(api_response=response)

        # Extract and return response
        if response:
            # Check for errors
            if "error" in response:
                error_msg = format_error_message(response["error"])
                st.error(error_msg)
                return None

            # Extract assistant message
            content = extract_assistant_message(response)
            if content:
                return content
            else:
                st.error("Could not extract response from API")
                return None
        else:
            st.error("No response received from API")
            return None

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        error_msg = format_error_message(str(e))
        st.error(error_msg)
        return None


def main():
    """Main application entry point."""
    # Configure page
    configure_page()

    # Initialize session state
    initialize_session_state()

    # Render sidebar
    render_sidebar()

    # Render main chat interface
    render_chat_interface()


if __name__ == "__main__":
    main()

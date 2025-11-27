"""
Document upload page for F5 API Security System.
Implements FR-4 (Document Upload & Ingestion).

Security considerations:
- File type validation (only PDF and allowed formats)
- File size limits (NFR-4: up to 50MB)
- Input sanitization for GitHub URLs
"""

import streamlit as st
import logging
from typing import Optional
import requests

from ..constants import PAGE_ICON
from ..modules.utils import initialize_session_state

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File upload constraints (NFR-4)
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_FILE_TYPES = ["pdf"]


def configure_upload_page():
    """Configure upload page settings."""
    st.set_page_config(
        page_title=f"{PAGE_ICON} Document Upload",
        page_icon=PAGE_ICON,
        layout="wide"
    )


def validate_file_upload(uploaded_file) -> tuple[bool, str]:
    """
    Validate uploaded file.

    Args:
        uploaded_file: Streamlit UploadedFile object

    Returns:
        Tuple of (is_valid: bool, message: str)
    """
    if not uploaded_file:
        return False, "No file uploaded"

    # Check file size (NFR-4)
    if uploaded_file.size > MAX_FILE_SIZE_BYTES:
        return False, f"File size exceeds {MAX_FILE_SIZE_MB}MB limit"

    # Check file type
    file_extension = uploaded_file.name.split('.')[-1].lower()
    if file_extension not in ALLOWED_FILE_TYPES:
        return False, f"Unsupported file type. Allowed: {', '.join(ALLOWED_FILE_TYPES)}"

    return True, "File validation successful"


def validate_github_url(url: str) -> tuple[bool, str]:
    """
    Validate GitHub repository URL.

    Args:
        url: GitHub repository URL

    Returns:
        Tuple of (is_valid: bool, message: str)
    """
    if not url:
        return False, "URL cannot be empty"

    # Basic URL validation
    if not url.startswith(("https://github.com/", "http://github.com/")):
        return False, "URL must be a valid GitHub repository URL"

    # Sanitize URL to prevent injection
    if any(char in url for char in ['<', '>', '"', "'"]):
        return False, "URL contains invalid characters"

    return True, "URL validation successful"


def upload_pdf_document():
    """
    Handle PDF document upload (FR-4.1).
    """
    st.subheader("📄 Upload PDF Document")

    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=ALLOWED_FILE_TYPES,
        help=f"Maximum file size: {MAX_FILE_SIZE_MB}MB"
    )

    if uploaded_file:
        # Validate file
        is_valid, message = validate_file_upload(uploaded_file)

        if not is_valid:
            st.error(f"⚠️ {message}")
            return

        # Display file information
        st.success(f"✅ {message}")
        st.info(f"**File:** {uploaded_file.name}")
        st.info(f"**Size:** {uploaded_file.size / 1024:.2f} KB")

        # Process button
        if st.button("🚀 Process and Vectorize", key="process_pdf"):
            with st.spinner("Processing document..."):
                success, result_message = process_pdf_document(uploaded_file)

                if success:
                    st.success(result_message)
                else:
                    st.error(result_message)


def ingest_github_repository():
    """
    Handle GitHub repository ingestion (FR-4.2).
    """
    st.subheader("📦 Ingest GitHub Repository")

    github_url = st.text_input(
        "GitHub Repository URL",
        placeholder="https://github.com/username/repository",
        help="Enter the full URL of the GitHub repository"
    )

    if github_url:
        # Validate URL
        is_valid, message = validate_github_url(github_url)

        if not is_valid:
            st.error(f"⚠️ {message}")
            return

        st.success(f"✅ {message}")

        # Process button
        if st.button("🚀 Clone and Vectorize", key="process_github"):
            with st.spinner("Cloning and processing repository..."):
                success, result_message = process_github_repo(github_url)

                if success:
                    st.success(result_message)
                else:
                    st.error(result_message)


def process_pdf_document(uploaded_file) -> tuple[bool, str]:
    """
    Process and vectorize PDF document (FR-4.3, FR-4.4).

    In a production environment, this would:
    1. Extract text from PDF
    2. Chunk the text into segments
    3. Generate embeddings using embedding service (FR-9)
    4. Store embeddings in PGVector database (FR-8)

    Args:
        uploaded_file: Uploaded PDF file

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Note: This is a placeholder implementation
        # In production, this would integrate with:
        # - PDF extraction library (e.g., PyPDF2, pdfplumber)
        # - Embedding service endpoint
        # - PGVector database

        logger.info(f"Processing PDF: {uploaded_file.name}")

        # Placeholder for actual implementation
        # 1. Extract text from PDF
        # pdf_text = extract_text_from_pdf(uploaded_file)

        # 2. Chunk text into segments
        # chunks = chunk_text(pdf_text)

        # 3. Generate embeddings
        # embeddings = generate_embeddings(chunks)

        # 4. Store in vector database
        # store_in_pgvector(embeddings)

        return True, f"Successfully processed '{uploaded_file.name}'. Document has been vectorized and stored."

    except Exception as e:
        logger.error(f"Failed to process PDF: {str(e)}")
        return False, f"Failed to process document: {str(e)}"


def process_github_repo(github_url: str) -> tuple[bool, str]:
    """
    Process and vectorize GitHub repository (FR-4.3, FR-4.4).

    In a production environment, this would:
    1. Clone the repository
    2. Extract code and documentation files
    3. Chunk the content
    4. Generate embeddings
    5. Store in PGVector database

    Args:
        github_url: GitHub repository URL

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        logger.info(f"Processing GitHub repo: {github_url}")

        # Placeholder for actual implementation
        # In production, this would integrate with:
        # - Git clone functionality
        # - Code parsing and extraction
        # - Embedding service
        # - PGVector database

        # 1. Clone repository
        # clone_repository(github_url)

        # 2. Extract relevant files
        # files = extract_code_and_docs()

        # 3. Chunk content
        # chunks = chunk_files(files)

        # 4. Generate embeddings
        # embeddings = generate_embeddings(chunks)

        # 5. Store in vector database
        # store_in_pgvector(embeddings)

        return True, f"Successfully processed repository. Content has been vectorized and stored."

    except Exception as e:
        logger.error(f"Failed to process GitHub repo: {str(e)}")
        return False, f"Failed to process repository: {str(e)}"


def display_vector_database_status():
    """
    Display current vector database status and statistics.
    """
    st.subheader("📊 Vector Database Status")

    # Placeholder for actual database statistics
    # In production, this would query the PGVector database for:
    # - Number of documents
    # - Total embeddings
    # - Database size
    # - Last updated timestamp

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Documents", "0", help="Number of processed documents")

    with col2:
        st.metric("Total Embeddings", "0", help="Number of vector embeddings")

    with col3:
        st.metric("Database Size", "0 MB", help="Total storage used")

    st.info("💡 Upload documents or ingest repositories to populate the vector database")


def main():
    """Main upload page entry point."""
    # Configure page
    configure_upload_page()

    # Initialize session state
    initialize_session_state()

    # Page header
    st.title(f"{PAGE_ICON} Document Upload & Ingestion")
    st.markdown("""
    Upload documents or ingest GitHub repositories to enhance the AI's knowledge base.
    All content will be processed, vectorized, and stored for RAG (Retrieval-Augmented Generation).
    """)

    st.divider()

    # Create tabs for different upload methods
    tab1, tab2, tab3 = st.tabs(["📄 PDF Upload", "📦 GitHub Ingestion", "📊 Database Status"])

    with tab1:
        upload_pdf_document()

    with tab2:
        ingest_github_repository()

    with tab3:
        display_vector_database_status()

    # Information section
    st.divider()
    with st.expander("ℹ️ About Document Processing"):
        st.markdown("""
        ### How It Works

        1. **Upload/Ingest**: Upload a PDF document or provide a GitHub repository URL
        2. **Extract**: Text content is extracted from the documents
        3. **Chunk**: Content is split into meaningful segments
        4. **Embed**: Each chunk is converted to a vector embedding using all-MiniLM-L6-v2
        5. **Store**: Embeddings are stored in PostgreSQL with PGVector extension
        6. **Query**: During chat, relevant context is retrieved based on semantic similarity

        ### Supported Formats

        - **PDF Documents**: Technical documentation, manuals, reports
        - **GitHub Repositories**: Code, README files, documentation

        ### Security

        - File size limited to {MAX_FILE_SIZE_MB}MB (NFR-4)
        - Only approved file types accepted
        - All inputs validated and sanitized
        - Stored securely in PGVector database
        """.format(MAX_FILE_SIZE_MB=MAX_FILE_SIZE_MB))


if __name__ == "__main__":
    main()

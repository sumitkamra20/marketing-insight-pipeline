"""
Streamlit Application for RAG System

This module provides a user-friendly web interface for the RAG system.
"""

import streamlit as st
import os
import tempfile
from typing import Dict, Any, List
import time

# Import RAG components
from ai_agent.rag.rag_service import create_rag_service, RAGService
from ai_agent.rag.config import get_config, validate_config, create_env_template


# Page configuration
st.set_page_config(
    page_title="RAG System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def initialize_rag_service():
    """Initialize RAG service with caching."""
    try:
        # Validate configuration first
        validate_config()
        config = get_config()

        # Create RAG service
        service = create_rag_service(
            pinecone_api_key=config.pinecone_api_key,
            openai_api_key=config.openai_api_key,
            index_name=config.pinecone_index_name,
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            retrieval_k=config.retrieval_k
        )
        return service, None
    except Exception as e:
        return None, str(e)


def display_config_error(error_msg: str):
    """Display configuration error and setup instructions."""
    st.error("⚠️ Configuration Error")
    st.write(f"**Error:** {error_msg}")

    with st.expander("📝 Setup Instructions", expanded=True):
        st.write("""
        To use the RAG system, you need to set up your API keys:

        1. **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)
        2. **Pinecone API Key**: Get from [Pinecone Console](https://app.pinecone.io/)
        3. **Pinecone Environment**: Find in your Pinecone dashboard

        Create a `.env` file in the `ai_agent/rag/` directory with the following content:
        """)

        # Show env template
        env_template = create_env_template()
        st.code(env_template, language="bash")


def main():
    """Main Streamlit application."""

    # App header
    st.title("🔍 RAG System")
    st.markdown("**Retrieval-Augmented Generation with PDF Documents**")

    # Initialize RAG service
    rag_service, error = initialize_rag_service()

    if error:
        display_config_error(error)
        return

    # Sidebar for configuration and stats
    with st.sidebar:
        st.header("📊 System Status")

        # Display index stats
        try:
            stats = rag_service.get_index_stats()
            st.metric("📄 Total Documents", stats.get("total_vectors", "0"))
            st.metric("📐 Vector Dimension", stats.get("dimension", "1536"))
            st.metric("💾 Index Fullness", f"{stats.get('index_fullness', 0):.1%}")
        except Exception as e:
            st.error(f"Error getting stats: {str(e)}")

        st.divider()

        # Configuration section
        st.header("⚙️ Configuration")

        # Namespace input
        namespace = st.text_input(
            "Namespace (optional)",
            value="",
            help="Use namespaces to organize documents in Pinecone"
        )

        # Retrieval settings
        with st.expander("🔧 Advanced Settings"):
            retrieval_k = st.slider(
                "Number of documents to retrieve",
                min_value=1,
                max_value=10,
                value=4,
                help="How many relevant documents to use for answering questions"
            )

            conversational_mode = st.checkbox(
                "Conversational mode",
                value=False,
                help="Maintain conversation history for follow-up questions"
            )

            show_sources = st.checkbox(
                "Show source documents",
                value=True,
                help="Display the source documents used to generate the answer"
            )

        st.divider()

        # Clear conversation button
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            rag_service.clear_conversation_history()
            st.success("Conversation history cleared!")
            st.rerun()

    # Main content area
    col1, col2 = st.columns([1, 1])

    # Left column: PDF Upload
    with col1:
        st.header("📄 Upload PDF")

        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type="pdf",
            accept_multiple_files=True,
            help="Upload one or more PDF documents to add to the knowledge base"
        )

        if uploaded_files:
            st.write(f"📁 **{len(uploaded_files)} file(s) selected:**")
            for i, file in enumerate(uploaded_files):
                st.write(f"{i+1}. {file.name} ({file.size} bytes)")

            if st.button("🚀 Process All PDFs", use_container_width=True):
                progress_bar = st.progress(0)
                status_container = st.container()

                with status_container:
                    st.write("Processing PDFs...")

                try:
                    all_results = []
                    total_files = len(uploaded_files)

                    for i, uploaded_file in enumerate(uploaded_files):
                        with status_container:
                            st.write(f"📄 Processing: {uploaded_file.name}")

                        # Read file content
                        pdf_bytes = uploaded_file.read()

                        # Process PDF
                        result = rag_service.upload_pdf_from_bytes(
                            pdf_bytes=pdf_bytes,
                            filename=uploaded_file.name,
                            namespace=namespace
                        )

                        all_results.append(result)

                        # Update progress
                        progress_bar.progress((i + 1) / total_files)

                    # Show results summary
                    successful = [r for r in all_results if r["success"]]
                    failed = [r for r in all_results if not r["success"]]

                    if successful:
                        st.success(f"✅ Successfully processed {len(successful)}/{total_files} PDFs")

                        total_chunks = sum(r["document_count"] for r in successful)
                        st.write(f"**Total chunks created:** {total_chunks}")

                        # Show details for each successful upload
                        with st.expander("📋 Processing Details"):
                            for result in successful:
                                st.write(f"✅ {result['source']}: {result['document_count']} chunks")

                    if failed:
                        st.error(f"❌ Failed to process {len(failed)} PDFs")
                        with st.expander("❌ Failed Files"):
                            for result in failed:
                                st.write(f"❌ {result.get('source', 'Unknown')}: {result['message']}")

                    # Refresh the page to update stats
                    if successful:
                        time.sleep(1)
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Error processing PDFs: {str(e)}")

        # Document search section
        st.subheader("🔍 Document Search")

        search_query = st.text_input(
            "Search documents",
            placeholder="Enter search terms..."
        )

        if search_query and st.button("Search", use_container_width=True):
            with st.spinner("Searching..."):
                try:
                    results = rag_service.search_documents(
                        query=search_query,
                        k=retrieval_k,
                        namespace=namespace
                    )

                    if results:
                        st.write(f"Found {len(results)} relevant documents:")

                        for i, result in enumerate(results):
                            with st.expander(f"Document {i+1} (Score: {result['similarity_score']:.3f})"):
                                st.write(f"**Source:** {result['source']}")
                                st.write(f"**Content:** {result['content'][:300]}...")
                    else:
                        st.info("No relevant documents found.")

                except Exception as e:
                    st.error(f"Error searching: {str(e)}")

    # Right column: Question & Answer
    with col2:
        st.header("💬 Ask Questions")

        # Question input
        question = st.text_area(
            "Your question",
            placeholder="Ask a question about your uploaded documents...",
            height=100
        )

        if question and st.button("🤔 Get Answer", use_container_width=True):
            with st.spinner("Generating answer..."):
                try:
                    # Update retrieval_k in service if needed
                    rag_service.retrieval_k = retrieval_k

                    response = rag_service.ask_question(
                        question=question,
                        namespace=namespace,
                        conversational=conversational_mode,
                        return_sources=show_sources
                    )

                    # Display answer
                    st.subheader("💡 Answer")
                    st.write(response["answer"])

                    # Display sources if requested
                    if show_sources and response.get("sources"):
                        st.subheader("📚 Sources")

                        for i, source in enumerate(response["sources"]):
                            with st.expander(f"Source {i+1}: {source['source']}"):
                                st.write(f"**Chunk ID:** {source['chunk_id']}")
                                st.write(f"**Content:**")
                                st.write(source["content"])

                except Exception as e:
                    st.error(f"❌ Error generating answer: {str(e)}")

        # Conversation history
        if conversational_mode:
            st.subheader("💭 Conversation History")

            try:
                history = rag_service.get_conversation_history()

                if history:
                    for i, turn in enumerate(reversed(history[-5:])):  # Show last 5 turns
                        with st.expander(f"Turn {len(history)-i}"):
                            st.write(f"**Q:** {turn['question']}")
                            st.write(f"**A:** {turn['answer']}")
                else:
                    st.info("No conversation history yet.")

            except Exception as e:
                st.error(f"Error loading conversation history: {str(e)}")

    # Footer with additional actions
    st.divider()

    col_footer1, col_footer2, col_footer3 = st.columns([1, 1, 1])

    with col_footer1:
        if st.button("📊 Refresh Stats"):
            st.rerun()

    with col_footer2:
        if st.button("🗑️ Delete All Documents"):
            if st.session_state.get("confirm_delete", False):
                try:
                    result = rag_service.delete_documents(
                        namespace=namespace,
                        delete_all=True
                    )
                    if result["success"]:
                        st.success("All documents deleted!")
                        st.session_state["confirm_delete"] = False
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Error: {result['message']}")
                except Exception as e:
                    st.error(f"Error deleting documents: {str(e)}")
            else:
                st.session_state["confirm_delete"] = True
                st.warning("Click again to confirm deletion of all documents!")

    with col_footer3:
        if st.button("📖 API Documentation"):
            st.info("API documentation available at: http://localhost:8000/docs")


if __name__ == "__main__":
    main()

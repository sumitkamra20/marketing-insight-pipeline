"""
Integrated Chatbot Application
Combines data querying (Snowflake) and document processing (RAG) in a single Streamlit interface
"""

import streamlit as st
import os
import sys
from typing import Optional, Dict, Any, List
import tempfile
from dotenv import load_dotenv

# Add parent directories to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import core data extraction functionality
from core.workflows.data_extraction import create_data_extraction_agent, DataExtractionAgent
from core.tools.query_tool import test_snowflake_connection

# Import RAG functionality
from rag.rag_service import create_rag_service, RAGService
from rag.config import get_config, validate_config, create_env_template

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Marketing Insight Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    .user-message {
        background-color: #f0f2f6;
        border-left-color: #667eea;
    }
    .bot-message {
        background-color: #e8f4fd;
        border-left-color: #26a69a;
    }
    .mode-selector {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_data_agent():
    """Initialize data extraction agent with caching."""
    try:
        # Test Snowflake connection first
        connection_result = test_snowflake_connection.invoke({})

        # Create agent with memory enabled
        agent = create_data_extraction_agent(enable_memory=True)
        return agent, None
    except Exception as e:
        return None, f"Failed to initialize data agent: {str(e)}"

@st.cache_resource
def initialize_rag_service():
    """Initialize RAG service with caching."""
    try:
        # Validate RAG configuration
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
        return None, f"Failed to initialize RAG service: {str(e)}"

def display_setup_instructions():
    """Display setup instructions for missing configuration."""
    st.error("⚠️ Configuration Required")

    with st.expander("📝 Setup Instructions", expanded=True):
        st.write("""
        To use this chatbot, you need to configure both data and document processing:

        ### For Data Querying (Snowflake):
        Set these environment variables:
        - `SNOWFLAKE_USER`
        - `SNOWFLAKE_PASSWORD`
        - `SNOWFLAKE_ACCOUNT`
        - `SNOWFLAKE_WAREHOUSE`
        - `SNOWFLAKE_DATABASE`
        - `SNOWFLAKE_SCHEMA`
        - `OPENAI_API_KEY`

        ### For Document Processing (RAG):
        - `OPENAI_API_KEY` (same as above)
        - `PINECONE_API_KEY`
        - `PINECONE_ENV`
        - `PINECONE_INDEX_NAME` (optional)

        Create a `.env` file in your project root with these variables.
        """)

def display_chat_message(message: str, is_user: bool = False):
    """Display a chat message with proper styling."""
    if is_user:
        st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {message}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-message bot-message"><strong>Assistant:</strong> {message}</div>', unsafe_allow_html=True)

def process_data_query(query: str, data_agent: DataExtractionAgent, session_id: str) -> str:
    """Process a data query using the data extraction agent."""
    try:
        response = data_agent.process_query(query, session_id=session_id)
        return response
    except Exception as e:
        return f"Error processing data query: {str(e)}"

def process_document_query(query: str, rag_service: RAGService, namespace: str = "") -> str:
    """Process a document query using the RAG service."""
    try:
        response = rag_service.ask_question(
            question=query,
            namespace=namespace,
            conversational=True,
            return_sources=True
        )

        answer = response.get("answer", "No answer generated")
        sources = response.get("sources", [])

        # Format response with sources
        if sources:
            answer += "\n\n**Sources:**\n"
            for i, source in enumerate(sources[:3], 1):  # Show top 3 sources
                source_name = source.get("source", "Unknown")
                answer += f"{i}. {source_name}\n"

        return answer
    except Exception as e:
        return f"Error processing document query: {str(e)}"

def main():
    """Main Streamlit application."""

    # Header
    st.markdown('<div class="main-header"><h1>🤖 Marketing Insight Chatbot</h1><p>Query your data or ask questions about your documents</p><p style="font-size: 0.9em; margin-top: 0.5rem;">Developed by: Sumit Kamra, FoundryAI</p></div>', unsafe_allow_html=True)

    # Initialize services
    data_agent, data_error = initialize_data_agent()
    rag_service, rag_error = initialize_rag_service()

    # Check if at least one service is available
    if data_error and rag_error:
        display_setup_instructions()
        st.stop()

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        import uuid
        st.session_state.session_id = str(uuid.uuid4())

    # Sidebar configuration
    with st.sidebar:
        st.header("🔧 Configuration")

        # Mode selection
        st.markdown('<div class="mode-selector">', unsafe_allow_html=True)
        st.subheader("Chat Mode")

        available_modes = []
        if data_agent:
            available_modes.append("📊 Talk to Data")
        if rag_service:
            available_modes.append("📄 Talk to Documents")

        if len(available_modes) == 0:
            st.error("No services available")
            return

        chat_mode = st.selectbox(
            "Choose what to chat with:",
            available_modes,
            help="Select whether to query your database or ask questions about vectorized documents"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # Mode-specific configuration
        if chat_mode == "📄 Talk to Documents" and rag_service:
            st.divider()
            st.subheader("📁 Document Management")

            # Document upload
            uploaded_files = st.file_uploader(
                "Vectorize PDF documents",
                type=['pdf'],
                accept_multiple_files=True,
                help="Upload PDF files to chunk, vectorize, and ask questions about them"
            )

            # Namespace for organization
            namespace = st.text_input(
                "Namespace (optional)",
                value="",
                help="Use namespaces to organize documents"
            )

            # Process uploaded files
            if uploaded_files and st.button("⚡ Vectorize PDFs"):
                progress_bar = st.progress(0)
                success_count = 0

                for i, uploaded_file in enumerate(uploaded_files):
                    try:
                        pdf_bytes = uploaded_file.read()
                        result = rag_service.upload_pdf_from_bytes(
                            pdf_bytes=pdf_bytes,
                            filename=uploaded_file.name,
                            namespace=namespace
                        )

                        if result["success"]:
                            success_count += 1
                            st.success(f"✅ {uploaded_file.name}")
                        else:
                            st.error(f"❌ {uploaded_file.name}: {result['message']}")

                    except Exception as e:
                        st.error(f"❌ {uploaded_file.name}: {str(e)}")

                    progress_bar.progress((i + 1) / len(uploaded_files))

                st.info(f"Processed {success_count}/{len(uploaded_files)} files successfully")

                # Clear file uploader
                st.rerun()

            # Display document stats
            try:
                if rag_service:
                    stats = rag_service.get_index_stats()
                    st.metric("📄 Total Vectors", stats.get("total_vectors", "0"))
            except:
                pass

        elif chat_mode == "📊 Talk to Data" and data_agent:
            st.divider()
            st.subheader("📊 Data Information")
            st.info("""
            You can ask questions about:
            - Sales data and metrics
            - Customer segments
            - Product information
            - Bitcoin price data (streaming)

            Example queries:
            - "What were total sales last month?"
            - "Show me customer segments"
            - "What's the current Bitcoin price?"
            """)

        # Clear chat button
        st.divider()
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            if rag_service:
                rag_service.clear_conversation_history()
            st.rerun()

    # Main chat interface
    st.header("💬 Chat")

    # Display chat history
    for message in st.session_state.messages:
        display_chat_message(message["content"], message["role"] == "user")

    # Chat input
    if prompt := st.chat_input("Ask me anything..."):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        display_chat_message(prompt, is_user=True)

        # Process query based on selected mode
        with st.spinner("Thinking..."):
            if chat_mode == "📊 Talk to Data" and data_agent:
                response = process_data_query(prompt, data_agent, st.session_state.session_id)
            elif chat_mode == "📄 Talk to Documents" and rag_service:
                response = process_document_query(prompt, rag_service, namespace)
            else:
                response = "Sorry, the selected service is not available."

        # Add assistant response to history
        st.session_state.messages.append({"role": "assistant", "content": response})
        display_chat_message(response)

    # Show example queries based on mode
    if len(st.session_state.messages) == 0:
        st.subheader("💡 Example Queries")

        if chat_mode == "📊 Talk to Data":
            examples = [
                "What are the total sales for this year?",
                "Show me customer segments and their characteristics",
                "What's the average order value by customer type?",
                "How has Bitcoin price changed today?"
            ]
        else:
            examples = [
                "What is this document about?",
                "Summarize the key points",
                "What are the main conclusions?",
                "Explain the methodology used"
            ]

        cols = st.columns(2)
        for i, example in enumerate(examples):
            col = cols[i % 2]
            if col.button(f"💡 {example}", key=f"example_{i}"):
                # Simulate user input
                st.session_state.messages.append({"role": "user", "content": example})
                st.rerun()

if __name__ == "__main__":
    main()

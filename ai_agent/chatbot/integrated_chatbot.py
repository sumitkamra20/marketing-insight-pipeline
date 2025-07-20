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
    page_title="Marketing Insight Explorer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="auto"  # Let Streamlit decide based on screen size
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 0.5rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .main-title {
        font-size: 1.8rem;
        font-weight: bold;
        margin: 0;
        line-height: 1.2;
    }
    .developer-credit {
        font-size: 1rem;
        margin-top: 0.2rem;
        opacity: 0.9;
        font-weight: 500;
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
        margin-bottom: 1rem;
    }
    .service-status {
        margin-top: 2rem;
        padding: 0.5rem;
        background-color: #f8f9fa;
        border-radius: 8px;
        font-size: 0.8rem;
    }
    /* Compact suggested queries styling */
    .stButton button {
        font-size: 0.65rem !important;
        padding: 0.25rem 0.4rem !important;
        height: auto !important;
        min-height: 1.8rem !important;
        line-height: 1.1 !important;
        white-space: normal !important;
        word-wrap: break-word !important;
    }
    /* Mobile optimization */
    @media (max-width: 768px) {
        .main-title {
            font-size: 1.5rem;
        }
        .developer-credit {
            font-size: 0.9rem;
        }
        /* Hide sidebar by default on mobile */
        .css-1d391kg {
            transform: translateX(-100%);
        }
        /* Overlay for mobile sidebar */
        .css-1d391kg.css-1aumxhk {
            transform: translateX(0);
            position: fixed;
            z-index: 999;
            background: white;
            box-shadow: 2px 0 10px rgba(0,0,0,0.1);
        }
    }
    .explore-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
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
        # Check for required environment variables first
        required_env_vars = ["OPENAI_API_KEY", "PINECONE_API_KEY"]
        missing_vars = []

        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            return None, f"Missing required environment variables: {', '.join(missing_vars)}"

        # Validate RAG configuration
        validate_config()
        config = get_config()

        # Create RAG service with enhanced error reporting
        print(f"🔧 Initializing RAG service with index: {config.pinecone_index_name}")
        service = create_rag_service(
            pinecone_api_key=config.pinecone_api_key,
            openai_api_key=config.openai_api_key,
            index_name=config.pinecone_index_name,
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            retrieval_k=config.retrieval_k
        )
        print("✅ RAG service initialized successfully")
        return service, None
    except ImportError as e:
        return None, f"Missing dependencies for RAG service: {str(e)}. Please install: pip install pinecone langchain-pinecone PyPDF2"
    except Exception as e:
        error_msg = f"Failed to initialize RAG service: {str(e)}"
        print(f"❌ RAG initialization error: {error_msg}")
        return None, error_msg

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
        - `PINECONE_INDEX_NAME` (optional, defaults to 'rag-index')

        ### Deployment Notes:
        - **Local Development**: Create a `.env` file in your project root with these variables
        - **Cloud Deployment**: Set these as environment variables in your deployment platform
        - **Docker**: Pass environment variables using `-e` flags or docker-compose.yml
        - **Streamlit Cloud**: Add variables in the "Secrets" section of your app settings

        ### Troubleshooting Document Processing:
        If document processing works locally but not in deployment:
        1. ✅ Verify `OPENAI_API_KEY` and `PINECONE_API_KEY` are set
        2. ✅ Check network connectivity to external APIs
        3. ✅ Ensure all dependencies are installed: `pinecone`, `langchain-pinecone`, `PyPDF2`
        4. ✅ Verify the Pinecone index exists or can be created
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

def display_suggested_queries(chat_mode: str, data_agent, rag_service, namespace: str = "", show_header: bool = True):
    """Display 4 compact suggested queries."""
    if chat_mode == "📊 Talk to Data":
        queries = [
            "What tables and data is available to analyse?",
            "Which customer segments exist in the data?",
            "What's the monthly trend of net sales?",
            "What is the average revenue by males and females?"
        ]
    else:
        queries = [
            "What is this document about?",
            "Summarize the key points",
            "What are the main conclusions?",
            "Explain the methodology used"
        ]

    # Show header only initially to save space
    if show_header:
        st.markdown('<p style="font-size: 0.8rem; margin-bottom: 0.3rem; color: #666;">💡 <strong>Suggested Queries</strong></p>', unsafe_allow_html=True)

    cols = st.columns(2)
    for i, query in enumerate(queries):
        col = cols[i % 2]
        with col:
            # Use different keys based on whether it's initial or persistent display
            key_suffix = "_initial" if show_header else "_persistent"
            if st.button(query, key=f"suggestion_{i}{key_suffix}", help="Click to ask this question", use_container_width=True):
                # Add user message to history
                st.session_state.messages.append({"role": "user", "content": query})

                # Process the query immediately
                with st.spinner("Thinking..."):
                    if chat_mode == "📊 Talk to Data" and data_agent:
                        response = process_data_query(query, data_agent, st.session_state.session_id)
                    elif chat_mode == "📄 Talk to Documents" and rag_service:
                        response = process_document_query(query, rag_service, namespace)
                    else:
                        response = "Sorry, the selected service is not available."

                # Add assistant response to history
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()

def main():
    """Main Streamlit application."""

    # Add mobile detection and sidebar toggle
    st.markdown("""
    <script>
        // Simple mobile detection and sidebar management
        function isMobile() {
            return window.innerWidth <= 768;
        }

        // Hide sidebar on mobile by default
        if (isMobile()) {
            const sidebar = document.querySelector('.css-1d391kg');
            if (sidebar) {
                sidebar.style.transform = 'translateX(-100%)';
            }
        }
    </script>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('''
    <div class="main-header">
        <div class="main-title">🔍 Marketing Insight Explorer</div>
        <div class="developer-credit">Developed by Sumit Kamra</div>
    </div>
    ''', unsafe_allow_html=True)

    # Initialize services
    data_agent, data_error = initialize_data_agent()
    rag_service, rag_error = initialize_rag_service()

        # Store service status for later display at bottom

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

        # Initialize namespace variable
        namespace = ""

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

        # Service status at bottom with smaller text
        st.markdown('<div class="service-status">', unsafe_allow_html=True)
        st.caption("🔧 **Service Status**")

        # Data service status
        if data_agent:
            st.caption("📊 Data Querying: ✅")
        else:
            st.caption("📊 Data Querying: ❌")
            if data_error:
                st.caption(f"Error: {data_error[:50]}...")

        # RAG service status
        if rag_service:
            st.caption("📄 Document Processing: ✅")
            # Add test button for RAG service
            if st.button("🧪 Test", help="Test Pinecone and OpenAI connectivity", key="test_rag"):
                try:
                    # Test basic functionality
                    stats = rag_service.get_index_stats()
                    st.caption(f"✅ Test passed! {stats.get('total_vectors', 0)} vectors")
                except Exception as e:
                    st.caption(f"❌ Test failed: {str(e)[:30]}...")
        else:
            st.caption("📄 Document Processing: ❌")
            if rag_error:
                st.caption(f"Error: {rag_error[:50]}...")

        st.markdown('</div>', unsafe_allow_html=True)

    # Show suggested queries initially with header
    display_suggested_queries(chat_mode, data_agent, rag_service, namespace, show_header=True)

    # Main chat interface
    st.markdown('<div class="explore-header"><h2>💬 Explore</h2></div>', unsafe_allow_html=True)

    # Display chat history
    for message in st.session_state.messages:
        display_chat_message(message["content"], message["role"] == "user")

    # Show suggested queries again after interactions (without header to save space)
    if len(st.session_state.messages) > 0:
        display_suggested_queries(chat_mode, data_agent, rag_service, namespace, show_header=False)

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

if __name__ == "__main__":
    main()

"""
RAG System Package

A complete PDF-based Retrieval-Augmented Generation system using LangChain, Pinecone, and OpenAI.

Main Components:
- RAGService: Main orchestration service
- PDFProcessor: PDF text extraction and chunking
- PineconeVectorStore: Vector storage and similarity search
- RAGQAChain: Question answering with LLM chains

Quick Start:
    from ai_agent.rag import create_rag_service

    rag = create_rag_service(
        pinecone_api_key="your-key",
        pinecone_env="your-env",
        openai_api_key="your-key"
    )

    # Upload PDF and ask questions
    rag.upload_pdf("document.pdf")
    response = rag.ask_question("What is this document about?")
"""

from .rag_service import RAGService, create_rag_service
from .pdf_processor import PDFProcessor, create_pdf_processor
from .vector_store import PineconeVectorStore, create_vector_store
from .qa_chain import RAGQAChain, create_qa_chain
from .config import RAGConfig, get_config, validate_config, create_env_template

__version__ = "1.0.0"

__all__ = [
    # Main service
    "RAGService",
    "create_rag_service",

    # Core components
    "PDFProcessor",
    "create_pdf_processor",
    "PineconeVectorStore",
    "create_vector_store",
    "RAGQAChain",
    "create_qa_chain",

    # Configuration
    "RAGConfig",
    "get_config",
    "validate_config",
    "create_env_template",

    # Version
    "__version__"
]

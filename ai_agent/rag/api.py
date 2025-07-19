"""
FastAPI Application for RAG System

This module provides REST API endpoints for the RAG system.
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from .rag_service import create_rag_service, RAGService


# Load environment variables
load_dotenv()


# Pydantic models for API requests/responses
class QuestionRequest(BaseModel):
    question: str = Field(..., description="The question to ask")
    namespace: str = Field("", description="Optional Pinecone namespace")
    conversational: bool = Field(False, description="Use conversational mode")
    return_sources: bool = Field(True, description="Return source documents")


class QuestionResponse(BaseModel):
    question: str
    answer: str
    sources: List[Dict[str, Any]] = []


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    k: int = Field(5, description="Number of results to return")
    namespace: str = Field("", description="Optional Pinecone namespace")


class UploadResponse(BaseModel):
    success: bool
    message: str
    document_count: int
    doc_id: Optional[str] = None
    source: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    message: str
    index_stats: Dict[str, Any] = {}


# Global RAG service instance
rag_service: Optional[RAGService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup for the FastAPI app."""
    global rag_service

    # Initialize RAG service on startup
    try:
        print("🚀 Initializing RAG service...")

        # Check required environment variables
        required_vars = ["PINECONE_API_KEY", "PINECONE_ENV", "OPENAI_API_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")

        rag_service = create_rag_service(
            pinecone_api_key=os.getenv("PINECONE_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            index_name=os.getenv("PINECONE_INDEX_NAME", "rag-index"),
            chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
            retrieval_k=int(os.getenv("RETRIEVAL_K", "4"))
        )

        print("✅ RAG service initialized successfully!")

    except Exception as e:
        print(f"❌ Failed to initialize RAG service: {str(e)}")
        raise

    yield

    # Cleanup on shutdown
    print("🔄 Shutting down RAG service...")


# Create FastAPI app
app = FastAPI(
    title="RAG System API",
    description="REST API for PDF-based Retrieval-Augmented Generation system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_rag_service() -> RAGService:
    """Dependency to get RAG service instance."""
    if rag_service is None:
        raise HTTPException(
            status_code=503,
            detail="RAG service not initialized"
        )
    return rag_service


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "message": "RAG System API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check(service: RAGService = Depends(get_rag_service)):
    """Health check endpoint."""
    try:
        stats = service.get_index_stats()
        return HealthResponse(
            status="healthy",
            message="RAG system is operational",
            index_stats=stats
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Health check failed: {str(e)}"
        )


@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    namespace: str = "",
    background_tasks: BackgroundTasks = None,
    service: RAGService = Depends(get_rag_service)
):
    """
    Upload and process a PDF file.

    Args:
        file: PDF file to upload
        namespace: Optional Pinecone namespace
        background_tasks: FastAPI background tasks
        service: RAG service dependency

    Returns:
        Upload result information
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    try:
        # Read file content
        content = await file.read()

        # Process PDF
        result = service.upload_pdf_from_bytes(
            pdf_bytes=content,
            filename=file.filename,
            namespace=namespace
        )

        if result["success"]:
            return UploadResponse(**result)
        else:
            raise HTTPException(
                status_code=400,
                detail=result["message"]
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDF: {str(e)}"
        )


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    service: RAGService = Depends(get_rag_service)
):
    """
    Ask a question and get an answer from the RAG system.

    Args:
        request: Question request with parameters
        service: RAG service dependency

    Returns:
        Answer with source documents
    """
    try:
        response = service.ask_question(
            question=request.question,
            namespace=request.namespace,
            conversational=request.conversational,
            return_sources=request.return_sources
        )

        return QuestionResponse(**response)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)}"
        )


@app.post("/search")
async def search_documents(
    request: SearchRequest,
    service: RAGService = Depends(get_rag_service)
):
    """
    Search for relevant documents without generating an answer.

    Args:
        request: Search request with parameters
        service: RAG service dependency

    Returns:
        List of relevant documents
    """
    try:
        results = service.search_documents(
            query=request.query,
            k=request.k,
            namespace=request.namespace
        )

        return {"results": results}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching documents: {str(e)}"
        )


@app.get("/conversation/history")
async def get_conversation_history(
    service: RAGService = Depends(get_rag_service)
):
    """Get conversation history."""
    try:
        history = service.get_conversation_history()
        return {"history": history}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting conversation history: {str(e)}"
        )


@app.delete("/conversation/history")
async def clear_conversation_history(
    service: RAGService = Depends(get_rag_service)
):
    """Clear conversation history."""
    try:
        service.clear_conversation_history()
        return {"message": "Conversation history cleared"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing conversation history: {str(e)}"
        )


@app.get("/index/stats")
async def get_index_stats(
    service: RAGService = Depends(get_rag_service)
):
    """Get Pinecone index statistics."""
    try:
        stats = service.get_index_stats()
        return {"stats": stats}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting index stats: {str(e)}"
        )


@app.delete("/documents")
async def delete_documents(
    namespace: str = "",
    delete_all: bool = False,
    service: RAGService = Depends(get_rag_service)
):
    """
    Delete documents from the vector store.

    Args:
        namespace: Pinecone namespace
        delete_all: Whether to delete all documents
        service: RAG service dependency

    Returns:
        Deletion result
    """
    try:
        result = service.delete_documents(
            namespace=namespace,
            delete_all=delete_all
        )

        if result["success"]:
            return result
        else:
            raise HTTPException(
                status_code=400,
                detail=result["message"]
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting documents: {str(e)}"
        )


# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "type": "internal_error"
        }
    )


# Run the app
if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting RAG API server...")

    uvicorn.run(
        "ai_agent.rag.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

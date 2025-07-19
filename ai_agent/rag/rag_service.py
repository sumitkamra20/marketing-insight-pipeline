"""
Main RAG Service Module

This module orchestrates all RAG components: PDF processing, vector storage, and QA chains.
"""

import os
import tempfile
from typing import List, Dict, Any, Optional
from pathlib import Path

from .pdf_processor import PDFProcessor, create_pdf_processor
from .vector_store import PineconeVectorStore, create_vector_store
from .qa_chain import RAGQAChain, create_qa_chain


class RAGService:
    """Main service that orchestrates the entire RAG pipeline."""

    def __init__(
        self,
        pinecone_api_key: str,
        pinecone_env: str,
        openai_api_key: str,
        index_name: str = "rag-index",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        embedding_model: str = "text-embedding-ada-002",
        llm_model: str = "gpt-3.5-turbo",
        retrieval_k: int = 4
    ):
        """
        Initialize RAG Service.

        Args:
            pinecone_api_key: Pinecone API key
            pinecone_env: Pinecone environment
            openai_api_key: OpenAI API key
            index_name: Name of the Pinecone index
            chunk_size: Size of text chunks for processing
            chunk_overlap: Overlap between text chunks
            embedding_model: OpenAI embedding model name
            llm_model: OpenAI LLM model name
            retrieval_k: Number of documents to retrieve for QA
        """
        # Set environment variables
        os.environ["OPENAI_API_KEY"] = openai_api_key
        os.environ["PINECONE_API_KEY"] = pinecone_api_key
        os.environ["PINECONE_ENV"] = pinecone_env

        self.index_name = index_name
        self.retrieval_k = retrieval_k

        # Initialize components
        print("Initializing RAG Service components...")

        # 1. Initialize PDF processor
        self.pdf_processor = create_pdf_processor(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        print("✓ PDF processor initialized")

        # 2. Initialize vector store
        self.vector_store = create_vector_store(
            pinecone_api_key=pinecone_api_key,
            index_name=index_name,
            embedding_model=embedding_model
        )
        print("✓ Vector store initialized")

        # 3. Initialize QA chain
        retriever = self.vector_store.get_retriever(k=retrieval_k)
        self.qa_chain = create_qa_chain(
            retriever=retriever,
            llm_model=llm_model
        )
        print("✓ QA chain initialized")

        print("🚀 RAG Service fully initialized and ready!")

    def upload_pdf(self, pdf_path: str, namespace: str = "") -> Dict[str, Any]:
        """
        Upload and process a PDF file.

        Args:
            pdf_path: Path to the PDF file
            namespace: Optional Pinecone namespace

        Returns:
            Dictionary with upload results
        """
        try:
            print(f"\n📄 Processing PDF: {pdf_path}")

            # 1. Process PDF and create chunks
            documents = self.pdf_processor.process_pdf(pdf_path)

            if not documents:
                return {
                    "success": False,
                    "message": "No documents were created from the PDF",
                    "document_count": 0,
                    "doc_id": None
                }

            # 2. Add documents to vector store
            doc_ids = self.vector_store.add_documents(
                documents=documents,
                namespace=namespace
            )

            # 3. Get document metadata
            doc_id = documents[0].metadata.get("doc_id")
            source_name = documents[0].metadata.get("source")

            result = {
                "success": True,
                "message": f"Successfully processed and uploaded PDF: {source_name}",
                "document_count": len(documents),
                "doc_id": doc_id,
                "source": source_name,
                "vector_ids": doc_ids,
                "namespace": namespace
            }

            print(f"✅ PDF upload complete: {result['message']}")
            return result

        except Exception as e:
            error_msg = f"Error uploading PDF {pdf_path}: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "message": error_msg,
                "document_count": 0,
                "doc_id": None
            }

    def upload_pdf_from_bytes(
        self,
        pdf_bytes: bytes,
        filename: str,
        namespace: str = ""
    ) -> Dict[str, Any]:
        """
        Upload and process a PDF from bytes (useful for web uploads).

        Args:
            pdf_bytes: PDF file content as bytes
            filename: Name of the PDF file
            namespace: Optional Pinecone namespace

        Returns:
            Dictionary with upload results
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                temp_file.write(pdf_bytes)
                temp_path = temp_file.name

            # Process the temporary file
            result = self.upload_pdf(temp_path, namespace)

            # Update source name to original filename
            if result["success"]:
                result["source"] = filename
                result["message"] = f"Successfully processed and uploaded PDF: {filename}"

            # Clean up temporary file
            os.unlink(temp_path)

            return result

        except Exception as e:
            error_msg = f"Error uploading PDF from bytes ({filename}): {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "message": error_msg,
                "document_count": 0,
                "doc_id": None
            }

    def ask_question(
        self,
        question: str,
        namespace: str = "",
        conversational: bool = False,
        return_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Ask a question and get an answer from the RAG system.

        Args:
            question: The question to ask
            namespace: Optional Pinecone namespace to search in
            conversational: Whether to use conversational chain (maintains history)
            return_sources: Whether to return source documents

        Returns:
            Dictionary containing the answer and sources
        """
        try:
            print(f"\n🤔 Question: {question}")

            # Update retriever namespace if needed
            if namespace:
                retriever = self.vector_store.get_retriever(k=self.retrieval_k, namespace=namespace)
                # Create new QA chain with namespace-specific retriever
                qa_chain = create_qa_chain(
                    retriever=retriever,
                    llm_model=self.qa_chain.llm_model
                )
            else:
                qa_chain = self.qa_chain

            # Get answer
            if conversational:
                response = qa_chain.ask_conversational(
                    question=question,
                    return_sources=return_sources
                )
            else:
                response = qa_chain.ask_question(
                    question=question,
                    return_sources=return_sources
                )

            print(f"✅ Answer generated with {len(response.get('sources', []))} sources")
            return response

        except Exception as e:
            error_msg = f"Error processing question: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "question": question,
                "answer": error_msg,
                "sources": []
            }

    def search_documents(
        self,
        query: str,
        k: int = 5,
        namespace: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents without generating an answer.

        Args:
            query: Search query
            k: Number of documents to return
            namespace: Optional Pinecone namespace

        Returns:
            List of relevant documents with metadata
        """
        try:
            print(f"\n🔍 Searching for: {query}")

            # Perform similarity search
            docs_with_scores = self.vector_store.similarity_search_with_scores(
                query=query,
                k=k,
                namespace=namespace
            )

            # Format results
            results = []
            for i, (doc, score) in enumerate(docs_with_scores):
                result = {
                    "index": i,
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "source": doc.metadata.get("source", "Unknown"),
                    "chunk_id": doc.metadata.get("chunk_id"),
                    "similarity_score": float(score)
                }
                results.append(result)

            print(f"✅ Found {len(results)} relevant documents")
            return results

        except Exception as e:
            print(f"❌ Error searching documents: {str(e)}")
            return []

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the conversation history from the QA chain."""
        return self.qa_chain.get_conversation_history()

    def clear_conversation_history(self):
        """Clear the conversation history."""
        self.qa_chain.clear_conversation_history()

    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the Pinecone index."""
        return self.vector_store.get_index_stats()

    def delete_documents(
        self,
        doc_id: str = None,
        namespace: str = "",
        delete_all: bool = False
    ) -> Dict[str, Any]:
        """
        Delete documents from the vector store.

        Args:
            doc_id: Document ID to delete (specific document)
            namespace: Pinecone namespace
            delete_all: Whether to delete all documents

        Returns:
            Dictionary with deletion results
        """
        try:
            if delete_all:
                success = self.vector_store.delete_all(namespace=namespace)
                message = f"Deleted all documents" + (f" from namespace {namespace}" if namespace else "")
            elif doc_id:
                # This would require storing document ID mappings
                # For now, we'll indicate that this feature needs implementation
                return {
                    "success": False,
                    "message": "Individual document deletion requires additional implementation"
                }
            else:
                return {
                    "success": False,
                    "message": "Must specify either doc_id or delete_all=True"
                }

            if success:
                print(f"✅ {message}")
                return {"success": True, "message": message}
            else:
                return {"success": False, "message": "Deletion failed"}

        except Exception as e:
            error_msg = f"Error deleting documents: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "message": error_msg}


def create_rag_service(
    pinecone_api_key: str,
    openai_api_key: str,
    index_name: str = "rag-index",
    **kwargs
) -> RAGService:
    """
    Factory function to create a RAGService instance.

    Args:
        pinecone_api_key: Pinecone API key
        openai_api_key: OpenAI API key
        index_name: Name of the Pinecone index
        **kwargs: Additional configuration options

    Returns:
        Configured RAGService instance
    """
    return RAGService(
        pinecone_api_key=pinecone_api_key,
        pinecone_env="",  # No longer needed with new Pinecone API
        openai_api_key=openai_api_key,
        index_name=index_name,
        **kwargs
    )


if __name__ == "__main__":
    # Example usage
    print("RAG Service module ready!")

    # Example initialization (requires environment variables)
    # rag_service = create_rag_service(
    #     pinecone_api_key=os.getenv("PINECONE_API_KEY"),
    #     pinecone_env=os.getenv("PINECONE_ENV"),
    #     openai_api_key=os.getenv("OPENAI_API_KEY"),
    #     index_name="my-rag-index"
    # )
    #
    # # Upload a PDF
    # result = rag_service.upload_pdf("document.pdf")
    # print(f"Upload result: {result}")
    #
    # # Ask a question
    # response = rag_service.ask_question("What is this document about?")
    # print(f"Answer: {response['answer']}")
    # print(f"Sources: {len(response['sources'])}")

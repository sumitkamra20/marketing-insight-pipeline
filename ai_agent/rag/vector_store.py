"""
Vector Store Module for RAG System

This module handles embeddings generation and Pinecone vector database operations.
"""

import os
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore as LangChainPineconeVectorStore
from langchain.schema import Document


class PineconeVectorStore:
    """Handles embeddings and Pinecone vector database operations."""

    def __init__(
        self,
        api_key: str,
        index_name: str,
        embedding_model: str = "text-embedding-ada-002",
        dimension: int = 1536,
        metric: str = "cosine"
    ):
        """
        Initialize Pinecone vector store.

        Args:
            api_key: Pinecone API key
            index_name: Name of the Pinecone index
            embedding_model: OpenAI embedding model name
            dimension: Vector dimension (1536 for text-embedding-ada-002)
            metric: Distance metric for similarity search
        """
        self.api_key = api_key
        self.index_name = index_name
        self.dimension = dimension
        self.metric = metric

        # Initialize OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(model=embedding_model)

        # Initialize Pinecone client
        self.pc = self._initialize_pinecone()

        # Initialize LangChain Pinecone vector store
        # The langchain_pinecone will handle index creation if needed
        self.vector_store = None
        self._initialize_vector_store()

    def _initialize_pinecone(self):
        """Initialize Pinecone client."""
        try:
            pc = Pinecone(api_key=self.api_key)
            print(f"Successfully initialized Pinecone client")
            return pc
        except Exception as e:
            raise Exception(f"Failed to initialize Pinecone: {str(e)}")

    def _initialize_vector_store(self):
        """Initialize LangChain Pinecone vector store."""
        try:
            # Use the new langchain_pinecone approach
            self.vector_store = LangChainPineconeVectorStore(
                index_name=self.index_name,
                embedding=self.embeddings
            )
            print("LangChain Pinecone vector store initialized")
        except Exception as e:
            raise Exception(f"Failed to initialize vector store: {str(e)}")

    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the Pinecone index."""
        try:
            # Get the index from Pinecone client
            index = self.pc.Index(self.index_name)
            stats = index.describe_index_stats()
            return {
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": stats.namespaces
            }
        except Exception as e:
            print(f"Error getting index stats: {str(e)}")
            return {}

    def add_documents(
        self,
        documents: List[Document],
        namespace: str = "",
        batch_size: int = 100
    ) -> List[str]:
        """
        Add documents to Pinecone vector store.

        Args:
            documents: List of Document objects to add
            namespace: Pinecone namespace (optional)
            batch_size: Number of documents to process in each batch

        Returns:
            List of document IDs that were added
        """
        if not documents:
            print("No documents to add")
            return []

        try:
            print(f"Adding {len(documents)} documents to Pinecone...")

            # Process documents in batches
            all_ids = []
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]

                # Add batch to vector store
                if namespace:
                    ids = self.vector_store.add_documents(
                        documents=batch,
                        namespace=namespace
                    )
                else:
                    ids = self.vector_store.add_documents(documents=batch)

                all_ids.extend(ids)
                print(f"Added batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")

                # Small delay between batches to avoid rate limits
                if i + batch_size < len(documents):
                    time.sleep(1)

            print(f"Successfully added {len(all_ids)} documents to Pinecone")

            # Print updated stats
            stats = self.get_index_stats()
            print(f"Index now contains {stats.get('total_vectors', 'unknown')} vectors")

            return all_ids

        except Exception as e:
            print(f"Error adding documents to Pinecone: {str(e)}")
            raise

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        namespace: str = "",
        score_threshold: float = None
    ) -> List[Document]:
        """
        Perform similarity search.

        Args:
            query: Search query
            k: Number of results to return
            namespace: Pinecone namespace to search in
            score_threshold: Minimum similarity score threshold

        Returns:
            List of relevant Documents
        """
        try:
            if namespace:
                if score_threshold is not None:
                    results = self.vector_store.similarity_search_with_score(
                        query=query,
                        k=k,
                        namespace=namespace
                    )
                    # Filter by score threshold
                    filtered_results = [
                        doc for doc, score in results
                        if score >= score_threshold
                    ]
                    return filtered_results
                else:
                    return self.vector_store.similarity_search(
                        query=query,
                        k=k,
                        namespace=namespace
                    )
            else:
                if score_threshold is not None:
                    results = self.vector_store.similarity_search_with_score(
                        query=query,
                        k=k
                    )
                    # Filter by score threshold
                    filtered_results = [
                        doc for doc, score in results
                        if score >= score_threshold
                    ]
                    return filtered_results
                else:
                    return self.vector_store.similarity_search(
                        query=query,
                        k=k
                    )
        except Exception as e:
            print(f"Error during similarity search: {str(e)}")
            return []

    def similarity_search_with_scores(
        self,
        query: str,
        k: int = 4,
        namespace: str = ""
    ) -> List[Tuple[Document, float]]:
        """
        Perform similarity search and return documents with scores.

        Args:
            query: Search query
            k: Number of results to return
            namespace: Pinecone namespace to search in

        Returns:
            List of (Document, score) tuples
        """
        try:
            if namespace:
                return self.vector_store.similarity_search_with_score(
                    query=query,
                    k=k,
                    namespace=namespace
                )
            else:
                return self.vector_store.similarity_search_with_score(
                    query=query,
                    k=k
                )
        except Exception as e:
            print(f"Error during similarity search with scores: {str(e)}")
            return []

    def delete_documents(self, ids: List[str], namespace: str = "") -> bool:
        """
        Delete documents from Pinecone.

        Args:
            ids: List of document IDs to delete
            namespace: Pinecone namespace

        Returns:
            True if successful, False otherwise
        """
        try:
            index = self.pc.Index(self.index_name)
            if namespace:
                index.delete(ids=ids, namespace=namespace)
            else:
                index.delete(ids=ids)

            print(f"Deleted {len(ids)} documents from Pinecone")
            return True
        except Exception as e:
            print(f"Error deleting documents: {str(e)}")
            return False

    def delete_all(self, namespace: str = "") -> bool:
        """
        Delete all documents from the index or namespace.

        Args:
            namespace: Pinecone namespace (if empty, deletes entire index)

        Returns:
            True if successful, False otherwise
        """
        try:
            index = self.pc.Index(self.index_name)
            if namespace:
                index.delete(delete_all=True, namespace=namespace)
                print(f"Deleted all documents from namespace: {namespace}")
            else:
                index.delete(delete_all=True)
                print("Deleted all documents from index")

            return True
        except Exception as e:
            print(f"Error deleting all documents: {str(e)}")
            return False

    def get_retriever(self, k: int = 4, namespace: str = ""):
        """
        Get a LangChain retriever for the vector store.

        Args:
            k: Number of documents to retrieve
            namespace: Pinecone namespace

        Returns:
            LangChain VectorStoreRetriever
        """
        search_kwargs = {"k": k}
        if namespace:
            search_kwargs["namespace"] = namespace

        return self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs=search_kwargs
        )


def create_vector_store(
    pinecone_api_key: str,
    index_name: str,
    embedding_model: str = "text-embedding-ada-002"
) -> PineconeVectorStore:
    """
    Factory function to create a PineconeVectorStore instance.

    Args:
        pinecone_api_key: Pinecone API key
        index_name: Name of the Pinecone index
        embedding_model: OpenAI embedding model name

    Returns:
        Configured PineconeVectorStore instance
    """
    return PineconeVectorStore(
        api_key=pinecone_api_key,
        index_name=index_name,
        embedding_model=embedding_model
    )


if __name__ == "__main__":
    # Example usage (requires environment variables)
    print("Vector Store module ready!")

    # Example initialization (uncomment and set environment variables)
    # vector_store = create_vector_store(
    #     pinecone_api_key=os.getenv("PINECONE_API_KEY"),
    #     index_name=os.getenv("PINECONE_INDEX_NAME", "rag-index")
    # )
    # print("Vector store initialized!")
    # print(f"Index stats: {vector_store.get_index_stats()}")

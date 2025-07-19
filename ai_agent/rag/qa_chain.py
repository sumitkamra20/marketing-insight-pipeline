"""
Question Answering Chain Module for RAG System

This module handles the retrieval and LLM chain operations for question answering.
"""

import os
from typing import List, Dict, Any, Optional, Tuple

from langchain_openai import OpenAI, ChatOpenAI
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.chains.question_answering import load_qa_chain
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseRetriever, Document
from langchain.prompts import PromptTemplate


class RAGQAChain:
    """Handles question answering using retrieval-augmented generation."""

    def __init__(
        self,
        retriever: BaseRetriever,
        llm_model: str = "gpt-3.5-turbo",
        temperature: float = 0.0,
        max_tokens: int = 500,
        chain_type: str = "stuff"
    ):
        """
        Initialize RAG QA Chain.

        Args:
            retriever: LangChain retriever for document retrieval
            llm_model: OpenAI model name for LLM
            temperature: LLM temperature for response generation
            max_tokens: Maximum tokens for LLM response
            chain_type: Type of QA chain ("stuff", "map_reduce", "refine", "map_rerank")
        """
        self.retriever = retriever
        self.llm_model = llm_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.chain_type = chain_type

        # Initialize conversation memory first
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )

        # Initialize LLM
        self.llm = self._initialize_llm()

        # Initialize QA chain
        self.qa_chain = self._initialize_qa_chain()

        # Initialize conversational chain (for multi-turn conversations)
        self.conversational_chain = self._initialize_conversational_chain()

    def _initialize_llm(self):
        """Initialize the language model."""
        try:
            if self.llm_model.startswith("gpt-"):
                return ChatOpenAI(
                    model_name=self.llm_model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
            else:
                return OpenAI(
                    model_name=self.llm_model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
        except Exception as e:
            raise Exception(f"Failed to initialize LLM: {str(e)}")

    def _initialize_qa_chain(self):
        """Initialize the RetrievalQA chain."""
        try:
            # Custom prompt template for better responses
            prompt_template = """Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
Try to provide specific details from the context when possible.

Context:
{context}

Question: {question}

Answer:"""

            PROMPT = PromptTemplate(
                template=prompt_template,
                input_variables=["context", "question"]
            )

            return RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type=self.chain_type,
                retriever=self.retriever,
                return_source_documents=True,
                chain_type_kwargs={"prompt": PROMPT}
            )
        except Exception as e:
            raise Exception(f"Failed to initialize QA chain: {str(e)}")

    def _initialize_conversational_chain(self):
        """Initialize the ConversationalRetrievalChain."""
        try:
            # Custom prompt for conversational chain
            prompt_template = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question, in its original language.

Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:"""

            CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(prompt_template)

            qa_template = """Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
Use three sentences maximum and keep the answer concise.

Context:
{context}

Question: {question}
Answer:"""

            QA_PROMPT = PromptTemplate(
                template=qa_template,
                input_variables=["context", "question"]
            )

            return ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.retriever,
                memory=self.memory,
                return_source_documents=True,
                condense_question_prompt=CONDENSE_QUESTION_PROMPT,
                combine_docs_chain_kwargs={"prompt": QA_PROMPT}
            )
        except Exception as e:
            raise Exception(f"Failed to initialize conversational chain: {str(e)}")

    def ask_question(
        self,
        question: str,
        return_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Ask a question using the QA chain.

        Args:
            question: The question to ask
            return_sources: Whether to return source documents

        Returns:
            Dictionary containing answer and optionally source documents
        """
        try:
            print(f"Processing question: {question}")

            # Get answer from QA chain
            result = self.qa_chain({"query": question})

            response = {
                "question": question,
                "answer": result["result"],
                "sources": []
            }

            # Add source information if requested
            if return_sources and "source_documents" in result:
                sources = []
                for i, doc in enumerate(result["source_documents"]):
                    source_info = {
                        "index": i,
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "source": doc.metadata.get("source", "Unknown"),
                        "chunk_id": doc.metadata.get("chunk_id", f"chunk_{i}")
                    }
                    sources.append(source_info)

                response["sources"] = sources
                print(f"Retrieved {len(sources)} source documents")

            return response

        except Exception as e:
            print(f"Error processing question: {str(e)}")
            return {
                "question": question,
                "answer": f"Error processing question: {str(e)}",
                "sources": []
            }

    def ask_conversational(
        self,
        question: str,
        return_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Ask a question using the conversational chain (maintains conversation history).

        Args:
            question: The question to ask
            return_sources: Whether to return source documents

        Returns:
            Dictionary containing answer and optionally source documents
        """
        try:
            print(f"Processing conversational question: {question}")

            # Get answer from conversational chain
            result = self.conversational_chain({"question": question})

            response = {
                "question": question,
                "answer": result["answer"],
                "sources": []
            }

            # Add source information if requested
            if return_sources and "source_documents" in result:
                sources = []
                for i, doc in enumerate(result["source_documents"]):
                    source_info = {
                        "index": i,
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "source": doc.metadata.get("source", "Unknown"),
                        "chunk_id": doc.metadata.get("chunk_id", f"chunk_{i}")
                    }
                    sources.append(source_info)

                response["sources"] = sources
                print(f"Retrieved {len(sources)} source documents")

            return response

        except Exception as e:
            print(f"Error processing conversational question: {str(e)}")
            return {
                "question": question,
                "answer": f"Error processing question: {str(e)}",
                "sources": []
            }

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        Get the conversation history.

        Returns:
            List of conversation turns
        """
        try:
            history = []
            if hasattr(self.memory, 'chat_memory') and self.memory.chat_memory.messages:
                messages = self.memory.chat_memory.messages
                for i in range(0, len(messages), 2):
                    if i + 1 < len(messages):
                        history.append({
                            "question": messages[i].content,
                            "answer": messages[i + 1].content
                        })
            return history
        except Exception as e:
            print(f"Error getting conversation history: {str(e)}")
            return []

    def clear_conversation_history(self):
        """Clear the conversation history."""
        try:
            self.memory.clear()
            print("Conversation history cleared")
        except Exception as e:
            print(f"Error clearing conversation history: {str(e)}")

    def get_relevant_documents(
        self,
        question: str,
        k: int = 4
    ) -> List[Document]:
        """
        Get relevant documents for a question without generating an answer.

        Args:
            question: The question to search for
            k: Number of documents to retrieve

        Returns:
            List of relevant documents
        """
        try:
            # Update retriever's k value if it supports it
            if hasattr(self.retriever, 'search_kwargs'):
                original_k = self.retriever.search_kwargs.get('k', 4)
                self.retriever.search_kwargs['k'] = k

                docs = self.retriever.get_relevant_documents(question)

                # Restore original k value
                self.retriever.search_kwargs['k'] = original_k

                return docs
            else:
                return self.retriever.get_relevant_documents(question)
        except Exception as e:
            print(f"Error getting relevant documents: {str(e)}")
            return []


def create_qa_chain(
    retriever: BaseRetriever,
    llm_model: str = "gpt-3.5-turbo",
    temperature: float = 0.0,
    max_tokens: int = 500
) -> RAGQAChain:
    """
    Factory function to create a RAGQAChain instance.

    Args:
        retriever: LangChain retriever for document retrieval
        llm_model: OpenAI model name for LLM
        temperature: LLM temperature for response generation
        max_tokens: Maximum tokens for LLM response

    Returns:
        Configured RAGQAChain instance
    """
    return RAGQAChain(
        retriever=retriever,
        llm_model=llm_model,
        temperature=temperature,
        max_tokens=max_tokens
    )


if __name__ == "__main__":
    # Example usage
    print("QA Chain module ready!")

    # Example initialization (requires a retriever)
    # from vector_store import create_vector_store
    # vector_store = create_vector_store(...)
    # retriever = vector_store.get_retriever(k=3)
    # qa_chain = create_qa_chain(retriever)
    #
    # response = qa_chain.ask_question("What is this document about?")
    # print(f"Answer: {response['answer']}")
    # print(f"Sources: {len(response['sources'])}")

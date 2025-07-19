"""
PDF Processing Module for RAG System

This module handles PDF text extraction and chunking for the RAG system.
"""

import os
import hashlib
from typing import List, Dict, Any
from pathlib import Path

import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document


class PDFProcessor:
    """Handles PDF text extraction and chunking."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] = None
    ):
        """
        Initialize PDF processor.

        Args:
            chunk_size: Maximum size of each text chunk
            chunk_overlap: Number of characters to overlap between chunks
            separators: Custom separators for text splitting
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Default separators for text splitting
        if separators is None:
            separators = ["\n\n", "\n", " ", ""]

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            length_function=len,
        )

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Extracted text as a string

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            Exception: If PDF cannot be processed
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""

                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"

                return text
        except Exception as e:
            raise Exception(f"Error processing PDF {pdf_path}: {str(e)}")

    def generate_document_id(self, pdf_path: str) -> str:
        """
        Generate a unique document ID based on file path and content.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Unique document ID
        """
        # Use file name and modification time for ID
        file_stat = os.stat(pdf_path)
        content = f"{pdf_path}_{file_stat.st_mtime}_{file_stat.st_size}"
        return hashlib.md5(content.encode()).hexdigest()

    def chunk_text(self, text: str, doc_id: str, source: str) -> List[Document]:
        """
        Split text into chunks and create Document objects.

        Args:
            text: Text to be chunked
            doc_id: Document ID
            source: Source file path or name

        Returns:
            List of Document objects with metadata
        """
        # Split text into chunks
        chunks = self.text_splitter.split_text(text)

        # Create Document objects with metadata
        documents = []
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={
                    "source": source,
                    "doc_id": doc_id,
                    "chunk_id": f"{doc_id}_chunk_{i}",
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            )
            documents.append(doc)

        return documents

    def process_pdf(self, pdf_path: str) -> List[Document]:
        """
        Complete PDF processing pipeline: extract text and create chunks.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of Document objects ready for embedding

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            Exception: If processing fails
        """
        # Extract text from PDF
        text = self.extract_text_from_pdf(pdf_path)

        if not text.strip():
            raise Exception(f"No text extracted from PDF: {pdf_path}")

        # Generate document ID
        doc_id = self.generate_document_id(pdf_path)

        # Get source name (just filename for cleaner metadata)
        source = Path(pdf_path).name

        # Create chunks
        documents = self.chunk_text(text, doc_id, source)

        print(f"Processed PDF: {source}")
        print(f"Document ID: {doc_id}")
        print(f"Total chunks created: {len(documents)}")

        return documents

    def process_multiple_pdfs(self, pdf_paths: List[str]) -> List[Document]:
        """
        Process multiple PDF files.

        Args:
            pdf_paths: List of paths to PDF files

        Returns:
            Combined list of Document objects from all PDFs
        """
        all_documents = []

        for pdf_path in pdf_paths:
            try:
                documents = self.process_pdf(pdf_path)
                all_documents.extend(documents)
                print(f"Successfully processed: {pdf_path}")
            except Exception as e:
                print(f"Error processing {pdf_path}: {str(e)}")
                continue

        print(f"Total documents processed: {len(all_documents)}")
        return all_documents


def create_pdf_processor(chunk_size: int = 1000, chunk_overlap: int = 200) -> PDFProcessor:
    """
    Factory function to create a PDFProcessor instance.

    Args:
        chunk_size: Maximum size of each text chunk
        chunk_overlap: Number of characters to overlap between chunks

    Returns:
        Configured PDFProcessor instance
    """
    return PDFProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)


if __name__ == "__main__":
    # Example usage
    processor = create_pdf_processor()

    # Test with a sample PDF (replace with actual path)
    # documents = processor.process_pdf("sample.pdf")
    # for doc in documents[:2]:  # Show first 2 chunks
    #     print(f"Chunk: {doc.metadata['chunk_id']}")
    #     print(f"Content: {doc.page_content[:200]}...")
    #     print("---")

    print("PDF Processor module ready!")

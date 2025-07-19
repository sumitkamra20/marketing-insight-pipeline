"""
Configuration Module for RAG System

This module handles environment variables and configuration settings.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


class RAGConfig(BaseSettings):
    """Configuration settings for the RAG system."""

    # Required API Keys
    openai_api_key: str = Field(..., env="OPENAI_API_KEY", description="OpenAI API key")
    pinecone_api_key: str = Field(..., env="PINECONE_API_KEY", description="Pinecone API key")
    pinecone_env: str = Field("us-east-1-aws", env="PINECONE_ENV", description="Pinecone environment (legacy, not used with new API)")

    # Pinecone Configuration
    pinecone_index_name: str = Field("rag-index", env="PINECONE_INDEX_NAME", description="Pinecone index name")

    # Text Processing Configuration
    chunk_size: int = Field(1000, env="CHUNK_SIZE", description="Text chunk size")
    chunk_overlap: int = Field(200, env="CHUNK_OVERLAP", description="Text chunk overlap")
    retrieval_k: int = Field(4, env="RETRIEVAL_K", description="Number of documents to retrieve")

    # Model Configuration
    embedding_model: str = Field("text-embedding-ada-002", env="EMBEDDING_MODEL", description="OpenAI embedding model")
    llm_model: str = Field("gpt-3.5-turbo", env="LLM_MODEL", description="OpenAI LLM model")
    llm_temperature: float = Field(0.0, env="LLM_TEMPERATURE", description="LLM temperature")
    llm_max_tokens: int = Field(500, env="LLM_MAX_TOKENS", description="Maximum tokens for LLM response")

    # API Configuration
    api_host: str = Field("0.0.0.0", env="API_HOST", description="API server host")
    api_port: int = Field(8000, env="API_PORT", description="API server port")
    api_reload: bool = Field(True, env="API_RELOAD", description="Enable API reload")

    # Logging Configuration
    log_level: str = Field("info", env="LOG_LEVEL", description="Logging level")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


def get_config() -> RAGConfig:
    """
    Get configuration instance.

    Returns:
        RAGConfig instance

    Raises:
        ValueError: If required configuration is missing
    """
    try:
        return RAGConfig()
    except Exception as e:
        raise ValueError(f"Configuration error: {str(e)}")


def validate_config() -> bool:
    """
    Validate that all required configuration is present.

    Returns:
        True if configuration is valid

    Raises:
        ValueError: If configuration is invalid
    """
    try:
        config = get_config()

        # Check for required API keys
        if not config.openai_api_key or config.openai_api_key == "your_openai_api_key_here":
            raise ValueError("OPENAI_API_KEY is required. Get it from https://platform.openai.com/api-keys")

        if not config.pinecone_api_key or config.pinecone_api_key == "your_pinecone_api_key_here":
            raise ValueError("PINECONE_API_KEY is required. Get it from https://app.pinecone.io/")

        # PINECONE_ENV is now optional with the new Pinecone API
        # if not config.pinecone_env or config.pinecone_env == "your_pinecone_environment_here":
        #     raise ValueError("PINECONE_ENV is required. Find it in your Pinecone dashboard")

        # Validate numeric ranges
        if config.chunk_size <= 0:
            raise ValueError("CHUNK_SIZE must be positive")

        if config.chunk_overlap < 0:
            raise ValueError("CHUNK_OVERLAP must be non-negative")

        if config.retrieval_k <= 0:
            raise ValueError("RETRIEVAL_K must be positive")

        if not 0 <= config.llm_temperature <= 2:
            raise ValueError("LLM_TEMPERATURE must be between 0 and 2")

        if config.llm_max_tokens <= 0:
            raise ValueError("LLM_MAX_TOKENS must be positive")

        print("✅ Configuration validation passed")
        return True

    except Exception as e:
        print(f"❌ Configuration validation failed: {str(e)}")
        raise


def print_config_info():
    """Print configuration information (without sensitive data)."""
    try:
        config = get_config()

        print("\n🔧 RAG System Configuration:")
        print("=" * 50)
        print(f"Pinecone Environment: {config.pinecone_env}")
        print(f"Pinecone Index: {config.pinecone_index_name}")
        print(f"Chunk Size: {config.chunk_size}")
        print(f"Chunk Overlap: {config.chunk_overlap}")
        print(f"Retrieval K: {config.retrieval_k}")
        print(f"Embedding Model: {config.embedding_model}")
        print(f"LLM Model: {config.llm_model}")
        print(f"LLM Temperature: {config.llm_temperature}")
        print(f"LLM Max Tokens: {config.llm_max_tokens}")
        print(f"API Host: {config.api_host}")
        print(f"API Port: {config.api_port}")
        print(f"Log Level: {config.log_level}")
        print("=" * 50)

        # Mask API keys for display
        openai_key = config.openai_api_key[:10] + "..." if len(config.openai_api_key) > 10 else "***"
        pinecone_key = config.pinecone_api_key[:10] + "..." if len(config.pinecone_api_key) > 10 else "***"

        print(f"OpenAI API Key: {openai_key}")
        print(f"Pinecone API Key: {pinecone_key}")
        print("=" * 50)

    except Exception as e:
        print(f"❌ Error printing configuration: {str(e)}")


def create_env_template() -> str:
    """
    Create a template for the .env file.

    Returns:
        Template string for .env file
    """
    template = """# RAG System Environment Configuration
# Copy this file to .env and fill in your API keys

# =============================================================================
# Required API Keys
# =============================================================================

# OpenAI API Key (required)
# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# Pinecone API Key (required)
# Get from: https://app.pinecone.io/
PINECONE_API_KEY=your_pinecone_api_key_here

# Pinecone Environment (required)
# Find in your Pinecone dashboard (e.g., us-east-1-aws, us-west1-gcp)
PINECONE_ENV=your_pinecone_environment_here

# =============================================================================
# Pinecone Configuration (Optional)
# =============================================================================

# Pinecone Index Name (default: rag-index)
PINECONE_INDEX_NAME=rag-index

# =============================================================================
# Text Processing Configuration (Optional)
# =============================================================================

# Chunk size for text splitting (default: 1000)
CHUNK_SIZE=1000

# Chunk overlap for text splitting (default: 200)
CHUNK_OVERLAP=200

# Number of documents to retrieve for Q&A (default: 4)
RETRIEVAL_K=4

# =============================================================================
# Model Configuration (Optional)
# =============================================================================

# OpenAI Embedding Model (default: text-embedding-ada-002)
EMBEDDING_MODEL=text-embedding-ada-002

# OpenAI LLM Model (default: gpt-3.5-turbo)
LLM_MODEL=gpt-3.5-turbo

# LLM Temperature (default: 0.0)
LLM_TEMPERATURE=0.0

# Maximum tokens for LLM response (default: 500)
LLM_MAX_TOKENS=500

# =============================================================================
# API Configuration (Optional)
# =============================================================================

# API Server Host (default: 0.0.0.0)
API_HOST=0.0.0.0

# API Server Port (default: 8000)
API_PORT=8000

# Enable API reload in development (default: true)
API_RELOAD=true

# =============================================================================
# Logging Configuration (Optional)
# =============================================================================

# Log level (default: info)
# Options: debug, info, warning, error, critical
LOG_LEVEL=info

# =============================================================================
# Example Quick Start Configuration
# =============================================================================
# Uncomment and modify the following lines for a basic setup:

# OPENAI_API_KEY=sk-...
# PINECONE_API_KEY=...
# PINECONE_ENV=us-east-1-aws
# PINECONE_INDEX_NAME=my-rag-system
"""

    return template


if __name__ == "__main__":
    # Test configuration
    try:
        print("🔧 Testing RAG configuration...")

        # Print configuration info
        print_config_info()

        # Validate configuration
        validate_config()

        print("\n✅ Configuration test completed successfully!")

    except Exception as e:
        print(f"\n❌ Configuration test failed: {str(e)}")
        print("\n📝 Create a .env file with the following template:")
        print(create_env_template())

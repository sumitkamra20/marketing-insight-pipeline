# AI Agent for Marketing Insight Pipeline

This directory contains the AI agent functionality that provides intelligent data extraction and querying capabilities for the marketing insight pipeline.

## Features

- **LangGraph-powered AI Agent**: Uses LangGraph for orchestrating complex workflows
- **Snowflake Data Extraction**: Tools for querying and extracting data from Snowflake tables
- **RAG (Retrieval-Augmented Generation)**: Document upload and query capabilities
- **Interactive Chatbot**: User-friendly interface for natural language queries
- **RESTful API**: Programmatic access to agent capabilities

## Architecture

### Core Components

- `core/`: Main agent logic and LangGraph workflows
  - `tools/`: Snowflake data extraction tools
  - `workflows/`: LangGraph workflow definitions
  - `utils/`: Utility functions and helpers

- `rag/`: RAG functionality for document processing and retrieval

- `api/`: REST API endpoints for agent interaction

- `chatbot/`: Streamlit-based user interface

- `config/`: Configuration files for agent, database connections, and models

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure your environment:
   - Update configuration files in `config/`
   - Set up Snowflake credentials

3. Run the chatbot:
   ```bash
   streamlit run chatbot/streamlit_app.py
   ```

4. Or start the API server:
   ```bash
   uvicorn api.main:app --reload
   ```

## Available Tables

The agent can query the following tables from your marketing pipeline:
- `fct_customer_segments`: Customer segmentation data
- `fct_sales`: Sales transaction facts
- `dim_products`: Product dimension data
- `stg_bitcoin`: Bitcoin price streaming data
- `stg_news`: News data from streaming sources

## Usage Examples

- "Show me top 10 customers by revenue"
- "What are the sales trends for Q4?"
- "Analyze customer segments by location"
- "How does Bitcoin price correlate with news sentiment?"

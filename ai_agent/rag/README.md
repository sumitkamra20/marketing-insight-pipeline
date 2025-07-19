# PDF-Based RAG System 🔍

A complete Retrieval-Augmented Generation (RAG) system built with LangChain, Pinecone, and OpenAI. Upload PDF documents and ask questions about their content using natural language.

## 🌟 Features

- **PDF Upload & Processing**: Extract text from PDFs and chunk intelligently
- **Vector Search**: Store embeddings in Pinecone for fast similarity search
- **Question Answering**: Get accurate answers with source attribution
- **Conversational Mode**: Maintain context across multiple questions
- **REST API**: Complete FastAPI backend for integration
- **Web Interface**: User-friendly Streamlit app for testing
- **Configurable**: Flexible settings for chunking, retrieval, and models

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PDF Upload    │───▶│  Text Chunking   │───▶│   Embeddings    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Query    │───▶│  Vector Search   │◄───│   Pinecone DB   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │
         ▼                        ▼
┌─────────────────┐    ┌──────────────────┐
│   LLM Answer    │◄───│  Context + Query │
└─────────────────┘    └──────────────────┘
```

## 📦 Installation

### 1. Install Dependencies

```bash
# Install from the root directory
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the `ai_agent/rag/` directory:

```bash
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENV=your_pinecone_environment_here

# Optional Configuration
PINECONE_INDEX_NAME=rag-index
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
RETRIEVAL_K=4
```

#### Getting API Keys

1. **OpenAI API Key**:
   - Visit [OpenAI Platform](https://platform.openai.com/api-keys)
   - Create a new API key
   - Copy the key (starts with `sk-`)

2. **Pinecone API Key**:
   - Visit [Pinecone Console](https://app.pinecone.io/)
   - Create a free account
   - Find your API key in the dashboard
   - Note your environment (e.g., `us-east-1-aws`)

### 3. Verify Setup

Test your configuration:

```bash
python -m ai_agent.rag.config
```

## 🚀 Quick Start

### Option 1: Streamlit Interface (Recommended for Testing)

```bash
# From the project root directory
cd ai_agent/rag
streamlit run streamlit_app.py
```

Open your browser to `http://localhost:8501`

### Option 2: FastAPI Server

```bash
# From the project root directory
cd ai_agent/rag
python api.py
```

API documentation available at `http://localhost:8000/docs`

### Option 3: Python Code

```python
from ai_agent.rag.rag_service import create_rag_service

# Initialize RAG service
rag = create_rag_service(
    pinecone_api_key="your-key",
    pinecone_env="your-env",
    openai_api_key="your-key"
)

# Upload a PDF
result = rag.upload_pdf("document.pdf")
print(f"Uploaded: {result['message']}")

# Ask a question
response = rag.ask_question("What is this document about?")
print(f"Answer: {response['answer']}")
```

## 📖 Usage Guide

### PDF Upload

The system accepts PDF files and processes them automatically:

1. **Text Extraction**: Uses PyPDF2 to extract text from all pages
2. **Chunking**: Splits text into overlapping chunks for better context
3. **Embedding**: Generates OpenAI embeddings for each chunk
4. **Storage**: Stores vectors in Pinecone with metadata

```python
# Upload from file path
result = rag.upload_pdf("path/to/document.pdf")

# Upload from bytes (useful for web uploads)
with open("document.pdf", "rb") as f:
    result = rag.upload_pdf_from_bytes(f.read(), "document.pdf")
```

### Question Answering

Ask questions in natural language:

```python
# Simple Q&A
response = rag.ask_question("What are the main topics covered?")

# Conversational mode (maintains history)
response = rag.ask_question(
    "What is machine learning?",
    conversational=True
)
response = rag.ask_question(
    "How does it relate to AI?",  # References previous context
    conversational=True
)

# With namespace organization
response = rag.ask_question(
    "Summarize the key findings",
    namespace="research-papers"
)
```

### Document Search

Search for relevant chunks without generating answers:

```python
results = rag.search_documents(
    query="machine learning algorithms",
    k=5  # Number of results
)

for result in results:
    print(f"Source: {result['source']}")
    print(f"Content: {result['content'][:200]}...")
    print(f"Score: {result['similarity_score']}")
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ | - | OpenAI API key |
| `PINECONE_API_KEY` | ✅ | - | Pinecone API key |
| `PINECONE_ENV` | ✅ | - | Pinecone environment |
| `PINECONE_INDEX_NAME` | ❌ | `rag-index` | Index name |
| `CHUNK_SIZE` | ❌ | `1000` | Text chunk size |
| `CHUNK_OVERLAP` | ❌ | `200` | Chunk overlap |
| `RETRIEVAL_K` | ❌ | `4` | Documents to retrieve |
| `EMBEDDING_MODEL` | ❌ | `text-embedding-ada-002` | Embedding model |
| `LLM_MODEL` | ❌ | `gpt-3.5-turbo` | Language model |

### Advanced Configuration

```python
# Custom chunking strategy
rag = create_rag_service(
    pinecone_api_key="...",
    pinecone_env="...",
    openai_api_key="...",
    chunk_size=1500,          # Larger chunks
    chunk_overlap=300,        # More overlap
    retrieval_k=6            # More context
)

# Different models
rag = create_rag_service(
    pinecone_api_key="...",
    pinecone_env="...",
    openai_api_key="...",
    embedding_model="text-embedding-ada-002",
    llm_model="gpt-4"        # More powerful model
)
```

## 🌐 API Reference

### FastAPI Endpoints

#### Upload PDF
```http
POST /upload
Content-Type: multipart/form-data

Body:
- file: PDF file
- namespace: string (optional)
```

#### Ask Question
```http
POST /ask
Content-Type: application/json

{
  "question": "What is this document about?",
  "namespace": "",
  "conversational": false,
  "return_sources": true
}
```

#### Search Documents
```http
POST /search
Content-Type: application/json

{
  "query": "machine learning",
  "k": 5,
  "namespace": ""
}
```

#### Health Check
```http
GET /health
```

#### Get Index Stats
```http
GET /index/stats
```

### Example API Usage

```python
import requests

# Upload PDF
with open("document.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/upload",
        files={"file": f}
    )

# Ask question
response = requests.post(
    "http://localhost:8000/ask",
    json={"question": "What is the main topic?"}
)
answer = response.json()
```

## 🏃‍♂️ Performance Tips

### Chunking Strategy
- **Smaller chunks** (500-800): Better for specific facts
- **Larger chunks** (1200-1500): Better for context and summaries
- **Higher overlap** (200-400): Better continuity, more storage

### Retrieval Settings
- **More documents** (k=6-10): More context, slower responses
- **Fewer documents** (k=2-4): Faster, more focused answers

### Model Selection
- **gpt-3.5-turbo**: Fast, cost-effective
- **gpt-4**: Higher quality, more expensive
- **text-embedding-ada-002**: Standard embeddings

## 🔍 Troubleshooting

### Common Issues

#### 1. Configuration Errors
```bash
# Check configuration
python -m ai_agent.rag.config

# Validate API keys
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

#### 2. Pinecone Connection Issues
- Verify your environment name matches Pinecone dashboard
- Check API key permissions
- Ensure index name is valid (lowercase, no spaces)

#### 3. PDF Processing Errors
- Ensure PDF is not password-protected
- Check file size (large PDFs may timeout)
- Verify PDF contains extractable text (not just images)

#### 4. Memory Issues
- Reduce chunk size for large documents
- Process PDFs in smaller batches
- Monitor Pinecone index capacity

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable
export LOG_LEVEL=debug
```

## 🛠️ Development

### Project Structure

```
ai_agent/rag/
├── __init__.py
├── README.md
├── config.py              # Configuration management
├── pdf_processor.py       # PDF text extraction & chunking
├── vector_store.py        # Pinecone operations
├── qa_chain.py           # LangChain Q&A logic
├── rag_service.py        # Main orchestration service
├── api.py                # FastAPI application
└── streamlit_app.py      # Streamlit interface

Note: Dependencies are managed in the root requirements.txt file
```

### Adding New Features

1. **Custom PDF Processors**: Extend `PDFProcessor` class
2. **Alternative Vector Stores**: Implement vector store interface
3. **Different LLMs**: Modify `qa_chain.py` for other providers
4. **New Endpoints**: Add routes to `api.py`

### Testing

```bash
# Test configuration
python -m ai_agent.rag.config

# Test individual components
python -m ai_agent.rag.pdf_processor
python -m ai_agent.rag.vector_store
python -m ai_agent.rag.qa_chain
```

## 💰 Cost Estimation

### OpenAI Costs (Approximate)
- **Embeddings**: $0.0001 per 1K tokens
- **GPT-3.5-turbo**: $0.002 per 1K tokens
- **GPT-4**: $0.03 per 1K tokens

### Pinecone Costs
- **Free tier**: 1 index, 1M vectors, 5GB storage
- **Paid tiers**: Start at $70/month for production

### Example Usage Costs
- 100-page PDF: ~$0.50 in embeddings
- 1000 questions: ~$2-10 depending on model
- Monthly operation: ~$20-100 for moderate usage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is part of the larger marketing insight pipeline. See the main repository for license information.

## 🆘 Support

For issues and questions:
1. Check this README first
2. Review the troubleshooting section
3. Check Streamlit app for configuration errors
4. Open an issue in the main repository

---

**Happy RAG-ing!** 🚀

# 🤖 Marketing Insight Chatbot

An integrated Streamlit chatbot that combines data querying (Snowflake) and document processing (RAG) capabilities in a single, intuitive interface.

## 🌟 Features

- **📊 Data Querying**: Ask questions about your Snowflake data (sales, customers, products, Bitcoin prices)
- **📄 Document Processing**: Upload PDFs and ask questions about their content
- **🔄 Mode Switching**: Simple selector to switch between data and document modes
- **💬 Conversational Interface**: Maintains context for follow-up questions
- **📁 Document Management**: Upload, organize, and manage PDF documents
- **🎨 Beautiful UI**: Modern, responsive interface with custom styling

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd ai_agent/chatbot
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in your project root with:

```bash
# OpenAI (required for both features)
OPENAI_API_KEY=your_openai_api_key

# For Data Querying (Snowflake)
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema

# For Document Processing (RAG)
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENV=your_pinecone_environment
PINECONE_INDEX_NAME=rag-index  # optional
```

### 3. Launch the Chatbot

**Option A: Using the launcher script**
```bash
python run_chatbot.py
```

**Option B: Direct Streamlit command**
```bash
streamlit run integrated_chatbot.py
```

## 🎯 Usage

### Data Querying Mode 📊

Select "📊 Talk to Data" to query your Snowflake database:

- **Sales Analytics**: "What were total sales last month?"
- **Customer Insights**: "Show me customer segments and their characteristics"
- **Product Analysis**: "What's the average order value by product category?"
- **Real-time Data**: "What's the current Bitcoin price?"

### Document Processing Mode 📄

Select "📄 Talk to Documents" to work with PDF documents:

1. **Upload PDFs**: Use the sidebar to upload one or more PDF files
2. **Ask Questions**: "What is this document about?", "Summarize the key findings"
3. **Get Sourced Answers**: Responses include source document references

### Features

- **Mode Switching**: Use the sidebar dropdown to switch between data and document modes
- **File Management**: Upload multiple PDFs at once with progress tracking
- **Namespaces**: Organize documents using namespaces for better organization
- **Chat History**: Maintains conversation context within each session
- **Example Queries**: Click on suggested examples to get started
- **Error Handling**: Graceful handling of configuration and runtime errors

## 🏗️ Architecture

```
┌─────────────────────┐    ┌─────────────────────┐
│   Streamlit UI      │    │   Mode Selection    │
└─────────────────────┘    └─────────────────────┘
           │                           │
           ▼                           ▼
┌─────────────────────┐    ┌─────────────────────┐
│  Data Agent Mode    │    │   RAG Service Mode  │
│  (LangGraph +       │    │   (LangChain +      │
│   Snowflake)        │    │    Pinecone)        │
└─────────────────────┘    └─────────────────────┘
           │                           │
           ▼                           ▼
┌─────────────────────┐    ┌─────────────────────┐
│   Snowflake DB      │    │   Vector Store      │
│   (Sales, Customer, │    │   (PDF Embeddings)  │
│    Product Data)    │    │                     │
└─────────────────────┘    └─────────────────────┘
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ | - | OpenAI API key for LLM |
| `SNOWFLAKE_USER` | ✅* | - | Snowflake username |
| `SNOWFLAKE_PASSWORD` | ✅* | - | Snowflake password |
| `SNOWFLAKE_ACCOUNT` | ✅* | - | Snowflake account identifier |
| `SNOWFLAKE_WAREHOUSE` | ✅* | - | Snowflake warehouse |
| `SNOWFLAKE_DATABASE` | ✅* | - | Snowflake database |
| `SNOWFLAKE_SCHEMA` | ✅* | - | Snowflake schema |
| `PINECONE_API_KEY` | ✅** | - | Pinecone API key |
| `PINECONE_ENV` | ✅** | - | Pinecone environment |
| `PINECONE_INDEX_NAME` | ❌ | `rag-index` | Pinecone index name |

*Required for data querying functionality
**Required for document processing functionality

### Graceful Degradation

The chatbot is designed to work even if only one service is configured:

- **Data Only**: If only Snowflake is configured, only data querying will be available
- **Documents Only**: If only Pinecone is configured, only document processing will be available
- **Both**: If both are configured, you can switch between modes seamlessly

## 🛠️ Development

### Project Structure

```
ai_agent/chatbot/
├── integrated_chatbot.py    # Main Streamlit application
├── run_chatbot.py          # Launcher script
├── requirements.txt        # Dependencies
└── README.md              # This file
```

### Adding New Features

1. **New Data Sources**: Extend the `DataExtractionAgent` in `ai_agent/core/`
2. **New Document Types**: Extend the `PDFProcessor` in `ai_agent/rag/`
3. **UI Enhancements**: Modify `integrated_chatbot.py`

## 🤝 Support

For issues or questions:

1. Check the configuration in the sidebar
2. Review environment variable setup
3. Check logs in the terminal where you launched the chatbot

## 📝 Notes

- The chatbot maintains separate conversation histories for data and document modes
- Document uploads are processed in real-time with progress tracking
- All chat history is session-based and cleared when you restart the application
- The application uses caching for better performance

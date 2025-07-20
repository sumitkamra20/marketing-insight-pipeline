FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY ai_agent/chatbot/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install additional cloud dependencies
RUN pip install --no-cache-dir google-cloud-firestore google-cloud-storage

# Copy the entire ai_agent module
COPY ai_agent/ ./ai_agent/

# Create data directory for any local files
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Expose the port
EXPOSE 8501

# Health check for Cloud Run
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the Streamlit app
CMD ["streamlit", "run", "ai_agent/chatbot/integrated_chatbot.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]

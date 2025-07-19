"""
Integrated Marketing Insight Chatbot

A unified Streamlit application that combines data querying (Snowflake)
and document processing (RAG) capabilities in a single interface.

Usage:
    # Run the chatbot
    python -m ai_agent.chatbot.run_chatbot

    # Or directly with Streamlit
    streamlit run ai_agent/chatbot/integrated_chatbot.py
"""

__version__ = "1.0.0"
__author__ = "Marketing Insight Pipeline Team"

# Import main components for programmatic access
try:
    from .integrated_chatbot import main as run_chatbot_app
except ImportError:
    # Graceful handling if dependencies aren't installed
    def run_chatbot_app():
        print("❌ Chatbot dependencies not installed. Please run: pip install -r ai_agent/chatbot/requirements.txt")

__all__ = ["run_chatbot_app"]

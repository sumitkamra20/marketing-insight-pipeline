#!/usr/bin/env python3
"""
Launcher script for the Integrated Marketing Insight Chatbot
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Launch the integrated chatbot using Streamlit."""

    # Get the current script directory
    current_dir = Path(__file__).parent
    chatbot_script = current_dir / "integrated_chatbot.py"

    # Check if the chatbot script exists
    if not chatbot_script.exists():
        print(f"❌ Error: {chatbot_script} not found!")
        sys.exit(1)

    # Print startup message
    print("🚀 Starting Marketing Insight Chatbot...")
    print(f"📁 Script location: {chatbot_script}")
    print("🌐 Opening in your default browser...")
    print("\nTo stop the application, press Ctrl+C in this terminal\n")

    # Launch Streamlit
    try:
        cmd = [
            sys.executable, "-m", "streamlit", "run",
            str(chatbot_script),
            "--server.headless", "false",
            "--browser.gatherUsageStats", "false"
        ]

        subprocess.run(cmd, check=True)

    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching Streamlit: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n✅ Chatbot stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    main()

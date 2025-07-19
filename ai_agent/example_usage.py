#!/usr/bin/env python3
"""
Example Usage of the Data Extraction Agent
Demonstrates how to use the LangGraph agent for querying Snowflake data
"""

import os
import sys
from dotenv import load_dotenv

# Add the ai_agent directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.workflows.data_extraction import create_data_extraction_agent
from core.tools.query_tool import test_snowflake_connection


def main():
    """Example usage of the data extraction agent"""

    # Load environment variables from root directory
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(root_dir, '.env')
    load_dotenv(env_path)

    print("=== Marketing Insight Pipeline - AI Agent Demo ===\n")

    # Test Snowflake connection first
    print("1. Testing Snowflake connection...")
    try:
        connection_result = test_snowflake_connection.invoke({})
        print(f"   {connection_result}\n")
    except Exception as e:
        print(f"   Connection test failed: {e}")
        print("   Please check your Snowflake configuration and try again.\n")
        return

    # Create the agent with memory enabled
    print("2. Initializing Data Extraction Agent (with memory)...")
    try:
        agent = create_data_extraction_agent(enable_memory=True)
        print("   Agent initialized successfully with SQLite memory!\n")
    except Exception as e:
        print(f"   Agent initialization failed: {e}")
        print("   Please check your OpenAI API key and try again.\n")
        return

    # Example queries
    example_queries = [
        "What are the available tables and their schemas?",
        "Show me the total net sales by month",
        "What's the average discount percentage across all sales?",
        "Which sale size categories generate the most revenue?",
        "How many unique customers do we have in each segment?"
    ]

    # Demonstrate memory functionality first
    print("3. Memory Demonstration:")
    import uuid
    session_id = str(uuid.uuid4())

    print(f"\n--- Memory Test (Session: {session_id[:8]}...) ---")
    print("Establishing context...")
    memory_query1 = "Hi, I'm Sarah from the marketing team and I'm analyzing Q4 performance."
    print(f"User: {memory_query1}")
    try:
        response1 = agent.process_query(memory_query1, session_id=session_id)
        print(f"Agent: {response1}")
    except Exception as e:
        print(f"Error: {e}")

    print(f"\nTesting memory recall...")
    memory_query2 = "What's my name and what am I working on?"
    print(f"User: {memory_query2}")
    try:
        response2 = agent.process_query(memory_query2, session_id=session_id)
        print(f"Agent: {response2}")

        if "Sarah" in response2:
            print("✅ Memory working - agent remembered the name!")
        else:
            print("⚠️  Memory may not be working as expected")
    except Exception as e:
        print(f"Error: {e}")

    input("\nPress Enter to continue to data queries...")

    print("\n4. Data Query Examples:")

    for i, query in enumerate(example_queries, 1):
        print(f"\n--- Query {i}: {query} ---")
        try:
            # Use the same session to maintain conversation context
            response = agent.process_query(query, session_id=session_id)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error processing query: {e}")

        # Add a pause between queries for better readability
        if i < len(example_queries):
            input("\nPress Enter to continue to the next query...")

    print("\n=== Demo Complete ===")
    print("Key features demonstrated:")
    print("• SQLite-based session memory (isolated per session)")
    print("• Context persistence within the same session")
    print("• Data extraction and analysis capabilities")
    print("• Session isolation (new sessions = fresh memory)")
    print("\nYou can now use the agent interactively or integrate it into your applications!")


def interactive_mode():
    """Interactive mode for testing queries"""

    # Load environment variables from root directory
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(root_dir, '.env')
    load_dotenv(env_path)

    print("=== Interactive Data Extraction Agent ===")
    print("Type 'quit' to exit, 'help' for available commands\n")

    try:
        agent = create_data_extraction_agent(enable_memory=True)
        print("Agent ready with memory! Ask me anything about your marketing data.")
        print("Your conversation will be remembered within this session.\n")

        # Generate unique session ID for this interactive session
        import uuid
        session_id = str(uuid.uuid4())
        print(f"Session ID: {session_id[:8]}...\n")

    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        return

    while True:
        try:
            user_input = input("You: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            if user_input.lower() == 'help':
                print("\nAvailable commands:")
                print("- Ask questions about sales data: 'What are total sales for last month?'")
                print("- Query customer segments: 'Show me customer segments by revenue'")
                print("- Get schema info: 'What tables are available?'")
                print("- Type 'quit' to exit")
                print()
                continue

            if not user_input:
                continue

            print("\nAgent: ", end="")
            # Use consistent session_id for the interactive session
            response = agent.process_query(user_input, session_id=session_id)
            print(f"{response}\n")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    # Check if interactive mode is requested
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        main()

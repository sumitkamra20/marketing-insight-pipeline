"""
LangGraph Workflow for Data Extraction
Orchestrates data retrieval tools to answer user queries about sales and customer data
"""

from typing import TypedDict, Annotated, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
import logging
import uuid
from pathlib import Path
from datetime import datetime

from ..tools.query_tool import (
    run_sales_query,
    run_generic_query,
    get_table_schema_info,
    test_snowflake_connection
)

# Configure logging
logger = logging.getLogger(__name__)

# Define the state for our agent
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_query: str
    extracted_data: str
    analysis_complete: bool


class DataExtractionAgent:
    """LangGraph agent for data extraction and analysis with optional memory"""

    def __init__(self, llm_model: str = "gpt-4-turbo-preview", enable_memory: bool = True):
        """
        Initialize the data extraction agent

        Args:
            llm_model: OpenAI model to use for the agent
            enable_memory: Whether to enable conversation memory using SQLite
        """
        self.llm = ChatOpenAI(model=llm_model, temperature=0)
        self.enable_memory = enable_memory

        # Available tools
        self.tools = [
            run_sales_query,
            run_generic_query,
            get_table_schema_info,
            test_snowflake_connection
        ]

        # Tool node
        self.tool_node = ToolNode(self.tools)

        # Create the agent with tools - system prompt will be added in agent node
        self.system_prompt = """You are a data analysis assistant for the Marketing Insight Pipeline.
You can help users query and analyze data from the following tables:

- fct_sales: Sales transaction data with metrics like total sales, quantities, discounts
- fct_customer_segments: Customer segmentation data with ML-driven insights
- dim_products: Product dimension data with categories and tax information
- stg_bitcoin: Bitcoin price streaming data

You can answer questions about total sales, sales by category, customer segments, average discounts, etc.
Remember the user's name and preferences throughout the conversation."""

        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Build the workflow graph
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow with optional SQLite checkpointing"""

        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", self.tool_node)

        # Set entry point
        workflow.set_entry_point("agent")

        # Add edges
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )
        workflow.add_edge("tools", "agent")

        # Setup checkpointer (SQLite or Cloud) if memory is enabled
        checkpointer = None
        if self.enable_memory:
            # Try cloud memory first (for GCP deployment)
            try:
                from ..utils.cloud_memory import get_cloud_memory
                cloud_memory = get_cloud_memory()

                if cloud_memory and cloud_memory.is_available():
                    # Use a simple in-memory checkpointer for cloud deployment
                    # since Firestore will handle persistence through our custom logic
                    from langgraph.checkpoint.memory import MemorySaver
                    checkpointer = MemorySaver()
                    logger.info("Cloud memory available - using MemorySaver with Firestore persistence")
                else:
                    raise Exception("Cloud memory not available, falling back to SQLite")

            except Exception as e:
                logger.info(f"Cloud memory not available ({e}), trying SQLite...")

                # Fallback to SQLite for local development
                try:
                    from langgraph.checkpoint.sqlite import SqliteSaver

                    # Create data directory if it doesn't exist
                    data_dir = Path(__file__).parent.parent.parent / "data"
                    data_dir.mkdir(parents=True, exist_ok=True)

                    # Simple SQLite checkpointer setup with absolute path
                    db_file = data_dir / "agent_memory.db"

                    # Create checkpointer using direct constructor
                    import sqlite3
                    conn = sqlite3.connect(str(db_file), check_same_thread=False)
                    checkpointer = SqliteSaver(conn)
                    checkpointer.setup()  # Initialize database tables
                    logger.info(f"SQLite checkpointer enabled: {db_file}")

                except ImportError:
                    logger.warning("langgraph.checkpoint.sqlite not available, memory disabled")
                except Exception as e:
                    logger.warning(f"Failed to setup SQLite checkpointer: {e}")

        return workflow.compile(checkpointer=checkpointer)

    def _agent_node(self, state: AgentState) -> AgentState:
        """
        Agent node that processes user queries and decides on tool usage
        """
        messages = state["messages"]

        # Add system prompt if not already present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=self.system_prompt)] + messages

        # Get response from LLM
        response = self.llm_with_tools.invoke(messages)

        return {
            **state,
            "messages": state["messages"] + [response]
        }

    def _should_continue(self, state: AgentState) -> str:
        """
        Determine whether to continue with tool execution or end
        """
        messages = state["messages"]
        last_message = messages[-1]

        # If the last message has tool calls, continue to tools
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "continue"
        else:
            return "end"

    def process_query(self, user_query: str, session_id: Optional[str] = None, clear_session: bool = False) -> str:
        """
        Process a user query and return the response

        Args:
            user_query: User's question about the data
            session_id: Optional session ID for memory isolation. If None, generates new UUID for session isolation.
            clear_session: If True, clears existing memory for this session before processing

        Returns:
            Agent's response with data insights
        """
        try:
            # Generate unique session ID for memory isolation (don't persist across sessions)
            if session_id is None:
                session_id = str(uuid.uuid4())
                logger.info(f"Generated new session ID: {session_id[:8]}...")
            else:
                logger.info(f"Using provided session ID: {session_id[:8]}...")

            # Clear session memory if requested (to prevent cross-session bleeding)
            if clear_session and self.enable_memory:
                self.clear_session_memory(session_id)
                logger.info(f"Cleared memory for session: {session_id[:8]}...")

            # Load previous session if using cloud memory
            if self.enable_memory:
                from ..utils.cloud_memory import get_cloud_memory
                cloud_memory = get_cloud_memory()
                if cloud_memory and cloud_memory.is_available():
                    # Load previous session from Firestore
                    previous_session = cloud_memory.load_session(session_id)
                    if previous_session:
                        logger.info(f"Loaded previous session from cloud: {session_id[:8]}...")

            # Initialize state
            initial_state = {
                "messages": [HumanMessage(content=user_query)],
                "user_query": user_query,
                "extracted_data": "",
                "analysis_complete": False
            }

            # Prepare config for memory (only if enabled)
            config = {"configurable": {"thread_id": session_id}} if self.enable_memory else {}
            if self.enable_memory:
                logger.info(f"Memory enabled - using session: {session_id[:8]}...")

            # Run the workflow
            result = self.workflow.invoke(initial_state, config=config)

            # Save session to cloud memory if available
            if self.enable_memory:
                from ..utils.cloud_memory import get_cloud_memory
                cloud_memory = get_cloud_memory()
                if cloud_memory and cloud_memory.is_available():
                    # Extract messages for cloud storage
                    messages = result.get("messages", [])
                    message_data = []
                    for msg in messages:
                        if hasattr(msg, 'content'):
                            message_data.append({
                                "type": type(msg).__name__,
                                "content": str(msg.content),
                                "timestamp": datetime.now().isoformat()
                            })

                    # Save to Firestore
                    cloud_memory.save_session(
                        session_id=session_id,
                        messages=message_data,
                        metadata={"query": user_query, "mode": "data_extraction"}
                    )

            # Extract the final response
            final_messages = result["messages"]

            # Find the last AI message that's not a tool execution result
            for message in reversed(final_messages):
                if isinstance(message, AIMessage) and not message.content.startswith("Tool execution results:"):
                    return message.content

            return "I was unable to process your query. Please try rephrasing your question."

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return f"Sorry, I encountered an error while processing your query: {str(e)}"

    def clear_session_memory(self, session_id: str) -> bool:
        """
        Clear memory for a specific session to prevent cross-session bleeding

        Args:
            session_id: Session ID to clear memory for

        Returns:
            True if successful, False otherwise
        """
        if not self.enable_memory:
            return False

        try:
            # Get the checkpointer from the workflow
            checkpointer = self.workflow.checkpointer
            if checkpointer and hasattr(checkpointer, 'delete_thread'):
                checkpointer.delete_thread(session_id)
                logger.info(f"Cleared memory for session: {session_id[:8]}...")
                return True
        except Exception as e:
            logger.warning(f"Could not clear session memory: {e}")

        return False

    def get_available_tables(self) -> str:
        """
        Get information about available tables and their schemas
        """
        tables = ["fct_sales", "fct_customer_segments", "dim_products", "stg_bitcoin"]
        schema_info = []

        for table in tables:
            try:
                info = get_table_schema_info.invoke({"table_name": table})
                schema_info.append(info)
            except Exception as e:
                schema_info.append(f"Error getting schema for {table}: {str(e)}")

        return "\n\n".join(schema_info)


def create_data_extraction_agent(llm_model: str = "gpt-4-turbo-preview", enable_memory: bool = True) -> DataExtractionAgent:
    """
    Factory function to create a DataExtractionAgent

    Args:
        llm_model: OpenAI model to use
        enable_memory: Whether to enable SQLite-based conversation memory

    Returns:
        DataExtractionAgent instance
    """
    return DataExtractionAgent(llm_model, enable_memory)

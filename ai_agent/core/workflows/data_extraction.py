"""
LangGraph Workflow for Data Extraction
Orchestrates data retrieval tools to answer user queries about sales and customer data
"""

from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
import logging

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
    """LangGraph agent for data extraction and analysis"""

    def __init__(self, llm_model: str = "gpt-4-turbo-preview"):
        """
        Initialize the data extraction agent

        Args:
            llm_model: OpenAI model to use for the agent
        """
        self.llm = ChatOpenAI(model=llm_model, temperature=0)

        # Available tools
        self.tools = [
            run_sales_query,
            run_generic_query,
            get_table_schema_info,
            test_snowflake_connection
        ]

        # Tool node
        self.tool_node = ToolNode(self.tools)

        # Create the agent with tools
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Build the workflow graph
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""

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

        return workflow.compile()

    def _agent_node(self, state: AgentState) -> AgentState:
        """
        Agent node that processes user queries and decides on tool usage
        """
        messages = state["messages"]

        # Add system message if this is the first interaction
        if len(messages) == 1 and isinstance(messages[0], HumanMessage):
            system_message = AIMessage(content="""I am a data analysis assistant for the Marketing Insight Pipeline.
            I can help you query and analyze data from the following tables:

                        - fct_sales: Sales transaction data with metrics like total sales, quantities, discounts
            - fct_customer_segments: Customer segmentation data with ML-driven insights
            - dim_products: Product dimension data with categories and tax information
            - stg_bitcoin: Bitcoin price streaming data

            I can answer questions like:
            - "What are the total sales for last month?"
            - "Show me sales by product category"
            - "Which customer segments have the highest revenue?"
            - "What's the average discount percentage?"

            What would you like to analyze?""")

            messages = [system_message] + messages

        # Get response from LLM
        response = self.llm_with_tools.invoke(messages)

        return {
            **state,
            "messages": messages + [response]
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

    def process_query(self, user_query: str) -> str:
        """
        Process a user query and return the response

        Args:
            user_query: User's question about the data

        Returns:
            Agent's response with data insights
        """
        try:
            # Initialize state
            initial_state = {
                "messages": [HumanMessage(content=user_query)],
                "user_query": user_query,
                "extracted_data": "",
                "analysis_complete": False
            }

            # Run the workflow
            result = self.workflow.invoke(initial_state)

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


def create_data_extraction_agent(llm_model: str = "gpt-4-turbo-preview") -> DataExtractionAgent:
    """
    Factory function to create a DataExtractionAgent

    Args:
        llm_model: OpenAI model to use

    Returns:
        DataExtractionAgent instance
    """
    return DataExtractionAgent(llm_model)

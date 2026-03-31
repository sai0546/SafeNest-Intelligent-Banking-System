"""
Agentic transaction wrapper for the V6 UI.
"""

from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate

from agents.tools.transaction_tools import TRANSACTION_TOOLS
from llm.groq_client import get_agent_llm

TRANSACTION_AGENT_PROMPT = """You are a transaction specialist at SafeNest bank. You help customers understand their transaction status.

You have access to these tools:
{tools}

Use the following format:

Question: the transaction inquiry
Thought: think about what information to look up
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: a clear explanation of the transaction status

APPROACH:
1. If asking about blocked/failed transactions, use get_blocked_transactions first
2. If asking about a specific transaction, use lookup_transaction
3. Use explain_block_reason to translate technical codes into customer-friendly explanations
4. Always provide actionable next steps

Begin!

Question: {input}
Thought: {agent_scratchpad}"""


def _create_agent():
    prompt = PromptTemplate(
        template=TRANSACTION_AGENT_PROMPT,
        input_variables=["input", "agent_scratchpad"],
        partial_variables={
            "tools": "\n".join([f"{tool.name}: {tool.description}" for tool in TRANSACTION_TOOLS]),
            "tool_names": ", ".join([tool.name for tool in TRANSACTION_TOOLS]),
        },
    )
    agent = create_react_agent(llm=get_agent_llm(), tools=TRANSACTION_TOOLS, prompt=prompt)
    return AgentExecutor(
        agent=agent,
        tools=TRANSACTION_TOOLS,
        verbose=False,
        max_iterations=8,
        handle_parsing_errors=True,
    )


def explain_transaction(customer_id: int, query: str = "Why was my transaction blocked?") -> str:
    try:
        result = _create_agent().invoke({"input": f"Customer ID: {customer_id}\nQuestion: {query}"})
        return result["output"]
    except Exception as e:
        return f"Error looking up transaction: {str(e)}"
